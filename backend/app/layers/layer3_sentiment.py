"""Layer 3 sentiment — Loughran-McDonald lexicon and daily z-score processor."""

import math
import re
from collections import deque
from datetime import date

from layers.layer3_config import CONFIG
from layers.lm_lexicon import POSITIVE as LM_POSITIVE, NEGATIVE as LM_NEGATIVE

# Merge LM lexicon with original hardcoded words for backward compatibility.
# Original words not in LM: surge, gain, rise, beat, up, positive (positive);
# fall, drop, miss, down, slump, bad, negative (negative).
# Vocabulario ampliado para análisis de sentimiento financiero
# Vocabulario financiero ampliado
_OLD_POSITIVE = {
    # Crecimiento y rendimiento
    "surge", "rally", "gain", "rise", "beat", "up", "positive", "growth",
    "record", "high", "breakout", "momentum", "outperform", "strong",
    "profit", "earnings", "revenue", "raised", "upgrade", "buy", "bullish",
    "confidence", "opportunity", "recovery", "expansion", "innovation",
    "leadership", "dominant", "advantage", "potential", "promising",
    "robust", "solid", "impressive", "excellent", "superior", "outstanding",
    "remarkable", "significant", "substantial", "accelerating", "boom",
    "thriving", "flourishing", "prospering", "success", "successful",
    "achievement", "milestone", "breakthrough", "pioneer", "trailblazer",
    "market", "share", "demand", "adoption", "expansion", "strategic",
    "partnership", "collaboration", "alliance", "acquisition", "merger",
    "dividend", "yield", "return", "shareholder", "value", "wealth"
}

_OLD_NEGATIVE = {
    # Declive y riesgo
    "fall", "drop", "miss", "down", "slump", "bad", "negative", "decline",
    "loss", "cut", "lower", "downgrade", "sell", "bearish", "weak",
    "pressure", "volatile", "uncertainty", "warning", "doubt", "risk",
    "concern", "underperform", "struggle", "challenge", "headwind",
    "slowing", "slowdown", "recession", "inflation", "fear", "panic",
    "crash", "plunge", "tumble", "slide", "correction", "crisis",
    "disappoint", "disappointing", "missed", "shortfall", "debt",
    "liability", "lawsuit", "investigation", "regulatory", "fine",
    "penalty", "sanction", "violation", "breach", "default", "bankruptcy",
    "insolvency", "liquidation", "layoff", "restructuring", "turmoil",
    "volatility", "instability", "uncertain", "unpredictable"
}

POSITIVE_WORDS = LM_POSITIVE | _OLD_POSITIVE
NEGATIVE_WORDS = LM_NEGATIVE | _OLD_NEGATIVE

# Palabras de contexto que pueden modificar el sentimiento
# Palabras que indican intensidad o negación
INTENSIFIERS = {
    "very", "extremely", "highly", "significantly", "substantially",
    "remarkably", "exceptionally", "particularly", "notably", "strongly",
    "deeply", "profoundly", "dramatically", "massively", "enormously"
}

NEGATION_WORDS = {
    "not", "no", "never", "neither", "nor", "without", "lack",
    "lacks", "lacking", "absence", "absence of", "fails", "failed",
    "failure", "fail", "failing"
}


def polarity(text: str) -> float:
    """
    Calcula el sentimiento de un texto usando el vocabulario Loughran-McDonald.
    Considera palabras negativas y modificadores de negación.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    text_lower = text.lower()
    tokens = re.findall(r"\b[a-z]+\b", text_lower)
    
    if not tokens:
        return 0.0
    
    # Detectar negaciones
    negated = False
    pos_count = 0
    neg_count = 0
    
    for i, token in enumerate(tokens):
        # Verificar si es un modificador de negación
        if token in NEGATION_WORDS:
            negated = True
            continue
        
        # Verificar si es un intensificador
        if token in INTENSIFIERS:
            continue
        
        # Verificar sentimiento de la palabra
        is_positive = token in POSITIVE_WORDS
        is_negative = token in NEGATIVE_WORDS
        
        # Aplicar negación si corresponde
        if negated:
            if is_positive:
                neg_count += 1
            elif is_negative:
                pos_count += 1
            negated = False
        else:
            if is_positive:
                pos_count += 1
            elif is_negative:
                neg_count += 1
    
    # Si no hay palabras con sentimiento, retornar 0
    if pos_count == 0 and neg_count == 0:
        return 0.0
    
    # Calcular sentimiento como proporción balanceada
    total = pos_count + neg_count
    return (pos_count - neg_count) / total