import argparse, json, os, hashlib, re
from pathlib import Path
from neo4j import GraphDatabase

# label mapping for node types
LABEL_MAP = {
    "medical_condition": "MedicalCondition",
    "medication": "Medication",
    "treatment_type": "Treatment",
    "outcome": "Outcome",
    "measure": "Measure",
    "patient_group": "PatientGroup",
    "study": "Study",
}

def title_case(s): return s[:1].upper() + s[1:].lower() if s else "EntityType"
def sanitize_rel_type(raw):
    if not raw: raw = "related_to"
    raw = raw.lower().replace(" ", "_")
    return re.sub(r"[^a-zA-Z0-9_]+", "_", raw).upper()

def clean_props(d):
    return {k: v for k, v in d.items() if v not in (None, "", [], {}) and k != "id"}

def load_json_any_shape(p):
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        ents = data.get("entities") or []
        rels = data.get("relationships") or []
        return ents, rels
    return [], []

def canonical_entity(e):
    e_id = e.get("id") or e.get("uid") or e.get("node_id")
    e_text = e.get("text") or e.get("name") or e.get("label")
    e_type = (e.get("type") or e.get("category") or "entitytype").lower()
    dyn_label = LABEL_MAP.get(e_type) or title_case(e_type)
    props = clean_props(e.copy())
    return {"sourceId": e_id, "text": e_text, "etype_lower": e_type, "dynLabel": dyn_label, "props": props}

def canonical_rel(r):
    head = r.get("head") or r.get("source") or r.get("from")
    tail = r.get("tail") or r.get("target") or r.get("to")
    rtype = r.get("type") or r.get("relation") or "related_to"
    ev = r.get("evidence")
    rel_type = sanitize_rel_type(rtype)
    ev_hash = hashlib.md5((str(ev) if ev else "").encode()).hexdigest()
    rel_key = f"{head}|{rel_type}|{tail}|{ev_hash}"
    return {"head": head, "tail": tail, "relType": rel_type, "evidence": ev, "raw": clean_props(r.copy()), "relKey": rel_key}

CYPHER_ENTITIES = """
UNWIND $rows AS row
WITH row WHERE row.sourceId IS NOT NULL
MERGE (n:Entity {sourceId: row.sourceId})
ON CREATE SET n.createdAt = datetime()
SET n.updatedAt = datetime(),
    n.text = coalesce(row.text, n.text),
    n.type = row.etype_lower
// add/refresh discovered properties (sans sourceId)
SET n += row.props
WITH n, row
CALL apoc.create.addLabels(n, [row.dynLabel]) YIELD node
RETURN count(*) AS upserted;
"""


CYPHER_RELS = """
UNWIND $rows AS r
MATCH (h:Entity {sourceId: r.head})
MATCH (t:Entity {sourceId: r.tail})
MERGE (idx:RelIndex {key: r.relKey})
ON CREATE SET idx.createdAt = datetime(), idx.relType = r.relType
WITH h,t,r,idx,idx.createdAt IS NOT NULL AS isNew
CALL apoc.do.when(
  isNew,
  "CALL apoc.create.relationship($h, $type, {evidence:$ev}, $t) YIELD rel RETURN rel",
  "RETURN null AS rel",
  {h:h,t:t,type:r.relType,ev:r.evidence}
) YIELD value
RETURN count(*) AS created;
"""


def chunked(it, size=500):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf)>=size:
            yield buf; buf=[]
    if buf: yield buf

def ingest(uri,user,pwd,files):
    driver = GraphDatabase.driver(uri,auth=(user,pwd))
    total_nodes=total_rels=0
    with driver.session() as sess:
        entities,rels=[],[]
        for f in files:
            e_list,r_list = load_json_any_shape(Path(f))
            entities += [canonical_entity(e) for e in e_list]
            rels += [canonical_rel(r) for r in r_list]
        for batch in chunked(entities,500):
            res=sess.run(CYPHER_ENTITIES,rows=batch).single()
            total_nodes+=res["upserted"]
        for batch in chunked(rels,500):
            res=sess.run(CYPHER_RELS,rows=batch).single()
            total_rels+=res["created"]
    driver.close()
    print(f"✅ Upserted nodes: {total_nodes}, New relationships: {total_rels}")

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--uri",required=True)
    ap.add_argument("--user",required=True)
    ap.add_argument("--password",required=True)
    ap.add_argument("files",nargs="+",help="JSON files or folder path")
    args=ap.parse_args()
    all_files=[]
    for p in args.files:
        P=Path(p)
        if P.is_dir():
            all_files += [str(x) for x in P.glob("*.json")]
        else:
            all_files.append(str(P))
    ingest(args.uri,args.user,args.password,all_files)

if __name__=="__main__":
    main()
