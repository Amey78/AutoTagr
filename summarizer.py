# summarizer.py (CPU version)
import re
from collections import Counter
import torch
import streamlit as st

# =========================
# Device Setup (GPU/CPU auto detect)
# =========================
if torch.cuda.is_available():
    _DEVICE = 0
    device_name = torch.cuda.get_device_name(0)
else:
    _DEVICE = -1
    device_name = "CPU"

# Print in console
print(f"Running on: {device_name}")

# Show in Streamlit app
st.sidebar.markdown(f"**Device:** {device_name}")

# Model setup
_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
_summarizer = None
_tokenizer = None

def _get_pipeline():
    global _summarizer, _tokenizer
    if _summarizer is None or _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME, use_fast=False)
        model = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_NAME)
        _summarizer = pipeline(
            "summarization",
            model=model,
            tokenizer=_tokenizer,
            framework="pt",
            device=_DEVICE,
        )
    return _summarizer

# ... rest of your summarizer.py code unchanged ...


# Debug: Check whether running on GPU or CPU
if torch.cuda.is_available():
    print(" Running on GPU:", torch.cuda.get_device_name(0))
else:
    print(" Running on CPU")

# Model setup
_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# Force CPU (always -1, no GPU check)
_DEVICE = -1
_summarizer = None
_tokenizer = None


def _get_pipeline():
    global _summarizer, _tokenizer
    if _summarizer is None or _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME, use_fast=False)
        model = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_NAME)
        _summarizer = pipeline(
            "summarization",
            model=model,
            tokenizer=_tokenizer,
            framework="pt",
            device=_DEVICE,   # Always CPU
        )
    return _summarizer


def _clean_text(text: str) -> str:
    text = text.replace("\u200b", " ").replace("\ufeff", " ")
    text = re.sub(r"[^\S\r\n]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t")
    return text.strip()


def _extractive_summary(text: str, max_sentences: int = 3) -> str:
    """Simple extractive summarizer → picks important sentences."""
    sentences = re.split(r"(?<=[.!?]) +", text)
    chosen = [s.strip() for s in sentences if len(s.split()) > 4][:max_sentences]
    return " ".join(chosen) if chosen else text[:200]


def generate_summary(text: str, max_words: int = 150, progress_callback=None) -> str:
    """
    Generate summary with progress updates (CPU only).
    - progress_callback: function(int percent) to update UI
    """
    try:
        text = _clean_text(text)
        if not text or len(text.split()) < 5:
            return "No meaningful text found to summarize."

        # Detect structured text (like tables/lists)
        avg_len = sum(len(line.split()) for line in text.splitlines() if line.strip()) / max(1, len(text.splitlines()))
        if avg_len < 6:
            if progress_callback:
                progress_callback(100)
            return _extractive_summary(text)

        pipe = _get_pipeline()

        # Short text → single summary
        if len(text.split()) < 600:
            result = pipe(
                text,
                truncation=True,
                min_length=max(10, int(max_words * 0.5)),
                max_length=min(180, max(30, int(max_words * 1.5))),
                do_sample=False,
            )[0]["summary_text"].strip()
            if progress_callback:
                progress_callback(100)
            return result

        # Long text → chunk summarization with progress
        words = text.split()
        chunks = [" ".join(words[i:i + 400]) for i in range(0, len(words), 400)]
        total = len(chunks)
        partials = []

        for i, ch in enumerate(chunks, start=1):
            try:
                s = pipe(ch, truncation=True, min_length=50, max_length=120, do_sample=False)[0]["summary_text"]
            except Exception as e:
                s = f"[Chunk error: {str(e)}] " + " ".join(ch.split()[:80])
            partials.append(s)

            # 👇 update progress after each chunk
            if progress_callback:
                progress_callback(int((i / total) * 90))  # keep last 10% for final merge

        combined = " ".join(partials)
        final = pipe(
            combined,
            truncation=True,
            min_length=max(10, int(max_words * 0.5)),
            max_length=min(180, int(max_words * 1.5)),
            do_sample=False,
        )[0]["summary_text"].strip()

        if progress_callback:
            progress_callback(100)

        return final

    except Exception as e:
        safe = _clean_text(text or "")
        if progress_callback:
            progress_callback(100)
        return f"❌ Error in summarizer: {str(e)}\n⚠️ Fallback:\n{' '.join(safe.split()[:max_words])}"


def generate_tags(text: str, max_tags: int = 5) -> list:
    stopwords = set([
        "the","is","and","in","on","at","of","to","a","an","for","by","with","about",
        "from","into","that","this","it","as","be","are","or","was","were","but",
        "can","if","then","so","such","not","no","yes","do","does","did","you",
        "we","they","he","she","him","her","them","our","your","their"
    ])
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    filtered = [w for w in words if w not in stopwords]
    if not filtered:
        return ["General Document"]
    freq = Counter(filtered)
    return [w.capitalize() for w, _ in freq.most_common(max_tags)]
