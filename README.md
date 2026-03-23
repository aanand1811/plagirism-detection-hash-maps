# Plagiarism Detection using Hash Maps

A document-level plagiarism detection system that uses Rabin-Karp rolling hashes and Jaccard similarity to identify copied or paraphrased content across a large corpus of documents.

---

## What Does This App Do?

Imagine you have thousands of essays or research papers and you want to know if any of them were copied from each other. Reading through all of them manually would take days. This app solves that problem automatically.

You give it a document, and within seconds it tells you which documents in the corpus are suspiciously similar, along with a similarity score. A score of 1.0 means the documents are identical. A score of 0.5 means roughly half the content overlaps.

No external libraries are needed. Everything runs on standard Python.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Setup and Quickstart](#setup-and-quickstart)
- [Configuration Parameters](#configuration-parameters)
- [Dataset](#dataset)
- [Algorithm Details](#algorithm-details)
- [Why Use Hashing? Algorithm vs Naive Approach](#why-use-hashing-algorithm-vs-naive-approach)
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

This script downloads three public domain books from Project Gutenberg, splits them into 150-word chunks, and creates verbatim plagiarised copies for 30% of the documents.

```bash
python generate_corpus.py
```

This writes a file called `corpus.csv` with approximately 3,000 documents (~2,400 original, ~700 plagiarised).

Note: `corpus.csv` is excluded from version control via `.gitignore`. You must generate it locally before running the detector.

### Step 2: Run the Detector

```bash
python detector.py
```

To test with a known plagiarised passage, open `detector.py` and replace the `query_text` value with any text from the corpus. The script will print the top matching documents along with their Jaccard similarity scores and ground-truth labels.

### Expected Output

```
Index built: 48321 unique k-gram hashes

Plagiarism detected:
  moby_dick_0042  score=0.87  category=plagiarized
  moby_dick_0043  score=0.61  category=plagiarized
```

---

## Configuration Parameters

These can be adjusted at the top of `detector.py`:

| Parameter | Default | What It Controls |
|---|---|---|
| `k` | `5` | K-gram window size. Smaller values are more sensitive to short matches. Larger values reduce false positives. |
| `threshold` | `0.5` | Jaccard score cutoff. Documents scoring above this are flagged. Lower values flag more documents. |
| `CHUNK_WORDS` | `150` | Number of words per document chunk when generating the corpus. |
| `PLAGIARISM_RATE` | `0.3` | Fraction of the generated corpus that contains plagiarised content. |

---

## Dataset

The corpus is generated from three public domain books sourced from [Project Gutenberg](https://www.gutenberg.org/):

- *Moby Dick* by Herman Melville
- *Pride and Prejudice* by Jane Austen
- *A Tale of Two Cities* by Charles Dickens

Each book is split into 150-word chunks. 30% of those chunks are duplicated with minor modifications to simulate real-world plagiarism.

### corpus.csv Format

| Column | Description |
|---|---|
| `file_name` | Unique document ID, e.g. `moby_dick_0042` |
| `text` | Raw document text |
| `category` | Ground truth label: `original` or `plagiarized` |
| `source` | The origin book or source document ID |

The corpus contains over 10,000 unique k-gram hashes across ~3,000 documents, satisfying the scale requirements of this project.

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

## Why Use Hashing? Algorithm vs Naive Approach

| | **Naive Approach** (direct text comparison) | **This App** (Rabin-Karp + Hash Index) |
|---|---|---|
| **How it works** | Compare every word of the query against every word of every document, one by one | Compute a short numeric fingerprint (hash) for each k-gram, then look up matches instantly in a hash table |
| **Speed on 10,000 docs** | Gets slower with every document added. Checking 1 query against 10k docs of 150 words each means around 1.5 million comparisons | Index is built once. Each query only touches docs that share at least one hash, typically a tiny fraction of the corpus |
| **Time complexity** | O(Q x N x L): query length times number of docs times doc length | O(L) to hash the query plus O(matches) to score, independent of corpus size |
| **Handles near-duplicates?** | Only catches exact copy paste | Catches paraphrasing and partial overlap via Jaccard similarity over k-gram fingerprints |
| **Memory** | No index needed, but must scan all docs for every query | Stores an inverted index in memory, trading space for speed |
| **Tunable sensitivity** | No. Either it matches or it does not | Yes. Adjust k-gram size and Jaccard threshold to control false positives vs false negatives |
| **Real world usability** | Impractical beyond a few hundred documents | Scales to tens of thousands of documents with sub-second query time |

### Concrete Example

Suppose the corpus has 10,000 documents, each 150 words long, and the query is also 150 words.

- **Naive approach:** up to 1,500,000 word level comparisons per query
- **This app:** hash the 146 k-grams (k=5) in the query, look up 146 entries in the hash table, then score only the small set of candidate docs that share at least one hash. Typically under 1,000 operations total.

### Why K-grams Instead of Whole Word Matching?

Matching individual words would flag any document that shares common words like "the", "and", or "is". K-grams, which are overlapping windows of k consecutive words, capture phrase level similarity instead. This is a much stronger signal of actual copying. The rolling hash computes all k-gram hashes in O(1) per step rather than re-hashing from scratch each time.

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
- The Streamlit UI (`app.py`), per the course policy permitting AI use for UI components

---

## Team

Built for MSML606 at the University of Maryland, Spring 2026.
By: Anoushka Anand, FNU Hardik, Muazuddin Syed
