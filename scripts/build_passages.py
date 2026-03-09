import os
import json
from tqdm import tqdm

INPUT_DIR = "./data/structured_v4_page"
OUTPUT_FILE = "./data/passages.json"

MAX_TOKENS = 300


def split_text(text, max_words=300):
    words = text.split()
    chunks = []

    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)

    return chunks


def build_passages():

    passages = []

    for domain in ["computer", "math", "physics"]:

        domain_dir = os.path.join(INPUT_DIR, domain)

        for file in tqdm(os.listdir(domain_dir)):

            if not file.endswith(".json"):
                continue

            path = os.path.join(domain_dir, file)

            with open(path) as f:
                paper = json.load(f)

            doc_id = paper["doc_id"]

            for sec in paper["sections"]:

                text = sec["text"]
                page = sec["start_page"]

                chunks = split_text(text)

                for c in chunks:
                    passages.append({
                        "doc_id": doc_id,
                        "page": page,
                        "text": c
                    })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(passages, f, indent=2)


if __name__ == "__main__":
    build_passages()