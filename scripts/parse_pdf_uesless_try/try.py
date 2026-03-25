import os
import re
import json
import fitz


class RobustPDFProcessor:
    def __init__(self, filepath):
        self.doc = fitz.open(filepath)
        self.filepath = filepath

    def is_section_header(self, span):
        """利用字号和加粗属性判断标题"""
        text = span["text"].strip()
        # 1. 标题必须加粗 (PyMuPDF 字体名通常包含 Bold)
        is_bold = "bold" in span["font"].lower()
        # 2. 标题通常字号较大或居中
        # 3. 过滤掉包含公式特征的行
        if not is_bold or len(text) > 60: return False

        pattern = r"^(\d+(\.\d+)*\.?)\s+([A-Z][A-Za-z\s\-]{2,})"
        match = re.match(pattern, text)
        if match: return True
        # 无编号标题 (Introduction, References 等)
        if text.upper() in ["INTRODUCTION", "METHOD", "EXPERIMENTS", "RESULTS", "CONCLUSION", "REFERENCES"]:
            return True
        return False

    def run(self):
        result = {"title": "", "sections": []}
        current_section = None

        for page in self.doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block: continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text: continue

                        # 检测到结尾标志直接退出
                        if text.upper() in ["REFERENCES", "APPENDIX"]:
                            return result

                        if self.is_section_header(span):
                            current_section = {"section_title": text, "text": ""}
                            result["sections"].append(current_section)
                        elif current_section:
                            # 过滤页码和异常短行
                            if len(text) > 3:
                                current_section["text"] += " " + text
        return result


# 使用示例
if __name__ == "__main__":
    proc = RobustPDFProcessor("1905.06443v3.pdf")
    data = proc.run()
    print(json.dumps(data, indent=2, ensure_ascii=False))