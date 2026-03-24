import csv
from preprocess import preprocess
from hash_index  import build_index, rolling_hashes


def load_corpus(filepath: str, k: int = 5):
    """
    Returns:
      index       — inverted index { hash: {doc_ids} }
      doc_lengths — { doc_id: number_of_kgrams }
      metadata    — { doc_id: { category, source } }
    """
    documents = {}
    metadata  = {}

    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            doc_id   = row['file_name']
            raw_text = row.get('text', '')

            if not raw_text.strip():         # skip empty documents
                continue

            clean = preprocess(raw_text)
            documents[doc_id] = clean
            metadata[doc_id]  = {
                'source': row.get('source', 'unknown'),
            }

    index       = build_index(documents, k)
    doc_lengths = { doc_id: max(0, len(text) - k + 1)
                    for doc_id, text in documents.items() }

    return index, doc_lengths, metadata