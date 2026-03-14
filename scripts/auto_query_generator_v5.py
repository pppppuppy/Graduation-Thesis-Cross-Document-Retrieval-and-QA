import json
import os
import random
from collections import Counter

INPUT_DIR = "./data/structured_v4_page"
OUTPUT_FILE = "./data/queries_v5.json"
QUALITY_REPORT_FILE = "./data/queries_v5_quality_report.txt"

MAX_QUERIES = 200
BATCH_SIZE = 15

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


SYSTEM_PROMPT = """You are an expert in machine learning and natural language processing.
Generate diverse, specific research questions based on academic paper content."""


def get_api_key():
    return os.environ.get("DASHSCOPE_API_KEY", "")


def load_papers():
    papers = []
    for root, dirs, files in os.walk(INPUT_DIR):
        for f in files:
            if not f.endswith(".json"):
                continue
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                paper = json.load(file)
            papers.append(paper)
    return papers


def extract_content_for_llm(paper, max_length=2500):
    content = []
    title = paper.get("title", "")
    if title:
        content.append(f"Title: {title}")

    abstract = paper.get("abstract", "")
    if abstract:
        content.append(f"Abstract: {abstract[:600]}")

    sections = paper.get("sections", [])
    for sec in sections[:6]:
        sec_title = sec.get("section_title", "")
        sec_text = sec.get("text", "")[:400]
        if sec_title and sec_text:
            content.append(f"{sec_title}: {sec_text}")

    return "\n".join(content)[:max_length]


def generate_questions_with_qwen(content, api_key, num_questions=15):
    if not REQUESTS_AVAILABLE or not api_key:
        return None

    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    diverse_templates = [
        "Generate {n} diverse research questions covering: (1) method details, (2) experimental results, (3) theoretical properties, (4) comparisons with baselines, (5) applications. Make each question unique and specific to the paper content.",
        "Based on this paper, create {n} different types of questions: definition questions, comparison questions, cause-effect questions, advantage questions, and limitation questions. Each must be specific.",
        "Write {n} research questions that can be answered by reading this paper. Vary the question types: how, why, what, compare, explain.",
    ]

    template = random.choice(diverse_templates).format(n=num_questions)

    user_prompt = f"""Paper content:
{content}

{template}

Return ONLY a JSON array of questions."""

    data = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 3000
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            content_str = result["choices"][0]["message"]["content"]
            questions = json.loads(content_str)
            if isinstance(questions, list):
                return questions
    except Exception as e:
        print(f"API error: {e}")

    return None


def generate_questions_fallback(num_questions=15):
    keywords = [
        "attention mechanism", "transformer", "neural network", "deep learning",
        "machine translation", "language model", "BERT", "GPT", "embedding",
        "encoder", "decoder", "self-attention", "multi-head attention",
        "pre-training", "fine-tuning", "transfer learning", "gradient descent",
        "optimization", "loss function", "backpropagation", "batch normalization",
        "dropout", "regularization", "cross-entropy", "perplexity", "BLEU score",
        "word embedding", "positional encoding", "residual connection", "layer normalization",
        "feed-forward network", "softmax", "query key value", "attention span",
        "tokenization", "subword", "BPE", "WordPiece", "SentencePiece",
        "sequence-to-sequence", "encoder-decoder", "beam search", "greedy decoding",
        "teacher forcing", "cross-attention", "masked language model", "next sentence prediction"
    ]

    templates = [
        "How does {k} improve neural network performance?",
        "Why is {k} important in deep learning?",
        "What are the advantages of {k}?",
        "How does {k} differ from traditional methods?",
        "What is the role of {k} in {k2}?",
        "Why does {k} improve model generalization?",
        "How does {k} affect training convergence?",
        "What limitations does {k} overcome?",
        "Why is {k} effective for NLP tasks?",
        "How does {k} enable better representation learning?",
        "What is the impact of {k} on model efficiency?",
        "Why does {k} reduce overfitting?",
        "How does {k} improve computational speed?",
        "What are the benefits of {k} in transformers?",
        "How does {k} enhance model accuracy?"
    ]

    k2_options = ["transformer", "neural network", "NLP", "deep learning",
                  "BERT", "GPT", "sequence model", "language model"]

    questions = []
    for _ in range(num_questions):
        k = random.choice(keywords)
        k2 = random.choice(k2_options)
        template = random.choice(templates)
        q = template.format(k=k, k2=k2)
        questions.append(q)

    return questions


