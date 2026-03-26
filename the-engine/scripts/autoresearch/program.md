# SEO AutoResearch Program

> Adaptado de Karpathy's autoresearch para análisis SEO autónomo.
> Loop: fetch → analyze → generate insight → self-evaluate → iterate

## Objetivo

Analizar datos SEO de un proyecto en The Engine y generar hallazgos accionables.
Cada iteración debe mejorar sobre la anterior — más datos, mejor análisis, más específico.

## Datos disponibles (via Engine API)

| Fuente | Endpoint | Datos |
|--------|----------|-------|
| GSC | `/content-performance/projects/{pid}/intent-shift` | Distribución intent + YoY |
| GSC | `/content-performance/projects/{pid}/intent-yoy` | Intent por landing page |
| GSC | `/content-performance/projects/{pid}/performance-by-page-type` | Clicks por tipo página |
| GSC | `/rank-tracker/keywords` | Posiciones actuales + cambios |
| Sistrix | `/sistrix/visibility` | Índice de visibilidad |
| Sistrix | `/sistrix/sync-keywords` | Top keywords del dominio |
| GA4 | `/content-performance/lead-attribution` | Leads por landing page |
| Engine | `/content-performance/freshness-health` | Frescura del contenido |
| Engine | `/content-performance/engagement-overview` | Calidad de engagement |
| Engine | `/influence/score` | Score de influencia (SEO + AI) |

## Proceso por iteración

### Iteración 1: Vista panorámica
1. Fetch intent-shift, performance-by-page-type, visibility
2. Responder: "¿Qué tipo de tráfico domina? ¿Las money pages reciben clicks?"
3. Hallazgo: distribución actual con números concretos

### Iteración 2: Profundizar en money pages
1. Fetch intent-yoy con foco en URLs de money pages
2. Responder: "¿Cuántos clicks orgánicos reciben las landings de producto?"
3. Hallazgo: clicks por money page vs competidores

### Iteración 3: Análisis de competidores
1. Fetch Sistrix keywords (si hay créditos), rank-tracker/keywords
2. Responder: "¿En qué keywords comerciales somos invisibles? ¿Quién rankea?"
3. Hallazgo: tabla de gaps vs competidores

### Iteración 4: Oportunidades y quick wins
1. Cruzar: engagement × intent × page_type
2. Responder: "¿Qué páginas tienen tráfico pero no convierten? ¿Dónde mejorar?"
3. Hallazgo: lista priorizada de acciones

### Iteración 5: Síntesis ejecutiva
1. Compilar hallazgos anteriores
2. Generar informe ejecutivo con:
   - Resumen de 1 párrafo
   - 3-5 hallazgos clave con datos
   - Tabla de acciones priorizadas
   - Proyección de impacto

## Criterios de calidad (auto-evaluación)

Cada hallazgo se puntúa 1-10:
- **Accionable** (3 pts): ¿dice qué hacer? No solo "el tráfico bajó" sino "crear contenido para X keyword"
- **Con datos** (3 pts): ¿tiene números concretos? Clicks, posiciones, %, €
- **Específico** (2 pts): ¿nombra URLs, keywords, competidores específicos?
- **Novedoso** (2 pts): ¿aporta algo que no era obvio antes?

Score < 7 → iterar con más datos o diferente ángulo
Score >= 7 → guardar como hallazgo final

## Output

- `findings.json`: lista de hallazgos con score, datos, recomendación
- `report.md`: informe ejecutivo generado
- `iteration_log.json`: registro de cada iteración con métricas

## Budget

- Max 10 iteraciones por ejecución
- Max 20 API calls a Engine por iteración
- Max 5 calls a Sistrix por ejecución (créditos limitados)
- Max $2 en tokens Claude por ejecución
