import glob
import os
import re
from dataclasses import dataclass

import snowballstemmer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import KNOWLEDGE_DIR, TOP_K

_STEMMER = snowballstemmer.stemmer("english")


@dataclass
class Chunk:
    source: str
    section: str
    text: str
    is_current: bool = False
    has_dates: bool = False
    has_location: bool = False


DATES_LINE = re.compile(r"Dates:\s*(.+)")
LOCATION_LINE = re.compile(r"Location:\s*(.+)")
H1_TITLE = re.compile(r"^#\s+(.+)", re.MULTILINE)
WORD = re.compile(r"[a-zA-Z]{2,}")
CURRENT_CUES = re.compile(r"\b(current|currently|now)\b", re.IGNORECASE)
PRIOR_CUES = re.compile(r"\b(before|prior|previous|previously)\b", re.IGNORECASE)
RECENT_CUES = re.compile(r"\b(recent|recently|latest|newest)\b", re.IGNORECASE)
WHERE_CUES = re.compile(r"\b(where|location|located|based)\b", re.IGNORECASE)
TITLE_WORD = re.compile(r"[a-zA-Z]{6,}")
SUBJECT_TITLE_SEPARATOR = re.compile(r"\s+[—-]\s+")
GENERIC_TITLE_WORDS = {"employment", "experience"}
CURRENT_ROLE_BOOST = 1.2
PRIOR_ROLE_BOOST = 0.5
RECENT_ROLE_BOOST = 0.3
TITLE_MATCH_BOOST = 1.5
TITLE_MATCH_FLOOR_BOOST = 0.4
LOCATION_MATCH_BOOST = 0.35
NO_SIGNAL_FLOOR_BOOST = 0.4


def stem(word: str) -> str:
    # Real Porter2/Snowball stemming, not a hand-picked suffix list, so derivational variants match.
    return _STEMMER.stemWord(word)


def _stemmed_analyzer(stop_words: set[str]):
    # Stemming inside the vectorizer's own analyzer fixes word-form mismatches for every query, not just titles.
    def analyze(text: str) -> list[str]:
        return [stem(w) for w in WORD.findall(text.lower()) if w not in stop_words]

    return analyze


