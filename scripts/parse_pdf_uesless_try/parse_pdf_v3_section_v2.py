import os
import re
import json
import fitz

INPUT_ROOT = "./data/raw_pdfs"
OUTPUT_ROOT = "./data/structured_v3_section_level_v2"

os.makedirs(OUTPUT_ROOT, exist_ok=True)


class PDFProcessor:
    def __init__(self, filepath):
        self.doc = fitz.open(filepath)
        self.file_name = os.path.basename(filepath)
        self.full_text = ""
        for page in self.doc:
            self.full_text += page.get_text()

    def extract_title(self):
        page = self.doc[0]
        blocks = page.get_text("dict")["blocks"]
        candidates = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if len(text) < 6 or re.search(r"arxiv|published|conference|proceedings|http|©|vol\.|no\.", text,
                                                      re.I):
                            continue
                        candidates.append({"text": text, "size": span["size"], "y": span["origin"][1]})

        if not candidates: return "Unknown Title"
        candidates.sort(key=lambda x: (-x["size"], x["y"]))
        max_size = candidates[0]["size"]
        title_parts = [c["text"] for c in candidates if abs(c["size"] - max_size) < 1]
        return " ".join(title_parts).strip()

    def extract_abstract(self):
        # 优化匹配，兼容更多情况
        patterns = [
            r"Abstract[:\s]+(.*?)(?=\n\s*(\d\.?\s+)?(?:INTRODUCTION|Introduction))",
            r"(?<=\n)Abstract\n(.*?)(?=\n\s*(\d\.?\s+)?(?:INTRODUCTION|Introduction))"
        ]
        for p in patterns:
            match = re.search(p, self.full_text, re.DOTALL | re.IGNORECASE)
            if match:
                return re.sub(r"\s+", " ", match.group(1)).strip()
        return ""

    def is_section_header(self, text):
        """
        增强版标题判定逻辑
        """
        clean_text = re.sub(r"\s+", " ", text).strip()

        # 1. 排除明显的数学公式和坐标 (包含希腊字母、特殊数学符号或全是数字/点)
        if re.search(r"[αβγδεζηθικλμνξοπρστυφχψωΣΔΓΛΦΨΩ∫∑∏√=≠≤≥±\(\)\[\]\{\}]", clean_text):
            return False, None, clean_text

        # 2. 识别带数字编号的标题 (1 Introduction, 2.3 Method)
        # 增加限制：编号后面必须跟至少两个字母，且不能全是数字
        num_pattern = r"^(\d+(\.\d+)*)\.?\s+([A-Za-z][A-Za-z\s\-\:\&]{2,})"
        num_match = re.match(num_pattern, clean_text)

        if num_match:
            sec_id = num_match.group(1)
            # 排除像 190.0 这种纯坐标数值
            if sec_id.endswith(".0") and len(clean_text) < 15:
                return False, None, clean_text
            return True, sec_id, clean_text

        # 3. 识别不带数字的重要标题 (Conclusion, Discussion, References, Appendix)
        keyword_pattern = r"^(Conclusion|Discussion|References|Appendix|Summary|Acknowledge?ment)s?$"
        if re.match(keyword_pattern, clean_text, re.IGNORECASE):
            return True, "None", clean_text

        return False, None, clean_text

    def run(self):
        structured = {
            "doc_id": self.file_name,
            "title": self.extract_title(),
            "abstract": self.extract_abstract(),
            "sections": []
        }

        current_section = None

        for page in self.doc:
            blocks = page.get_text("blocks")
            page_height = page.rect.height

            for block in blocks:
                raw_text = block[4].strip()
                if not raw_text or len(raw_text) < 3: continue

                # 过滤页眉页脚
                y_pos = block[1]
                if y_pos < 40 or y_pos > (page_height - 40): continue

                is_header, sec_id, full_header = self.is_section_header(raw_text)

                if is_header:
                    # 避免重复添加同一个标题
                    if structured["sections"] and structured["sections"][-1]["section_title"] == full_header:
                        continue

                    current_section = {
                        "section_id": sec_id,
                        "section_title": full_header,
                        "level": sec_id.count(".") + 1 if sec_id != "None" else 1,
                        "text": ""
                    }
                    structured["sections"].append(current_section)
                elif current_section:
                    # 正文清理：移除像 14, 15 这样的独立页码行
                    if raw_text.isdigit(): continue

                    clean_content = re.sub(r"\s+", " ", raw_text)
                    current_section["text"] += " " + clean_content

        return structured


def process_all():
    for domain in os.listdir(INPUT_ROOT):
        domain_path = os.path.join(INPUT_ROOT, domain)
        if not os.path.isdir(domain_path): continue
        output_domain_dir = os.path.join(OUTPUT_ROOT, domain)
        os.makedirs(output_domain_dir, exist_ok=True)

        for filename in os.listdir(domain_path):
            if filename.endswith(".pdf"):
                try:
                    processor = PDFProcessor(os.path.join(domain_path, filename))
                    data = processor.run()
                    with open(os.path.join(output_domain_dir, filename.replace(".pdf", ".json")), "w",
                              encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"Done: {filename}")
                except Exception as e:
                    print(f"Error {filename}: {str(e)}")


if __name__ == "__main__":
    process_all()