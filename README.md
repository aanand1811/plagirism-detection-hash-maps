# Plagiarism Detection using Hash Maps

A document-level plagiarism detection system that uses Rabin-Karp rolling hashes and Jaccard similarity to identify copied or paraphrased content across a large corpus of documents.

Built for MSML606 at the University of Maryland.

---

## Overview

Given a reference corpus of source documents and a query text, the system identifies which corpus documents the query was likely copied from, ranked by similarity score. A score of 1.0 means identical content; lower scores indicate partial overlap.

No external libraries are needed. Everything runs on standard Python. (For GUI, we have used streamlit)

---

## Table of Contents

- [Plagiarism Detection using Hash Maps](#plagiarism-detection-using-hash-maps)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [How It Works](#how-it-works)
  - [Project Structure](#project-structure)
  - [Setup and Quickstart](#setup-and-quickstart)
    - [Requirements](#requirements)
    - [Step 1: Generate the Corpus](#step-1-generate-the-corpus)
    - [Step 2: Run the Detector](#step-2-run-the-detector)
    - [Expected Output](#expected-output)
  - [Configuration Parameters](#configuration-parameters)
  - [Dataset](#dataset)
    - [corpus.csv Format](#corpuscsv-format)
  - [Algorithm Details](#algorithm-details)
    - [Rolling Hash (Rabin-Karp)](#rolling-hash-rabin-karp)
    - [Inverted Index](#inverted-index)
    - [Jaccard Similarity](#jaccard-similarity)
    - [Overall Complexity](#overall-complexity)
  - [Why Rabin-Karp Instead of Plain K-gram Hashing?](#why-rabin-karp-instead-of-plain-k-gram-hashing)
    - [Concrete Example](#concrete-example)
  - [Noise and Edge Case Handling](#noise-and-edge-case-handling)
  - [AI Usage Statement](#ai-usage-statement)
  - [Team](#team)

---

## How It Works

The detection pipeline has four stages:

```
Your document
     |
     v
1. Preprocess      lowercase, remove punctuation, normalize whitespace
     |
     v
2. Hash            slide a window of k words across the text,
                   compute a Rabin-Karp rolling hash at each position
     |
     v
3. Index Lookup    check each hash against an inverted index built
                   from the entire corpus: { hash -> set of doc IDs }
     |
     v
4. Score           compute Jaccard similarity for each candidate doc,
                   flag any doc scoring above the threshold
```

---

## Project Structure

```
.
├── preprocess.py        Text cleaning: lowercase, strip punctuation, normalize whitespace
├── hash_index.py        Rabin-Karp rolling hash implementation and inverted index builder
├── similarity.py        Hash matching and Jaccard similarity scorer
├── corpus.py            Loads corpus.csv into the index with metadata
├── detector.py          Main entry point: builds the index and runs a query
├── generate_corpus.py   Generates a synthetic corpus from Project Gutenberg books
├── convert.py           Utility for corpus format conversion
└── README.md
```

---

## Setup and Quickstart

### Requirements

- Python 3.10 or higher
- No pip installs required — standard library only

### Step 1: Generate the Corpus

This script downloads three public domain books from Project Gutenberg and splits them into 150-word chunks to form the reference corpus.

```bash
python generate_corpus.py
```

This writes a file called `corpus.csv` with approximately 2,400 documents.

Note: `corpus.csv` is excluded from version control via `.gitignore`. You must generate it locally before running the detector.

### Step 2: Run the Detector

```bash
python detector.py
```

To test with a known plagiarised passage, open `detector.py` and replace the `query_text` value with any text from the corpus. The script will print the top matching documents along with their Jaccard similarity scores and ground-truth labels.

### Expected Output

```
Index built: 861325 unique k-gram hashes

Plagiarism detected:
  moby_dick_0042  score=0.87
  moby_dick_0043  score=0.61
```

---

## Configuration Parameters

These can be adjusted at the top of `detector.py`:

| Parameter | Default | What It Controls |
|---|---|---|
| `k` | `5` | K-gram window size. Smaller values are more sensitive to short matches. Larger values reduce false positives. |
| `threshold` | `0.1` | Jaccard score cutoff. Documents scoring above this are flagged. Lower values flag more documents. |
| `CHUNK_WORDS` | `150` | Number of words per document chunk when generating the corpus. |

---

## Dataset

The corpus is generated from three public domain books sourced from [Project Gutenberg](https://www.gutenberg.org/):

- *Moby Dick* by Herman Melville
- *Pride and Prejudice* by Jane Austen
- *Alice's Adventures in Wonderland* by Lewis Carroll

Each book is downloaded from Project Gutenberg and split into 150-word chunks. These chunks form the reference corpus — the library of source documents that submitted text is checked against.

### corpus.csv Format

| Column | Description |
|---|---|
| `file_name` | Unique document ID, e.g. `moby_dick_0042` |
| `text` | Raw document text (150 words per chunk) |
| `source` | The book the chunk was taken from |

The corpus contains over 800,000 unique k-gram hashes across ~2,400 documents.

---

## Algorithm Details

### Rolling Hash (Rabin-Karp)

A k-gram is a sequence of k consecutive words. For a document of length L words, there are L - k + 1 overlapping k-grams.

Rather than computing a fresh hash for each k-gram from scratch, Rabin-Karp uses a rolling hash that updates in O(1) per step by sliding a window:

```
hash = sum( ord(char[i]) * P^i ) mod M

Base P = 31
Modulus M = 1,000,003
```

Each new hash is derived from the previous one by dropping the leftmost character contribution and adding the new rightmost character. This gives O(L) total hashing for any document, regardless of k.

### Inverted Index

After hashing, we build an index that maps each hash value to the set of document IDs that contain it:

```
{ hash_value -> { doc_id_1, doc_id_2, ... } }
```

This is the hash map at the core of the project. A query document only needs to look up its own hashes in this index to find candidate matches. Documents that share no hashes are never touched.

### Jaccard Similarity

Once candidate documents are identified, we score each one:

```
J(Query, Doc) = |shared k-gram hashes| / ( |Query hashes| + |Doc hashes| - |shared hashes| )
```

A score of 1.0 is a perfect match. A score of 0.0 means no overlap at all.

### Overall Complexity

| Phase | Complexity |
|---|---|
| Index build | O(N x L) for N documents of average length L |
| Query hashing | O(L) for a query of length L |
| Candidate scoring | O(matches), where matches is the number of docs sharing at least one hash |

---

## Why Rabin-Karp Instead of Plain K-gram Hashing?

The naive way to hash k-grams is to recompute each hash from scratch — iterating over all k characters of every window. For a document of length L characters with k-gram size k, that costs O(k) per k-gram and O(L x k) total.

Rabin-Karp eliminates that redundancy with a rolling update. When the window slides one character to the right, the new hash is derived from the previous one in O(1) by:
- Subtracting the contribution of the character that left the window
- Adding the contribution of the character that entered

```
new_hash = (old_hash - ord(out_char) + M) * P + ord(in_char) * P^(k-1)  mod M
```

This brings total hashing cost down to O(L) regardless of k.

| | **Plain K-gram Hashing** | **Rabin-Karp Rolling Hash** |
|---|---|---|
| **Cost per k-gram** | O(k) — rehash all k characters each time | O(1) — slide the window, update incrementally |
| **Total cost for document of length L** | O(L x k) | O(L) |
| **Impact when k is large** | Gets significantly slower as k grows | No change — cost is independent of k |
| **Implementation complexity** | Simple loop | Slightly more complex, but a one-time implementation cost |

### Concrete Example

For a 150-word document (~900 characters) with k=10:

- **Plain hashing:** ~900 × 10 = 9,000 character operations
- **Rabin-Karp:** ~900 operations, regardless of k

The difference compounds across a corpus of 2,400 documents: plain hashing costs roughly 21.6 million operations to build the index; Rabin-Karp costs 2.16 million.

---

## Noise and Edge Case Handling

Real-world text data is messy. Here is how the pipeline handles common issues:

| Issue | How It Is Handled |
|---|---|
| Uppercase and mixed case | Lowercased during preprocessing so "The" and "the" are treated as the same word |
| Punctuation and special characters | Stripped during preprocessing so "hello," and "hello" hash identically |
| Extra whitespace or blank lines | Normalized to single spaces before hashing |
| Missing or empty fields in CSV | Rows with empty `text` fields are skipped during corpus loading |
| Very short documents | Documents shorter than k words produce no k-grams and are skipped gracefully |
| Hash collisions | Modular arithmetic can cause collisions, but with M=1,000,003 and typical doc sizes, false positive rates are negligible |

---

## AI Usage Statement

This project was completed in accordance with the MSML606 course AI policy.

The following components were written manually without AI assistance:
- All data preprocessing logic (`preprocess.py`)
- The Rabin-Karp rolling hash implementation (`hash_index.py`)
- The inverted index construction (`hash_index.py`, `corpus.py`)
- The Jaccard similarity scoring (`similarity.py`)
- All code comments and this README

AI tools were used only for the following auxiliary components:
- The Streamlit UI (`app.py`), per the course policy permitting AI use for UI components. 
- Reference for Rabin-karp algo - [here](https://en.wikipedia.org/wiki/Rabin%E2%80%93Karp_algorithm) 

---

## Team

Built for MSML606 at the University of Maryland, Spring 2026.
By: Anoushka Anand, FNU Hardik, Muazuddin Syed
