import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os

PASSAGES_FILE = "./data/passages.json"
EMBEDDINGS_FILE = "./data/bge_embeddings.npy"
META_FILE = "./data/faiss_bge_meta.json"


def build_bge_index(passages, model_name="BAAI/bge-base-en-v1.5"):
    print(f"正在加载模型: {model_name}")
    model = SentenceTransformer(model_name)

    print(f"正在构建 {len(passages)} 个段落的索引...")
    texts = [p["text"] for p in passages]

    print("正在生成BGE向量（这需要几分钟）...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    embeddings = embeddings.astype('float32')

    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    dimension = embeddings.shape[1]
    print(f"向量维度: {dimension}")

    print("正在保存...")
    np.save(EMBEDDINGS_FILE, embeddings)

    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(passages, f, ensure_ascii=False)

    print("索引构建完成！")
    print(f"  - 向量文件: {EMBEDDINGS_FILE}")
    print(f"  - 元数据: {META_FILE}")

    return model, embeddings


class BGERetriever:
    def __init__(self, model_name="BAAI/bge-base-en-v1.5"):

        if not os.path.exists(EMBEDDINGS_FILE) or not os.path.exists(META_FILE):
            raise FileNotFoundError(
                f"索引文件不存在，请先运行本脚本构建索引"
            )

        print(f"正在加载模型: {model_name}")
        self.model = SentenceTransformer(model_name)

        self.embeddings = np.load(EMBEDDINGS_FILE)

        with open(META_FILE, "r", encoding="utf-8") as f:
            self.passages = json.load(f)

        print(f"加载完成: 模型={model_name}, 段落数={len(self.passages)}, 向量维度={self.embeddings.shape[1]}")

    def retrieve(self, query, topk=5):
        query_emb = self.model.encode([query]).astype('float32')
        query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)

        scores = query_emb @ self.embeddings.T
        scores = scores[0]

        top_indices = np.argsort(scores)[::-1][:topk]

        results = []
        for idx in top_indices:
            results.append(self.passages[idx])

        return results

    def multi_hop_retrieve(self, query, topk=5):
        hop1 = self.retrieve(query, topk=topk * 2)

        context_parts = [query]
        for i, p in enumerate(hop1[:2]):
            context_parts.append(f"[Evidence {i+1}]: {p['text'][:200]}")
        enhanced_query = " | ".join(context_parts)

        hop2 = self.retrieve(enhanced_query, topk=topk)

        seen = set()
        results = []
        for p in hop1 + hop2:
            if p['doc_id'] not in seen:
                seen.add(p['doc_id'])
                results.append(p)

        return results[:topk]


if __name__ == "__main__":
    print("=" * 50)
    print("BGE 检索系统 - 构建索引")
    print("=" * 50)

    print("\n正在加载 passages...")
    with open(PASSAGES_FILE, "r", encoding="utf-8") as f:
        passages = json.load(f)
    print(f"加载了 {len(passages)} 个段落")

    if not os.path.exists(EMBEDDINGS_FILE):
        print("\n正在构建BGE索引（首次运行需要下载模型，约440MB）...")
        print("这可能需要5-10分钟，请耐心等待...")
        model, embeddings = build_bge_index(passages)
    else:
        print("\n索引已存在，跳过构建步骤")

    print("\n正在加载检索器...")
    retriever = BGERetriever()

    test_queries = [
        "How does attention mechanism improve neural network performance?",
        "What is the role of embedding in transformer?",
        "How does BERT pre-training work?",
    ]

    for query in test_queries:
        print("\n" + "=" * 50)
        print(f"查询: {query}")
        print("=" * 50)

        results = retriever.retrieve(query, topk=5)

        print(f"\n返回 {len(results)} 个最相关段落:")
        for i, r in enumerate(results):
            print(f"\n[{i+1}] {r['doc_id']} (page {r['page']})")
            print(f"    {r['text'][:150]}...")

    print("\n\n测试多跳检索...")
    mh_query = "How does SentencePiece reduce overfitting and improve model performance?"
    mh_results = retriever.multi_hop_retrieve(mh_query, topk=5)
    print(f"\n多跳查询: {mh_query}")
    print(f"返回 {len(mh_results)} 个结果:")
    for i, r in enumerate(mh_results):
        print(f"  [{i+1}] {r['doc_id']} (page {r['page']})")
