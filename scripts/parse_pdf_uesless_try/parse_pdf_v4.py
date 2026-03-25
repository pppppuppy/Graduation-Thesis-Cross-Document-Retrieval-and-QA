import fitz  # PyMuPDF
import os
import re
import json


# ===============================
# 基础文本清洗
# ===============================

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def is_noise_paragraph(text):
    """
    过滤公式碎片/乱码段落
    """
    if len(text) < 20:
        return True

    # 单字符占比过高
    single_chars = re.findall(r'\b[a-zA-Z]\b', text)
    if len(single_chars) > len(text.split()) * 0.4:
        return True

    # 数学符号过多
    if len(re.findall(r'[=+\-*/\\^{}]', text)) > 10:
        return True

    return False


# ===============================
# 标题识别
# ===============================

section_pattern = re.compile(r'^(\d+(\.\d+)*)\s+(.+)')


def detect_section(line):
    match = section_pattern.match(line)
    if match:
        section_id = match.group(1)
        section_title = match.group(3)
        level = section_id.count('.') + 1
        return section_id, section_title, level
    return None


# ===============================
# PDF 解析主函数
# ===============================

def parse_pdf(pdf_path):
    doc = fitz.open(pdf_path)

    full_text_pages = []
    for page in doc:
        text = page.get_text("text")
        full_text_pages.append(text)

    # -------- 标题提取 --------
    title = ""
    first_page_lines = full_text_pages[0].split('\n')
    for line in first_page_lines:
        if len(line.strip()) > 10:
            title = clean_text(line)
            break

    # -------- 摘要提取（只前2页）--------
    abstract = ""
    abstract_found = False

    for page_index in range(min(2, len(full_text_pages))):
        lines = full_text_pages[page_index].split('\n')
        for i, line in enumerate(lines):
            if re.match(r'(?i)^abstract', line.strip()):
                abstract_found = True
                for j in range(i+1, len(lines)):
                    if detect_section(lines[j]):
                        break
                    abstract += " " + lines[j]
                break
        if abstract_found:
            break

    abstract = clean_text(abstract)

    # -------- 正文解析 --------
    sections = []
    current_section = None
    para_id_counter = 1

    for page_num, page_text in enumerate(full_text_pages, start=1):
        lines = page_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过摘要部分
            if abstract_found and abstract and line in abstract:
                continue

            section_info = detect_section(line)
            if section_info:
                section_id, section_title, level = section_info
                current_section = {
                    "section_id": section_id,
                    "section_title": clean_text(section_title),
                    "level": level,
                    "paragraphs": []
                }
                sections.append(current_section)
                para_id_counter = 1
                continue

            if current_section:
                cleaned = clean_text(line)

                if is_noise_paragraph(cleaned):
                    continue

                paragraph = {
                    "para_id": f"{current_section['section_id']}_{para_id_counter}",
                    "text": cleaned,
                    "page": page_num
                }
                current_section["paragraphs"].append(paragraph)
                para_id_counter += 1

    result = {
        "title": title,
        "abstract": abstract,
        "sections": sections
    }

    return result


# ===============================
# 批量处理
# ===============================

def process_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            print(f"Processing: {filename}")

            try:
                data = parse_pdf(pdf_path)
                output_path = os.path.join(
                    output_folder,
                    filename.replace(".pdf", ".json")
                )

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"Error processing {filename}: {e}")


# ===============================
# 入口
# ===============================

if __name__ == "__main__":
    input_root = "data/raw_pdfs"
    output_root = "data/structured_v4_fixed"

    for domain in os.listdir(input_root):
        domain_path = os.path.join(input_root, domain)
        if os.path.isdir(domain_path):
            print(f"\n=== Processing domain: {domain} ===")
            process_folder(
                domain_path,
                os.path.join(output_root, domain)
            )