import os
import re
import json
import fitz  # PyMuPDF

INPUT_ROOT = "./data/raw_pdfs"
OUTPUT_ROOT = "./data/structured_v3_section_level"

# 建立输出目录
os.makedirs(OUTPUT_ROOT, exist_ok=True)


# ===============================
# 核心解析类：处理学术论文特有的格式
# ===============================
class PDFProcessor:
    def __init__(self, filepath):
        self.doc = fitz.open(filepath)
        self.file_name = os.path.basename(filepath)
        self.full_text = ""
        # 预加载全文用于 Abstract 匹配
        for page in self.doc:
            self.full_text += page.get_text()


    """def extract_title(self):
        #通过字号和位置定位标题，过滤掉会议信息
        page = self.doc[0]
        blocks = page.get_text("dict")["blocks"]
        candidates = []

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        # 过滤掉干扰项：页码、会议名、arXiv编号、URL
                        if len(text) < 6 or re.search(r"arxiv|published|conference|proceedings|http|©|vol\.|no\.", text,
                                                      re.I):
                            continue
                        candidates.append({
                            "text": text,
                            "size": span["size"],
                            "y": span["origin"][1]
                        })

        if not candidates: return "Unknown Title"

        # 排序：字号从大到小，位置从上到下
        candidates.sort(key=lambda x: (-x["size"], x["y"]))

        # 聚合第一梯队字号的所有文本（处理多行标题）
        max_size = candidates[0]["size"]
        title_parts = [c["text"] for c in candidates if abs(c["size"] - max_size) < 1]
        return " ".join(title_parts).strip()
        
        """

    def extract_title(self):
        """优化版：处理大字号文本中首字母丢失的情况"""
        page = self.doc[0]
        blocks = page.get_text("dict")["blocks"]
        candidates = []

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    # 将同一行的所有 spans 拼接在一起，防止 span 切割导致的漏字
                    line_text = "".join([span["text"] for span in line["spans"]])
                    # 获取该行平均字号
                    avg_size = sum([s["size"] for s in line["spans"]]) / len(line["spans"])
                    y_pos = line["bbox"][1]

                    if len(line_text.strip()) < 6 or re.search(r"arxiv|published|conference|proceedings|http|©",
                                                               line_text, re.I):
                        continue

                    candidates.append({
                        "text": line_text.strip(),
                        "size": avg_size,
                        "y": y_pos
                    })

        if not candidates: return "Unknown Title"

        # 排序：字号大者优先，位置靠上者优先
        candidates.sort(key=lambda x: (-x["size"], x["y"]))

        max_size = candidates[0]["size"]
        # 聚合字号相近的行
        title_parts = [c["text"] for c in candidates if abs(c["size"] - max_size) < 1.5]
        full_title = " ".join(title_parts).strip()

        # 修复逻辑：如果发现词汇首字母缺失（例如 "ACHINE RANSLATION"）
        # 这里使用正则表达式修复常见的丢失首字母情况
        # 匹配以非字母开头、后接小写字母的模式，尝试在前面补回正确的首字母（这需要领域词库，此处提供基础修复）
        # 简单暴力修复：将所有全大写的词如果发现是常见词的残缺，可以考虑后续加 AI 校正，
        # 目前先解决因为 "span" 切割导致的漏字：
        return full_title

    def extract_abstract(self):
        """增强版摘要提取：利用 Introduction 作为边界"""
        # 尝试正则 1: 标准 Abstract 标签
        match = re.search(
            r"Abstract[:\s]+(.*?)(?=\n\s*(?:1\.?\s+|INTRODUCTION|1\s+Introduction))",
            self.full_text,
            re.DOTALL | re.IGNORECASE
        )
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()

        # 尝试正则 2: 兜底逻辑，截取 1. Introduction 之前的内容
        parts = re.split(r"\n\s*1\.?\s+(?:INTRODUCTION|Introduction)", self.full_text, maxsplit=1)
        if len(parts) > 1:
            pre_text = parts[0]
            abs_start = pre_text.lower().rfind("abstract")
            if abs_start != -1:
                return re.sub(r"\s+", " ", pre_text[abs_start + 8:]).strip()

        return ""

    def is_section_header(self, text):
        """识别 Section 标题并返回清洗后的标题名"""
        # 移除内部换行，处理 "1\nINTRODUCTION"
        clean_text = re.sub(r"\s+", " ", text).strip()
        # 匹配 1 或 1. 或 1.1 形式
        pattern = r"^(\d+(\.\d+)*)\.?\s+([A-Z][A-Za-z\s\-\:\&]{2,})"
        match = re.match(pattern, clean_text)

        if match and len(clean_text) < 100:
            return True, match.group(1), clean_text
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
            # 获取页面高度，用于简单过滤页脚
            page_height = page.rect.height

            for block in blocks:
                raw_text = block[4].strip()
                if not raw_text: continue

                # 过滤页码和会议重复页眉（通常在页面顶部或底部 50 像素内）
                y_pos = block[1]
                if y_pos < 50 or y_pos > (page_height - 50):
                    if re.search(r"arXiv:|Published as|Page \d+|ICLR", raw_text, re.I):
                        continue

                is_header, sec_id, full_header = self.is_section_header(raw_text)

                if is_header:
                    current_section = {
                        "section_id": sec_id,
                        "section_title": full_header,
                        "level": sec_id.count(".") + 1,
                        "text": ""
                    }
                    structured["sections"].append(current_section)
                elif current_section:
                    # 清洗正文中的多余换行符
                    clean_content = re.sub(r"\s+", " ", raw_text)
                    current_section["text"] += " " + clean_content

        return structured


# ===============================
# 批量处理逻辑
# ===============================
def process_all():
    if not os.path.exists(INPUT_ROOT):
        print(f"Error: {INPUT_ROOT} 不存在")
        return

    for domain in os.listdir(INPUT_ROOT):
        domain_path = os.path.join(INPUT_ROOT, domain)
        if not os.path.isdir(domain_path): continue

        output_domain_dir = os.path.join(OUTPUT_ROOT, domain)
        os.makedirs(output_domain_dir, exist_ok=True)

        print(f"\n>>> 开始处理领域: {domain}")

        for filename in os.listdir(domain_path):
            if filename.endswith(".pdf"):
                try:
                    pdf_path = os.path.join(domain_path, filename)
                    processor = PDFProcessor(pdf_path)
                    data = processor.run()

                    output_path = os.path.join(output_domain_dir, filename.replace(".pdf", ".json"))
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    print(f"  [成功] {filename}")
                except Exception as e:
                    print(f"  [失败] {filename}: {str(e)}")


if __name__ == "__main__":
    process_all()
