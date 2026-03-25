import json
import os
import re
import random
from collections import Counter

INPUT_DIR = "./data/structured_v4_page"
OUTPUT_FILE = "./data/queries_v2.json"

MAX_QUERIES = 150

STOPWORDS = {
    "introduction","related","work","method","methods",
    "results","discussion","conclusion","experiment",
    "experiments","analysis","approach","background",
    "evaluation","implementation"
}

QUESTION_TEMPLATES = [
    "how does {k} work",
    "why is {k} important in deep learning",
    "what problem does {k} solve",
    "how does {k} improve model performance",
    "what is the role of {k} in neural networks",
    "how is {k} different from traditional methods",
    "why is {k} effective in machine learning"
]


def clean_text(text):

    text = text.lower()

    text = re.sub(r"[^a-z0-9\s]", " ", text)

    words = text.split()

    words = [w for w in words if w not in STOPWORDS and len(w) > 3]

    return words


def extract_keywords(text):

    words = clean_text(text)

    counter = Counter(words)

    return [w for w,_ in counter.most_common(5)]


def extract_phrases(section_titles):

    phrases = []

    for t in section_titles:

        words = clean_text(t)

        if len(words) >= 2:

            phrases.append(" ".join(words[:2]))

        if len(words) >= 3:

            phrases.append(" ".join(words[:3]))

    return phrases


def build_queries(keywords):

    queries = []

    for k in keywords:

        template = random.choice(QUESTION_TEMPLATES)

        queries.append(template.format(k=k))

    return queries


def main():

    keywords = []

    paper_count = 0

    for root, dirs, files in os.walk(INPUT_DIR):

        for f in files:

            if not f.endswith(".json"):
                continue

            path = os.path.join(root,f)

            with open(path,"r",encoding="utf-8") as file:

                paper = json.load(file)

            paper_count += 1

            title = paper.get("title","")

            abstract = paper.get("abstract","")

            sections = paper.get("sections",[])

            section_titles = [s.get("section_title","") for s in sections]

            keywords += extract_keywords(title)
            keywords += extract_keywords(abstract)

            keywords += extract_phrases(section_titles)

    print("Raw keywords:",len(keywords))

    keywords = list(set(keywords))

    print("Unique keywords:",len(keywords))

    queries = build_queries(keywords)

    queries = list(set(queries))

    random.shuffle(queries)

    queries = queries[:MAX_QUERIES]

    print("Final queries:",len(queries))
    print("Papers processed:",paper_count)

    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:

        json.dump(queries,f,indent=2)

    print("Queries saved to",OUTPUT_FILE)


if __name__ == "__main__":
    main()