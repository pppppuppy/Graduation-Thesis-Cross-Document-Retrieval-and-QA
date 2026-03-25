import os
import re
import json
import fitz

INPUT_DIR = "./data/raw_pdfs"
OUTPUT_DIR = "./data/structured_v6"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------
# 判断 section 标题
# -------------------------
def is_section_title(text):
    text = text.strip()
    pattern = r"^\d+(\.\d+)*\.?\s+[A-Za-z]"
    return re.match(pattern, text) and len(text) < 150


# -------------------------
# 过滤明显是公式/垃圾文本
# -------------------------
def is_noise(text):
    # 太短
    if len(text) < 20:
        return True

    # 数学符号比例过高
    symbol_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
    if symbol_ratio > 0.4:
        return True

    # 单字符重复
    if len(set(text)) < 5:
        return True

    return False


# -------------------------
# 提取标题
# -------------------------
def extract_title(doc):
    page = doc[0]
    blocks = page.get_text("dict")["blocks"]

    max_size = 0
    title_text = ""

    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    size = span["size"]
                    text = span["text"].strip()
                    if len(text) > 5 and size > max_size:
                        max_size = size
                        title_text = text

    return title_text


# -------------------------
# 主解析函数（稳定版）
# -------------------------
def parse_pdf(filepath):
    doc = fitz.open(filepath)

    structured = {
        "doc_id": os.path.basename(filepath),
        "title": extract_title(doc),
        "abstract": "",
        "sections": []
    }

    current_section = None
    para_counter = 0

    for page_num, page in enumerate(doc):

        # 关键：使用 text 而不是 blocks
        page_text = page.get_text("text")

        # 用空行切段
        raw_paragraphs = re.split(r"\n\s*\n", page_text)

        for text in raw_paragraphs:

            text = text.strip()
            text = text.replace("\n", " ")

            if not text:
                continue

            # 遇到 References 停止
            if text.startswith("References"):
                return structured

            # 过滤噪声
            if is_noise(text):
                continue

            # Section 标题
            if is_section_title(text):
                section_id_match = re.match(r"^(\d+(\.\d+)*)", text)
                section_id = section_id_match.group(1)
                level = section_id.count(".") + 1

                current_section = {
                    "section_id": section_id,
                    "section_title": text,
                    "level": level,
                    "paragraphs": []
                }

                structured["sections"].append(current_section)
                para_counter = 0
                continue

            # 正文
            if current_section:
                para_counter += 1
                paragraph = {
                    "para_id": f"{current_section['section_id']}_{para_counter}",
                    "text": text,
                    "page": page_num + 1
                }

                current_section["paragraphs"].append(paragraph)

    return structured


# -------------------------
# 批量处理
# -------------------------
def main():
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".pdf"):
            continue

        pdf_path = os.path.join(INPUT_DIR, filename)
        print(f"Processing {filename}...")

        structured_data = parse_pdf(pdf_path)

        output_path = os.path.join(
            OUTPUT_DIR,
            filename.replace(".pdf", ".json")
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)

        print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()