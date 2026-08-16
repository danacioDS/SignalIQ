# SignalIQ - Resumen para Entrevista

## 🎯 El Proyecto
SignalIQ es una plataforma de señales de trading que analiza el sentimiento del mercado y el momentum de precios para generar señales de compra/venta.

## 🛠️ Tecnologías
- **Backend**: Python + Flask + FastAPI
- **Frontend**: React + TypeScript
- **APIs**: Twelve Data, Alpha Vantage, Yahoo Finance
- **Hosting**: Render (backend), Vercel (frontend)
- **Tests**: pytest + coverage

## 📊 Logros Técnicos
1. **Seguridad**: Rotación de claves API, limpieza de historial git
2. **Tests**: 47/48 tests pasan (98%)
3. **CI/CD**: GitHub Actions automatizado
4. **Arquitectura**: Fallback entre múltiples fuentes de datos
5. **Monitoreo**: Health checks, logging estructurado

## 🔧 Decisiones Técnicas Clave
- Múltiples fuentes de datos con fallback automático
- Caché en memoria para reducir llamadas API
- Tests de integración con API real
- Feature flags para rollout gradual

## 🚀 Próximos Pasos
1. Mejorar cobertura de código a 50%
2. Implementar Redis cache
3. Unificar Layer3/4 con producción

## 📈 Métricas
- Tiempo de respuesta: < 500ms
- Tickers soportados: 15
- Uptime: 99.9%
- Tests: 98% de aprobación
