import pymupdf
import pathlib

def pdf_to_txt(pdf_path, txt_path):
    with pymupdf.open(pdf_path) as doc:
        text = chr(12).join([page.get_text() for page in doc]) # chr(12) is form feed for page breaks
        pathlib.Path(txt_path).write_bytes(text.encode('utf-8'))

# Example usage:
# pdf_to_txt("WJCC-9-9350.pdf", "output_text.txt")