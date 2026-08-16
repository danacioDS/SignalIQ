# Dónde se calcula el NDI

Existen **3 implementaciones distintas** de NDI (la "triplicación" documentada en `architecture.md`):

## 1. Core Layer 4 (pipeline por capas)

| | |
|---|---|
| Archivo | `backend/app/layers/layer4_measurement.py:31` |
| Función | `calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)` (alias `calculate_ndi`, línea 41) |
| Fórmula | `ndi = sentiment_zscore - momentum_zscore` |
| Llamada desde | `backend/app/layers/layer4_orchestrator.py:56` dentro de `process_asset()` |
| Nota | Sin clamping. Retorna `None` si alguna entrada es `None`. Los z-scores vienen de Layer 3 (rolling 20 días). |

## 2. API de producción (`main.py`)

| | |
|---|---|
| Archivo | `backend/app/main.py:485` |
| Función | `calculate_ndi(ticker)` |
| Fórmula | `ndi = (sentiment - momentum) * 3` (línea 531, factor de escala) |
| Entradas | `sentiment` = TextBlob sobre noticias reales del pipeline (`process_news_for_ticker`, con fallback simulado); `momentum` = retorno 10 días `(history[-1] - history[-10]) / history[-10]` |
| Nota | No hay clamp explícito aquí; el output se redondea a 3 decimales. Usa clasificación de 7 regímenes (`classify_regime`, línea 466). |

## 3. API nueva basada en yfinance (`api.py`)

| | |
|---|---|
| Archivo | `backend/app/api.py:37` |
| Función | `calculate_ndi(closes)` |
| Fórmula | `ndi = sentiment_zscore - momentum_zscore` (línea 68), clamped a `[-3.0, 3.0]` (línea 69) |
| Entradas | Ambas son z-scores calculados internamente desde los precios de cierre: `sentiment_zscore` = z-score del retorno diario más reciente; `momentum_zscore` = z-score del retorno a 20 días |
| Nota | Devuelve tupla `(ndi, sentiment_zscore, momentum_zscore)`. Usa `classify_regime` (línea 72, 7 regímenes). |

## Dónde se calculan sentiment_zscore y momentum_zscore

### Core Layer 3 (pipeline por capas)

- Cálculo: `backend/app/layers/layer3_orchestrator.py:105-110` (dentro de `finalize_day`):
  - `sentiment_zscore = self._sentiment.get_rolling_zscore(ticker, dt, daily_raw)` (línea 105)
  - `momentum_zscore = self._momentum.get_rolling_zscore(ticker, dt, daily_return)` (línea 110)
- `momentum_zscore` real: `backend/app/layers/layer3_momentum.py:94-117` — z-score del retorno diario actual contra el historial anterior a `dt`: `(current_return - mean) / std`. Ventana `momentum_window_days=20` y mín. `min_valid_days_momentum=10` (`layer3_config.py:16-17`).
- `sentiment_zscore` real: **no existe / import roto** — `SentimentProcessor` se importa en `layer3_orchestrator.py:9` pero la clase no está definida en ningún archivo (en `layer3_sentiment.py` solo existe `polarity()`).

### API yfinance (`api.py`)

- `sentiment_zscore`: `backend/app/api.py:49` — `(daily_returns[-1] - mean_ret) / std_ret` (z-score del último retorno diario).
- `momentum_zscore`: `backend/app/api.py:62` — `(momentum_returns[-1] - mean_mom) / std_mom` (z-score del último retorno a 20 días).

### API de producción (`main.py`)

- No usa z-scores: `sentiment` (línea 502, noticias reales / fallback simulado en línea 517) y `momentum` (línea 524, retorno 10 días) se calculan inline.

### Consumidores de los z-scores

- `backend/app/layers/layer4_orchestrator.py:56` — `calculate_ndi(sentiment_zscore, momentum_zscore)`.
- `backend/app/services/ndi_service.py:60-68` — extrae los z-scores del resultado de Layer 3 y los pasa a `process_asset()`.
- `backend/app/services/ndi_service_simple.py:47-48` — ídem (variante simplificada).
- `backend/fix_analyze.py:39` — lee `ndi, sentiment_zscore, momentum_zscore` desde la BD.
- `scripts/run_layer3_*.py` — persisten `sentiment_zscore`/`momentum_zscore` en la tabla de señales.

## Otros usos/derivados

- `backend/app/services/ndi_service.py:23` — `NDIService.calculate()` conecta `main.py` con el pipeline de Layers (delega en Layer 4).
- `backend/app/services/ndi_service_simple.py` — variante simplificada del servicio.
- `scripts/run_layer3_daily.py:77` — `ndi = sentiment - momentum` (sin z-scores ni escala).
- `scripts/generate_signals_direct.py:70` — `ndi = sentiment - (momentum / 100)`, clamped a `[-2, 2]`.
- `scripts/backtest_engine.py`, `scripts/backtest_improved.py` — NDI simulado (no derivado de datos reales).
- Tests: `tests/pytest/test_ndi.py` importa `calculate_ndi` desde `app.main`.
- Prueba de consistencia: `tests/pytest/test_architecture.py:65` (`test_ndi_formula_consistency`) falla porque espera el módulo `domain.ndi_calculator` que no existe.

## Referencias

- Fórmula canónica del README: `NDI = sentiment_zscore − momentum_zscore`
- Regímenes (7): `architecture.md:359-367` — EXTREME OVERHEATING (>2.0) … CAPITULATION (≤-2.0)
