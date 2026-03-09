

📚 Multi-Hop QA Dataset Generation from arXiv Papers

This project automatically generates multi-hop question answering (QA) datasets from academic papers (arXiv) using a Retrieval-Augmented Generation (RAG) pipeline.

The system processes structured paper data (title, abstract, sections), retrieves relevant passages, and uses a Large Language Model (LLM) to generate multi-hop QA pairs with evidence grounding.

The output format is compatible with RAG / multimodal QA research.

🧠 Motivation

Multi-hop QA requires reasoning across multiple pieces of information.

Academic papers are a natural source because:

information is distributed across sections

reasoning often requires combining concepts

evidence exists in text / tables / figures

This project builds a pipeline that automatically generates multi-hop QA pairs from such documents.

🏗 System Pipeline

The system follows a 5-step pipeline.

arXiv Papers
     │
     ▼
JSON Cleaning
     │
     ▼
Passage Chunking
     │
     ▼
Dense Retrieval (YouTu-RAG style)
     │
     ▼
LLM-based QA Generation
     │
     ▼
Multi-hop QA Dataset
⚙️ Method Overview
Step 1 — Paper Parsing

Each paper is converted into JSON format containing:

paper ID

title

abstract

sections

Example:

{
  "id": "1409.0473v7",
  "title": "...",
  "abstract": "...",
  "sections": [
    {
      "heading": "Introduction",
      "text": "..."
    },
    {
      "heading": "Method",
      "text": "..."
    }
  ]
}
Step 2 — Passage Chunking

Each section is split into passages (~150 words).

Example:

Section: Method
Chunk 1
Chunk 2
Chunk 3

Each chunk is stored as:

{
    "paper_id": "...",
    "section": "Method",
    "chunk_id": 3,
    "text": "..."
}
Step 3 — Dense Retrieval

We use a sentence embedding model:

sentence-transformers/all-MiniLM-L6-v2

This model converts passages into vectors.

Then we compute cosine similarity to retrieve the top-k relevant passages.

This step mimics the retrieval module used in YouTu-RAG.

Step 4 — Multi-Hop QA Generation

We use OpenAI GPT to generate QA pairs.

The prompt forces the model to create multi-hop reasoning questions.

Example prompt:

Given the following scientific passages:

[PASSAGE 1]
...

[PASSAGE 2]
...

Generate a multi-hop question that requires combining
information from both passages.

Return JSON with:
- question
- answer
- evidence
Step 5 — Evidence Annotation

The model outputs evidence locations:

{
  "doc_id": "paper.pdf",
  "page": 5,
  "modality": "text",
  "location": "Section Method paragraph 2"
}
📂 Project Structure
multi-hop-qa-dataset
│
├── data
│   ├── papers/               # cleaned paper JSON
│   │    └── 1409.0473v7.json
│   │
│   └── generated
│        └── multi_hop_qa.json
│
├── scripts
│
│   ├── generate_qa.py        # main pipeline
│   └── youtu_rag_retrieve.py # retrieval module
│
├── README.md
└── requirements.txt
💻 Installation