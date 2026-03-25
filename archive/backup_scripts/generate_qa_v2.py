import json
import os
import re
import random
from openai import OpenAI
from youtu_rag_retrieve import multi_hop_retrieve

TARGET_QA = 100

PASSAGE_FILE = "./data/passages.json"
QUERIES_FILE = "./data/queries_v5.json"
OUTPUT_FILE = "./data/qa_dataset/multihop_qa.json"


def get_api_key():
    key_file = "./api_key.txt"
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            return f.read().strip()
    return os.environ.get("DASHSCOPE_API_KEY", "")


api_key = get_api_key()
if not api_key:
    print("[!] 请在 api_key.txt 文件中设置 API Key")
    exit(1)

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

PROMPT_SERIAL = """
请基于证据生成一个【串行推理】多跳问题。

要求：
1. 问题需要结合多个证据才能回答
2. 必须先通过证据A得到中间结论B，再通过B得到最终答案C
3. 问题必须与提供的证据内容相关

只返回JSON，不要其他内容：

{
  "question": "问题内容",
  "answer": "答案内容",
  "evidence": [{"doc_id":"文件名", "page":页码}]
}

证据：
"""

PROMPT_PARALLEL = """
请基于证据生成一个【并行推理】多跳问题。

要求：
1. 问题需要结合两个不同证据才能回答
2. 答案必须同时依赖两个不同方面的证据
3. 问题必须与提供的证据内容相关

只返回JSON，不要其他内容：

{
  "question": "问题内容",
  "answer": "答案内容",
  "evidence": [{"doc_id":"文件名", "page":页码}]
}

证据：
"""


def extract_json(text):
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("JSON not found")
    return json.loads(match.group())


def load_queries():
    with open(QUERIES_FILE, "r", encoding="utf-8") as f:
        queries = json.load(f)
    print(f"加载 queries: {len(queries)}")
    return queries


def generate_qa(evidence, mode):
    context = ""
    for e in evidence:
        context += f"[{e['doc_id']} p{e['page']}] {e['text'][:300]}\n"

    prompt = PROMPT_SERIAL if mode == "serial" else PROMPT_PARALLEL

    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=[{"role": "user", "content": prompt + context}],
            temperature=0.8
        )
        text = response.choices[0].message.content
        return extract_json(text)
    except Exception as e:
        print(f"API error: {e}")
        return None


def quality_filter(qa):
    if not qa:
        return False
    if len(qa.get("question", "")) < 10:
        return False
    if len(qa.get("answer", "")) < 5:
        return False
    if "evidence" not in qa:
        return False
    return True


def main():
    queries = load_queries()

    dataset = []
    question_set = set()

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        for q in dataset:
            question_set.add(q["question"])
        print(f"已加载QA: {len(dataset)}")

    print(f"\n目标: {TARGET_QA} QA对")
    print("=" * 50)

    serial_count = sum(1 for q in dataset if q.get("type") == "serial")
    parallel_count = sum(1 for q in dataset if q.get("type") == "parallel")
    print(f"当前: 串行={serial_count}, 并行={parallel_count}")

    attempts = 0
    max_attempts = TARGET_QA * 3

    while len(dataset) < TARGET_QA and attempts < max_attempts:
        attempts += 1

        query = random.choice(queries)
        evidence = multi_hop_retrieve(query)

        if not evidence:
            continue

        mode = random.choice(["serial", "parallel"])

        try:
            qa = generate_qa(evidence, mode)

            if not qa:
                continue

            if qa["question"] in question_set:
                print(f"[重复] {qa['question'][:50]}")
                continue

            if not quality_filter(qa):
                print(f"[质量问题] 跳过")
                continue

            qa["type"] = mode
            qa["query"] = query

            dataset.append(qa)
            question_set.add(qa["question"])

            print(f"[{mode[:3]}] {qa['question'][:60]}...")

            if len(dataset) % 10 == 0:
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(dataset, f, indent=2, ensure_ascii=False)
                print(f"  -> 已保存 {len(dataset)}")

        except Exception as e:
            print(f"[错误] {e}")
            continue

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print(f"完成! 总QA: {len(dataset)}")
    print(f"  串行: {sum(1 for q in dataset if q.get('type') == 'serial')}")
    print(f"  并行: {sum(1 for q in dataset if q.get('type') == 'parallel')}")


if __name__ == "__main__":
    main()
