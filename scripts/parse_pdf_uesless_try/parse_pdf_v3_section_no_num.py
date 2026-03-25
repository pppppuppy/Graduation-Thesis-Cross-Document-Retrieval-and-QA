import os
import re
import json
import fitz

INPUT_ROOT = "./data/raw_pdfs"
OUTPUT_ROOT = "./data/structured_v3_section_no_numpy"


class PDFProcessor:
    def __init__(self, filepath):
        self.doc = fitz.open(filepath)
        self.file_name = os.path.basename(filepath)
        # 预计算页面的平均字体大小，作为基准
        self.base_size = self._get_base_font_size()

    def _get_base_font_size(self):
        """计算文档中出现频率最高的字号作为正文字号"""
        sizes = []
        for page in self.doc:
            for b in page.get_text("dict")["blocks"]:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            sizes.append(round(s["size"]))
        return max(set(sizes), key=sizes.count) if sizes else 10

    def run(self):
        structured = {"doc_id": self.file_name, "sections": []}
        current_section = None

        # 定义标题关键字
        headers = ["INTRODUCTION", "METHOD", "EXPERIMENTS", "RESULTS", "CONCLUSION", "REFERENCES", "APPENDIX"]

        for page in self.doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block: continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        size = span["size"]

                        # 1. 终止判断
                        if text.upper() in ["REFERENCES", "APPENDIX"]:
                            return structured

                        # 2. 标题判断：字号比正文大 (如 > base_size + 0.5)
                        # 或者符合特定大写格式
                        is_title = (size > self.base_size + 0.5) or (text.upper() in headers)

                        if is_title and len(text) < 60:
                            current_section = {"section_title": text, "text": ""}
                            structured["sections"].append(current_section)
                        elif current_section:
                            # 3. 内容过滤：过滤页码
                            if not re.match(r"^\d+$", text):
                                current_section["text"] += " " + text
        return structured


# 批量处理逻辑保持不变
def process_all():
    for domain in os.listdir(INPUT_ROOT):
        domain_path = os.path.join(INPUT_ROOT, domain)
        if not os.path.isdir(domain_path): continue
        output_domain_dir = os.path.join(OUTPUT_ROOT, domain)
        os.makedirs(output_domain_dir, exist_ok=True)

        for filename in os.listdir(domain_path):
            if filename.endswith(".pdf"):
                processor = PDFProcessor(os.path.join(domain_path, filename))
                data = processor.run()
                output_path = os.path.join(output_domain_dir, filename.replace(".pdf", ".json"))
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Parsed: {filename}")


if __name__ == "__main__":
    process_all()