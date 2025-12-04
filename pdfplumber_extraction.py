import pdfplumber
import pathlib

def pdf_to_txt(pdf_path, txt_path):
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
    output_text = chr(12).join(all_text)  # add page breaks
    pathlib.Path(txt_path).write_text(output_text, encoding="utf-8")
    print(f"Saved extracted text to {txt_path}")

if __name__ == "__main__":
    pdf_file = "/Users/krrishkohli/Desktop/Text_extraction/WJCC-9-9350.pdf"
    output_file = "/Users/krrishkohli/Desktop/Text_extraction/output_text.txt"
    pdf_to_txt(pdf_file, output_file)
