import os
import json
import re
import time
import random
import urllib.request
import urllib.error

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
OUTPUT_FILE = "./data/qa_dataset/multihop_qa_v3.json"

TARGET_QA = 500


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


def retrieve_passages(query, passages, topk=5):
    query_words = set(query.lower().split())
    scored = []
    for p in passages:
        text_words = set(p.get("text", "").lower().split())
        overlap = len(query_words & text_words)
        scored.append((overlap, random.random(), p))
    scored.sort(reverse=True)
    return scored[:topk]


SYSTEM_PROMPT = """你是一个学术问答助手，基于提供的证据生成多跳问答对。

规则：
- 问题必须基于提供的证据
- 必须使用证据中的 doc_id 和 page
- 返回 JSON 格式
"""


def extract_json(text):
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
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
        "max_tokens": 800
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
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result["choices"][0]["message"]["content"]
            return extract_json(text)
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} - {e.reason}")
        print(e.read().decode('utf-8')[:200])
    except Exception as e:
        print(f"Error: {e}")
    return None


def build_prompt(query, evidence, reasoning_type):
    evidence_text = ""
    for i, e in enumerate(evidence):
        doc_id = e.get("doc_id", "")
        page = e.get("page", 1)
        text = e.get("text", "")[:300]
        evidence_text += f"[证据{i+1}] doc_id={doc_id}, page={page}\n{text}\n\n"

    prompt = f"""基于以下证据，生成一个多跳问答对。

问题主题：{query}
推理类型：{reasoning_type}

证据：
{evidence_text}

要求：
1. 问题必须结合至少两个证据才能回答
2. 答案必须来自提供的证据
3. evidence 中的 doc_id 和 page 必须从上述证据中选取

请返回JSON格式：
{{"question": "问题", "answer": "答案", "evidence": [{{"doc_id": "文件名", "page": 页码}}]}}"""

    return prompt


def quality_check(qa):
    if not qa:
        return False, "空结果"
    if len(qa.get("question", "")) < 10:
        return False, "问题太短"
    if len(qa.get("answer", "")) < 5:
        return False, "答案太短"
    if not qa.get("evidence"):
        return False, "无证据"
    return True, "通过"


def main():
    passages = load_passages()
    queries = load_queries()

    qa_dataset = []
    question_set = set()

    print(f"\n目标: {TARGET_QA} QA对")
    print("=" * 50)

    attempts = 0
    max_attempts = TARGET_QA * 5
    fail_count = 0

    while len(qa_dataset) < TARGET_QA and attempts < max_attempts:
        attempts += 1

        query = random.choice(queries)
        if isinstance(query, dict):
            query = query.get("query", query.get("question", str(query)))

        evidence_list = retrieve_passages(query, passages, topk=5)
        if not evidence_list:
            continue

        evidence = [{"doc_id": e[2]["doc_id"], "page": e[2]["page"], "text": e[2]["text"]} for e in evidence_list]

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

        print(f"[{len(qa_dataset)}/{TARGET_QA}] {qa['question'][:50]}...")

        if len(qa_dataset) % 10 == 0:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(qa_dataset, f, indent=2, ensure_ascii=False)

        time.sleep(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(qa_dataset, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print(f"完成! 总QA: {len(qa_dataset)}/{TARGET_QA}")
    print(f"失败次数: {fail_count}")


if __name__ == "__main__":
    main()
