import json
import os
import re
import random
from collections import Counter

INPUT_DIR = "./data/structured_v4_page"
OUTPUT_FILE = "./data/queries_v4.json"
QUALITY_REPORT_FILE = "./data/queries_v4_quality_report.txt"

MAX_QUERIES = 150

STOPWORDS = {
    "introduction", "related", "work", "method", "methods",
    "results", "discussion", "conclusion", "experiment",
    "experiments", "analysis", "approach", "background",
    "evaluation", "implementation", "appendix", "abstract",
    "preliminaries", "summary", "dataset", "paper", "proposed",
    "based", "using", "show", "shown", "present",
    "presented", "describe", "described", "propose", "proposed",
    "introduction", "section", "chapter", "part", "figure", "table"
}

BAD_KEYWORDS = {
    "also", "current", "practical", "suit", "towards", "new",
    "one", "two", "first", "second", "last", "final",
    "additional", "relevant", "following", "similar", "such",
    "existing", "various", "several", "different", "specific",
    "certain", "particular", "general", "main", "key", "core",
    "mechanism", "multiple", "model", "models", "system", "systems",
    "approach", "based", "using", "result", "results", "performance",
    "training", "test", "train", "data", "example", "paper", "work",
    "task", "tasks", "problem", "problems", "number", "case",
    "way", "time", "point", "form", "type", "set", "field",
    "level", "side", "part", "order", "term", "note", "end"
}

TECHNICAL_TERMS = {
    "transformer", "attention", "BERT", "GPT", "LSTM", "CNN", "RNN",
    "embedding", "encoder", "decoder", "softmax", "gradient", "loss",
    "optimizer", "adam", " SGD", "layer", "network", "neural",
    "token", "vocabulary", "sequence", "batch", "epoch", "hyperparameter",
    "backpropagation", "convergence", "regularization", "dropout",
    "batch normalization", "activation", "relu", "sigmoid", "tanh",
    "precision", "recall", "F1", "BLEU", "ROUGE", "perplexity",
    "cross-entropy", "KL divergence", "likelihood", "posterior", "prior",
    "variational", "autoencoder", "VAE", "GAN", "diffusion", "latent",
    "embedding", "attention", "self-attention", "multi-head", "positional",
    "residual", "normalization", "feed-forward", "attention mask",
    "beam search", "greedy", "sampling", "temperature", "top-k", "top-p",
    "fine-tuning", "pre-training", "transfer learning", "domain adaptation",
    "question answering", "named entity recognition", "sentiment analysis",
    "text classification", "machine translation", "summarization", "generation",
    "retrieval", "similarity", "cosine", "embedding space", "vector",
    "FAISS", "ANN", "index", "query", "document", "passage", "chunk",
    "RAG", "retrieval-augmented", "knowledge base", "information extraction"
}

QUESTION_TEMPLATES = [
    "How does {k} improve performance in neural networks?",
    "Why is {k} important for training deep learning models?",
    "What problem does {k} solve in machine learning?",
    "How does {k} differ from traditional methods?",
    "What is the role of {k} in transformer architectures?",
    "Why is {k} effective for natural language processing?",
    "How does {k} help with sequence modeling?",
    "What are the advantages of {k} in neural networks?",
    "Why does {k} improve model generalization?",
    "How does {k} affect training convergence?",
    "Why is {k} crucial for attention mechanisms?",
    "How does {k} enable better representation learning?",
    "What limitations does {k} overcome?",
    "Why is {k} essential for efficient training?"
]


def is_valid_keyword(keyword):
    keyword = keyword.lower().strip()

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
    if re.match(r"^[a-z]$", keyword):
        return False

    common_suffixes = ["ing", "tion", "ness", "ment", "able", "ible", "ed", "ly"]
    if any(keyword.endswith(s) and len(keyword) < 6 for s in common_suffixes):
        return False

    return True


