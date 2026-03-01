import pdfplumber
import json
import os
import re


def clean_text(text):
    if not text:
        return ""

    # 1. 去除多余空格
    text = re.sub(r'\s+', ' ', text)

    # 2. 去除页码（简单规则：单独数字行）
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    # 3. 去掉连续空格
    text = text.strip()

    return text


def parse_pdf_to_json(pdf_path, output_path):
    pages_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            raw_text = page.extract_text()
            cleaned_text = clean_text(raw_text)

            if cleaned_text:
                pages_data.append({
                    "page_id": i + 1,
                    "text": cleaned_text
                })

    result = {
        "doc_id": os.path.basename(pdf_path),
        "total_pages": len(pages_data),
        "pages": pages_data
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def batch_parse(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, file)
            json_path = os.path.join(output_folder, file.replace(".pdf", ".json"))
            parse_pdf_to_json(pdf_path, json_path)
            print(f"Processed {file}")


if __name__ == "__main__":
    input_folder = "data/raw_pdfs"
    output_folder = "data/parsed_pages"
    batch_parse(input_folder, output_folder)