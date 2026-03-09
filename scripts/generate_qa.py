import json
import os
from openai import OpenAI
from youtu_rag_retrieve import multi_hop_retrieve

# 阿里云百炼配置
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 结构 1：串行逻辑 (A -> B -> C)
PROMPT_SERIAL = """
请基于证据生成一个【串行推理】问题。
要求：必须先通过证据A推理出中间结论B，再根据B得到最终答案C。
必须返回如下格式的JSON：
{
  "question": "...",
  "answer": "...",
  "logic_path": "简述A->B->C的推理过程",
  "evidence": [{"doc_id": "...", "page": ...}, ...]
}
证据: {context}
"""

# 结构 2：并行聚合逻辑 (A, B -> C)
PROMPT_PARALLEL = """
请基于证据生成一个【并行推理】问题。
要求：证据中包含两个独立的事实A和B，回答最终问题C必须同时结合A和B的信息。
必须返回如下格式的JSON：
{
  "question": "...",
  "answer": "...",
  "logic_path": "简述如何结合A和B得出C",
  "evidence": [{"doc_id": "...", "page": ...}, ...]
}
证据: {context}
"""


def generate_complex_qa(evidence, mode="serial"):
    context = ""
    for e in evidence:
        context += f"[来源:{e['doc_id']}, 页码:{e['page']}] 内容: {e['text']}\n"

    prompt = PROMPT_SERIAL if mode == "serial" else PROMPT_PARALLEL

    response = client.chat.completions.create(
        model="qwen-max",
        messages=[{"role": "user", "content": prompt + context}]
    )

    return json.loads(response.choices[0].message.content.replace("```json", "").replace("```", ""))


def main():
    queries = ["BERT attention mechanism", "Transformer training stability"]
    dataset = []

    for q in queries:
        evidence = multi_hop_retrieve(q)
        # 依次生成两种逻辑
        for mode in ["serial", "parallel"]:
            try:
                qa = generate_complex_qa(evidence, mode=mode)
                dataset.append(qa)
            except Exception as e:
                print(f"生成失败: {e}")

    with open("./data/qa_dataset/logical_multihop_qa.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()