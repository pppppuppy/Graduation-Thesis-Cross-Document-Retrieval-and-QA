import os
import re
import json
import fitz

INPUT_ROOT = "./data/raw_pdfs"
OUTPUT_ROOT = "./data/structured_v6"
os.makedirs(OUTPUT_ROOT, exist_ok=True)


class AdvancedPDFProcessor:
    def __init__(self, filepath):
        self.doc = fitz.open(filepath)
        self.file_name = os.path.basename(filepath)

    def extract_title_and_meta(self):
        """利用页面顶部前两块内容提取标题"""
        blocks = self.doc[0].get_text("blocks")
        # 按 y 坐标排序
        blocks.sort(key=lambda x: x[1])
        # 简单取最靠上的大字号文本
        return blocks[0][4].strip().replace("\n", " ")

    def extract_clean_abstract(self):
        """过滤掉 Index Terms 的摘要提取"""
        full_text = ""
        for page in self.doc: full_text += page.get_text()

        # 提取 Abstract 到 Introduction 之间的内容
        match = re.search(r"Abstract(.*?)(?:1\.?\s+(?:INTRODUCTION|Introduction))", full_text, re.DOTALL)
        if match:
            abs_text = match.group(1)
            # 移除 Index Terms 及后面的词
            abs_text = re.split(r"Index\s+Terms", abs_text, flags=re.IGNORECASE)[0]
            return re.sub(r"\s+", " ", abs_text).strip()
        return ""

    def is_real_section(self, text):
        """精准判断标题：确保任何分支都返回 3 个值"""
        text = text.strip()

        # 1. 排除包含非法字符的行（公式行）
        # 这里必须显式处理，确保不符合条件的返回 False
        if any(c in text for c in ['=', '∑', '∫', '∈']):
            return False, None, None

        # 2. 识别编号标题
        match = re.match(r"^(\d+(\.\d+)*\.?)\s+([A-Z][A-Za-z\s\-]{2,})", text)
        if match:
            return True, match.group(1), text

        # 3. 识别无编号标题
        if text.upper() in ["INTRODUCTION", "CONCLUSION", "REFERENCES", "DISCUSSION", "ACKNOWLEDGEMENTS"]:
            return True, "None", text

        # 必须确保兜底返回 False, None, None
        return False, None, None

    def run(self):
        result = {
            "doc_id": self.file_name,
            "title": self.extract_title_and_meta(),
            "abstract": self.extract_clean_abstract(),
            "sections": []
        }

        current_section = None

        for page in self.doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                text = block[4].strip()
                if not text or len(text) < 3: continue

                is_header, s_id, title = self.is_real_section(text)

                if is_header:
                    current_section = {"section_id": s_id, "section_title": title, "text": ""}
                    result["sections"].append(current_section)
                elif current_section:
                    # 过滤页码和多余换行
                    if re.match(r"^\d+$", text): continue
                    current_section["text"] += " " + re.sub(r"\s+", " ", text)
        return result


# 批量执行
def main():
    for domain in os.listdir(INPUT_ROOT):
        path = os.path.join(INPUT_ROOT, domain)
        if not os.path.isdir(path): continue
        for f in os.listdir(path):
            if f.endswith(".pdf"):
                proc = AdvancedPDFProcessor(os.path.join(path, f))
                data = proc.run()
                with open(os.path.join(OUTPUT_ROOT, f.replace(".pdf", ".json")), "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()