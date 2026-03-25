import os
import json
import re

INPUT_DIR = "./data/parsed_pages"
OUTPUT_DIR = "./data/parsed_structured_v2"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_title(text):
    lines = text.split("\n")
    # 假设前 5 行内包含标题
    return lines[0].strip()


def extract_abstract(text):
    abstract_match = re.search(r'Abstract(.*?)(?=\n\d+\.\s)', text, re.DOTALL)
    if abstract_match:
        return abstract_match.group(1).strip()
    return ""


def split_sections(text):
    sections = []
    pattern = r'(\n\d+\.\s+[^\n]+)'
    splits = re.split(pattern, text)

    # splits 格式：
    # [前导文本, 标题1, 内容1, 标题2, 内容2, ...]

    if len(splits) < 3:
        return sections

    for i in range(1, len(splits), 2):
        section_title = splits[i].strip()
        section_text = splits[i + 1].strip() if i + 1 < len(splits) else ""

        sections.append({
            "section_id": len(sections) + 1,
            "section_title": section_title,
            "text": section_text
        })

    return sections


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    full_text = ""
    for page in data["pages"]:
        full_text += page["text"] + "\n"

    structured = {
        "doc_id": data["doc_id"],
        "title": extract_title(full_text),
        "abstract": extract_abstract(full_text),
        "sections": split_sections(full_text)
    }

    return structured


def main():
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".json"):
            input_path = os.path.join(INPUT_DIR, filename)
            output_path = os.path.join(OUTPUT_DIR, filename)

            structured_data = process_file(input_path)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)

            print(f"Processed {filename}")


if __name__ == "__main__":
    main()