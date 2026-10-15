"""Camada B - metricas NLP automaticas (Secao 3.9.1 do TCC / Secao 4.5 do artigo aprovado).

Stopwords are a short curated Portuguese list, not NLTK's downloaded corpus — keeps
tokenization deterministic and offline (no network access needed to run tests).
"""

import re

import textstat

_STOPWORDS_PT = {
    "a",
    "as",
    "o",
    "os",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "e",
    "ou",
    "em",
    "um",
    "uma",
    "uns",
    "umas",
    "para",
    "por",
    "com",
    "sem",
    "que",
    "se",
    "no",
    "na",
    "nos",
    "nas",
    "ao",
    "aos",
    "à",
    "às",
    "é",
    "são",
    "foi",
    "ser",
    "como",
    "mais",
    "mas",
    "seu",
    "sua",
    "seus",
    "suas",
    "este",
    "esta",
    "isso",
    "isto",
    "esse",
    "essa",
    "pela",
    "pelo",
    "entre",
    "sobre",
}

_TOKEN_RE = re.compile(r"[a-zà-ÿA-ZÀ-Ÿ]+")


def tokenizar(texto: str) -> list[str]:
    """Lowercase, strip punctuation/digits, remove a short Portuguese stopword list."""
    tokens = _TOKEN_RE.findall(texto.lower())
    return [t for t in tokens if t not in _STOPWORDS_PT]


def cobertura_lexical(tokens_item: list[str], tokens_objetos_conhecimento: list[str]) -> float:
    """C(i,h) = |T(i) intersect O(h)| / |T(i)| (Secao 4.5 do artigo aprovado)."""
    if not tokens_item:
        return 0.0
    conjunto_item = set(tokens_item)
    conjunto_oc = set(tokens_objetos_conhecimento)
    return len(conjunto_item & conjunto_oc) / len(conjunto_item)


def especificidade_curricular(cobertura_habilidade_alvo: float, coberturas_outras_habilidades: list[float]) -> float:
    """E(i,h) = C(i, h_alvo) / mean(C(i, h_j)) para as demais habilidades do recorte (Secao 4.5).

    Returns 0.0 when the target coverage is zero, and a large sentinel (not inf) when the
    denominator would be zero but the numerator is positive — a ratio undefined in that
    direction is reported as maximal specificity rather than raising.
    """
    if cobertura_habilidade_alvo == 0.0:
        return 0.0
    outras_validas = [c for c in coberturas_outras_habilidades if c > 0]
    if not outras_validas:
        return cobertura_habilidade_alvo / 1e-6
    media_outras = sum(outras_validas) / len(outras_validas)
    return cobertura_habilidade_alvo / media_outras


def diversidade_lexical_ttr(tokens: list[str]) -> float:
    """Type-Token Ratio: proporcao de tokens unicos (Secao 3.9.1 do TCC)."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def legibilidade_fkgl(texto: str) -> float:
    """Flesch-Kincaid Grade Level (Secao 3.9.1 do TCC)."""
    return float(textstat.flesch_kincaid_grade(texto))


def similaridade_cosseno(vetor_a: list[float], vetor_b: list[float]) -> float:
    """Cosine similarity between two embedding vectors (Secao 3.9.1 do TCC)."""
    if len(vetor_a) != len(vetor_b) or not vetor_a:
        return 0.0
    produto_escalar: float = sum(a * b for a, b in zip(vetor_a, vetor_b, strict=True))
    norma_a: float = sum(a * a for a in vetor_a) ** 0.5
    norma_b: float = sum(b * b for b in vetor_b) ** 0.5
    if norma_a == 0.0 or norma_b == 0.0:
        return 0.0
    return produto_escalar / (norma_a * norma_b)
