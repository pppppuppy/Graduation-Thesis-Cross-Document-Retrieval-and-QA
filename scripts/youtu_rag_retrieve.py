import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_FILE = "./data/faiss.index"
META_FILE = "./data/faiss_meta.json"

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index(INDEX_FILE)

with open(META_FILE) as f:
    meta = json.load(f)


def retrieve(query, topk=5):

    emb = model.encode([query])

    D, I = index.search(np.array(emb), topk)

    results = []

    for idx in I[0]:

        results.append(meta[idx])

    return results


def multi_hop_retrieve(query):

    hop1 = retrieve(query, 3)

    context = " ".join([p["text"] for p in hop1])

    hop2 = retrieve(context, 3)

    return hop1 + hop2