def is_meaningful_phrase(phrase):
    phrase = phrase.lower()

    if phrase in TECHNICAL_TERMS:
        return True

    technical_count = sum(1 for t in TECHNICAL_TERMS if t.lower() in phrase)
    if technical_count > 0:
        return True

    if any(t in phrase for t in ["attention", "transformer", "embedding", "network", "neural", "learning", "model"]):
        return True

    return False


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()
    words = [w for w in words if w not in STOPWORDS and len(w) > 3]
    return words


def extract_keywords(text):
    words = clean_text(text)
    counter = Counter(words)
    return [w for w, _ in counter.most_common(15) if is_valid_keyword(w)]


def extract_phrases(section_titles):
    phrases = []
    for t in section_titles:
        words = clean_text(t)
        if len(words) >= 2:
            phrase = " ".join(words[:2])
            if is_valid_keyword(phrase.replace(" ", "")) and is_meaningful_phrase(phrase):
                phrases.append(phrase)
        if len(words) >= 3:
            phrase = " ".join(words[:3])
            if is_valid_keyword(phrase.replace(" ", "")) and is_meaningful_phrase(phrase):
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
    query_lower = query.lower()
    words = query_lower.split()

    if len(words) < 6:
        issues.append("问题太短")

    bad_phrases = ["mechanism enable", "multiple improve", "train test", "example example",
                   "model model", "system system", "task task", "problem problem"]
    for bp in bad_phrases:
        if bp in query_lower:
            issues.append("包含重复/无意义短语")

    if query_lower.count("does does") > 0 or query_lower.count("is is") > 0:
        issues.append("语法错误")

    if not query.endswith("?"):
        issues.append("没有问号")

    question_starters = ["how does", "how is", "how do", "how can", "how will",
                         "why is", "why does", "why do", "why can",
                         "what is", "what does", "what do", "what are",
                         "when does", "when is", "where does", "where is"]
    has_valid_starter = any(query_lower.startswith(s) for s in question_starters)
    if not has_valid_starter:
        issues.append("缺少有效疑问词")

    return issues


def main():
    print("=" * 60)
    print("Auto Query Generator v4 - 优化版")
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
            section_texts = [s.get("text", "") for s in sections]

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

    good_keywords = [k for k in keywords if is_meaningful_phrase(k)]
    if len(good_keywords) > 50:
        keywords = good_keywords

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
    quality_report.append("Query Quality Report v4")
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
v4 版本的改进 (相比 v3):

1. 扩展关键词过滤:
   - 添加更多 BAD_KEYWORDS (mechanism, multiple, train test 等)
   - 添加 TECHNICAL_TERMS 白名单
   - 使用 is_meaningful_phrase() 判断短语是否有意义

2. 技术术语识别:
   - 优先保留包含技术术语的关键词
   - 过滤掉太通用的词(model, system, task 等)
   - 过滤掉动词/形容词形式

3. 增强质量检查:
   - 检查重复短语 (mechanism enable, multiple improve)
   - 检查问题长度(至少6个词)
   - 更严格的语法检查

4. 问题模板优化:
   - 简化模板，避免语法错误
   - 使用更通用的表达
""")

    final_queries = passed_queries[:MAX_QUERIES]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_queries, f, indent=2)

    print(f"\n[4] 最终问题数量: {len(final_queries)}")
    print(f"    保存至: {OUTPUT_FILE}")

    quality_report.append(f"\nFinal saved queries: {len(final_queries)}")
    quality_report.append("\nSample queries (first 15):")
    for q in final_queries[:15]:
        quality_report.append(f"  - {q}")

    with open(QUALITY_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(quality_report))

    print(f"    质量报告: {QUALITY_REPORT_FILE}")

    print("\n" + "=" * 60)
    print("示例问题")
    print("=" * 60)
    for q in final_queries[:15]:
        print(f"  • {q}")


if __name__ == "__main__":
    main()
