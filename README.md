# Multi-Hop QA Dataset Construction

## 📌 Project Overview

This project aims to construct a multi-hop cross-document question answering dataset for graduation thesis research. The dataset is built from scientific papers (CS / Math / Physics domains) and organized in a section-level structured format to support downstream retrieval and QA tasks.

The pipeline mainly includes:

- PDF scientific paper parsing

- Section-level structure extraction

- Dataset cleaning and normalization

- Cross-document QA dataset construction (future work)

---

## 📂 Current Project Structure

<<<<<<< HEAD

=======
>>>>>>> 684f8d1c2a253c9588628fa51d822359390f3238
```text
multi-hop-qa-dataset/
│
├ data/
│   ├ parsed_pages/                 # Page-level parsing results
│   ├ qa_dataset/                   # Constructed QA datasets
│   ├ raw_pdfs/                    # Raw scientific paper PDFs
│   └ structured_v3_section_level/ # Structured JSON outputs (section-level)
│       ├ computer/
│       ├ math/
│       └ physics/
│
├ scripts/
│   ├ parse_pdf.py                 # Basic PDF parsing script
│   └ parse_pdf_v3_section.py      # Section-level structured parsing script
│
<<<<<<< HEAD
├ venv/
├ .gitignore
└ README.md

=======
└── README.md
>>>>>>> 684f8d1c2a253c9588628fa51d822359390f3238
```

---

## 📊 Current Progress

- ✅ Collected and cleaned 20 research papers
- ✅ Built section-level structured JSON parsing pipeline
- ✅ Constructed initial cross-document QA samples (manual)
- ⏳ Developing automatic QA construction pipeline
- ⏳ Planning multi-hop reasoning evaluation experiments

---

## 🧠 Dataset Format

The parsed documents are stored in JSON format with section-level granularity:

```json
{
  "doc_id": "attention_is_all_you_need.pdf",
  "title": "Attention Is All You Need",
  "abstract": "The dominant sequence transduction models are based on...",
  "sections": [
    {
      "section_id": "1",
      "section_title": "1 INTRODUCTION",
      "level": 1,
      "text": "The fundamental constraint of sequential computation remains..."
    }
  ]
}
```
<<<<<<< HEAD
=======
---
>>>>>>> 684f8d1c2a253c9588628fa51d822359390f3238

## ⚠️ Notes

<<<<<<< HEAD
## ⚠️ Notes⚠️ 

Raw PDFs are not included due to size limitations.

Cleaned text files are provided for reproducibility.
=======
- Raw PDFs are not included due to size limitations.
- Cleaned text files are provided for reproducibility.
- This repository currently contains a prototype version of the dataset.
>>>>>>> 684f8d1c2a253c9588628fa51d822359390f3238

---