def check_query_quality(query):
    issues = []
    query_lower = query.lower()
    words = query_lower.split()

    if len(words) < 5:
        issues.append("问题太短")

    bad_patterns = ["lstm lstm", "model model", "test test", "train train",
                   "example example", "task task", "neural neural"]
    for bp in bad_patterns:
        if bp in query_lower:
            issues.append("包含重复词")

    if query_lower.count("does does") > 0 or query_lower.count("is is") > 0:
        issues.append("语法错误")

    if not query.endswith("?"):
        issues.append("没有问号")

    question_starters = ["how does", "how is", "how do", "how can",
                         "why is", "why does", "why do",
                         "what is", "what does", "what are",
                         "when", "where", "which"]
    has_valid_starter = any(query_lower.startswith(s) for s in question_starters)
    if not has_valid_starter:
        issues.append("缺少有效疑问词")

    return issues


def main():
    print("=" * 60)
    print("Auto Query Generator v5 - 改进版")
    print("=" * 60)

    api_key = get_api_key()

    if api_key:
        print(f"\n[✓] 检测到 Qwen API Key")
    else:
        print(f"\n[!] 未检测到 API Key，将使用备用方案")
        print("    请设置环境变量: set DASHSCOPE_API_KEY=your_key")

    papers = load_papers()
    print(f"[1] 加载论文数量: {len(papers)}")

    all_questions = []

    if api_key and REQUESTS_AVAILABLE:
        print(f"\n[2] 使用 Qwen API 生成问题...")

        papers_to_process = min(20, len(papers))

        for i, paper in enumerate(papers[:papers_to_process]):
            content = extract_content_for_llm(paper)
            title = paper.get("title", "")[:30]
            print(f"  处理论文 {i+1}/{papers_to_process}: {title}...")

            questions = generate_questions_with_qwen(content, api_key, BATCH_SIZE)

            if questions:
                all_questions.extend(questions)
                print(f"    -> 生成 {len(questions)} 个问题")
            else:
                fallback = generate_questions_fallback(BATCH_SIZE)
                all_questions.extend(fallback)
                print(f"    -> API失败，使用备用 {len(fallback)} 个")

            if len(all_questions) >= MAX_QUERIES * 1.5:
                break
    else:
        print(f"\n[2] 使用备用方案生成问题...")
        for paper in papers[:20]:
            content = extract_content_for_llm(paper)
            questions = generate_questions_fallback(BATCH_SIZE)
            all_questions.extend(questions)

    all_questions = [q.strip() for q in all_questions if q.strip()]
    all_questions = list(set(all_questions))
    random.shuffle(all_questions)
    all_questions = all_questions[:MAX_QUERIES]

    print(f"\n[3] 生成的问题总数: {len(all_questions)}")

    print("\n" + "=" * 60)
    print("质量检查")
    print("=" * 60)

    quality_report = []
    quality_report.append("=" * 60)
    quality_report.append("Query Quality Report v5 - Improved")
    quality_report.append("=" * 60)
    quality_report.append(f"API Used: {bool(api_key)}")
    quality_report.append(f"Source: Qwen API" if api_key else "Fallback")

    passed_queries = []
    failed_queries = []

    for q in all_questions:
        issues = check_query_quality(q)
        if not issues:
            passed_queries.append(q)
        else:
            failed_queries.append((q, issues))

    pass_rate = len(passed_queries)/len(all_questions)*100 if all_questions else 0

    print(f"\n通过质量检查: {len(passed_queries)}/{len(all_questions)} ({pass_rate:.1f}%)")
    print(f"未通过: {len(failed_queries)}")

    if failed_queries:
        print("\n未通过原因统计:")
        issue_counter = Counter()
        for q, issues in failed_queries:
            for issue in issues:
                issue_counter[issue] += 1
        for issue, count in issue_counter.most_common():
            print(f"  - {issue}: {count}")

    final_queries = passed_queries[:MAX_QUERIES]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_queries, f, indent=2)

    print(f"\n[4] 最终问题数量: {len(final_queries)}")
    print(f"    保存至: {OUTPUT_FILE}")

    quality_report.append(f"\nTotal: {len(all_questions)}")
    quality_report.append(f"Passed: {len(passed_queries)} ({pass_rate:.1f}%)")
    quality_report.append("\nSample queries:")
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
