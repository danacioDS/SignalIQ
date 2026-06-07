# Informe de Auditoría Técnica — SignalIQ

> **Fecha:** 2026-06-06
> **Auditor:** Staff Software Engineer / Senior Technical Auditor
> **Tipo:** Auditoría integral de código, seguridad, arquitectura y producción

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Top 10 Problemas](#2-top-10-problemas-mas-importantes)
3. [Hallazgos Detallados](#3-hallazgos-detallados)
   - [3.1 Bugs Potenciales](#31-bugs-potenciales)
   - [3.2 Seguridad](#32-seguridad)
   - [3.3 Calidad del Código y Arquitectura](#33-calidad-del-codigo-y-arquitectura)
   - [3.4 Rendimiento](#34-rendimiento)
   - [3.5 Base de Datos](#35-base-de-datos)
   - [3.6 Testing](#36-testing)
   - [3.7 Producción y Operaciones](#37-produccion-y-operaciones)
4. [Evaluaciones Cuantitativas](#4-evaluaciones-cuantitativas)
5. [Recomendaciones Priorizadas](#5-recomendaciones-priorizadas)

---

## 1. Resumen Ejecutivo

| Métrica | Puntaje |
|---------|---------|
| Preparación para Producción | **28/100** |
| Calidad Arquitectónica | **42/100** |
| Mantenibilidad | **35/100** |
| Riesgo General | **ALTO** |

SignalIQ tiene una base conceptual interesante pero su implementación actual presenta **riesgos críticos** que impiden su despliegue en producción:

1. **5+ API keys de Google Gemini hardcodeadas** en el código fuente y commiteadas en git.
2. **Tests de las capas principales rotos** — fallan con `ImportError` al instante.
3. **Schema de base de datos incompleto** — el código referencia funciones SQL que no existen.
4. **Side effects en import-time** que hacen impredecible el comportamiento del sistema.
5. **Múltiples implementaciones duplicadas** del mismo concepto con nombres idénticos.

---

## 2. Top 10 Problemas Más Importantes

| # | Severidad | Archivo | Problema |
|---|-----------|---------|----------|
| 1 | 🔴 CRÍTICA | `backend/app/main.py:21-25`, `backend/app/llm_provider.py:15-19`, `layers/layer4_orchestrator.py:11`, `docker-compose.yml:9-11`, `.env:9` | **5 API keys de Google Gemini hardcodeadas** en 5 ubicaciones distintas + `.env` commiteado |
| 2 | 🔴 CRÍTICA | `tests/test_layer4.py:27-31`, `tests/test_layer1_integration.py:57` | **Tests principales rotos**: importan símbolos que no existen (`process_asset`, `normalize_price_response`). Fallan con `ImportError` |
| 3 | 🔴 CRÍTICA | `backend/app/main.py:177` | **Recursión infinita en endpoint HTTP**: error 429 de llama a `analyze(ticker)` recursivamente, causa stack overflow |
| 4 | 🔴 CRÍTICA | `data_storage/001_create_layer2_schema.sql` vs `layer1/writer.py:49-55` | **Schema BD incompleto**: código llama a `raw.insert_price_record()` y `raw.insert_headline_record()`, pero el SQL solo crea tablas en `public` sin schemas ni funciones |
| 5 | 🔴 ALTA | `layer1/collect_news.py:179`, `layer1/collect_prices.py:69` | **`sys.exit(1)` en funciones de librería**: mata todo el proceso sin posibilidad de recovery |
| 6 | 🔴 ALTA | `.env:5,21`, `layers/layer4_orchestrator.py:8-11` | **Config duplicada y forzada**: `PRIMARY_LLM` definido dos veces en `.env`, y el orquestador forza `gemini` pisando variable de entorno |
| 7 | 🔴 ALTA | `backend/app/main.py:53` vs `layers/layer4_measurement.py:27` | **Dos funciones `calculate_ndi`** con el mismo nombre pero semántica diferente (una basada en precio, otra en divergencia narrativa) |
| 8 | 🔴 ALTA | `signaliq/core/config.py:16-33` | **Config incompleta**: referencia `config.db.url` y `config.DATA_DIR` que no existen, causa `AttributeError` |
| 9 | 🔴 ALTA | `layer1/writer.py:86-89` | **Sin rollback en `UniqueViolation`**: transacción queda abortada después de duplicado, fallan queries subsecuentes |
| 10 | 🔴 ALTA | `layers/layer4_orchestrator.py` y `layers/layer4_orchestrator_simple.py` | **Clase `Layer4Orchestrator` duplicada**: dos archivos con la misma clase, compitiendo en namespace |

---

## 3. Hallazgos Detallados

### 3.1 Bugs Potenciales

---

#### B-01 [CRÍTICA] Tests de Layer 4 importan símbolos inexistentes

**Archivo:** `tests/test_layer4.py:27-31`

```python
from layers.layer4_orchestrator import (
    process_asset,
    process_batch,
    validate_batch_input,
    OUTPUT_FIELDS,
)
```

**Problema:** El archivo `layers/layer4_orchestrator.py` solo define la clase `Layer4Orchestrator`, no las funciones `process_asset`, `process_batch`, `validate_batch_input`, ni la constante `OUTPUT_FIELDS`. Estas parecen ser de una versión anterior del código que fue reemplazada pero los tests no se actualizaron.

**Impacto:** El comando `python tests/test_layer4.py` falla inmediatamente con `ImportError`. Todo el suite de tests de Layer 4 (518 líneas, 15 casos de prueba) es inservible. Cobertura de pruebas: 0% para Layer 4.

**Recomendación:** Reimplementar los tests para usar la API actual de `Layer4Orchestrator`, o restaurar las funciones exportadas que los tests esperan. La segunda opción es más rápida pero perpetúa el problema.

---

#### B-02 [CRÍTICA] Tests de Layer 1 importan función inexistente

**Archivo:** `tests/test_layer1_integration.py:57`

```python
from layer1.collect_prices import normalize_price_response
```

**Problema:** La función `normalize_price_response` no existe en `layer1/collect_prices.py`. El `collect_prices.py` actual usa `yfinance` directamente y no tiene esa función.

**Impacto:** `python tests/test_layer1_integration.py` falla con `ImportError`. 14 tests de integración de Layer 1 no se ejecutan.

**Recomendación:** Eliminar la importación y reescribir el test para que use la API real de `fetch_asset_price` o bien implementar `normalize_price_response` si se considera parte de la interfaz.

---

#### B-03 [CRÍTICA] Recursión infinita en endpoint Flask por error 429

**Archivo:** `backend/app/main.py:172-178`

```python
except Exception as e:
    error_msg = str(e)
    if "429" in error_msg:
        next_key = (current_key_index + 1) % len(API_KEYS)
        if init_gemini(next_key):
            return analyze(ticker)  # <-- RECURSIÓN
    return jsonify({'error': error_msg}), 500
```

**Problema:** Cuando el endpoint recibe un error 429 (too many requests), la función se llama a sí misma recursivamente (`return analyze(ticker)`). No hay límite de profundidad. Si todas las API keys están rate-limited, la condición de 429 se repite infinitamente.

**Impacto:** Stack overflow del worker de Flask. Denegación de servicio. El servidor crashea y requiere reinicio manual.

**Recomendación:** Reemplazar la recursión con un bucle iterativo con límite máximo de reintentos:

```python
for attempt in range(len(API_KEYS)):
    # intentar con clave rotada...
    break
```

---

#### B-04 [ALTA] `sys.exit(1)` dentro de funciones de biblioteca

**Archivo:** `layer1/collect_news.py:179`, `layer1/collect_prices.py:69`

```python
# collect_news.py
if not result:
    logger.critical("All %d feeds failed to fetch", len(sources_to_fetch))
    sys.exit(1)

# collect_prices.py
if not results:
    logger.critical("All %d assets failed to fetch", len(ASSETS))
    sys.exit(1)
```

**Problema:** `sys.exit(1)` es llamado dentro de funciones que no son `main()`. En un contexto de servidor o pipeline automatizado, esto mata **todo el proceso** sin posibilidad de manejo de errores, logging adicional, o recuperación graceful.

**Impacto:** Si una ingesta programada de noticias tiene todos los feeds caídos temporalmente, el proceso completo muere. El scheduler (cron) podría no reintentar adecuadamente, perdiendo datos de todo el día.

**Recomendación:** Lanzar una excepción personalizada (e.g. `IngestionError`) y dejar que el llamador (el orquestador) decida si debe salir del proceso:

```python
class IngestionError(Exception):
    pass

# en lugar de sys.exit(1):
raise IngestionError(f"All {len(sources_to_fetch)} feeds failed")
```

---

#### B-05 [ALTA] Transacción abortada sin rollback en `write_headline`

**Archivo:** `layer1/writer.py:86-89`

```python
except psycopg2.UniqueViolation:
    # Rollback is not needed for news (no transaction)
    logger.warning("Duplicate headline for URL: %s", record.get("article_url"))
    return None
```

**Problema:** El comentario dice "no transaction" pero el orquestador (`layer1/orchestrator.py:196-210`) crea una conexión con `autocommit=False` y ejecuta `conn.commit()` después de escribir. Cuando ocurre `UniqueViolation`, PostgreSQL marca la transacción como abortada. Sin `conn.rollback()`, cualquier query posterior falla con `InternalError: current transaction is aborted`.

**Impacto:** Si hay un headline duplicado, el resto del batch falla. Pérdida de datos del batch parcial.

**Recomendación:** Agregar `conn.rollback()`:

```python
except psycopg2.UniqueViolation:
    conn.rollback()
    logger.warning("Duplicate headline for URL: %s", record.get("article_url"))
    return None
```

---

#### B-06 [ALTA] `validate_input` no maneja `price_history = None`

**Archivo:** `layers/layer4_measurement.py:6-24`

```python
def validate_input(sentiment_zscore, momentum_zscore, price_history):
    if sentiment_zscore is None:
        return ("INVALID_INPUT", "sentiment is None")
    if momentum_zscore is None:
        return ("INVALID_INPUT", "momentum is None")
    if len(price_history) < 6:  # TypeError si price_history es None
```

**Problema:** Si `price_history` es `None`, la instrucción `len(price_history)` lanza `TypeError`.

**Impacto:** Crash del pipeline de Layer 4 si el historial de precios no está disponible. El error no es capturado elegantemente.

**Recomendación:** Agregar verificación al inicio:

```python
if price_history is None:
    return ("INVALID_INPUT", "price_history is None")
```

---

#### B-07 [MEDIA] Variable de entorno pisada en import-time

**Archivo:** `layers/layer4_orchestrator.py:8-11`

```python
os.environ['PRIMARY_LLM'] = 'gemini'
os.environ['FALLBACK_LLM'] = 'mock'
os.environ['GEMINI_API_KEY'] = 'AQ.Ab8RN6KaJryb1fOwZEqQED8VkglkrbPEV_xV0gJHRZih-N4zKQ'
```

**Problema:** Al importar el módulo, las variables de entorno se sobrescriben sin importar la configuración existente. La API key hardcodeada prevalece sobre cualquier configuración del operador.

**Impacto:** Configuración de entorno pisada. Imposible usar diferentes API keys sin modificar el código fuente.

**Recomendación:** Eliminar estas líneas. El LLM Router ya lee de entorno correctamente. La configuración debe venir de `.env` o variables del sistema.

---

#### B-08 [MEDIA] `process_headline` puede generar `__UNRESOLVED__` como ticker real

**Archivo:** `layers/layer3_orchestrator.py:79-80`

```python
if not tickers:
    tickers = ["__UNRESOLVED__"]
```

**Problema:** Cuando un headline no se puede resolver a ningún ticker conocido, se usa `"__UNRESOLVED__"` como clave en el buffer de headlines. Este string podría persistir en reports o bases de datos como si fuera un ticker válido. No hay limpieza de este dato.

**Impacto:** Posible contaminación de datos en capas superiores. Un reporte podría mostrar señales para `__UNRESOLVED__`.

**Recomendación:** Usar `None` o un string que sea claramente inválido como ticker, y filtrarlo explícitamente en `finalize_day`.

---

#### B-09 [MEDIA] Duplicados en léxico Loughran-McDonald

**Archivo:** `layers/lm_lexicon.py`

**Problema:** Las palabras `resolve`, `wind_down`, `write_down`, `write_off`, `write_up` aparecen duplicadas en `NEGATIVE`. La palabra `resolve` aparece también en `POSITIVE`. Muchas palabras aparecen en múltiples categorías (`pending` en `UNCERTAINTY` y `LITIGIOUS`, `optimistic` en `POSITIVE` y `UNCERTAINTY`).

**Impacto:** Doble contaje de palabras en análisis de sentimiento. Resultados inconsistentes.

**Recomendación:** Asegurar que cada palabra pertenezca a una sola categoría usando un set para detección de conflictos.

---

#### B-10 [BAJA] Mock response usa emojis en string de retorno

**Archivo:** `signaliq/core/llm.py:150-186`

**Problema:** La respuesta mock contiene emojis (🔴, 🟡, 🟢, 📊, etc.) que pueden no renderizarse correctamente en todos los sistemas y complican el parsing downstream.

**Impacto:** Integraciones que parsean la respuesta del LLM pueden fallar por caracteres inesperados.

**Recomendación:** Usar texto plano en mock responses.

---

### 3.2 Seguridad

---

#### S-01 [CRÍTICA] API keys hardcodeadas en 5 ubicaciones

**Archivos:**
- `backend/app/main.py:21-25` — 3 keys en lista `API_KEYS`
- `backend/app/llm_provider.py:15-19` — mismas 3 keys
- `layers/layer4_orchestrator.py:11` — 1 key forzada en entorno
- `docker-compose.yml:9-11` — mismas 3 keys
- `.env:9` — 1 key real

```python
# backend/app/main.py
API_KEYS = [
    {'key': 'AQ.Ab8RN6J9aaoIwC5njV4N0Fkm7xO7jP7L42b8HMr2ngCP46dd9g', 'name': 'Proyecto_1'},
    {'key': 'AQ.Ab8RN6KPY1GhOw0r0Lc40OoMfUvbVNLmAJQU8wT9nnk76x2PpQ', 'name': 'Proyecto_2'},
    {'key': 'AQ.Ab8RN6IRvhpDXr9TKI0ZQ1L58imMmYQmctdrdMUYeNlTamhnnQ', 'name': 'SignalIQ_03'},
]
```

**Impacto:** Cualquier persona con acceso al repositorio puede usar estas claves para llamar a Gemini API. Riesgo de:
- Abuso económico (cada llamada cuesta dinero)
- Ban de cuentas por parte de Google
- Exposición en forks, mirrors, o si el repo se hace público
- Irreversible: aunque se roten las keys, el historial de git las conserva para siempre

**Recomendación INMEDIATA:**
1. Rotar las 3 keys en Google Cloud Console.
2. Eliminar secrets del historial git con `git-filter-repo` (BFG está presente en el repo pero no se ejecutó correctamente).
3. Eliminar todas las keys hardcodeadas de los archivos fuente.
4. Usar exclusivamente variables de entorno.
5. Configurar alertas de uso anómalo en Google Cloud.

---

#### S-02 [CRÍTICA] `.env` con credenciales reales commiteado en git

**Archivo:** `.env`

```
GEMINI_API_KEY=AQ.Ab8RN6KaJryb1fOwZEqQED8VkglkrbPEV_xV0gJHRZih-N4zKQ
DATABASE_URL=postgresql://usuario:password@localhost:5432/signaliq
```

**Problema:** El archivo `.env` contiene una API key real de Gemini y credenciales de base de datos. Está en el índice de git. El `.gitignore` excluye `.env`, pero el archivo ya fue commiteado antes de agregarlo al ignore.

**Impacto:** Las credenciales están en el historial de git para siempre. Cualquiera que clone el repositorio y explore el historial puede obtenerlas.

**Recomendación:** Rotar inmediatamente la API key y la contraseña de PostgreSQL. Eliminar `.env` del historial con `git-filter-repo`.

---

#### S-03 [CRÍTICA] API keys en docker-compose.yml

**Archivo:** `docker-compose.yml:9-11`

```yaml
environment:
  - GEMINI_API_KEY_1=AQ.Ab8RN6J9aaoIwC5njV4N0Fkm7xO7jP7L42b8HMr2ngCP46dd9g
  - GEMINI_API_KEY_2=AQ.Ab8RN6KPY1GhOw0r0Lc40OoMfUvbVNLmAJQU8wT9nnk76x2PpQ
  - GEMINI_API_KEY_3=AQ.Ab8RN6IRvhpDXr9TKI0ZQ1L58imMmYQmctdrdMUYeNlTamhnnQ
```

**Problema:** Las claves están en texto plano en el archivo de composición de Docker. Cualquier persona con acceso al servidor o al repositorio puede verlas. Docker puede exponerlas en logs, inspect, y volúmenes compartidos.

**Impacto:** Exposición adicional de las mismas 3 keys.

**Recomendación:** Usar variables de entorno con `${GEMINI_API_KEY_1}` o archivo `.env` referenciado con `env_file:`.

---

#### S-04 [ALTA] IP interna hardcodeada en frontend

**Archivo:** `frontend/src/App.tsx:25`

```typescript
const API_URL = 'http://163.176.128.135:8000';
```

**Problema:** Una dirección IP interna está hardcodeada en el código fuente del frontend. Esto filtra información de infraestructura. Además, HTTP sin TLS es inseguro para transmisión de datos financieros.

**Impacto:**
- Filtración de topología de red interna
- No funciona en diferentes entornos (dev/staging/prod)
- Sin cifrado en tránsito

**Recomendación:** Usar variable de entorno `REACT_APP_API_URL` y siempre HTTPS en producción.

---

#### S-05 [MEDIA] Sin rate limiting ni validación de entrada

**Archivo:** `backend/app/main.py:126-131`

```python
@app.route('/analyze/<ticker>', methods=['GET'])
def analyze(ticker):
    ...
    ticker = ticker.upper()
    asset_info = classifier.classify(ticker)
```

**Problema:** No hay:
- Rate limiting (un atacante puede hacer miles de requests por segundo)
- Validación del ticker (solo `.upper()`, acepta cualquier string)
- Autenticación (API abierta a internet)

**Impacto:**
- Agotamiento de cuota de API Gemini por abuso
- Costos inesperados en Google Cloud
- Posible inyección de caracteres especiales en llamadas a yfinance

**Recomendación:** Implementar `Flask-Limiter`, validar ticker con regex (`^[A-Z]{1,10}$`), y agregar API key de acceso.

---

#### S-06 [MEDIA] Health endpoint expone estado interno

**Archivo:** `backend/app/main.py:116-124`

```python
return jsonify({
    'status': 'ok',
    'service': 'SignalIQ',
    'active_key': API_KEYS[current_key_index]['name'] if model else 'MOCK',
    'keys_available': len(API_KEYS),
    'mode': 'REAL' if model else 'MOCK'
})
```

**Problema:** El endpoint `/health` expone:
- El nombre de la API key activa
- El número total de keys configuradas
- El modo de operación (REAL/MOCK)

**Impacto:** Un atacante conoce cuántas credenciales tienes y cuál está activa, facilitando ataques dirigidos.

**Recomendación:** Reportar solo `status` y `service`.

---

#### S-07 [BAJA] Conexiones a BD hardcodeadas en scripts

**Archivos:** `simple_ndi.py:22`, `scripts/run_backtest_real.py:6`

```python
conn = psycopg2.connect("dbname=signaliq host=/var/run/postgresql")
```

**Problema:** Dependencia de socket Unix local. No configurable.

**Impacto:** Los scripts solo funcionan en la máquina con PostgreSQL local. Imposible usar en contenedores o entornos remotos.

**Recomendación:** Usar `os.environ.get("DATABASE_URL")`.

---

### 3.3 Calidad del Código y Arquitectura

---

#### A-01 [ALTA] Dos funciones `calculate_ndi` con diferente semántica

**Archivos:**
- `backend/app/main.py:53` → NDI basado en variación de precio (0.3/0.5/0.7)
- `layers/layer4_measurement.py:27` → NDI = sentiment_zscore - momentum_zscore

```python
# backend/app/main.py
def calculate_ndi(ticker):
    change = (current - prev) / prev
    if change > 0.02: return 0.3
    elif change < -0.02: return 0.7
    return 0.5

# layers/layer4_measurement.py
def calculate_ndi(sentiment_zscore, momentum_zscore):
    return sentiment_zscore - momentum_zscore
```

**Problema:** Ambas funciones se llaman `calculate_ndi` pero:
- Una toma un ticker y devuelve 0.3/0.5/0.7
- La otra toma dos z-scores y devuelve un valor continuo
- Una inversa (precio sube → NDI bajo), la otra directa (sentimiento alto - momentum bajo → NDI alto)

**Impacto:** Confusión total sobre qué NDI se está calculando. Un desarrollador no iniciado usará la función equivocada, generando señales financieras incorrectas y potencialmente pérdidas económicas.

**Recomendación:** Renombrar:
- `calculate_ndi` en `main.py` → `calculate_price_divergence_index`
- `calculate_ndi` en `measurement.py` → `calculate_narrative_divergence_index`

---

#### A-02 [ALTA] Dos clases `Layer4Orchestrator` duplicadas

**Archivos:**
- `layers/layer4_orchestrator.py` — usa `signaliq.core.llm.llm_router`
- `layers/layer4_orchestrator_simple.py` — usa `signaliq.core.llm_simple.simple_llm`

**Problema:** Ambas definen `class Layer4Orchestrator`. Dependiendo de:
1. El orden de importación en `__init__.py`
2. El `sys.path` configurado
3. Qué archivo se importa primero

...se usará una implementación u otra silenciosamente. Además, `layers/__init__.py` importa de `layer4_orchestrator.py` (la versión con `llm_router`), mientras `signal_analyzer.py` también usa `llm_router` directamente.

**Impacto:** Comportamiento inconsistente. Posible uso de la implementación incorrecta sin advertencia.

**Recomendación:** Unificar en una sola clase con inyección de dependencias del proveedor LLM.

---

#### A-03 [ALTA] Config central incompleta — referencias a atributos inexistentes

**Archivo:** `signaliq/core/config.py:16-33`

```python
class SignalIQConfig:
    ...
    def _load(self):
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.llm = LLMConfig(...)
        # FALTA: self.db y self.DATA_DIR
```

**Archivo:** `signaliq/core/persistence.py:14`

```python
self.state_file = config.DATA_DIR / "persistence_state.json"  # AttributeError
```

**Archivo:** `signaliq/core/persistence.py:21`

```python
return psycopg2.connect(config.db.url)  # AttributeError
```

**Problema:** El singleton `config` no tiene atributos `db` ni `DATA_DIR`, pero `SignalPersistence` los usa directamente. `config.db` es `None` (nunca asignado), así que `config.db.url` lanza `AttributeError: 'NoneType' object has no attribute 'url'`.

**Impacto:** El módulo de persistencia (`signaliq/core/persistence.py`) crashea al instanciarse. Cualquier código que importe `persistence.py` falla.

**Recomendación:** Completar la configuración:

```python
class SignalIQConfig:
    def _load(self):
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.db = DatabaseConfig(url=os.getenv("DATABASE_URL"))
        self.llm = LLMConfig(...)
```

---

#### A-04 [ALTA] Side effects en import-time en múltiples módulos

**Archivos:**
- `signaliq/core/llm.py:8` — `load_dotenv()` al importar
- `layers/layer4_orchestrator.py:8-12` — `os.environ[...]` forzado
- `backend/app/main.py:51` — `get_available_key()` al importar
- `synthetic/data_generator.py:36` — `random.seed(42)` al importar

**Problema:** Estos módulos ejecutan código con efectos secundarios en el momento de la importación. Esto hace que:
- El orden de importación importe (nunca mejor dicho)
- Los tests sean impredecibles (el estado global cambia al importar)
- Sea imposible importar el módulo para inspeccionar sus tipos sin ejecutar efectos secundarios

**Impacto:** Tests flaky. Dificultad para debuggear. Comportamiento no determinista.

**Recomendación:** Mover toda inicialización a funciones explícitas `initialize()`, `configure()`, etc. que el llamador invoque deliberadamente.

---

#### A-05 [ALTA] Duplicación masiva en todo el código base

| Elemento duplicado | Ubicaciones |
|--------------------|-------------|
| API keys Gemini | `main.py`, `llm_provider.py`, `layer4_orchestrator.py`, `docker-compose.yml`, `.env` |
| `Layer4Orchestrator` | `layer4_orchestrator.py`, `layer4_orchestrator_simple.py` |
| `calculate_ndi` | `main.py`, `measurement.py` |
| `PRIMARY_LLM` config | `.env` línea 5 y 21 |
| `NEGATIVE_WORDS` / `POSITIVE_WORDS` | `layer3_sentiment.py` y `synthetic/data_generator.py` |
| Dockerfiles | `Dockerfile` (raíz) y `backend/Dockerfile` |
| Entity aliases | `layer3_entity.py` (hardcoded) y `config/entity_aliases.json` |
| Backtest engines | `backtest_engine.py` y `backtest_improved.py` |

---

#### A-06 [MEDIA] Código muerto y archivos legacy

**Problema:** El repositorio contiene:
- `legacy/apis/` con 11 versiones de API obsoletas
- `legacy/llm_simple.py` (importado por `layer4_orchestrator_simple.py`)
- `tests/legacy/` con 10 archivos de test obsoletos
- `lm_lexicon.py`: 558 líneas, pero solo se usan `POSITIVE` y `NEGATIVE` (~40 líneas). `CONSTRAINING`, `SUPERFLUOUS`, `LITIGIOUS`, `UNCERTAINTY` son ~500 líneas de código muerto.
- Múltiples archivos HTML de frontend en raíz (`frontend.html`, `frontend_automatico.html`, `test_frontend.html`)
- `oracle.md`, `architecture.md`, `ARCHITECTURE.md` (duplicados)

**Impacto:** 40%+ del código en el repositorio es muerto o legacy. Aumenta la carga cognitiva, el tiempo de build, y el riesgo de importar accidentalmente código incorrecto.

**Recomendación:** Eliminar `legacy/`, unificar archivos de documentación, y recortar `lm_lexicon.py` a solo las categorías usadas.

---

#### A-07 [MEDIA] Mezcla de idiomas (español/inglés)

**Problema:** El código base mezcla español e inglés inconsistentemente:
- Variables en español: `precios`, `tickers_con_datos` en `simple_ndi.py`
- Comentarios en español en `metrics_calculator.py` y `score_aggregator.py`
- Strings de UI en español en `signal_analyzer.py` (`"CONSIDERAR VENTA"`, `"MONITOREAR"`)
- Strings en inglés en otros lugares
- Docstrings mixtos

**Impacto:** Dificulta el mantenimiento por equipos internacionales. Confusión sobre el idioma estándar.

**Recomendación:** Estandarizar a inglés para todo el código fuente. Español aceptable solo en strings de UI si es requisito del producto.

---

#### A-08 [MEDIA] Magic numbers sin constantes nombradas

**Problema:** El código usa valores literales sin nombre en múltiples lugares:

| Valor | Ubicaciones | Significado |
|-------|-------------|-------------|
| `1.5` | `persistence.py`, `measurement.py`, `backtest_engine.py` | Threshold NDI |
| `0.7` | `main.py`, `llm.py`, `orchestrator.py` | Límite señal fuerte |
| `0.005` | `layer4_classification.py:48` | Threshold flat price |
| `0.3` | `layer4_classification.py:69` | Threshold NDI delta |
| `6` | `measurement.py:19` | Mínimo de precios para return 5d |
| `0.02` | `main.py:62-65` | Threshold cambio precio |
| `10` | `layer3_config.py` | Mínimo días válidos |
| `16` | `layer3_config.py` | Cutoff hour ET |

**Impacto:** Cambiar un threshold requiere encontrar y modificar múltiples ocurrencias. Alto riesgo de inconsistencias.

**Recomendación:** Definir todas las constantes en archivos de configuración (`layer3_config.py`, etc.) con nombres descriptivos.

---

### 3.4 Rendimiento

---

#### P-01 [MEDIA] Falta de índices en tabla `prices`

**Archivo:** `data_storage/001_create_layer2_schema.sql:7-19`

```sql
CREATE TABLE IF NOT EXISTS prices (
    ...
    UNIQUE (ticker, price_date, source)
);
```

**Problema:** La constraint `UNIQUE (ticker, price_date, source)` crea un índice B-tree compuesto (ticker, price_date, source). Sin embargo, muchas consultas comunes filtran solo por ticker + rango de fechas, y el índice actual tiene `source` como tercera columna, lo que lo hace menos eficiente para queries sin filtro de source.

La tabla `headlines` tiene índice `(ticker, headline_date)` pero la tabla `prices` carece de un índice diseñado explícitamente para búsqueda por rango de fechas.

**Impacto:** Con miles de registros de precios, las consultas como `SELECT * FROM prices WHERE ticker='NVDA' AND price_date BETWEEN '2026-01-01' AND '2026-06-01'` harán sequential scan.

**Recomendación:** Agregar índice explícito:

```sql
CREATE INDEX idx_prices_ticker_date ON prices (ticker, price_date DESC);
```

---

#### P-02 [BAJA] LLM blocking en Flask worker

**Archivo:** `backend/app/main.py:146`

```python
response = model.generate_content(prompt)
```

**Problema:** `generate_content` es una llamada sincrónica que bloquea el worker de Flask. En producción, con `gunicorn` y 4 workers, solo 4 usuarios pueden ser atendidos simultáneamente. Cada request típicamente toma 2-10 segundos dependiendo de Gemini.

**Impacto:** Escalabilidad limitada. Tiempo de respuesta alto bajo concurrentcia.

**Recomendación:** Usar Celery + Redis Queue para tareas asincrónicas, o usar las APIs async de Google AI.

---

### 3.5 Base de Datos

---

#### D-01 [CRÍTICA] Schema de base de datos incompleto

**Archivos involucrados:**
- `data_storage/001_create_layer2_schema.sql` — crea solo `public.prices`, `public.headlines`, `public.ndi_signals`
- `layer1/writer.py:49-55` — llama a `raw.insert_price_record(...)`
- `layer1/writer.py:99-100` — consulta `config.news_sources`
- `simple_ndi.py:45` — consulta `raw.prices`
- `scripts/run_backtest_real.py:13` — consulta `layer4.signals`

**Problema:** El SQL maestro crea tablas en schema `public`, pero el código referencia:

| Referencia en código | Schema requerido | ¿Existe en SQL? |
|----------------------|------------------|-----------------|
| `raw.insert_price_record(...)` | `raw` | ❌ No |
| `raw.insert_headline_record(...)` | `raw` | ❌ No |
| `raw.prices` | `raw` | ❌ No (solo `public.prices`) |
| `raw.news_headlines` | `raw` | ❌ No (solo `public.headlines`) |
| `config.news_sources` | `config` | ❌ No |
| `layer4.signals` | `layer4` | ❌ No (solo `public.ndi_signals`) |

**Impacto:** La aplicación crashea al intentar la primera inserción porque las funciones/stored procedures `raw.insert_price_record()` no existen. El sistema es **inoperable** en cualquier entorno con esta base de datos.

**Recomendación:** Reconciliar el schema SQL con el código:
1. Crear schemas `raw`, `config`, `layer4` en el SQL maestro.
2. Implementar las funciones `insert_price_record` e `insert_headline_record` como stored procedures o cambiar el código para usar INSERT directo.
3. Crear la tabla `config.news_sources`.

---

#### D-02 [MEDIA] Rollback script destructivo sin verificación

**Archivo:** `data_storage/rollback.sql`

```sql
DROP TABLE IF EXISTS ndi_signals CASCADE;
DROP TABLE IF EXISTS headlines CASCADE;
DROP TABLE IF EXISTS prices CASCADE;
```

**Problema:** El script de rollback solo maneja tablas en `public`, no considera los schemas `raw`, `config`, `layer4`. Además, `CASCADE` puede eliminar objetos dependientes involuntariamente.

**Impacto:** Si se ejecuta en producción, elimina datos pero deja schemas huérfanos. Dependencias externas (vistas, funciones) se pierden por CASCADE.

**Recomendación:** Hacer rollback específico por schema y evitar CASCADE a menos que sea explícitamente necesario.

---

### 3.6 Testing

---

#### T-01 [ALTA] Framework de tests casero incompatible con CI/CD

**Archivos:** `tests/test_layer4.py`, `tests/test_layer3.py`, `tests/test_layer1_integration.py`

```python
_FAILURES = 0
def _check(label, actual, expected):
    global _FAILURES
    if actual != expected:
        print(f"  FAIL: {label}")
        _FAILURES += 1
    else:
        print(f"  PASS: {label}")
```

**Problema:** Los tests usan un framework casero con variables globales y `print()`. No son detectables por `pytest` (no siguen convención `test_` con assertions estándar), no producen reports JUnit/XML, no tienen fixtures, no soportan parametrización.

**Impacto:** No se pueden integrar con CI/CD estándar. No hay métricas de cobertura. `pytest tests/` reporta 0 tests descubiertos.

**Recomendación:** Migrar a `pytest` con assertions nativas (`assert`) y fixture de limpieza.

---

#### T-02 [ALTA] Test de mock de API verifica con estructura incorrecta

**Archivo:** `tests/test_layer1_integration.py:296-326`

```python
def test_write_price():
    ...
    call_kwargs = mock_cursor.execute.call_args[0][1]
    _check("ticker in call", call_kwargs["ticker"], "NVDA")  # TypeError
```

**Problema:** El test asume que el segundo argumento de `cursor.execute()` es un `dict` accesible por clave (`call_kwargs["ticker"]`). Pero la función real usa:

```python
cur.execute(
    """SELECT raw.insert_price_record(%s, %s, ...)""",
    (ticker, vendor, date, ...)  # <-- ESTO ES UNA TUPLA, NO UN DICT
)
```

**Impacto:** `TypeError: tuple indices must be integers or slices, not str`. El test está roto y no detecta cambios en el código.

**Recomendación:** Cambiar el test para acceder por índice de tupla: `call_args[0][1][0]` para ticker, etc.

---

#### T-03 [ALTA] Test de mock parchea función equivocada

**Archivo:** `tests/test_layer1_integration.py:90-117`

```python
with patch("layer1.collect_prices.fetch_with_retry") as mock_fetch:
    ...
    result = fetch_asset_price("NVDA", "NVDA")
```

**Problema:** `fetch_asset_price` en `collect_prices.py` usa `yf.Ticker(symbol).history(period="2d")` para obtener datos. NO usa `fetch_with_retry`. El parche sobre `fetch_with_retry` no intercepta ninguna llamada real.

**Impacto:** El test hace llamadas reales a Yahoo Finance. Dependencia de red. Falla si no hay conectividad.

**Recomendación:** Parchear `yfinance.Ticker.history` directamente.

---

#### T-04 [MEDIA] `test_fundamental_engine.py` no es un test

**Archivo:** `tests/test_fundamental_engine.py`

**Problema:** Este archivo es un script de demostración que imprime resultados con `print()`. No contiene ninguna assertion. No reporta éxito/fallo. No es detectable como test.

**Impacto:** Falsa sensación de cobertura. Parece que hay tests de fundamentales pero no verifican nada.

**Recomendación:** Convertir a tests reales con valores esperados documentados.

---

#### T-05 [MEDIA] Sin tests para el backend API

**Problema:** El archivo `backend/app/main.py` (189 líneas, endpoint Flask con lógica crítica de clasificación de activos, rotación de API keys, y llamadas a Gemini) no tiene ningún test.

**Impacto:** Cualquier cambio en el API puede romper la funcionalidad sin ser detectado.

**Recomendación:** Agregar tests de integración con Flask test client.

---

#### T-06 [BAJA] Sin cobertura para `signal_analyzer.py`

**Problema:** `layers/signal_analyzer.py` (39 líneas) orquesta el LLM Router con Layer 4 pero no tiene tests.

**Impacto:** Bajo (es código delgado de integración), pero es un punto de unión crítico entre capas.

---

### 3.7 Producción y Operaciones

---

#### O-01 [ALTA] Single replica en Railway

**Archivo:** `railway.json:7`

```json
{
    "deploy": {
        "numReplicas": 1,
        "restartPolicyType": "ON_FAILURE"
    }
}
```

**Problema:** Una sola réplica significa punto único de falla. Si el contenedor crashea (por ejemplo, por la recursión infinita descrita en B-03), hay downtime durante el reinicio. `ON_FAILURE` solo reintenta en caso de fallo, no proporciona alta disponibilidad.

**Impacto:** Ventanas de indisponibilidad. Sin redundancia.

**Recomendación:** Mínimo 2 réplicas. Considerar `always` como restart policy.

---

#### O-02 [MEDIA] Sin logging estructurado en backend API

**Archivo:** `backend/app/main.py`

```python
print(f"✅ Conectado con {API_KEYS[key_index]['name']}")
print(f"❌ Error: {str(e)[:80]}")
print(f"📊 Analizando {ticker}... (Tipo: {asset_type})")
```

**Problema:** La API usa `print()` en vez de `logging` estructurado. No hay:
- Niveles de log (INFO, WARNING, ERROR)
- Formato estructurado (JSON)
- Timestamps ISO 8601
- Correlation IDs para tracing de requests
- Output a archivo o servicio de logs

**Impacto:** Imposible debuggear en producción. No hay trazabilidad de requests. No se pueden configurar alertas sobre errores.

**Recomendación:** Reemplazar `print()` con `logging.getLogger(__name__)` y configurar un handler JSON.

---

#### O-03 [MEDIA] Sin graceful degradation cuando todas las LLM keys fallan

**Archivo:** `backend/app/main.py:130-131`

```python
if not model:
    return jsonify({'error': 'No API keys available'}), 429
```

**Problema:** Cuando todas las API keys están agotadas, el endpoint devuelve error 429 sin posibilidad de:
- Usar un proveedor alternativo (Groq, mock)
- Poner en cola la request
- Degradar gracefulmente a datos cacheados

**Impacto:** Los usuarios reciben error directo. Sin failover.

**Recomendación:** Implementar el LLMRouter con fallback a mock cuando todos los providers fallen, y registrar la degradación.

---

#### O-04 [MEDIA] `persistence_state.json` sin protección de concurrencia

**Archivo:** `layers/layer4_persistence.py:29-32`

```python
def save(self):
    with self._state_file.open("w") as f:
        json.dump(self._data, f, indent=2)
```

**Problema:** El archivo JSON se escribe sin file locking. Si dos procesos (e.g., dos cron jobs) escriben simultáneamente, el archivo se corrompe.

**Impacto:** Streaks de tickers perdidos. Señales incorrectas.

**Recomendación:** Agregar `fcntl.flock(f, fcntl.LOCK_EX)` o migrar este estado a PostgreSQL (la tabla `ndi_signals` ya existe).

---

#### O-05 [BAJA] Dockerfile duplicado con estructura diferente

**Archivos:**
- `Dockerfile` (raíz): copia `backend/` a `/app`, usa `CMD python -m app.main`
- `backend/Dockerfile`: copia `app/` a `/app/app/`, usa `CMD python -m app.main`

**Problema:** Ambos Dockerfiles hacen lo mismo pero con estructuras de directorio diferentes. El de raíz copia toda la carpeta `backend/` al `WORKDIR /app`, resultando en `/app/requirements.txt`, `/app/app/`, etc. El otro copia solo `app/` dentro de `/app/`, resultando en `/app/app/main.py`. Esto causa confusión sobre cuál usar y Railway apunta al de `backend/`.

**Impacto:** Posible error de importación si se usa el Dockerfile incorrecto.

**Recomendación:** Unificar en un solo Dockerfile y eliminar el otro.

---

## 4. Evaluaciones Cuantitativas

### 4.1 Preparación para Producción: 28/100

| Factor | Penalización | Justificación |
|--------|-------------|---------------|
| Secretos en código | -30 | 5 API keys hardcodeadas + .env commiteado. Blocker absoluto |
| Tests rotos | -15 | Tests principales fallan con ImportError |
| Sin rate limiting | -10 | Endpoint público sin protección |
| Schema BD incompleto | -8 | Funciones SQL que no existen |
| Sin logging | -5 | `print()` en vez de logging |
| Single replica | -4 | Sin alta disponibilidad |
| Sin graceful degradation | -3 | Error 429 sin failover |
| Sin auth | -3 | API pública sin autenticación |
| **Total** | **28/100** | |

### 4.2 Calidad Arquitectónica: 42/100

| Factor | Penalización | Justificación |
|--------|-------------|---------------|
| Duplicación masiva | -15 | Múltiples implementaciones del mismo concepto |
| Side effects en import-time | -12 | Código ejecutado al importar módulos |
| Acoplamiento excesivo | -10 | `layer4` depende de path absolutos y configuración global |
| Puntos únicos de falla | -8 | Single replica, sin circuit breaker |
| Violación SRP | -8 | `main.py` mezcla routing, lógica, clientes HTTP, config |
| Sin inyección de dependencias | -5 | Todo usa singletons y estado global |
| **Total** | **42/100** | |

### 4.3 Mantenibilidad: 35/100

| Factor | Penalización | Justificación |
|--------|-------------|---------------|
| Código muerto | -15 | ~40% del repo es legacy o no usado |
| Mezcla de idiomas | -12 | Español/inglés mezclados |
| Magic numbers | -10 | Thresholds literales sin constantes |
| Tests no estándar | -8 | Framework casero incompatible con CI/CD |
| Archivos legacy | -5 | `legacy/apis/` con 11 versiones obsoletas |
| **Total** | **35/100** | |

### 4.4 Riesgo General del Proyecto: **ALTO**

| Factor | Nivel | Detalle |
|--------|-------|---------|
| Exposición de credenciales | 🔴 Crítico | 5+ ubicaciones con API keys reales |
| Tests no funcionales | 🔴 Crítico | Capa 4 y 1 sin cobertura real |
| Schema BD incompleto | 🔴 Crítico | Código inejecutable por falta de funciones SQL |
| Side effects | 🟠 Alto | Comportamiento impredecible en imports |
| Sin seguridad perimetral | 🟠 Alto | Sin auth, sin rate limiting, sin validación |
| Deuda técnica | 🟠 Alto | Duplicación masiva, código muerto, magic numbers |
| Observabilidad | 🟡 Medio | Sin logging estructurado, sin métricas |
| **Riesgo General** | **🔴 ALTO** | **No apto para producción sin correcciones críticas** |

---

## 5. Recomendaciones Priorizadas

### Inmediatas (Semana 1)

| # | Acción | Esfuerzo | Impacto |
|---|--------|----------|---------|
| 1 | **Rotar todas las API keys de Google Gemini** | 30 min | Elimina riesgo de abuso económico |
| 2 | **Eliminar secrets del historial git** con `git filter-repo` | 1 hora | Detiene exposición permanente |
| 3 | **Eliminar keys hardcodeadas** de `main.py`, `llm_provider.py`, `docker-compose.yml`, `layer4_orchestrator.py` | 30 min | Remueve源头 de exposición |
| 4 | **Corregir imports rotos en tests** (L4 y L1) | 2 horas | Restaura capacidad de testear |

### Corto plazo (Semana 2-3)

| # | Acción | Esfuerzo | Impacto |
|---|--------|----------|---------|
| 5 | **Completar schema SQL**: crear schemas `raw`, `config`, funciones stored procedures | 4 horas | Hace el sistema ejecutable |
| 6 | **Eliminar `sys.exit(1)`** de funciones de biblioteca | 1 hora | Permite recovery graceful |
| 7 | **Unificar `calculate_ndi` y `Layer4Orchestrator`** | 3 horas | Elimina ambigüedad crítica |
| 8 | **Completar `SignalIQConfig`** con atributos faltantes | 1 hora | Corrige AttributeError en persistence |

### Mediano plazo (Semana 4-6)

| # | Acción | Esfuerzo | Impacto |
|---|--------|----------|---------|
| 9 | **Migrar tests a pytest** | 8 horas | Habilita CI/CD y cobertura |
| 10 | **Eliminar side effects en import-time** | 4 horas | Hace el código predecible |
| 11 | **Implementar rate limiting + validación + auth** | 6 horas | Seguridad perimetral |
| 12 | **Reemplazar `print()` con logging estructurado** | 3 horas | Observabilidad en producción |
| 13 | **Configurar 2+ réplicas en Railway** | 30 min | Alta disponibilidad |
| 14 | **Eliminar código muerto** (legacy/, lm_lexicon redundante, archivos duplicados) | 4 horas | Reduce deuda técnica ~40% |

---

*Fin del reporte de auditoría. Documento generado el 2026-06-06.*
