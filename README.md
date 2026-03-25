# Multi-Hop QA Dataset Generation from arXiv Papers

This project automatically generates multi-hop question answering (QA) datasets from arXiv papers using a Retrieval-Augmented Generation (RAG) pipeline. The system leverages advanced retrieval techniques and large language models to create high-quality scientific QA pairs.

## Key Features

- **Automated Pipeline**: End-to-end process from PDF papers to structured QA datasets
- **Advanced Retrieval**: BGE embedding model + Cross-Encoder re-ranking for improved relevance
- **Quality Assurance**: Multi-hop reasoning with 2+ evidence sources per question
- **Academic Focus**: Specialized for scientific document understanding
- **Structured Output**: Comprehensive JSON format with evidence tracking

## Project Pipeline

```
PDF Papers (50 papers)        │
        ▼                  │
PDF → Structured JSON        │
        ▼                  │
Passage Chunking (3,697 passages) │
        ▼                  │
Query Generation (187 queries)    │
        ▼                  │
BGE Retrieval + Cross-Encoder Re-ranking │
        ▼                  │
LLM Generation (DeepSeek)      │
        ▼                  │
QA Dataset (520 multi-hop QA pairs)  │
```

## Data Statistics

| Dataset | Count |
|---------|-------|
| Papers (Computer/Math/Physics) | 50 |
| Passages | 3,697 |
| Generated Queries | 187 |
| Multi-hop QA Pairs | 520 |

### QA Quality

| Metric | Value |
|--------|-------|
| Avg Question Length | 25.3 words |
| Avg Answer Length | 52.7 words |
| Avg Evidence Count | 2.3 |
| Sequential Reasoning | 289 |
| Parallel Reasoning | 231 |

## Data Formats

### Paper JSON Format

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

### Passage Format

```json
{
  "doc_id": "1409.0473v7.pdf",
  "page": 10,
  "text": "The authors propose a neural translation model..."
}
```

### Multi-Hop QA Output Format

```json
[
  {
    "question": "How does self-attention address computational limitations of convolutional models?",
    "answer": "Self-attention enables direct modeling of relationships between all input positions in parallel...",
    "evidence": [
      {"doc_id": "1803.02155v2.pdf", "page": 2},
      {"doc_id": "1706.03762v7.pdf", "page": 2}
    ],
    "type": "sequential",
    "query": "How does self-attention enable better representation learning?"
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
├── data/
│   ├── raw_pdfs/             # Original PDF papers
│   │   ├── computer/
│   │   ├── math/
│   │   └── physics/
│   │
│   ├── structured_v4_page/    # Paper JSON with sections
│   │   ├── computer/
│   │   ├── math/
│   │   └── physics/
│   │
│   ├── passages.json          # 3,697 passages (300 words each)
│   ├── queries_v5.json        # 187 generated queries
│   ├── bge_embeddings.npy     # BGE embeddings for retrieval
│   ├── faiss_bge_meta.json    # Metadata for BGE index
│   └── qa_dataset/
│       ├── multihop_qa_v3.json      # Original QA pairs
│       └── multihop_qa_v4_filtered.json  # Quality-filtered QA pairs (520)
│
├── scripts/
│   ├── parse_pdf_v4_page.py        # PDF to structured JSON
│   ├── build_passages.py           # Chunk sections to passages
│   ├── auto_query_generator_v5.py   # Generate queries from keywords
│   ├── youtu_rag_retrieve.py       # Basic retrieval module
│   ├── enhanced_retriever.py        # BGE + Cross-Encoder retrieval
│   ├── generate_qa_v3.py           # Original QA generation
│   ├── generate_qa_v4.py           # Optimized QA generation
│   └── quality_filter.py           # QA quality assessment
│
├── README.md
├── .gitignore
└── requirements.txt
```

## Environment Setup

### Recommended Python Version

```
Python 3.10+
```

### Create Environment

```bash
conda create -n multihopqa python=3.10
conda activate multihopqa
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Dependencies

- sentence-transformers (for BGE and Cross-Encoder)
- numpy
- faiss-cpu (for efficient similarity search)
- tqdm (for progress bars)
- PyMuPDF (for PDF parsing)

## API Key Setup

This project uses DeepSeek API for LLM generation.

Create a file `deepseek_key.txt` and add your API key:

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

### Step 4: Generate Multi-hop QA (Optimized)

```bash
python scripts/generate_qa_v4.py
```

### Step 5: Filter QA Quality

```bash
python scripts/quality_filter.py
```

## Generated Dataset

The final filtered dataset contains **520 high-quality multi-hop QA pairs**:

- Each QA requires **2+ evidence** passages to answer
- Questions are specific to scientific paper content
- Evidence includes **doc_id** and **page** for verification
- Supports both sequential and parallel reasoning types

### Sample QA

**Question:**
```
How does the self-attention mechanism address computational limitations of previous sequence transduction models?
```

**Answer:**
```
Self-attention enables direct modeling of relationships between all input positions in parallel, regardless of their distance. Previous convolutional models required operations that grew with distance between positions, while self-attention captures pairwise relationships in constant time.
```

**Evidence:**
- 1803.02155v2.pdf page 2
- 1706.03762v7.pdf page 2

**Type:** sequential

## Research Context

This project is inspired by research on:

- Retrieval-Augmented Generation (RAG)
- Multi-hop question answering datasets
- Scientific document understanding
- Dense retrieval techniques (BGE, Cross-Encoder)
- Large language model prompting

## Key Innovations

1. **Advanced Retrieval Pipeline**: BGE embedding model with Cross-Encoder re-ranking for improved relevance
2. **Quality Assurance**: Comprehensive filtering to ensure multi-hop reasoning quality
3. **Efficient Processing**: Optimized embedding and retrieval for scientific documents
4. **Flexible Architecture**: Modular design for easy extension and experimentation

## Future Improvements

- Graph-based multi-hop retrieval
- Table and figure evidence extraction
- Cross-document reasoning capabilities
- Hard negative sampling for better training
- Automated evaluation metrics (EM, F1, BLEU)
- Support for additional languages and disciplines

## Author

**Graduation Thesis Project**

**Topic:** Automatic Multi-Hop QA Dataset Construction from Scientific Papers

**Year:** 2026