def load_chunks(knowledge_dir: str = KNOWLEDGE_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(glob.glob(os.path.join(knowledge_dir, "*.md"))):
        source = os.path.basename(path)
        with open(path, encoding="utf-8") as handle:
            raw = handle.read()
        blocks = [b.strip() for b in re.split(r"\n(?=## )", raw) if b.strip()]
        preamble = ""
        if blocks and not blocks[0].startswith("## "):
            preamble = blocks.pop(0) + "\n\n"
        for i, block in enumerate(blocks):
            first_line = block.splitlines()[0]
            section = first_line.lstrip("#").strip()
            # Preamble only folds into the first chunk, not every chunk (avoids tanking its IDF weight to zero).
            full_text = (preamble + block) if i == 0 else block
            dates_match = DATES_LINE.search(full_text)
            has_dates = dates_match is not None
            is_current = has_dates and "present" in dates_match.group(1).lower()
            has_location = LOCATION_LINE.search(full_text) is not None
            chunks.append(
                Chunk(
                    source=source,
                    section=section,
                    text=full_text,
                    is_current=is_current,
                    has_dates=has_dates,
                    has_location=has_location,
                )
            )
    return chunks


def _derive_subject_stopwords(chunks: list[Chunk]) -> set[str]:
    titles_by_source: dict[str, str] = {}
    for chunk in chunks:
        if chunk.source in titles_by_source:
            continue
        match = H1_TITLE.search(chunk.text)
        if match:
            titles_by_source[chunk.source] = match.group(1)
    # The part of a title before " - Doc Type" (e.g. "Kevin Lee - Resume") is the subject's own name and never discriminative for retrieval; works with a single knowledge file too, unlike the old cross-file-intersection approach.
    stopwords: set[str] = set()
    for title in titles_by_source.values():
        subject_part = SUBJECT_TITLE_SEPARATOR.split(title, maxsplit=1)[0]
        stopwords |= {w.lower() for w in WORD.findall(subject_part)}
    return stopwords


class KnowledgeIndex:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        stop_words = ENGLISH_STOP_WORDS | _derive_subject_stopwords(chunks)
        self.vectorizer = TfidfVectorizer(analyzer=_stemmed_analyzer(stop_words))
        self.matrix = self.vectorizer.fit_transform([c.text for c in chunks])
        # Raw corpus words (not the vectorizer's filtered vocabulary) so subject names count as known.
        corpus_words = {w.lower() for chunk in chunks for w in WORD.findall(chunk.text)}
        self.known_words: set[str] = corpus_words | ENGLISH_STOP_WORDS
        # Stemmed vocabulary so a real-but-unseen word form isn't mistaken for gibberish.
        self.known_stems: set[str] = {stem(w) for w in self.known_words}

    def _temporal_boost(self, query: str, chunk: Chunk, top_raw: float) -> float:
        if not chunk.has_dates or top_raw <= 0:
            return 0.0
        if CURRENT_CUES.search(query) and chunk.is_current:
            return top_raw * CURRENT_ROLE_BOOST
        if PRIOR_CUES.search(query) and not chunk.is_current:
            return top_raw * PRIOR_ROLE_BOOST
        if RECENT_CUES.search(query) and not chunk.is_current:
            return top_raw * RECENT_ROLE_BOOST
        return 0.0

    def _title_match_boost(self, query: str, chunk: Chunk, top_raw: float) -> float:
        query_words = {w.lower() for w in TITLE_WORD.findall(query)} - GENERIC_TITLE_WORDS
        title_words = {w.lower() for w in TITLE_WORD.findall(chunk.section)} - GENERIC_TITLE_WORDS
        if not query_words or not title_words:
            return 0.0
        query_stems = {stem(w) for w in query_words}
        title_stems = {stem(w) for w in title_words}
        if not (query_stems & title_stems):
            return 0.0
        # A conceptual title match is trustworthy even at zero raw TF-IDF overlap, so give it a flat floor.
        return (top_raw * TITLE_MATCH_BOOST) if top_raw > 0 else TITLE_MATCH_FLOOR_BOOST

    def _location_boost(self, query: str, chunk: Chunk) -> float:
        # has_location is only ever true for the contact chunk, so it's trustworthy even with zero overlap.
        if not chunk.has_location:
            return 0.0
        has_temporal_cue = CURRENT_CUES.search(query) or PRIOR_CUES.search(query) or RECENT_CUES.search(query)
        return LOCATION_MATCH_BOOST if WHERE_CUES.search(query) and not has_temporal_cue else 0.0

    def _no_signal_floor_boost(self, top_raw: float) -> float:
        # A raw TF-IDF score of exactly zero means every query word is either a stopword or absent from the whole corpus's vocabulary -- there's no lexical signal to rank on either way, so let the naturally-ordered top chunks through and trust the LLM's own grounding instructions to decline if they turn out not to answer the question, instead of hard-refusing on a coin flip.
        return NO_SIGNAL_FLOOR_BOOST if top_raw == 0.0 else 0.0

    def search(self, query: str, top_k: int = TOP_K, intent_query: str | None = None) -> list[tuple[Chunk, float]]:
        intent_query = intent_query if intent_query is not None else query
        query_vector = self.vectorizer.transform([query])
        raw_scores = cosine_similarity(query_vector, self.matrix)[0]
        top_raw = max(raw_scores) if len(raw_scores) else 0.0
        no_signal_floor = self._no_signal_floor_boost(top_raw)
        boosted = [
            score
            + self._temporal_boost(intent_query, chunk, top_raw)
            + self._title_match_boost(intent_query, chunk, top_raw)
            + self._location_boost(intent_query, chunk)
            + no_signal_floor
            for chunk, score in zip(self.chunks, raw_scores, strict=True)
        ]
        ranked = sorted(zip(self.chunks, boosted, strict=True), key=lambda pair: pair[1], reverse=True)
        return ranked[:top_k]


def build_index(knowledge_dir: str = KNOWLEDGE_DIR) -> KnowledgeIndex:
    return KnowledgeIndex(load_chunks(knowledge_dir))


def rank_texts_by_query(query: str, texts: list[str], threshold: float, top_k: int = TOP_K) -> list[tuple[int, float]]:
    # Ad-hoc TF-IDF ranking for texts that aren't part of the pre-built knowledge index (e.g. live GitHub repos fetched per request), so the caller can filter out unrelated items instead of dumping the whole batch as "sources".
    if not texts:
        return []
    vectorizer = TfidfVectorizer(analyzer=_stemmed_analyzer(set(ENGLISH_STOP_WORDS)))
    matrix = vectorizer.fit_transform(texts)
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix)[0]
    ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
    return [(i, float(s)) for i, s in ranked if s >= threshold][:top_k]
