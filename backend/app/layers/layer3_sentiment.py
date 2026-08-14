"""Layer 3 sentiment — Loughran-McDonald lexicon and daily z-score processor."""

import math
import re
from collections import deque
from datetime import date

from app.layers.layer3_config import CONFIG
from app.layers.lm_lexicon import POSITIVE as LM_POSITIVE, NEGATIVE as LM_NEGATIVE

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
    "dividend", "yield", "return", "shareholder", "value", "wealth", 
    "expands", "partnership", "partnerships", "open", "opens", "becomes",
    "believe", "believes", "maintains", "maintain", "rating", "upgrade",
    "target", "price", "potential", "opportunity", "breakthrough"
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
    "volatility", "instability", "uncertain", "unpredictable",
    "declines", "decline", "amid", "turmoil", "lowered", "lowering",
    "pressure", "concern", "uncertainty", "volatility", "headwind"
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
    Considera palabras negativas, modificadores de negación y frases compuestas.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    text_lower = text.lower()
    tokens = re.findall(r"\b[a-z]+\b", text_lower)
    
    if not tokens:
        return 0.0
    
    # Frases compuestas clave (2-3 palabras)
    phrases = {
        "opens new doors": 0.3,
        "buy rating": 0.4,
        "target price": 0.2,
        "amid turmoil": -0.4,
        "holdings lowered": -0.3,
        "stock declines": -0.4,
        "expands reach": 0.3,
        "becomes first": 0.2,
        "believes": 0.2,
        "maintains rating": 0.3,
        "cheapest valuation": 0.2,
        "pre-ai boom": 0.5
    }
    
    # Verificar frases compuestas
    phrase_score = 0.0
    for phrase, score in phrases.items():
        if phrase in text_lower:
            phrase_score += score
    
    # Análisis de palabras individuales
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
    
    # Calcular sentimiento base
    total = pos_count + neg_count
    if total == 0:
        base_score = 0.0
    else:
        base_score = (pos_count - neg_count) / total
    
    # Combinar con el score de frases
    if phrase_score != 0.0:
        # Normalizar el score de frases (máximo 0.5)
        normalized_phrase = min(0.5, max(-0.5, phrase_score / 3))
        # Combinar con el score base (base pesa 60%, frases 40%)
        combined_score = (base_score * 0.6) + (normalized_phrase * 0.4)
        # Limitar el rango [-1, 1]
        return max(-1.0, min(1.0, combined_score))
    
    return base_score