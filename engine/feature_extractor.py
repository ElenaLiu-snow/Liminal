"""
Liminal — feature_extractor.py
Extracts linguistic features from a raw ASR transcript.
Input: raw transcript string (with optional [pause Xs] markers)
Output: features dict matching analysis_schema.json input spec
"""

import re
from collections import Counter


FILLER_WORDS = {
    "um", "uh", "er", "ah", "hmm", "like", "you know", "you know what i mean",
    "i mean", "sort of", "kind of", "kinda", "sorta", "basically", "actually",
    "literally", "right", "okay so", "so", "well"
}

SELF_CORRECTION_PHRASES = [
    "no wait", "i mean", "actually", "or rather", "let me rephrase",
    "what i meant", "not exactly", "correction", "no no", "well actually",
    "scratch that"
]

ABSOLUTIST_WORDS = {
    "always", "never", "everyone", "no one", "nobody", "everybody",
    "everything", "nothing", "all", "none", "completely", "totally",
    "absolutely", "forever", "impossible", "must", "have to", "have got to",
    "can't possibly", "will never", "would never"
}

NEGATION_WORDS = {
    "not", "never", "no", "don't", "won't", "can't", "couldn't",
    "wouldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't",
    "doesn't", "didn't", "haven't", "hasn't", "hadn't"
}

FIRST_PERSON = {"i", "me", "my", "myself", "mine"}


def extract_pauses(text: str) -> list[str]:
    """Extract [pause Xs] annotations from transcript."""
    return re.findall(r'\[pause\s+[\d.]+s?\]', text, re.IGNORECASE)


def extract_significant_pauses(text: str, threshold: float = 1.5) -> list[float]:
    """Return pause durations above threshold (seconds)."""
    pauses = re.findall(r'\[pause\s+([\d.]+)s?\]', text, re.IGNORECASE)
    return [float(p) for p in pauses if float(p) >= threshold]


def clean_text(text: str) -> str:
    """Remove pause markers and normalize whitespace."""
    text = re.sub(r'\[pause\s+[\d.]+s?\]', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text: str) -> list[str]:
    """Simple word tokenizer, lowercased."""
    return re.findall(r"\b[a-z']+\b", text.lower())


def get_first_person_density(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    count = sum(1 for t in tokens if t in FIRST_PERSON)
    return round(count / len(tokens), 3)


def get_filler_info(text: str) -> tuple[int, list[str]]:
    """Count fillers and return distinct ones found. Handles multi-word fillers first."""
    text_lower = text.lower()
    found = []
    count = 0

    # Check multi-word fillers first to avoid double-counting
    multi_word = sorted([f for f in FILLER_WORDS if ' ' in f], key=len, reverse=True)
    single_word = [f for f in FILLER_WORDS if ' ' not in f]

    for phrase in multi_word:
        occurrences = len(re.findall(r'\b' + re.escape(phrase) + r'\b', text_lower))
        if occurrences:
            found.append(phrase)
            count += occurrences

    for word in single_word:
        occurrences = len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
        if occurrences:
            found.append(word)
            count += occurrences

    return count, sorted(set(found))


def get_self_corrections(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for phrase in SELF_CORRECTION_PHRASES:
        if re.search(r'\b' + re.escape(phrase) + r'\b', text_lower):
            found.append(phrase)
    return found


def get_absolutist_words(tokens: list[str]) -> list[str]:
    found = [t for t in tokens if t in ABSOLUTIST_WORDS]
    return sorted(set(found))


def get_negation_count(tokens: list[str]) -> int:
    return sum(1 for t in tokens if t in NEGATION_WORDS)


def get_repeated_phrases(tokens: list[str], min_n: int = 2, max_n: int = 3, min_count: int = 2) -> list[str]:
    """Find n-grams appearing min_count or more times."""
    repeated = []
    for n in range(min_n, max_n + 1):
        ngrams = [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
        counts = Counter(ngrams)
        repeated.extend([ng for ng, c in counts.items() if c >= min_count])
    return sorted(set(repeated))


def extract_features(raw_transcript: str, speaking_duration_seconds: float = None) -> dict:
    """
    Main entry point.
    Args:
        raw_transcript: verbatim ASR text, may contain [pause Xs] markers
        speaking_duration_seconds: optional float from audio metadata
    Returns:
        features dict matching analysis_schema input spec
    """
    pause_markers = extract_pauses(raw_transcript)
    significant_pauses = extract_significant_pauses(raw_transcript)
    clean = clean_text(raw_transcript)
    tokens = tokenize(clean)

    filler_count, fillers_found = get_filler_info(clean)
    self_corrections = get_self_corrections(clean)
    absolutist = get_absolutist_words(tokens)
    repeated = get_repeated_phrases(tokens)

    return {
        "first_person_density": get_first_person_density(tokens),
        "absolutist_words": absolutist,
        "absolutist_count": len(absolutist),
        "filler_count": filler_count,
        "fillers_found": fillers_found,
        "self_corrections": self_corrections,
        "self_correction_count": len(self_corrections),
        "repeated_phrases": repeated,
        "pause_markers": pause_markers,
        "significant_pauses": significant_pauses,
        "negation_count": get_negation_count(tokens),
        "word_count": len(tokens),
        "speaking_duration_seconds": speaking_duration_seconds
    }


if __name__ == "__main__":
    import json

    sample = (
        "I see... [pause 2.3s] um... a figure on a cliff. I don't know, it feels like "
        "they're about to fall, or maybe jump. I mean, not like in a bad way. They seem "
        "free actually. It's always like this with me, I never know if I'm about to fall "
        "or fly. [pause 1.8s] I always feel like I'm on the edge of something. Always."
    )

    result = extract_features(sample, speaking_duration_seconds=42.0)
    print(json.dumps(result, indent=2))
