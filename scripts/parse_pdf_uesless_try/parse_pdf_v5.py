import os
import re
import json
import fitz

INPUT_DIR = "./data/raw_pdfs"
OUTPUT_DIR = "./data/structured_v5"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------
# 判断 section 标题
# -------------------------
def is_section_title(text):
    text = text.strip()
    pattern = r"^\d+(\.\d+)*\.?\s+[A-Z]"
    return re.match(pattern, text) and len(text) < 120


# -------------------------
# 合并 block 成段落
# -------------------------
def merge_blocks_into_paragraphs(blocks, y_threshold=10):
    paragraphs = []
    current_para = ""
    last_y1 = None

    for block in blocks:
        text = block[4].strip()
        if not text:
            continue

        y0 = block[1]
        y1 = block[3]

        if last_y1 is None:
            current_para = text
        else:
            if abs(y0 - last_y1) < y_threshold:
                current_para += " " + text
            else:
                paragraphs.append(current_para.strip())
                current_para = text

        last_y1 = y1

    if current_para:
        paragraphs.append(current_para.strip())

    return paragraphs


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
# 提取第一页 Abstract（更安全）
# -------------------------
def extract_abstract_from_first_page(doc):
    page = doc[0]
    text = page.get_text()

    # 找 Abstract 开头
    match = re.search(r"Abstract(.*?)(?=\n\s*\d+\.|\nIntroduction)", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""


# -------------------------
# 主解析
# -------------------------
def parse_pdf(filepath):
    doc = fitz.open(filepath)

    structured = {
        "doc_id": os.path.basename(filepath),
        "title": extract_title(doc),
        "abstract": extract_abstract_from_first_page(doc),
        "sections": []
    }

    current_section = None
    para_counter = 0
    stop_parsing = False

    for page_num, page in enumerate(doc):

        blocks = page.get_text("blocks")
        merged_paragraphs = merge_blocks_into_paragraphs(blocks)

        for text in merged_paragraphs:

            text = text.strip()
            if not text:
                continue

            # 跳过 abstract 本身（避免重复）
            if structured["abstract"] and structured["abstract"][:50] in text:
                continue

            # 遇到 References 停止
            if re.match(r"^References", text):
                stop_parsing = True
                break

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

            # 正文段落
            if current_section:
                para_counter += 1
                paragraph = {
                    "para_id": f"{current_section['section_id']}_{para_counter}",
                    "text": text,
                    "page": page_num + 1
                }
                current_section["paragraphs"].append(paragraph)

        if stop_parsing:
            break

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