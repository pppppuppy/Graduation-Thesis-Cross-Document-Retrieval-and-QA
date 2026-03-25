import json
import os
import re
import random
from collections import Counter

INPUT_DIR = "./data/structured_v4_page"
OUTPUT_FILE = "./data/queries_v3.json"
QUALITY_REPORT_FILE = "./data/queries_v3_quality_report.txt"

MAX_QUERIES = 150

STOPWORDS = {
    "introduction", "related", "work", "method", "methods",
    "results", "discussion", "conclusion", "experiment",
    "experiments", "analysis", "approach", "background",
    "evaluation", "implementation", "appendix", "abstract",
    "preliminaries", "summary", "dataset", "paper", "proposed",
    "based", "using", "using", "show", "shown", "present",
    "presented", "describe", "described", "propose", "proposed"
}

BAD_KEYWORDS = {
    "also", "current", "practical", "suit", "towards", "new",
    "one", "two", "first", "second", "last", "final",
    "additional", "relevant", "following", "similar", "such",
    "existing", "various", "several", "different", "specific",
    "certain", "particular", "general", "main", "key", "core"
}

QUESTION_TEMPLATES = [
    "How does {k} improve model performance in neural networks?",
    "Why is {k} important for training deep learning models?",
    "What problem does {k} address in machine learning?",
    "How does {k} differ from traditional approaches?",
    "What is the role of {k} in transformer architectures?",
    "Why is {k} effective for natural language processing?",
    "How does {k} help with sequence modeling tasks?",
    "What are the advantages of using {k} in neural networks?",
    "Why does {k} improve generalization in deep learning?",
    "How does {k} affect the training dynamics of neural models?",
    "What is the impact of {k} on model convergence?",
    "Why is {k} crucial for attention mechanisms?",
    "How does {k} enable better representation learning?",
    "What limitations does {k} overcome in existing methods?",
    "Why is {k} essential for efficient model training?"
]


def is_valid_keyword(keyword):
    if len(keyword) < 4:
        return False
    if keyword in BAD_KEYWORDS:
        return False
    if keyword in STOPWORDS:
        return False
    if keyword.isdigit():
        return False
    if re.match(r"^\d+$", keyword):
        return False
    return True


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()
    words = [w for w in words if w not in STOPWORDS and len(w) > 3]
    return words


def extract_keywords(text):
    words = clean_text(text)
    counter = Counter(words)
    return [w for w, _ in counter.most_common(10) if is_valid_keyword(w)]


def extract_phrases(section_titles):
    phrases = []
    for t in section_titles:
        words = clean_text(t)
        if len(words) >= 2:
            phrase = " ".join(words[:2])
            if is_valid_keyword(phrase.replace(" ", "")):
                phrases.append(phrase)
        if len(words) >= 3:
            phrase = " ".join(words[:3])
            if is_valid_keyword(phrase.replace(" ", "")):
                phrases.append(phrase)
    return phrases


def build_queries(keywords):
    queries = []
    for k in keywords:
        template = random.choice(QUESTION_TEMPLATES)
        queries.append(template.format(k=k))
    return queries


def check_query_quality(query):
    """检查问题质量"""
    issues = []

    words = query.lower().split()

    if len(words) < 5:
        issues.append("问题太短")

    if "also" in words or "current" in words or "practical" in words:
        issues.append("包含无意义词汇")

    if query.lower().count("does does") > 0 or query.lower().count("is is") > 0:
        issues.append("语法错误")

    if not query.endswith("?"):
        issues.append("没有问号")

    if "?" in query:
        question_part = query.split("?")[0]
        if len(question_part.split()) < 4:
            issues.append("问号前内容太少")

    question_starters = ["how does", "how is", "how do", "how can", "how will",
                         "why is", "why does", "why do", "why can",
                         "what is", "what does", "what do", "what are",
                         "when does", "when is", "where does", "where is"]
    has_valid_starter = any(query.lower().startswith(s) for s in question_starters)
    if not has_valid_starter:
        issues.append("缺少有效疑问词")

    return issues


