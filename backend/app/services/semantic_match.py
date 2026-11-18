import math
import re
from typing import Iterable, List, Sequence

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None


_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None and SentenceTransformer is not None:
        try:
            _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:  # pragma: no cover
            _MODEL = False
    return _MODEL


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return re.findall(r"[a-zA-Z0-9+/.-]+", text.lower())


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if np is None:
        return 0.0
    a_vec = np.asarray(a, dtype=float)
    b_vec = np.asarray(b, dtype=float)
    if a_vec.size == 0 or b_vec.size == 0:
        return 0.0
    denom = math.sqrt(float(np.dot(a_vec, a_vec))) * math.sqrt(float(np.dot(b_vec, b_vec)))
    if denom == 0:
        return 0.0
    return float(np.dot(a_vec, b_vec) / denom)


def _fallback_similarity(text_a: str, text_b: str) -> float:
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0

    set_a = set(tokens_a)
    set_b = set(tokens_b)
    common = set_a & set_b
    if not common:
        return 0.0

    overlap = len(common) / min(len(tokens_a), len(tokens_b))
    jaccard = len(common) / len(set_a | set_b)
    score = max(overlap, jaccard) + (0.2 * min(overlap, jaccard))
    return max(0.0, min(1.0, score))


def semantic_similarity(text_a: str, text_b: str) -> float:
    """Compute a semantic match score between two technical text snippets.

    Uses SentenceTransformers when available, with a deterministic lexical fallback
    so the service remains usable in offline/dev environments.
    """
    if not text_a or not text_b:
        return 0.0

    model = _get_model()
    if model and model is not False:
        try:
            emb1 = model.encode(text_a, convert_to_numpy=True, normalize_embeddings=True)
            emb2 = model.encode(text_b, convert_to_numpy=True, normalize_embeddings=True)
            score = _cosine_similarity(emb1, emb2)
            if 0.0 <= score <= 1.0:
                return float(score)
        except Exception:  # pragma: no cover
            pass

    return _fallback_similarity(text_a, text_b)


def score_candidate(job_description: str, candidate_text: str) -> float:
    return semantic_similarity(job_description, candidate_text)
