# Multi-Hop QA Dataset Construction

## 📌 Project Overview

This project aims to construct a cross-document retrieval and question answering (QA) dataset for evaluating multi-document reasoning capabilities.

The goal is to build a structured dataset where each question requires synthesizing evidence from multiple documents.

---

## 📂 Current Project Structure
multi-hop-qa-dataset/
│
├── data/
│ ├── parsed_pages/ # Cleaned text extracted from raw PDFs
│
├── qa_dataset/
│ └── train/
│ └── demo.json # Manually constructed cross-document QA samples
│
├── scripts/
│ └── parse_pdf.py # PDF parsing and preprocessing script
│
└── README.md


---

## 📊 Current Progress

- ✅ Collected and cleaned 20 research papers
- ✅ Constructed initial cross-document QA samples (manual)
- ⏳ Developing automatic QA construction pipeline
- ⏳ Planning multi-hop reasoning evaluation experiments

---

## 🧠 Dataset Format

Each QA instance follows this structure:

```json
{
  "qa_id": "...",
  "source_paper_id": "...",
  "task_type": "...",
  "question": "...",
  "answer": "...",
  "evidence": [
    {
      "doc_id": "...",
      "page": 1,
      "modality": "text",
      "location": "Abstract"
    }
  ]
}


⚠️ Notes⚠️ 

Raw PDFs are not included due to size limitations.

Cleaned text files are provided for reproducibility.

This repository currently contains a prototype version of the dataset.