def main():
    print("=" * 60)
    print("Auto Query Generator v3 - 优化版")
    print("=" * 60)

    keywords = []
    paper_count = 0
    keyword_sources = {"title": [], "abstract": [], "section": []}

    for root, dirs, files in os.walk(INPUT_DIR):
        for f in files:
            if not f.endswith(".json"):
                continue

            path = os.path.join(root, f)

            with open(path, "r", encoding="utf-8") as file:
                paper = json.load(file)

            paper_count += 1

            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            sections = paper.get("sections", [])
            section_titles = [s.get("section_title", "") for s in sections]

            title_kw = extract_keywords(title)
            abstract_kw = extract_keywords(abstract)
            section_kw = extract_phrases(section_titles)

            keyword_sources["title"].extend(title_kw)
            keyword_sources["abstract"].extend(abstract_kw)
            keyword_sources["section"].extend(section_kw)

            keywords.extend(title_kw)
            keywords.extend(abstract_kw)
            keywords.extend(section_kw)

    print(f"\n[1] 原始关键词数量: {len(keywords)}")

    keywords = [k for k in keywords if is_valid_keyword(k)]
    keywords = list(set(keywords))
    print(f"[2] 过滤后唯一关键词: {len(keywords)}")

    queries = build_queries(keywords)
    queries = list(set(queries))
    random.shuffle(queries)
    queries = queries[:MAX_QUERIES]

    print(f"[3] 生成的问题数量: {len(queries)}")

    print("\n" + "=" * 60)
    print("质量检查")
    print("=" * 60)

    quality_report = []
    quality_report.append("=" * 60)
    quality_report.append("Query Quality Report v3")
    quality_report.append("=" * 60)

    passed_queries = []
    failed_queries = []

    for i, q in enumerate(queries):
        issues = check_query_quality(q)
        if not issues:
            passed_queries.append(q)
        else:
            failed_queries.append((q, issues))

    print(f"\n通过质量检查: {len(passed_queries)}/{len(queries)} ({len(passed_queries)/len(queries)*100:.1f}%)")
    print(f"未通过: {len(failed_queries)}/{len(queries)} ({len(failed_queries)/len(queries)*100:.1f}%)")

    quality_report.append(f"\nTotal queries: {len(queries)}")
    quality_report.append(f"Passed: {len(passed_queries)} ({len(passed_queries)/len(queries)*100:.1f}%)")
    quality_report.append(f"Failed: {len(failed_queries)} ({len(failed_queries)/len(queries)*100:.1f}%)")

    if failed_queries:
        print("\n未通过原因统计:")
        issue_counter = Counter()
        for q, issues in failed_queries:
            for issue in issues:
                issue_counter[issue] += 1

        for issue, count in issue_counter.most_common():
            print(f"  - {issue}: {count}")
            quality_report.append(f"  - {issue}: {count}")

    print("\n" + "=" * 60)
    print("推理过程说明")
    print("=" * 60)
    print("""
v3 版本的改进:

1. 关键词过滤优化:
   - 添加 BAD_KEYWORDS 列表,过滤掉 also, current, practical 等无意义词
   - 过滤掉纯数字和太短的词
   - 区分标题、摘要、章节的关键词来源

2. 问题模板优化:
   - 使用更完整的问题模板(15个)
   - 问题包含更多上下文(例如 "in neural networks", "for training" 等)
   - 确保问题有实际意义

3. 质量检查函数:
   - 检查问题长度(至少5个词)
   - 检查是否包含无意义词汇
   - 检查语法错误
   - 检查问号
   - 检查有效疑问词开头

4. 统计报告:
   - 生成详细的质量报告
   - 统计未通过原因
   - 分类汇总
""")

    final_queries = passed_queries[:MAX_QUERIES]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_queries, f, indent=2)

    print(f"\n[4] 最终问题数量: {len(final_queries)}")
    print(f"    保存至: {OUTPUT_FILE}")

    quality_report.append(f"\nFinal saved queries: {len(final_queries)}")
    quality_report.append("\nSample queries (first 10):")
    for q in final_queries[:10]:
        quality_report.append(f"  - {q}")

    with open(QUALITY_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(quality_report))

    print(f"    质量报告: {QUALITY_REPORT_FILE}")

    print("\n" + "=" * 60)
    print("示例问题")
    print("=" * 60)
    for q in final_queries[:10]:
        print(f"  • {q}")


if __name__ == "__main__":
    main()
