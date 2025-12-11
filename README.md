# Brightside_Health_Team1A
### 👥 **Team Members**
| Name             | GitHub Handle | Contribution                                                             |
|------------------|---------------|--------------------------------------------------------------------------|
| Aline Jouaidi    | @Alinejj      | Generated the finalized JSON output                                      |
| Sahithi          | @             |                                                                          |
| Edwin            | @             |                                                                          |
| Krrish           | @             |                                                                          |
| Tiffany          | @             |                                                                          |

---

## 🎯 **Project Highlights**
* Developed a machine learning model using Chatgpt 4o to help clinicians with decision making prescriptions for depression and anxiety.
* Achieved `[key metric or result]`, demonstrating `[value or impact]` for `[host company]`.
* Generated actionable insights to inform business decisions at `[host company or stakeholders]`.
* Implemented `[specific methodology]` to address industry constraints or expectations.

---

## 👩🏽‍💻 **Setup and Installation**
1. Copy `.env.example` → `.env`
2. Open `.env` and paste your real OpenAI key:
3. 3. Run `python test_env.py` to check the key is loaded


To run: `docker compose up --build -d neo4j`
To run Graph generator: `docker compose -f 'docker-compose.yml' up -d --build 'loader'`
Go to: http://localhost:7474/browser/
Run `docker compose down` to stop contianers from running

---

## 🏗️ **Project Overview**
Emerging medical research on depression and anxiety is fragmented across thousands of research papers. Each study contains valuable insights about causes, therapeutic methods, medication interactions, and patient outcomes but this information is locked inside dense, technical text that can be difficult for clinicians to rapidly ingest and apply in practice.

🤝 **Break Through Tech AI Program**

This project was developed as part of the Break Through Tech AI Program, which connects undergraduate students with industry partners to work on real-world AI challenges. Through this program, our team collaborated with Brightside Health to address a critical challenge in healthcare information accessibility and clinical decision support.

🏥 **AI Studio Host: Brightside Health**

Brightside Health, our AI Studio host, is a leading virtual mental healthcare provider that delivers evidence-based treatment for depression and anxiety through a combination of therapy and psychiatry.
Project Objective
Develop an AI-powered system that can extract, synthesize, and present key findings from mental health research papers in a knowledge graph that is accessible and actionable for Brightside's clinicians.

🌍 **Real-World Significance**

**The Challenge**

The growing mental health crisis, affecting over 280 million people worldwide with depression alone, demands that clinicians have rapid access to the latest research findings. However:
  - Clinicians can spend only 2-5 hours per month on professional reading
  - An estimated 75 new clinical trials and studies are published daily across all medical fields
  - The average time for research findings to reach clinical practice is 17 years

**The Impact**

This disconnect between knowledge generation and knowledge application has real consequences: delayed adoption of effective treatments, inconsistent care quality, and missed opportunities for evidence-based interventions.
For a virtual-first provider like Brightside Health serving thousands of patients across multiple states, ensuring clinicians have access to the latest evidence is particularly crucial for maintaining high-quality, personalized care at scale.

💡 **Potential Impact**

Our AI solution has the potential to:

⚡**Accelerate Evidence-Based Care**

Enable Brightside's clinicians to quickly access synthesized findings from multiple studies, informing treatment decisions

📈 **Improve Patient Outcomes**

Help providers stay current with emerging therapeutic approaches, medication insights, and combination treatment strategies

🔄 **Scale Clinical Excellence**

Support Brightside's mission to provide consistent, high-quality mental healthcare by democratizing access to research insights across their clinical team

👤 **Support Personalized Treatment**

Provide rapid, relevant information that helps clinicians tailor interventions to individual patient needs and circumstances

⏰ **Reduce Provider Burden**

Free up clinician time currently spent on literature review, allowing more focus on direct patient care

🎯 **Vision**

By transforming how mental health research is accessed and utilized, this project could fundamentally improve the speed at which medical breakthroughs reach patients who need them most, while supporting Brightside Health's vision of making quality mental healthcare accessible to all.

---

## 📊 **Data Exploration**

**You might consider describing the following (as applicable):**

* The dataset(s) used: Three research papers about depression and anxiety
* Data exploration and preprocessing approaches
* Insights from your Exploratory Data Analysis (EDA)
* Challenges and assumptions when working with the dataset(s)

Edwin: add visuals for the knowledge graph

---

## 🧠 **Model Development**

Our system employs a Large Language Model (LLM)-based extraction pipeline using OpenAI's GPT-4o-mini to transform unstructured research text into structured knowledge graph representations.

**Model Selection**
**Primary Model:** GPT-4o-mini
**Rationale:** Chosen for its strong performance on information extraction tasks, cost-efficiency for processing large volumes of text, and ability to understand complex medical terminology
**Task:** Named Entity Recognition (NER) and Relationship Extraction from mental health research papers
**Temperature:** 0.2 (low temperature for consistent, factual extraction)

---

## 📈 **Results & Key Findings**
(can talk about knowledge graph here)
**You might consider describing the following (as applicable):**

* Performance metrics (e.g., Accuracy, F1 score, RMSE)
* How your model performed
* Insights from evaluating model fairness

**Potential visualizations to include:**

* Confusion matrix, precision-recall curve, feature importance plot, prediction distribution, outputs from fairness or explainability tools

---

## 🚀 **Next Steps**

* Implement filtering and search functionality by medication, condition, therapy type, or patient demographics
* Conduct pilot testing with Brightside Health clinicians
* Implement automated pipeline to continuously ingest new research publications
* Enable clinicians to annotate and contribute insights to the knowledge graph

---

## 🙏 **Acknowledgements** 

We want to thank our Challenge Advisors Andrew and Diane, our coach Harshini, and others who supported our project.
