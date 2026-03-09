import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

PASSAGE_FILE = "./data/passages.json"
INDEX_FILE = "./data/faiss.index"
META_FILE = "./data/faiss_meta.json"


def main():

    with open(PASSAGE_FILE) as f:
        passages = json.load(f)

    texts = [p["text"] for p in passages]

    model = SentenceTransformer("all-MiniLM-L6-v2")

    embeddings = model.encode(texts, show_progress_bar=True)

    dim = embeddings.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    faiss.write_index(index, INDEX_FILE)

    with open(META_FILE, "w") as f:
        json.dump(passages, f)


if __name__ == "__main__":
    main()