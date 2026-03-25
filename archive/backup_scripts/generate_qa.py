import json
import os
import re
import random
from openai import OpenAI
from youtu_rag_retrieve import multi_hop_retrieve

# ==============================
# 参数
# ==============================

TARGET_QA = 500

PASSAGE_FILE = "./data/passages.json"
OUTPUT_FILE = "./data/qa_dataset/logical_multihop_qa.json"

# ==============================
# API
# ==============================

client = OpenAI(
    api_key="sk-53d228caca6c4f3ab32443ea7769ca38",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ==============================
# PROMPT
# ==============================

PROMPT_SERIAL = """
请基于证据生成一个【串行推理】问题。

要求：
必须先通过证据A得到中间结论B，再通过B得到最终答案C。

只返回JSON：

{
  "question": "...",
  "answer": "...",
  "logic_path": "...",
  "evidence": [{"doc_id":"...", "page":1}]
}

证据：
"""

PROMPT_PARALLEL = """
请基于证据生成一个【并行推理】问题。

要求：
答案必须同时依赖两个不同证据。

只返回JSON：

{
  "question": "...",
  "answer": "...",
  "logic_path": "...",
  "evidence": [{"doc_id":"...", "page":1}]
}

证据：
"""

# ==============================
# JSON提取
# ==============================

def extract_json(text):

    text = text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("JSON not found")

    json_text = match.group()

    return json.loads(json_text)

# ==============================
# 自动生成 queries
# ==============================

def build_queries():

    with open(PASSAGE_FILE, "r", encoding="utf-8") as f:
        passages = json.load(f)

    queries = []

    for p in passages:

        text = p["text"]

        words = text.split()

        if len(words) > 8:

            q = " ".join(words[:6])

            queries.append(q)

    return queries

# ==============================
# QA生成
# ==============================

def generate_complex_qa(evidence, mode):

    context = ""

    for e in evidence:

        context += f"[source:{e['doc_id']}, page:{e['page']}] {e['text']}\n"

    prompt = PROMPT_SERIAL if mode == "serial" else PROMPT_PARALLEL

    response = client.chat.completions.create(
        model="qwen-max",
        messages=[{"role": "user", "content": prompt + context}]
    )

    text = response.choices[0].message.content

    return extract_json(text)

# ==============================
# 质量过滤
# ==============================

def quality_filter(qa):

    if len(qa["question"]) < 12:
        return False

    if len(qa["answer"]) < 5:
        return False

    return True

# ==============================
# 主函数
# ==============================

def main():



    queries = build_queries()

    print("自动生成queries:", len(queries))

    dataset = []

    question_set = set()

    # 读取已有数据
    if os.path.exists(OUTPUT_FILE):

        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        for q in dataset:
            question_set.add(q["question"])

        print("已加载已有QA:", len(dataset))

    while len(dataset) < TARGET_QA:

        query = random.choice(queries)

        print("\n当前query:", query)

        evidence = multi_hop_retrieve(query)

        for mode in ["serial", "parallel"]:

            try:

                qa = generate_complex_qa(evidence, mode)

                if qa["question"] in question_set:
                    continue

                if not quality_filter(qa):
                    continue

                dataset.append(qa)

                question_set.add(qa["question"])

                print("生成:", qa["question"])

                if len(dataset) % 5 == 0:

                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(dataset, f, indent=2, ensure_ascii=False)

                    print("已保存:", len(dataset))

            except Exception as e:

                print("生成失败:", e)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n完成，总QA:", len(dataset))


if __name__ == "__main__":
    main()