import os
import json
import re
import time
import random
import urllib.request
import urllib.error
import numpy as np

def get_api_key():
    key_file = os.path.join(os.path.dirname(__file__), "..", "deepseek_key.txt")
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            return f.read().strip()
    return os.environ.get("DEEPSEEK_API_KEY", "")

API_KEY = get_api_key()
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

PASSAGE_FILE = "./data/passages.json"
QUERY_FILE = "./data/queries_v5.json"
OUTPUT_FILE = "./data/qa_dataset/multihop_qa_v4.json"

EMBEDDINGS_FILE = "./data/bge_embeddings.npy"
META_FILE = "./data/faiss_bge_meta.json"

TARGET_QA = 550

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder

    print("正在加载BGE检索模型...")
    bi_encoder = SentenceTransformer("BAAI/bge-base-en-v1.5")
    print("正在加载Cross-Encoder重排序模型...")
    cross_encoder = CrossEncoder("BAAI/bge-reranker-base")

    passages = json.load(open(PASSAGE_FILE, "r", encoding="utf-8"))
    embeddings = np.load(EMBEDDINGS_FILE)
    passages_meta = json.load(open(META_FILE, "r", encoding="utf-8"))

    print(f"已加载 {len(passages)} 段落, {len(passages_meta)} 元数据")

    USE_BGE_RERANK = True

except ImportError:
    print("警告: sentence-transformers 未安装，将使用简单检索")
    USE_BGE_RERANK = False
except Exception as e:
    print(f"警告: 加载模型失败: {e}，将使用简单检索")
    USE_BGE_RERANK = False


def load_passages():
    with open(PASSAGE_FILE, "r", encoding="utf-8") as f:
        passages = json.load(f)
    print(f"加载 passages: {len(passages)}")
    return passages


def load_queries():
    with open(QUERY_FILE, "r", encoding="utf-8") as f:
        queries = json.load(f)
    print(f"加载 queries: {len(queries)}")
    return queries


def bge_rerank_retrieve(query, passages, embeddings, passages_meta, topk=20, rerank_top=5):
    query_emb = bi_encoder.encode([query]).astype('float32')
    query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)

    scores = query_emb @ embeddings.T
    scores = scores[0]

    top_indices = np.argsort(scores)[::-1][:topk]

    candidates = []
    for idx in top_indices:
        candidates.append(passages_meta[idx])

    if len(candidates) == 0:
        return []

    pairs = [(query, p["text"][:500]) for p in candidates]
    rerank_scores = cross_encoder.predict(pairs)

    ranked_indices = np.argsort(rerank_scores)[::-1][:rerank_top]

    results = [candidates[i] for i in ranked_indices]

    return results


def simple_retrieve(query, passages, topk=5):
    query_words = set(query.lower().split())
    scored = []
    for p in passages:
        text_words = set(p.get("text", "").lower().split())
        overlap = len(query_words & text_words)
        scored.append((overlap, random.random(), p))
    scored.sort(reverse=True)
    return [s[2] for s in scored[:topk]]


def retrieve_passages(query, passages, embeddings=None, passages_meta=None, topk=5):
    if USE_BGE_RERANK and embeddings is not None:
        return bge_rerank_retrieve(query, passages, embeddings, passages_meta, topk=20, rerank_top=topk)
    else:
        return simple_retrieve(query, passages, topk)


SYSTEM_PROMPT = """你是一个专业的学术问答对生成专家。你的任务是基于提供的证据段落，生成高质量的多跳问答对。

## 核心要求

1. **问题必须需要多步推理**：问题必须结合至少两个独立的证据才能完整回答
2. **答案必须精确**：答案必须直接来自提供的证据，不能添加外部知识
3. **证据选择正确**：在返回的evidence中，必须选择真正用于回答问题的证据的doc_id和page

## 推理类型说明

- **sequential（串行推理）**：问题需要按逻辑顺序逐步推理
  - 例如："A是如何导致B的，B又是如何影响C的？"
  - 需要先理解A→B的关系，再理解B→C的关系

- **parallel（并行推理）**：问题需要同时综合多个独立证据
  - 例如："哪位科学家因在A领域和B领域的贡献而获奖？"
  - 需要同时获取两个领域的证据并综合

## 问题质量标准

- 问题要具体、专业、基于学术内容
- 避免过于宽泛或模糊的问题
- 问题应该体现对学术内容的深入理解

## 输出格式

请返回JSON格式：
{
  "question": "具体的问题内容",
  "answer": "基于证据的详细答案",
  "evidence": [{"doc_id": "文件名.pdf", "page": 页码}]
}

注意：evidence必须只包含真正用于回答问题的证据，不要包含无关证据。"""


