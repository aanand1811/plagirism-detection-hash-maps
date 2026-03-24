"""
Generate a reference corpus from Project Gutenberg books.

Strategy:
  1. Download a few public-domain books
  2. Split each into fixed-size chunks (~150 words)
  3. Write corpus.csv — these are the source documents to check against

Run:  python generate_corpus.py
"""

import csv
import re
import urllib.request

# --- config ---
CHUNK_WORDS = 150    # words per chunk
OUTPUT      = 'corpus.csv'

BOOKS = [
    ('pride_and_prejudice', 'https://www.gutenberg.org/files/1342/1342-0.txt'),
    ('alice_in_wonderland', 'https://www.gutenberg.org/files/11/11-0.txt'),
    ('moby_dick',           'https://www.gutenberg.org/files/2701/2701-0.txt'),
]


def fetch_book(url: str) -> str:
    print(f"  Downloading {url} ...")
    with urllib.request.urlopen(url, timeout=30) as r:
        raw = r.read().decode('utf-8-sig', errors='ignore')

    # strip Gutenberg header/footer
    start = re.search(r'\*\*\* START OF (THE|THIS) PROJECT GUTENBERG', raw)
    end   = re.search(r'\*\*\* END OF (THE|THIS) PROJECT GUTENBERG',   raw)
    if start and end:
        raw = raw[start.end():end.start()]

    return re.sub(r'\s+', ' ', raw).strip()


def chunk_text(text: str, chunk_words: int) -> list[str]:
    words  = text.split()
    chunks = []
    for i in range(0, len(words) - chunk_words + 1, chunk_words):
        chunks.append(' '.join(words[i:i + chunk_words]))
    return chunks


# --- build corpus ---
rows = []

print("Fetching books...")
for book_name, url in BOOKS:
    try:
        text   = fetch_book(url)
        chunks = chunk_text(text, CHUNK_WORDS)
        print(f"  {book_name}: {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            rows.append({
                'file_name': f"{book_name}_{i:04d}",
                'text':      chunk,
                'source':    book_name,
            })
    except Exception as e:
        print(f"  WARNING: could not fetch {book_name}: {e}")

if not rows:
    raise SystemExit("No books downloaded — check your internet connection.")

with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['file_name', 'text', 'source'])
    writer.writeheader()
    writer.writerows(rows)

print(f"\nDone: {len(rows)} documents written to {OUTPUT}")
