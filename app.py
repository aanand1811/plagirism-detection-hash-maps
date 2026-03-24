import streamlit as st
from corpus import load_corpus
from preprocess import preprocess
from similarity import detect_plagiarism

st.set_page_config(page_title="Plagiarism Detector", layout="wide")

st.title("Plagiarism Detector")
st.caption("Rabin-Karp rolling hash + Jaccard similarity")

# --- sidebar config ---
with st.sidebar:
    st.header("Parameters")
    k         = st.slider("K-gram size (k)", min_value=3, max_value=15, value=5,
                          help="Larger k = fewer false positives, misses short matches")
    threshold = st.slider("Jaccard threshold", min_value=0.0, max_value=1.0, value=0.1, step=0.05,
                          help="Minimum similarity score to flag a document")
    top_n     = st.slider("Max results to show", min_value=1, max_value=20, value=5)
    corpus_path = st.text_input("Corpus CSV path", value="corpus.csv")

# --- load corpus (cached so it only runs once per session) ---
@st.cache_resource(show_spinner="Building index from corpus...")
def load(path, k):
    return load_corpus(path, k=k)

try:
    index, doc_lengths, metadata = load(corpus_path, k)
except FileNotFoundError:
    st.error(f"`{corpus_path}` not found. Run `python generate_corpus.py` first.")
    st.stop()

st.success(f"Index ready — {len(index):,} unique k-gram hashes across {len(doc_lengths):,} documents.")

# --- sample texts ---
SAMPLES = {
    "Pride and Prejudice": (
        "of discourse. In comparing her recollection of Pemberley with the minute description which Wickham "
        "could give, and in bestowing her tribute of praise on the character of its late possessor, she was "
        "delighting both him and herself. On being made acquainted with the present Mr. Darcy's treatment of "
        "him, she tried to remember something of that gentleman's reputed disposition, when quite a lad, which"
    ),
    "Alice in Wonderland": (
        "you're so easily offended, you know! The Mouse only growled in reply. Please come back and finish "
        "your story! Alice called after it; and the others all joined in chorus, Yes, please do! but the Mouse "
        "only shook its head impatiently, and walked a little quicker. What a pity it wouldn't stay! sighed "
        "the Lory, as soon as it was quite out of sight; and an old Crab took the opportunity of saying"
    ),
    "Moby Dick": (
        "from rowing; the boat drifted a little towards the ship's stern; so that, as if by magic, the letter "
        "suddenly ranged along with Gabriel's eager hand. He clutched it in an instant, seized the boat-knife, "
        "and impaling the letter on it, sent it thus loaded back into the ship. It fell at Ahab's feet. Then "
        "Gabriel shrieked out to his comrades to give way with their oars, and in that manner the mutinous"
    ),
}

# --- input area ---
st.subheader("Enter text to check")

st.caption("Try a sample from the corpus:")
cols = st.columns(len(SAMPLES))
for col, (label, text) in zip(cols, SAMPLES.items()):
    if col.button(f"📖 {label}", use_container_width=True):
        st.session_state["query_input"] = text

query_input = st.text_area("Paste your document here", height=200,
                           placeholder="Paste or type the text you want to check for plagiarism...",
                           value=st.session_state.get("query_input", ""),
                           key="query_input")

run = st.button("Check for Plagiarism", type="primary", disabled=not query_input.strip())

# --- results ---
if run and query_input.strip():
    query_clean = preprocess(query_input)

    with st.spinner("Scanning corpus..."):
        results = detect_plagiarism(query_clean, index, doc_lengths, k=k, threshold=threshold)

    if not results:
        st.info("No matches found above the threshold. The text appears to be original.")
    else:
        st.subheader(f"Found {len(results)} matching document(s)")

        for i, r in enumerate(results[:top_n]):
            doc_id = r["doc_id"]
            score  = r["score"]
            meta   = metadata.get(doc_id, {})
            source = meta.get("source", "unknown")

            color = "#d32f2f" if score >= 0.8 else "#f57c00" if score >= 0.5 else "#388e3c"
            label = "High match" if score >= 0.8 else "Moderate match" if score >= 0.5 else "Low match"

            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 2])
                col1.markdown(f"**{doc_id}**")
                col2.markdown(f"Score: **{score:.2%}**")
                col3.markdown(f"Source: `{source}`")

                st.progress(score, text=label)
