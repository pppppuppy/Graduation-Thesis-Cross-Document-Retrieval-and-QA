import json
import os
import re
import random
from collections import Counter

INPUT_DIR = "./data/structured_v4_page"
OUTPUT_FILE = "./data/queries.json"

MAX_QUERIES = 150

STOPWORDS = {
"introduction","related","work","method","methods",
"results","discussion","conclusion","experiment",
"experiments","analysis","approach","background",
"evaluation","implementation"
}


def clean_text(text):

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    words = text.split()

    words = [w for w in words if w not in STOPWORDS and len(w) > 3]

    return words


def extract_queries_from_title(title):

    words = clean_text(title)

    if len(words) >= 2:
        return [" ".join(words[:3])]

    return []


def extract_queries_from_sections(sections):

    queries = []

    for sec in sections:

        title = sec.get("section_title","")

        words = clean_text(title)

        if len(words) >= 2:

            q = " ".join(words[:3])

            queries.append(q)

    return queries


def extract_queries_from_abstract(abstract):

    words = clean_text(abstract)

    counter = Counter(words)

    keywords = [w for w,_ in counter.most_common(5)]

    queries = []

    for k in keywords:

        queries.append(k + " transformer")

    return queries


def filter_queries(queries):

    filtered = []

    for q in queries:

        words = q.split()

        if 2 <= len(words) <= 4:
            filtered.append(q)

    return list(set(filtered))


def main():

    queries = []

    paper_count = 0

    for root, dirs, files in os.walk(INPUT_DIR):

        for f in files:

            if not f.endswith(".json"):
                continue

            path = os.path.join(root, f)

            with open(path,"r",encoding="utf-8") as file:

                paper = json.load(file)

            paper_count += 1

            title = paper.get("title","")
            abstract = paper.get("abstract","")
            sections = paper.get("sections",[])

            queries += extract_queries_from_title(title)
            queries += extract_queries_from_sections(sections)
            queries += extract_queries_from_abstract(abstract)

    print("Raw queries:", len(queries))

    queries = filter_queries(queries)

    print("Filtered queries:", len(queries))

    random.shuffle(queries)

    queries = queries[:MAX_QUERIES]

    print("Final queries:", len(queries))
    print("Papers processed:", paper_count)

    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:

        json.dump(queries,f,indent=2)

    print("Queries saved to",OUTPUT_FILE)


if __name__ == "__main__":
    main()