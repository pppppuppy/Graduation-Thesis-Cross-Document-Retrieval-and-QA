# Multi-Hop QA Dataset Generation from arXiv Papers

This project automatically generates multi-hop question answering (QA) datasets from arXiv papers using a Retrieval-Augmented Generation (RAG) pipeline.

The system:

1. Converts PDF papers into structured JSON
2. Splits paper sections into 300-word passages
3. Uses dense retrieval (YouTu-RAG style) to retrieve evidence
4. Uses Qwen-Max LLM to generate multi-hop questions
5. Outputs a structured QA dataset with evidence pages

This project is designed for research and graduation thesis experiments on multi-hop reasoning over scientific documents.

## Project Pipeline

The full pipeline:

```
PDF Papers
   │
   ▼
PDF → Structured JSON
   │
   ▼
Passage Chunking (300 words)
   │
   ▼
Dense Retrieval (MiniLM embeddings)
   │
   ▼
Multi-hop QA Generation (Qwen-Max)
   │
   ▼
QA Dataset
```

## Paper JSON Format

Each paper is converted from PDF into structured JSON.

Example:

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

## Passage Chunking

Each section is split into passages of 300 words.

Chunking is performed sequentially.

Example:

```
Section: Introduction
   │
   ├── Chunk 1 (300 words)
   ├── Chunk 2 (300 words)
   └── Chunk 3 (300 words)
```

Each chunk has the format:

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

Page number is derived from section start_page.

## Retrieval Module

Retrieval is implemented using dense embeddings.

### Embedding model

```
sentence-transformers/all-MiniLM-L6-v2
```

### Steps

1. Encode all passages into embeddings
2. Encode query into embedding
3. Compute cosine similarity
4. Retrieve Top-K passages

This retrieval module follows the YouTu-RAG retrieval style.

## Multi-Hop QA Generation

After retrieving relevant passages, the system sends them to Qwen-Max to generate QA pairs.

The model is instructed to:

- combine multiple passages
- generate a multi-hop question
- produce the answer
- return evidence pages

## Output QA Format

Generated dataset format:

```json
[
  {
    "question": "What mechanism helps the model avoid compressing the entire sentence into a fixed-length vector?",
    "answer": "The model uses a soft alignment mechanism that allows it to attend to relevant positions in the source sentence.",
    "evidence": [
      {
        "doc_id": "1409.0473v7.pdf",
        "page": 1
      },
      {
        "doc_id": "1409.0473v7.pdf",
        "page": 2
      }
    ]
  }
]
```

Evidence format is simplified to:

- doc_id
- page

## Project Structure

```
multi-hop-qa-dataset
│
├── data
│   ├── structured_v4_page
│   │    └── computer
│   │    └── math
│   │    └── physics
│   │
│   └── qa_dataset
│        └── multi_hop_qa.json
│
├── scripts
│
│   ├── generate_qa.py
│   └── youtu_rag_retrieve.py
│
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
pip install tqdm
pip install requests
```

## Qwen-Max API Setup

This project uses Qwen-Max API.

Set your API key as environment variable.

### Linux / Mac:

```bash
export DASHSCOPE_API_KEY="your_api_key"
```

### Windows:

```bash
set DASHSCOPE_API_KEY=your_api_key
```

## Running the Pipeline

Run the QA generation pipeline:

```bash
python scripts/generate_qa.py
```

The script will:

1. Load paper JSON files
2. Chunk sections into 300-word passages
3. Build embeddings for passages
4. Retrieve relevant passages
5. Generate multi-hop QA using Qwen-Max
6. Save the dataset

Output file:

```
data/generated/multi_hop_qa.json
```

## Example Generated QA

Example:

### Question:

Why does the proposed neural translation model perform better on long sentences?

### Answer:

Because it uses a soft alignment mechanism that allows the decoder to attend to relevant parts of the source sentence instead of compressing the entire sentence into a fixed-length vector.

### Evidence:

- 1409.0473v7.pdf page 1
- 1409.0473v7.pdf page 2

## Dataset Scale

Example configuration:

- papers: 50+
- QA per paper: 

Total output:

≈ multi-hop QA pairs

## Future Improvements

Possible extensions:

- Graph-based multi-hop retrieval
- Table / figure evidence extraction
- Better page alignment
- Hard negative retrieval
- Multimodal QA dataset generation

## Research Context

This project is inspired by research on:

- Retrieval-Augmented Generation (RAG)
- YouTu-RAG
- Multi-hop QA datasets
- Scientific document reasoning

