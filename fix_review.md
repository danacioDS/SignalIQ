# SignalIQ Fix Review

## 1. NDI Formula — Eliminado el factor 5x artificial

**Archivo:** `layers/layer4_orchestrator.py`

**Problema:** `fix_ndi_formula.py` parcheaba la fórmula NDI agregando `* 5` para que los valores llegaran a ±1.5 con datos sintéticos. Esto distorsionaba toda la escala estadística del sistema.

**Cambio:**
```
# Antes (factor artificial):
raw_ndi = (narrative_score - momentum_score) * 5 * fundamental_adjustment
return max(-4.0, min(4.0, raw_ndi))

# Después (teóricamente correcto):
raw_ndi = (narrative_score - momentum_score) * fundamental_adjustment
return max(-2.0, min(2.0, raw_ndi))
```

**Thresholds recalibrados** para la escala sin amplificar (NDI en [-1, 1]):

| Régimen | Antes (5x) | Después |
|---|---|---|
| Critical Divergence | ≥ 2.5 | ≥ 0.5 |
| Divergence Warning | ≥ 1.5 | ≥ 0.3 |
| Narrative Exhaustion | ≥ 0.5 | ≥ 0.1 |
| Aligned | ≥ -0.5 | ≥ -0.1 |
| Silent Accumulation | ≥ -1.5 | ≥ -0.3 |
| Inverse Divergence | ≥ -2.0 | ≥ -0.4 |

**Confidence thresholds** recalibrados proporcionalmente (÷5).

Se eliminaron emojis de los strings de recomendación (inconsistentes con el formato texto del sistema).

---

## 2. Layer 2 — SQL Schema poblado

**Archivos creados en `data_storage/`:**

| Archivo | Propósito |
|---|---|
| `001_create_layer2_schema.sql` | `CREATE TABLE` para `prices`, `headlines` (con SHA256 dedup), `ndi_signals` — cada uno con índices y constraints `UNIQUE` |
| `master_build.sql` | Wrapper que ejecuta el schema en orden |
| `rollback.sql` | `DROP TABLE IF EXISTS ... CASCADE` |
| `test_queries.sql` | Queries de validación: row counts, últimos registros por ticker, verificación de schema |

Anteriormente los 4 archivos estaban vacíos (0 bytes). Ahora el proyecto es reproducible desde una BD PostgreSQL vacía con `psql -d signaliq -f data_storage/master_build.sql`.

---

## 3. Archivos basura eliminados del repo

| Archivo | Motivo |
|---|---|
| `layers/layer4_orchestrator.py.bak` | Backup residual que no debe estar versionado |
| `fix_ndi_formula.py` | Script de parcheo temporal — la corrección ya está aplicada directamente |

**`.gitignore`:** Se agregó `*.bak` para prevenir futuros archivos de backup.

---

## 4. Fundamental Engine integrado al pipeline

**Archivo nuevo:** `layers/integration.py`

Expone dos funciones de alto nivel:

- **`run_pipeline(ticker, narrative_score, technical_score, article_count, fundamental_data)`** — pipeline completo para un activo. Conecta `FundamentalEngine` (cálculo de métricas → score) con `Layer4Orchestrator` (NDI + Bubble Risk + Confidence + Regime).
- **`run_batch_pipeline(assets)`** — procesa múltiples activos en una sola llamada.

**Test movido:** `test_fundamental.py` (raíz) → `tests/test_fundamental_engine.py`

**`layers/__init__.py`** actualizado para exportar `Layer4Orchestrator`, `PersistenceTracker`, `run_pipeline`, `run_batch_pipeline`.

---

## 5. Loughran-McDonald Lexicon agregado

**Archivo nuevo:** `layers/lm_lexicon.py`

~600 palabras clasificadas en 6 categorías (Loughran & McDonald 2011):

| Categoría | Palabras | Uso en SignalIQ |
|---|---|---|
| `positive` | ~50 | Sentimiento alcista |
| `negative` | ~80 | Sentimiento bajista |
| `uncertainty` | ~80 | Riesgo / ambigüedad |
| `litigious` | ~280 | Riesgo legal |
| `constraining` | ~70 | Restricciones / obligaciones |
| `superfluous` | ~40 | Lenguaje redundante |

**Funciones:**
- `score_text(text)` — cuenta ocurrencias por categoría, devuelve raw counts + scores normalizados
- `net_sentiment(text)` — score neto positivo-negativo en rango [-1, 1]

---

## Resumen de archivos modificados/creados

```
MODIFICADOS:
  .gitignore                          + *.bak
  layers/__init__.py                  + exports
  layers/layer4_orchestrator.py       - factor 5x, thresholds recalibrados
  data_storage/001_create_layer2_schema.sql   vacío → schema completo
  data_storage/master_build.sql               vacío → build wrapper
  data_storage/rollback.sql                   vacío → rollback DDL
  data_storage/test_queries.sql               vacío → queries de validación

CREADOS:
  layers/lm_lexicon.py               Loughran-McDonald lexicon
  layers/integration.py               Pipeline connector L3→L4
  tests/test_fundamental_engine.py    Test movido desde raíz

ELIMINADOS:
  fix_ndi_formula.py                  Script de parcheo temporal
  layers/layer4_orchestrator.py.bak   Backup residual
  test_fundamental.py                 Movido a tests/
```