def extract_json(text):
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            result = json.loads(match.group())
            if "question" in result and "answer" in result:
                return result
        except:
            pass
    return None


def call_llm(prompt):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    data_bytes = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(
        API_URL,
        data=data_bytes,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result["choices"][0]["message"]["content"]
            return extract_json(text)
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} - {e.reason}")
        try:
            print(e.read().decode('utf-8')[:200])
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")
    return None


def build_prompt(query, evidence, reasoning_type):
    evidence_text = ""
    for i, e in enumerate(evidence):
        doc_id = e.get("doc_id", "")
        page = e.get("page", 1)
        text = e.get("text", "")[:400]
        evidence_text += f"[证据{i+1}] doc_id={doc_id}, page={page}\n{text}\n\n"

    prompt = f"""请基于以下证据，生成一个高质量的多跳问答对。

问题主题：{query}
推理类型：{reasoning_type}

证据：
{evidence_text}

要求：
1. 问题必须结合至少两个证据才能完整回答
2. 答案必须直接来自证据，不要添加外部知识
3. evidence中只选择真正用于回答问题的证据

请返回JSON格式：
{{"question": "问题", "answer": "答案", "evidence": [{{"doc_id": "文件名", "page": 页码}}]}}"""

    return prompt


def quality_check(qa):
    if not qa:
        return False, "空结果"

    question = qa.get("question", "")
    answer = qa.get("answer", "")
    evidence = qa.get("evidence", [])

    if len(question) < 15:
        return False, "问题太短"
    if len(answer) < 10:
        return False, "答案太短"
    if not evidence or len(evidence) < 1:
        return False, "无证据"

    if "doc_id" not in evidence[0] or "page" not in evidence[0]:
        return False, "证据格式错误"

    if len(question.split()) < 5:
        return False, "问题字数不足"

    return True, "通过"


def main():
    passages = load_passages()
    queries = load_queries()

    embeddings = None
    passages_meta = None
    if USE_BGE_RERANK:
        try:
            embeddings = np.load(EMBEDDINGS_FILE)
            with open(META_FILE, "r", encoding="utf-8") as f:
                passages_meta = json.load(f)
            print("BGE检索+重排序已启用")
        except Exception as e:
            print(f"加载BGE索引失败: {e}")

    qa_dataset = []
    question_set = set()

    print(f"\n目标: {TARGET_QA} QA对")
    print(f"检索模式: {'BGE+重排序' if USE_BGE_RERANK else '简单检索'}")
    print("=" * 50)

    attempts = 0
    max_attempts = TARGET_QA * 5
    fail_count = 0

    while len(qa_dataset) < TARGET_QA and attempts < max_attempts:
        attempts += 1

        query = random.choice(queries)
        if isinstance(query, dict):
            query = query.get("query", query.get("question", str(query)))

        evidence = retrieve_passages(query, passages, embeddings, passages_meta, topk=5)
        if not evidence:
            continue

        reasoning_type = random.choice(["sequential", "parallel"])

        prompt = build_prompt(query, evidence, reasoning_type)

        qa = call_llm(prompt)

        if qa is None:
            fail_count += 1
            if fail_count % 10 == 0:
                print(f"[失败 {fail_count}次] 继续...")
            continue

        is_valid, reason = quality_check(qa)
        if not is_valid:
            fail_count += 1
            continue

        if qa["question"] in question_set:
            continue

        qa["type"] = reasoning_type
        qa["query"] = query

        qa_dataset.append(qa)
        question_set.add(qa["question"])

        print(f"[{len(qa_dataset)}/{TARGET_QA}] {qa['question'][:60]}...")

        if len(qa_dataset) % 10 == 0:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(qa_dataset, f, indent=2, ensure_ascii=False)

        time.sleep(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(qa_dataset, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print(f"完成! 总QA: {len(qa_dataset)}/{TARGET_QA}")
    print(f"失败次数: {fail_count}")
    print(f"输出文件: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
