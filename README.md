# Multi-Hop QA Dataset Generation from arXiv Papers

This project automatically generates multi-hop question answering (QA) datasets from arXiv papers using a Retrieval-Augmented Generation (RAG) pipeline.

The system:

1. Converts PDF papers into structured JSON with sections and page numbers
2. Splits paper sections into passages (300 words)
3. Uses dense retrieval to retrieve relevant evidence passages
4. Uses DeepSeek LLM to generate multi-hop questions
5. Outputs a structured QA dataset with evidence doc_id and page

This project is designed for research and graduation thesis experiments on multi-hop reasoning over scientific documents.

## Project Pipeline

```
PDF Papers (50 papers)
        │
        ▼
PDF → Structured JSON (with sections, start_page)
        │
        ▼
Passage Chunking (3697 passages, 300 words each)
        │
        ▼
Query Generation (187 queries from paper keywords)
        │
        ▼
Dense Retrieval (retrieve top-5 relevant passages)
        │
        ▼
LLM Generation (DeepSeek - multi-hop QA)
        │
        ▼
QA Dataset (480 multi-hop QA pairs)
```

## Data Statistics

| Dataset | Count |
|---------|-------|
| Papers (Computer/Math/Physics) | 50 |
| Passages | 3,697 |
| Generated Queries | 187 |
| Multi-hop QA Pairs | 480 |

### QA Quality

| Metric | Value |
|--------|-------|
| Avg Question Length | 20.2 words |
| Avg Answer Length | 48.4 words |
| Avg Evidence Count | 2.1 |
| Sequential Reasoning | 273 |
| Parallel Reasoning | 227 |

## Paper JSON Format

Each paper is converted from PDF into structured JSON.

```json
{
  "doc_id": "1409.0473v7.pdf",
  "title": "NEURAL MACHINE TRANSLATION BY JOINTLY LEARNING TO ALIGN AND TRANSLATE",
  "abstract": "...",
  "sections": [
    {
      "section_id": "1",
      "original_section_number": "1",
      "section_title": "INTRODUCTION",
      "level": 1,
      "start_page": 1,
      "text": "Neural machine translation is a newly emerging approach..."
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| doc_id | paper filename |
| title | paper title |
| abstract | abstract |
| sections | list of sections |
| section_title | section name |
| start_page | starting page of section |
| text | full section text |

## Passage Format

Each section is split into passages of 300 words.

```json
{
  "doc_id": "1409.0473v7.pdf",
  "page": 10,
  "text": "The authors propose a neural translation model..."
}
```

| Field | Description |
|-------|-------------|
| doc_id | paper id |
| page | estimated page number |
| text | chunk text |

## Query Generation

Queries are generated from paper keywords using templates:

```json
[
  "How does attention improve neural network performance?",
  "Why is BERT important for NLP tasks?",
  "What are the advantages of transfer learning?"
]
```

## Multi-Hop QA Output Format

```json
[
  {
    "question": "Why does SentencePiece reduce overfitting, and how does this improve model performance?",
    "answer": "SentencePiece reduces overfitting by using subword regularization...",
    "evidence": [
      {"doc_id": "2106.09685v2.pdf", "page": 4},
      {"doc_id": "1206.5533v2.pdf", "page": 28}
    ],
    "type": "sequential",
    "query": "How does SentencePiece improve model performance?"
  }
]
```

### Reasoning Types

- **Sequential (串行)**: Requires step-by-step reasoning (A → B → C)
- **Parallel (并行)**: Requires combining multiple evidence (A + B → C)

## Project Structure

```
multi-hop-qa-dataset
│
├── data
│   ├── raw_pdfs/
│   │   ├── computer/
│   │   ├── math/
│   │   └── physics/
│   │
│   ├── structured_v4_page/     # Paper JSON with sections
│   │   ├── computer/
│   │   ├── math/
│   │   └── physics/
│   │
│   ├── passages.json           # 3,697 passages
│   │
│   ├── queries_v5.json         # 187 generated queries
│   │
│   └── qa_dataset/
│       └── multihop_qa_v3.json # 480 multi-hop QA pairs
│
├── scripts/
│   ├── parse_pdf_v4_page.py    # PDF to structured JSON
│   ├── build_passages.py       # Chunk to passages
│   ├── auto_query_generator_v5.py # Generate queries
│   ├── generate_qa_v3.py       # Generate multi-hop QA
│   └── youtu_rag_retrieve.py   # Retrieval module
│
├── api_key.txt
├── README.md
└── requirements.txt
```

## Environment Setup

Recommended Python version:

```
Python 3.10+
```

Create environment:

```bash
conda create -n multihopqa python=3.10
conda activate multihopqa
```

### Install Dependencies

```bash
pip install sentence-transformers
pip install numpy
pip install faiss-cpu
pip install tqdm
```

## API Key Setup

This project uses DeepSeek API for LLM generation.

Create a file `api_key.txt` and add your API key:

```
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Running the Pipeline

### Step 1: Parse PDFs to JSON

```bash
python scripts/parse_pdf_v4_page.py
```

### Step 2: Build Passages

```bash
python scripts/build_passages.py
```

### Step 3: Generate Queries

```bash
python scripts/auto_query_generator_v5.py
```

### Step 4: Generate Multi-hop QA

```bash
python scripts/generate_qa_v3.py
```

## Generated Dataset

The final dataset contains **480 high-quality multi-hop QA pairs**:

- Each QA requires **2+ evidence** passages to answer
- Questions are specific to paper content
- Evidence includes **doc_id** and **page** for verification

### Sample QA

**Question:**
```
Why does SentencePiece reduce overfitting, and how does this improve model performance?
```

**Answer:**
```
SentencePiece reduces overfitting by using subword regularization, which helps the model generalize better...
```

**Evidence:**
- 2106.09685v2.pdf page 4
- 1206.5533v2.pdf page 28

**Type:** sequential

## Research Context

This project is inspired by research on:

- Retrieval-Augmented Generation (RAG)
- Multi-hop QA datasets
- Scientific document reasoning
- Dense retrieval (BM25, DPR, BGE)

## Future Improvements

Possible extensions:

- Graph-based multi-hop retrieval
- Table / figure evidence extraction
- Cross-document reasoning
- Hard negative sampling
- Evaluation metrics (EM, F1)

## Author

Graduation Thesis Project

**Topic:** Automatic Multi-Hop QA Dataset Construction from Scientific Papers
