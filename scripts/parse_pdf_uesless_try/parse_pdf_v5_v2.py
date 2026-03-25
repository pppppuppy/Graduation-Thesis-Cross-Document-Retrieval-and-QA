import os
import re
import json
import fitz

INPUT_ROOT = "./data/raw_pdfs"
OUTPUT_ROOT = "./data/structured_v5_v2"

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
                    line_text = "".join([span["text"] for span in line["spans"]])
                    if len(line_text.strip()) < 6:
                        continue
                    if re.search(r"arxiv|published|conference|proceedings|http|©", line_text, re.I):
                        continue
                    avg_size = sum([s["size"] for s in line["spans"]]) / len(line["spans"])
                    y_pos = line["bbox"][1]
                    candidates.append({
                        "text": line_text.strip(),
                        "size": avg_size,
                        "y": y_pos
                    })

        if not candidates:
            return "Unknown Title"

        candidates.sort(key=lambda x: (-x["size"], x["y"]))
        max_size = candidates[0]["size"]
        title_parts = [c["text"] for c in candidates if abs(c["size"] - max_size) < 1.5]
        return " ".join(title_parts).strip()

    def extract_abstract(self):
        match = re.search(
            r"Abstract[:\s]+(.*?)(?=\n\s*(?:I\.?|II\.?|III\.?|IV\.?|V\.?|VI\.?|VII\.?|VIII\.?|IX\.?|X\.?|I\s+|II\s+|III\s+|IV\s+|V\s+|VI\s+|VII\s+|VIII\s+|IX\s+|X\s+|A\.?\s+|B\.?\s+|C\.?\s+|D\.?\s+|1\.?\s+|2\.?\s+|3\.?\s+|INTRODUCTION|Abstract\s*$))",
            self.full_text,
            re.DOTALL | re.IGNORECASE
        )
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()

        parts = re.split(r"\n\s*(?:I\.?|II\.?|III\.?|IV\.?|V\.?|VI\.?|VII\.?|VIII\.?|IX\.?|X\.?)\s+(?:INTRODUCTION|Method|Methods|Background|Results|Discussion|Conclusion)", self.full_text, maxsplit=1)
        if len(parts) > 1:
            pre_text = parts[0]
            abs_start = pre_text.lower().rfind("abstract")
            if abs_start != -1:
                return re.sub(r"\s+", " ", pre_text[abs_start + 8:]).strip()

        return ""

    def is_section_header(self, text, title_text):
        clean_text = re.sub(r"\s+", " ", text).strip()

        if len(clean_text) < 3:
            return False, None, None, None

        if title_text and (clean_text == title_text or clean_text.startswith(title_text[:20])):
            return False, None, None, None

        header_lower = clean_text.lower()
        if header_lower == "abstract" or header_lower.startswith("abstract "):
            return False, None, None, None

        if len(clean_text) < 30 and re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+$", clean_text):
            return False, None, None, None

        pattern1 = r"^(\d+(\.\d+)*)\.?\s+([A-Z][A-Za-z\s\-\:\&]{2,})"
        pattern2 = r"^(\d+(\.\d+)*)\s+([A-Z][A-Za-z\s\-\:\&]{2,})"
        pattern3 = r"^Section\s+(\d+(\.\d+)*)\.?\s+([A-Z][A-Za-z\s\-\:\&]{2,})"
        pattern4 = r"^(\d+(\.\d+)*)\.?\s+([A-Z\s\-\:\&]{3,})"

        for pattern in [pattern1, pattern2, pattern3, pattern4]:
            match = re.match(pattern, clean_text)
            if match and len(clean_text) < 100:
                sec_id = match.group(1)
                title_only = match.group(3).strip()
                return True, sec_id, title_only, sec_id

        roman_numeral_pattern = r"^(I{1,3}|IV|V|VI{1,3}|IX|X|I{1,2})\.?\s+([A-Z][A-Za-z\s\-\:\&]{2,})"
        match = re.match(roman_numeral_pattern, clean_text, re.IGNORECASE)
        if match and len(clean_text) < 100:
            sec_id = match.group(1).upper()
            title_only = match.group(2).strip()
            return True, sec_id, title_only, sec_id

        letter_pattern = r"^([A-Z])\.?\s+([A-Z][A-Za-z\s\-\:\&]{2,})"
        match = re.match(letter_pattern, clean_text)
        if match and len(clean_text) < 100:
            sec_id = match.group(1)
            title_only = match.group(2).strip()
            if len(title_only) > 3:
                return True, sec_id, title_only, sec_id

        common_sections = [
            "introduction", "background", "related work", "method", "methods",
            "experimental results", "experiments", "results", "discussion",
            "conclusion", "conclusions", "references", "acknowledgements", "appendix",
            "preliminaries", "abstract", "summary", "approach", "methodology",
            "problem definition", "problem formulation", "data", "dataset",
            "datasets", "analysis", "evaluation", "setup"
        ]

        if len(clean_text) < 50 and re.match(r"^[A-Z][A-Za-z\s\-\:\&]{3,}$", clean_text):
            if header_lower in common_sections:
                return True, None, clean_text, None
            if len(clean_text) > 10 and len(clean_text) < 40:
                return True, None, clean_text, None

        return False, None, None, None

    def run(self):
        title_text = self.extract_title()
        abstract_text = self.extract_abstract()

        structured = {
            "doc_id": self.file_name,
            "title": title_text,
            "abstract": abstract_text,
            "sections": []
        }

        section_counter = 0
        current_section = None

        for page in self.doc:
            blocks = page.get_text("blocks")
            page_height = page.rect.height

            for block in blocks:
                raw_text = block[4].strip()
                if not raw_text:
                    continue

                y_pos = block[1]
                if y_pos < 50 or y_pos > (page_height - 50):
                    if re.search(r"arXiv:|Published as|Page \d+|ICLR|Vol\.|No\.", raw_text, re.I):
                        continue

                is_header, sec_id, title_only, original_sec_id = self.is_section_header(raw_text, title_text)

                if is_header:
                    header_lower = title_only.lower() if title_only else ""
                    if header_lower == "abstract":
                        continue

                    section_counter += 1

                    if sec_id is None:
                        sec_id = str(section_counter)

                    current_section = {
                        "section_id": str(section_counter),
                        "original_section_number": original_sec_id if original_sec_id else "",
                        "section_title": title_only,
                        "level": 1,
                        "text": ""
                    }
                    structured["sections"].append(current_section)
                elif current_section:
                    clean_content = re.sub(r"\s+", " ", raw_text)
                    current_section["text"] += " " + clean_content

        if not structured["sections"]:
            self._extract_sections_fallback(structured)

        return structured

    def _extract_sections_fallback(self, structured):
        section_keywords = [
            "Introduction", "Background", "Related Work", "Method", "Methods",
            "Experimental Results", "Experiments", "Results", "Discussion", "Conclusion", "Conclusions",
            "References", "Acknowledgements", "Appendix", "Preliminaries"
        ]

        keyword_pattern = "|".join([re.escape(kw) for kw in section_keywords])
        pattern = re.compile(f"({keyword_pattern})", re.IGNORECASE)

        parts = pattern.split(self.full_text)

        section_counter = 0
        current_section = None

        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            if i % 2 == 1:
                section_counter += 1
                current_section = {
                    "section_id": str(section_counter),
                    "original_section_number": "",
                    "section_title": part.strip(),
                    "level": 1,
                    "text": ""
                }
                structured["sections"].append(current_section)
            elif current_section:
                clean_content = re.sub(r"\s+", " ", part)
                current_section["text"] += " " + clean_content


def process_all():
    if not os.path.exists(INPUT_ROOT):
        print(f"Error: {INPUT_ROOT} 不存在")
        return

    for domain in os.listdir(INPUT_ROOT):
        domain_path = os.path.join(INPUT_ROOT, domain)
        if not os.path.isdir(domain_path):
            continue

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
                    try:
                        simple_data = {
                            "doc_id": filename,
                            "title": "Unknown Title",
                            "abstract": "",
                            "sections": [{
                                "section_id": "1",
                                "original_section_number": "",
                                "section_title": "Full Text",
                                "level": 1,
                                "text": re.sub(r"\s+", " ", processor.full_text)
                            }]
                        }
                        output_path = os.path.join(output_domain_dir, filename.replace(".pdf", "_simple.json"))
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(simple_data, f, indent=2, ensure_ascii=False)
                        print(f"  [降级处理成功] {filename}")
                    except:
                        pass


if __name__ == "__main__":
    process_all()
