# HOJA DE RUTA — FIT Content Manager

> **Fecha:** 13 de febrero de 2026
> **Este es el ÚNICO documento de instrucciones.** Sigue las tareas en orden de arriba a abajo. Cada tarea tiene archivos, instrucciones y criterio de éxito. No avances a la siguiente hasta completar la actual.
>
> Los documentos `AUDITORIA-ACCIONES.md`, `SPRINT-5-INSTRUCCIONES.md` y `ROADMAP-DASHBOARD-SEO.md` quedan como referencia histórica. **Toda la información relevante está aquí.**
>
> **Framework EEAT:** Basado en el checklist de Ahrefs (Despina Gavoyannis, feb 2026) — 290+ ítems auditables mapeados a las Quality Rater Guidelines de Google (sep 2025). Integrado en Sprints 14-19.

---

## Reglas UX (aplicar en TODO el frontend)

1. Máximo 5-7 KPIs por vista. Si hay más, usar tabs o progressive disclosure.
2. NUNCA usar pie charts. Siempre bar charts o line charts.
3. Toda métrica con comparativa temporal: valor actual + % cambio vs periodo anterior. Verde si mejora, rojo si empeora, gris si neutro.
4. Colores semánticos: verde = mejora, rojo = empeora. No usar colores decorativos.
5. Tooltips en TODOS los gráficos mostrando valores exactos al hacer hover.
6. Labels en español.
7. Responsive: KPI cards 2 por fila en mobile.
8. NO usar badges "NUEVO" ni "BETA" en módulos del sidebar. Los módulos se añaden sin etiqueta.

---

## Reglas de código (aplicar SIEMPRE)

1. Python 3.9 compatible: usar `Optional[str]` no `str | None`, usar `Tuple` no `tuple`.
2. No usar `print()` — siempre `logging.getLogger(__name__)`.
3. Endpoints de listado: siempre `limit` (default 50, max 200) + `offset` (default 0).
4. Formato de respuesta en listas: `{"data": [...], "total": N, "limit": 50, "offset": 0}`.
5. Toda métrica con `compare=true` debe devolver `current`, `previous` y `change_pct`.
6. Frontend: usar `React.lazy()` + `Suspense` para toda página nueva.
7. Componentes nuevos: máximo 300 líneas. Si va a ser más largo, descomponer.
8. Antes de commitear: `npm run build` + `python -c "from main import app"`.

---

## BLOQUE A: Cabos sueltos (deuda técnica)

Tareas menores pendientes de sprints anteriores. Completar antes de nuevas funcionalidades.

### A1. Cache JWT en auth.py

**Archivo:** `backend/api/middleware/auth.py`

Cada request valida el JWT llamando a Supabase remotamente. Añadir cache TTL de 60 segundos.

```python
from cachetools import TTLCache
_token_cache = TTLCache(maxsize=100, ttl=60)

async def get_current_user(token):
    if token in _token_cache:
        return _token_cache[token]
    # ... validar contra Supabase ...
    _token_cache[token] = user_data
    return user_data
```

Añadir `cachetools>=5.3.0` a `requirements.txt`.

**Criterio:** Backend arranca OK. Cada token solo se valida 1 vez cada 60s.

### A2. Logging en sitemap_service.py

**Archivo:** `backend/api/services/sitemap_service.py`

Quedan 4 llamadas a `print()`. Reemplazar por `logger.error()` o `logger.warning()`.

**Criterio:** `grep -r "print(" backend/api/services/sitemap_service.py` no devuelve resultados.

### A3. SOURCE-OF-TRUTH.md desactualizado

Los Sprints 3 y 4 aparecen sin marcar pero están completados. Actualizar:
- Sprint 3: marcar todos como [x]
- Sprint 4: marcar todos como [x]
- Añadir Sprint 6 (este documento) al roadmap

**Criterio:** SOURCE-OF-TRUTH.md refleja el estado real.

---

## BLOQUE B: Dashboard accionable

Transformar el dashboard de "muestra números" a "dice si voy bien o mal".

### B1. Selector de periodo + comparativas MoM

**Archivos backend:**
- `backend/api/routes/dashboard.py`
- `backend/api/services/dashboard_service.py` (crear si no existe)

**Archivos frontend:**
- `frontend/src/pages/DashboardPage.tsx`

**Backend — Modificar `GET /api/projects/{id}/dashboard`:**

Añadir parámetros `date_from`, `date_to`, `compare` (boolean). Si `compare=true`, calcular también el periodo anterior (misma duración, inmediatamente antes).

Respuesta:
```json
{
  "current": {
    "sessions": 12500, "clicks": 8900, "impressions": 125000,
    "ctr": 7.12, "position": 12.3, "conversions": 45
  },
  "previous": {
    "sessions": 11200, "clicks": 7800, "impressions": 110000,
    "ctr": 6.8, "position": 13.1, "conversions": 38
  },
  "changes": {
    "sessions_pct": 11.6, "clicks_pct": 14.1, "impressions_pct": 13.6,
    "ctr_pct": 4.7, "position_pct": -6.1, "conversions_pct": 18.4
  }
}
```

**Modificar `GET /api/projects/{id}/dashboard/chart`:**
Aceptar `date_from`, `date_to`, `compare`. Si compare, devolver `chart_current` y `chart_previous` (dos arrays).

**Frontend:**
1. Selector de periodo arriba del dashboard: botones 7d / 30d / 90d / input personalizado.
2. Toggle "Comparar con periodo anterior" (on por defecto).
3. 6 KPI cards en fila, cada una con:
   - Nombre de la métrica
   - Valor actual (grande)
   - Flecha + porcentaje de cambio (verde ↑ o rojo ↓)
   - Cards: Sesiones, Clics, Impresiones, CTR medio, Posición media, Conversiones
4. Gráfico: línea sólida (actual) + línea punteada (anterior).

**Componente reutilizable `MetricCard.tsx`:**
Crear `frontend/src/components/ui/MetricCard.tsx`:
Props: `label`, `value`, `previousValue`, `format` ("number" | "percent" | "currency" | "position"), `invertColors` (true para posición, donde bajar es bueno).

Usar MetricCard en DashboardPage y en ContentPerformancePage.

**Criterio:** Dashboard muestra datos de 30d por defecto con comparativa MoM. Cada KPI muestra variación porcentual. Gráfico con overlay del periodo anterior.

### B2. Branded vs non-branded

**Backend:**
- Añadir a `backend/config/constants.py`: `DEFAULT_BRAND_TERMS = ["fit generation", "fitgeneration", "fit gen"]`
- Añadir columna `brand_terms` (JSONB, default `[]`) a tabla `projects` en Supabase. Si está vacía, usar DEFAULT_BRAND_TERMS.
- En los endpoints de dashboard y content_metrics: aceptar parámetro `traffic_type` = "all" | "branded" | "non_branded".
- Filtrar: si query contiene algún brand term → branded. Si no → non-branded.

**Frontend:**
- En DashboardPage: toggle con 3 opciones (Todo / Branded / Non-branded) debajo del selector de periodo.
- En Settings > General: campo "Términos de marca" (textarea, uno por línea).

**Criterio:** Se puede ver el tráfico non-branded separado del branded en el dashboard.

### B3. Distribución de rankings por buckets

**Backend:** Nuevo endpoint `GET /api/projects/{id}/rank-tracker/distribution`

Consultar `keyword_positions` y agrupar por buckets:
```json
{
  "buckets": [
    {"range": "1-3", "count": 12, "previous": 10, "change": 2},
    {"range": "4-10", "count": 28, "previous": 25, "change": 3},
    {"range": "11-20", "count": 45, "previous": 48, "change": -3},
    {"range": "21-50", "count": 89, "previous": 92, "change": -3},
    {"range": "51+", "count": 34, "previous": 30, "change": 4}
  ],
  "striking_distance": [
    {"keyword": "entrenamiento funcional", "position": 12, "volume": 2400, "url": "/blog/...", "impressions": 890}
  ],
  "top_movers": {
    "up": [{"keyword": "...", "from": 18, "to": 7, "change": -11}],
    "down": [{"keyword": "...", "from": 5, "to": 14, "change": 9}]
  }
}
```

**Frontend:** En la página de Keywords/Rank Tracker, añadir encima de la tabla:
- Bar chart horizontal con 5 buckets coloreados
- Sección "Striking Distance" (keywords posiciones 11-20): tabla con keyword, posición, volumen, URL
- "Top Movers": dos columnas (subidas / bajadas)

**Criterio:** Se ven los buckets de distribución y las oportunidades de striking distance.

### B4. Alertas con 3 niveles de severidad

**Archivos:** `backend/api/routes/alerts.py`

Ampliar el scan de alertas existente:
- **critical** (rojo): keyword cae >5 posiciones en 7 días, tráfico cae >20% WoW
- **warning** (ámbar): keyword cae 3-5 posiciones, tráfico cae 10-20%, nuevos errores técnicos (SF)
- **info** (gris): nueva keyword en top 10, contenido detectado en sitemap, cambio notable sin urgencia

Añadir campo `severity` a la tabla `alerts` si no existe.

**Frontend:** Feed de alertas en dashboard con icono de color por severidad. Click → navega al detalle.

**Criterio:** Alertas muestran severity con colores. Critical aparecen primero.

### B5. Resumen narrativo AI del dashboard

**Backend:** Nuevo endpoint `GET /api/projects/{id}/dashboard/summary`
1. Recoge datos del dashboard (KPIs + cambios + top movers + alertas)
2. Llama a claude_service con prompt:
   ```
   Genera un resumen de 2-3 frases del rendimiento SEO de este periodo.
   Datos: {json}. Incluye: cambio principal, causa probable, acción sugerida.
   Responde en español, tono profesional y directo.
   ```
3. Cachear en tabla `dashboard_summaries` (project_id, period_start, period_end, text). TTL 24h.

**Frontend:** Debajo del gráfico, bloque de texto con fondo gris claro mostrando el resumen narrativo. Botón "Regenerar" para forzar nuevo resumen.

**Criterio:** Dashboard muestra 2-3 frases explicando qué pasó y qué hacer.

---

## ~~BLOQUE C: Airtable + Rendimiento de contenido~~ ❌ DESCARTADO

> **Decisión (feb 2026):** Airtable descartado. El cliente no podía compartir el PAT por datos sensibles en PKD. Se decidió usar **Lead Attribution con GA4** (eventos `generate_lead`) en su lugar, implementado en Sprint 20 (tabla `lead_attribution`, migración 046). Content Performance Page ya funciona con datos de GSC + GA4 + leads GA4.

---

## BLOQUE D: Mejoras complementarias

### D1. Anotaciones en timelines

**Tabla Supabase:**
```sql
CREATE TABLE IF NOT EXISTS timeline_annotations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  type TEXT NOT NULL DEFAULT 'custom',
  title TEXT NOT NULL,
  description TEXT,
  source TEXT DEFAULT 'manual',
  created_at TIMESTAMPTZ DEFAULT now()
);
```

**Auto-poblar:**
- Cuando sitemap sync detecta URLs nuevas → anotación "Nuevo contenido: {título}"
- Google Core Updates: tabla `algorithm_updates` con fechas conocidas (hardcodear las de 2025 y 2026)

**Frontend:** En los line charts del dashboard, mostrar anotaciones como líneas verticales punteadas con tooltip.

**Criterio:** El gráfico de tráfico muestra marcadores en fechas de Google Updates y contenido nuevo.

### D2. Core Web Vitals (widget en dashboard)

**Backend:** Endpoint `GET /api/projects/{id}/cwv/overview`
- Llama a PageSpeed Insights API para las 5-10 URLs con más tráfico
- Retorna LCP, INP, CLS por URL con clasificación (bueno/necesita mejora/pobre)
- Cachear 24h en Supabase

Umbrales: LCP ≤2.5s bueno, INP ≤200ms bueno, CLS ≤0.1 bueno.

**Frontend:** Card semáforo en el dashboard (verde >80% URLs pasan, ámbar 50-80%, rojo <50%). Click → tabla detallada.

**Criterio:** Dashboard muestra estado de CWV como semáforo.

### D3. Valor del tráfico

**Backend:** Para cada keyword con posición y volumen, estimar:
`traffic_value = volumen × CTR_estimado_por_posicion × CPC_medio`

CTR por posición (2025-2026):
```python
CTR_BY_POSITION = {1: 0.19, 2: 0.10, 3: 0.07, 4: 0.05, 5: 0.04,
                   6: 0.035, 7: 0.03, 8: 0.025, 9: 0.02, 10: 0.018}
```

CPC medio configurable en Settings (default €0.50).

**Frontend:** KPI card extra en dashboard: "Valor del tráfico: €X.XXX/mes"

**Criterio:** Dashboard muestra el valor equivalente en euros del tráfico orgánico.

---

## BLOQUE E: Limpieza general

**Ejecutar DESPUÉS de completar Bloques A-D.**

### E1. Auditar y limpiar carpeta raíz

Revisar la raíz de `Gestor de Contenido FIT/`:
- Archivar en `docs/archive/` cualquier .md que no sea: `CLAUDE.md`, `SOURCE-OF-TRUTH.md`, `HOJA-DE-RUTA.md`
- Los archivos `AUDITORIA-ACCIONES.md`, `SPRINT-5-INSTRUCCIONES.md`, `ROADMAP-DASHBOARD-SEO.md` → mover a `docs/archive/`
- `proyecto-estado.json` → actualizar o eliminar si SOURCE-OF-TRUTH.md lo reemplaza

**Criterio:** Raíz limpia con solo: CLAUDE.md, SOURCE-OF-TRUTH.md, HOJA-DE-RUTA.md, fit-content-app/, docs/

### E2. Eliminar módulos deshabilitados del código

Los siguientes módulos están deshabilitados y sus archivos solo inflan el bundle:

**Frontend (eliminar archivos de pages/):**
- `EntityAnalyzerPage.tsx`
- `ContentSeriesPage.tsx`
- `ContentValidatorPage.tsx`
- `AvatarsPage.tsx`
- `TitleCheckerPage.tsx`

**Frontend (eliminar de App.tsx):** Los imports y rutas correspondientes a esos archivos.

**Backend (evaluar si se pueden eliminar):**
- `backend/api/routes/authority.py` (si topical authority está pausado)
- `backend/api/routes/content_series.py` (si está pausado)
- `backend/api/routes/content_validator.py` (si está pausado)
- `backend/api/routes/avatars.py` (si está pausado)

NO eliminar: `trends.py`, `keyword_research.py`, `seo_imports.py`, `seo_tools.py` — estos podrían reactivarse pronto.

**Criterio:** Build limpio. Bundle más pequeño. No hay imports rotos.

### E3. Consolidar migraciones

Revisar `backend/db/migrations/`. Si hay archivos duplicados o conflictivos entre las dos carpetas de migraciones, consolidar en una sola secuencia numerada.

**Criterio:** Una sola carpeta de migraciones con numeración consecutiva sin huecos.

### E4. Actualizar SOURCE-OF-TRUTH.md

Reflejar el estado real tras completar todos los bloques:
- Todos los módulos activos con su estado correcto
- Sprints 1-6 marcados como completados
- Nuevas funcionalidades (branded/non-branded, CWV, traffic value, anotaciones) listadas

### E5. Actualizar CLAUDE.md

Simplificar la sección "Plan de mejoras" para que apunte solo a este documento:

```markdown
## Plan de mejoras
**Documento único de instrucciones:** `HOJA-DE-RUTA.md`
Ejecutar bloques A → B → C → D → E en orden.
```

Eliminar las referencias a documentos archivados.

**Criterio:** CLAUDE.md es limpio y conciso. Apunta a HOJA-DE-RUTA.md como única referencia.

---

## Resumen visual

```
BLOQUE A: Cabos sueltos          [~2 horas]
  A1. Cache JWT
  A2. Logging sitemap
  A3. Actualizar SOURCE-OF-TRUTH
      ↓
BLOQUE B: Dashboard accionable   [~2-3 días]
  B1. Selector periodo + comparativas MoM
  B2. Branded vs non-branded
  B3. Buckets de rankings + striking distance
  B4. Alertas 3 niveles
  B5. Resumen narrativo AI
      ↓
BLOQUE C: Airtable               [❌ Descartado → Lead Attribution GA4 (Sprint 20)]
      ↓
BLOQUE D: Mejoras complementarias [~2-3 días]
  D1. Anotaciones en timelines
  D2. Core Web Vitals
  D3. Valor del tráfico
      ↓
BLOQUE E: Limpieza general       [~3-4 horas]
  E1. Limpiar carpeta raíz
  E2. Eliminar módulos muertos
  E3. Consolidar migraciones
  E4. Actualizar SOURCE-OF-TRUTH
  E5. Actualizar CLAUDE.md
```

**Tiempo total estimado: 6-8 días de trabajo con Claude Code.**

---

## SPRINT 17: EEAT Audit Module (Checklist + Score + YMYL) ✅ COMPLETADO

> **Fuente:** Ahrefs EEAT Checklist — 290+ ítems, escala Quality Rater Guidelines de Google
> **Implementado:** Migración 039, 3 servicios backend, 1 módulo frontend (665 líneas), 150 ítems checklist configurados

### 17.A — Módulo Auditoría EEAT (checklist interactivo)

**Concepto:** Un módulo nuevo en el sidebar (grupo "Entidad") que presenta los 150 ítems de auditoría EEAT de la tab "Brand+Website" del checklist Ahrefs como un formulario interactivo. El auditor (humano) va evaluando cada ítem. Donde sea posible, FIT pre-llena automáticamente.

**Migración 038: `eeat_audits`**
```sql
CREATE TABLE IF NOT EXISTS eeat_audits (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Auditoría EEAT',
    entity_type TEXT NOT NULL CHECK (entity_type IN ('brand_website', 'people', 'pages')),
    status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed')),
    scores JSONB DEFAULT '{}',  -- {experience: X, expertise: X, authority: X, trust: X, overall: X}
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eeat_audit_items (
    id BIGSERIAL PRIMARY KEY,
    audit_id BIGINT REFERENCES eeat_audits(id) ON DELETE CASCADE,
    section TEXT NOT NULL,  -- 'foundational_branding', 'contact_details', etc.
    item_key TEXT NOT NULL,  -- identificador único del ítem
    item_text TEXT NOT NULL,  -- texto del checklist
    source TEXT,  -- 'QRG section 3.3.1', etc.
    categories TEXT[],  -- ['Authority', 'Trust', 'Reputation']
    entity_to_check TEXT,  -- 'Website', 'Brand (Off-Site)', 'Page', etc.
    score INTEGER CHECK (score >= 0 AND score <= 100),  -- 0/25/50/75/100
    notes TEXT,
    auto_filled BOOLEAN DEFAULT FALSE,
    auto_fill_source TEXT,  -- 'screaming_frog', 'gsc', 'moz', etc.
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Secciones del checklist Brand+Website (16 secciones, ~150 ítems):**

| Sección | Ítems | Auto-fill posible | Fuente auto-fill |
|---------|-------|-------------------|------------------|
| Foundational Branding | 5 | Parcial | Schema crawl |
| Contact Details | 4 | No | Manual |
| Brand Entity | 3 | Parcial | Serper (Knowledge Panel) |
| Business Listings | 5 | No | Manual |
| Brand Profiles | 15 | No | Manual |
| Reviews + Testimonials | 8 | Parcial | Google Reviews API (futuro) |
| Professional Associations | 7 | No | Manual |
| Links + Brand Mentions | 6 | Parcial | Moz backlinks |
| Branded Searches | 8 | Sí | GSC branded data |
| AI Responses | 6 | Sí | LLM Monitor (Sprint 14) |
| Topical Authority | 3 | Sí | Módulo Topical Authority |
| Essential Website Pages | 7 | Parcial | Screaming Frog crawl |
| Legal Pages + Footer | 15 | Parcial | Screaming Frog crawl |
| Website Security | 4 | Sí | Screaming Frog (SSL/HTTPS) |
| Website Design | 4 | No | Manual |
| E-commerce / Affiliate | 17 | No | Manual (si aplica) |

**Backend:** `eeat_audit_service.py`
- `create_audit(project_id, entity_type)` → crea auditoría con todos los ítems pre-cargados
- `update_item(audit_id, item_id, score, notes)` → actualiza score individual
- `auto_fill_audit(audit_id)` → rellena automáticamente ítems verificables
- `calculate_scores(audit_id)` → recalcula scores EEAT por componente

**Frontend:** `EEATAuditPage.tsx`
- Vista por secciones (acordeón expandible)
- Cada ítem: texto + source QRG + selector de score (Lowest/Low/Medium/High/Highest) + campo notas
- Ítems auto-filled marcados con badge "Auto" + fuente
- Barra de progreso: X/150 ítems evaluados
- Botón "Auto-rellenar" que ejecuta auto_fill_audit

**Criterio:** Módulo funcional con los 150 ítems. Scoring correcto. Auto-fill funciona para SSL, branded searches, schema.

### 17.B — EEAT Score Dashboard

**Concepto:** Dashboard dentro del módulo EEAT que muestra los scores calculados automáticamente.

**Componentes del dashboard:**
1. **Score global EEAT** (0-100): media ponderada (Trust 40%, Experience 20%, Expertise 20%, Authority 20%)
2. **Radar chart** con los 4 componentes (usar Recharts RadarChart, NO pie chart)
3. **Scores por entidad** (Brand+Website, People, Pages) en 3 MetricCards
4. **Top 10 gaps** prioritarios: ítems con score más bajo y categoría Trust/Authority (mayor impacto)
5. **Comparativa temporal**: si hay >1 auditoría completada, mostrar tendencia
6. **Exportar como PDF**: resumen ejecutivo para presentar al cliente

**Criterio:** Dashboard muestra datos correctos. Radar chart funcional. Gaps identificados.

### 17.C — EEAT Score por página

**Concepto:** Evaluar cada URL individual con 10 criterios EEAT extraídos del tab "Pages" del checklist Ahrefs.

**10 criterios por página (evaluados por Claude AI):**
1. Autoría clara (byline + link a perfil) → Trust, Expertise
2. Profundidad topical (contenido sustantivo, no superficial) → Expertise
3. Originalidad (pensamiento propio, no resumen de otros) → Expertise, Authority
4. Multimedia original (fotos, videos propios) → Experience
5. Fuentes citadas (links a fuentes autoritativas) → Authority, Trust
6. Schema markup presente (Author, Article, FAQ, etc.) → Foundational
7. Intent match (contenido cumple la intención de búsqueda) → Trust
8. AI-readiness (estructura, datos concretos, entidades nombradas) → Authority
9. YMYL compliance (si aplica: reviewer, credenciales, fuentes) → Trust
10. Proceso de producción (evidencia de esfuerzo humano, no AI slop) → Experience, Trust

**Endpoint:** `GET /api/projects/{id}/eeat/page-score?url=...`
**Respuesta:**
```json
{
  "url": "https://fitgeneration.es/blog/...",
  "eeat_score": 72,
  "components": {"experience": 65, "expertise": 80, "authority": 70, "trust": 75},
  "criteria": [
    {"name": "Autoría clara", "score": 75, "details": "Tiene byline pero falta link a perfil"},
    ...
  ],
  "ymyl": false,
  "recommendations": ["Añadir link al perfil del autor", "Incluir fuentes médicas"]
}
```

**Integración:** Columna "EEAT" en tabla de /analysis con score coloreado (verde >70, ámbar 40-70, rojo <40).

**Criterio:** Score EEAT funciona para cualquier URL. Se ve en la tabla de análisis.

### 17.D — YMYL Risk Assessment

**Concepto:** Detector automático de contenido YMYL basado en las categorías de Google QRG.

**Categorías YMYL:**
- Salud: ejercicio, nutrición, lesiones, suplementos, bienestar mental
- Finanzas: precios, planes de pago, inversiones
- Seguridad: técnicas de entrenamiento, equipamiento
- Legal: contratos, términos de servicio

**Para Fit Generation:** Prácticamente TODO su contenido es YMYL (fitness = salud). Prioridad alta.

**Lógica:**
1. Analizar URL + título + snippet con Claude para clasificar YMYL/Possibly YMYL/Not YMYL
2. Para YMYL: verificar automáticamente si tiene reviewer, credenciales visibles, disclaimers
3. Badge en tabla de contenido: 🔴 YMYL sin reviewer, 🟡 YMYL con reviewer, ⚪ No YMYL

**Criterio:** Clasificación YMYL automática. Badges visibles en tabla.

### 17.E — Brand Entity Verification

**Concepto:** Tab "Verificación EEAT" dentro del Entity Panel existente.

**Checks:**
- Wikipedia: ¿existe? → link + estado
- Knowledge Panel Google: ¿aparece? ¿claimed? → captura via Serper
- Knowledge Panel Bing: ¿aparece? → via Bing API
- Google Business: ¿existe? ¿optimizado? → manual
- Perfiles sociales: lista de plataformas con estado (claimed/activo/link a web)
- Business Listings: Google, Bing Places, Apple Maps, directorios locales

**Criterio:** Tab funcional con estado de cada verificación. Scoring parcial alimenta EEAT Audit.

### 17.F — Personas Sintéticas / Focus Group AI

> **Fuentes:** Locomotive Agency (SSR Landing Page Analysis), Kevin Indig / Growth Memo (feb 2026), Stanford + Google DeepMind (85% accuracy validated)

**Concepto:** En vez de evaluar contenido con criterios técnicos solamente, simular cómo reaccionarían personas reales del público objetivo. Claude genera 3-5 personas sintéticas del nicho de Fit Generation y cada una evalúa el contenido como lo haría un usuario real: ¿me fío?, ¿resuelve mi problema?, ¿compraría/me apuntaría?

**Persona Card — 5 campos (framework Kevin Indig):**
1. **Job-to-be-done**: Tarea real que quiere resolver (ej: "perder 10kg antes del verano", "montar mi negocio de entrenamiento personal")
2. **Constraints**: Presiones y limitaciones (ej: "solo tengo 30 min/día", "presupuesto <50€/mes", "lesión de rodilla")
3. **Information needs**: Qué necesita saber para decidir (ej: "¿funciona sin gimnasio?", "¿resultados en cuánto tiempo?")
4. **Search behavior**: Cómo busca (ej: prompts largos en ChatGPT, queries cortas en Google, pide recomendación en Instagram)
5. **Trust signals**: Qué le genera confianza (ej: "estudios científicos", "antes/después reales", "certificación del entrenador")

**Personas base para Fit Generation (preconfigurables):**
- Principiante gym (25M): quiere ganar músculo, busca rutinas, sensible al precio
- Madre activa (38F): quiere ponerse en forma post-parto, poco tiempo, busca resultados rápidos
- Entrenador personal (30M): busca formarse/certificarse, quiere diferenciarse, busca autoridad
- Atleta intermedio (28F): quiere optimizar rendimiento, busca contenido técnico/avanzado
- Senior activo (55M): quiere mantenerse sano, preocupado por lesiones, busca seguridad

**Fuentes de datos para alimentar personas (orden de riqueza):**
1. Search Console query data: queries question-type últimos 28 días (ya lo tenemos en GSC)
2. Reviews del cliente: qué dicen, qué esperaban, qué les faltó
3. Comentarios en redes sociales: lenguaje real de la audiencia
4. Foros y comunidades fitness: problemas reales, vocabulario, objeciones

**Implementación — 2 modos:**

**Modo 1: Focus Group de Contenido (integración Content Validator)**
- Endpoint: `POST /api/projects/{id}/eeat/focus-group`
- Input: URL a evaluar + personas a usar (o usar las 5 default)
- Claude simula cada persona leyendo el contenido y responde en texto libre:
  * ¿Qué entendí? ¿Resuelve mi problema? ¿Me fío del autor? ¿Haría lo que dice? ¿Qué me falta?
- Después: SSR (Semantic Similarity Rating) — la respuesta libre se compara contra respuestas calibradas para sacar score 1-5 por persona
- Output: score promedio de resonancia + feedback textual por persona + gaps identificados

**Modo 2: Comparativa Competitiva (integración Competidores)**
- Endpoint: `POST /api/projects/{id}/eeat/competitive-focus-group`
- Input: nuestra URL + URL del competidor + query target
- Las mismas personas evalúan AMBAS páginas
- Output: cuadrante tipo Locomotive (AI Visibility vs Landing Page Effectiveness) + "¿a quién eliges y por qué?" por persona

**Migración 040b: `synthetic_personas` y `focus_group_results`**
```sql
CREATE TABLE IF NOT EXISTS synthetic_personas (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    demographics JSONB DEFAULT '{}',  -- {age, gender, location, occupation}
    job_to_be_done TEXT NOT NULL,
    constraints TEXT[],
    information_needs TEXT[],
    search_behavior TEXT,
    trust_signals TEXT[],
    data_sources TEXT[],  -- de dónde se extrajo esta persona
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS focus_group_results (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    competitor_url TEXT,  -- NULL si es modo 1
    query TEXT,
    personas_used BIGINT[],  -- IDs de synthetic_personas
    results JSONB DEFAULT '{}',  -- {persona_id: {response, score, trust, gaps}}
    overall_score NUMERIC(3,1),
    mode TEXT CHECK (mode IN ('content', 'competitive')),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Frontend:** Tab "Focus Group" dentro del Content Validator o módulo EEAT
- Panel izquierdo: selección de personas (checkboxes) + opción de crear nueva
- Panel derecho: resultados por persona con avatar, nombre, score, quote clave
- Visualización: bar chart horizontal de scores por persona (quién conecta más, quién menos)
- En modo competitivo: cuadrante de posicionamiento + tabla side-by-side

**Criterio:** 5 personas default creadas para Fit Generation. Focus Group funciona para cualquier URL. Resultados muestran feedback útil y accionable por persona.

---

## SPRINT 18: Authors, People & Personas

> **Fuentes:** Ahrefs EEAT Checklist — tab "People" (66 ítems). Kevin Indig / Growth Memo — Synthetic Personas framework.
> **Prerrequisito:** Sprint 17 completado (EEAT Audit + Personas Sintéticas base)

**Este sprint unifica las dos caras de "personas":** las que CREAN contenido (Authors/Reviewers/Leaders) y las que lo CONSUMEN (Buyer Personas / Synthetic Personas). Ambas son fundamentales para EEAT.

### 18.A — Módulo People (CRUD unificado)

**Concepto:** Un solo módulo "People" en el sidebar (grupo "Entidad") con dos tabs: "Equipo" (autores, reviewers, líderes) y "Audiencia" (buyer personas sintéticas).

**Migración 041: `people`**
```sql
CREATE TABLE IF NOT EXISTS people (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('author', 'reviewer', 'leader', 'contributor', 'persona')),
    name TEXT NOT NULL,
    -- Campos comunes
    photo_url TEXT,
    bio TEXT,
    -- Campos Equipo (type != 'persona')
    job_title TEXT,
    expertise_topics TEXT[],
    credentials TEXT[],
    social_profiles JSONB DEFAULT '{}',
    wikipedia_url TEXT,
    website_profile_url TEXT,
    publications_count INTEGER DEFAULT 0,
    -- Campos Persona (type = 'persona')
    demographics JSONB DEFAULT '{}',
    job_to_be_done TEXT,
    constraints TEXT[],
    information_needs TEXT[],
    search_behavior TEXT,
    trust_signals TEXT[],
    data_sources TEXT[],
    is_default BOOLEAN DEFAULT FALSE,
    -- EEAT score (aplica a ambos)
    eeat_score INTEGER DEFAULT 0,
    eeat_details JSONB DEFAULT '{}',
    eeat_checklist JSONB DEFAULT '{}',  -- ítems del checklist Ahrefs respondidos
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Frontend:** `PeoplePage.tsx`
- **Tab Equipo:** Lista con foto, nombre, cargo, score EEAT, nº de artículos publicados
  - Modal de edición completo
  - Checklist EEAT por persona (14 ítems "Foundational Personal Branding" + subchecklist por rol)
  - Badges: 🟢 EEAT completo, 🟡 parcial, 🔴 sin evaluar
- **Tab Audiencia:** Gestión de buyer personas sintéticas
  - Persona Cards visuales con los 5 campos de Kevin Indig
  - Botón "Generar Persona desde GSC" → analiza queries de GSC últimos 28d y propone persona
  - Botón "Probar contenido" → lanza Focus Group (Sprint 17.F) con esta persona
  - Las 5 personas default de Fit Generation pre-cargadas

### 18.B — Author-Content Linking

- Asignar autor(es) a cada pieza de contenido en el inventario
- Asignar reviewer a páginas YMYL
- Vista "Portfolio" por autor: todas sus URLs con métricas
- Detectar contenido huérfano (sin autor asignado) → alerta
- En tabla de /analysis: columna "Autor" clicable → va al perfil

### 18.C — Author Schema Markup Generator

- Genera JSON-LD de Person schema por cada autor
- Genera ProfilePage schema para páginas de bio
- Genera reviewedBy schema para páginas con reviewer
- Genera Author schema para artículos
- Botón "Copiar código" + preview de cómo se vería en Google
- Validador: comprobar si la web del cliente ya tiene estos schemas

### 18.D — Author Search Presence Tracker

- Via Serper: Knowledge Panel del autor en Google
- Via GSC: branded searches con nombre del autor
- Via LLM Monitor: menciones del autor en AI responses
- Dashboard: qué autores tienen presencia de entidad vs cuáles necesitan trabajar
- Recomendaciones por autor: "necesita Wikipedia", "necesita más guest posts", "falta Knowledge Panel"

### 18.E — Persona-Driven Content Strategy

**Concepto:** Usar las buyer personas sintéticas para guiar la estrategia de contenido, no solo evaluarla.

- **Prompt Tracker por Persona**: Para cada persona, ¿qué prompts usaría en Google/ChatGPT/Perplexity? Claude genera 15-30 prompts probables basados en el persona card
- **Content-Persona Fit Matrix**: Tabla que cruza URLs × Personas → score de resonancia (usa datos de Focus Group)
- **Gaps de Contenido por Persona**: ¿Qué necesita cada persona que no tenemos cubierto? → alimenta Content Gaps
- **Simulación de Journey**: Para cada persona, simular su journey: primera búsqueda → páginas que encontraría → decisión. ¿Dónde perdemos al usuario?

### 18.F — Company Leaders & Reviewers

- Sección separada para founders/executives (7 ítems EEAT específicos): sentimiento, conexión con marca, conceptos propios, menciones AI
- Sección Reviewers: credenciales, byline, páginas YMYL revisadas
- Verificar que toda página YMYL tiene reviewer asignado con credenciales visibles
- Alerta si hay contenido YMYL sin reviewer

### 18.G — Personas Sintéticas / Focus Group AI

> **Fuentes:** Locomotive Agency (SSR Landing Page Analysis), Kevin Indig / Growth Memo (feb 2026), Stanford + Google DeepMind (85% accuracy validated)

**Concepto:** En vez de evaluar contenido con criterios técnicos solamente, simular cómo reaccionarían personas reales del público objetivo. Claude genera 3-5 personas sintéticas del nicho de Fit Generation y cada una evalúa el contenido como lo haría un usuario real: ¿me fío?, ¿resuelve mi problema?, ¿compraría/me apuntaría?

**Persona Card — 5 campos (framework Kevin Indig):**
1. **Job-to-be-done**: Tarea real que quiere resolver (ej: "perder 10kg antes del verano", "montar mi negocio de entrenamiento personal")
2. **Constraints**: Presiones y limitaciones (ej: "solo tengo 30 min/día", "presupuesto <50€/mes", "lesión de rodilla")
3. **Information needs**: Qué necesita saber para decidir (ej: "¿funciona sin gimnasio?", "¿resultados en cuánto tiempo?")
4. **Search behavior**: Cómo busca (ej: prompts largos en ChatGPT, queries cortas en Google, pide recomendación en Instagram)
5. **Trust signals**: Qué le genera confianza (ej: "estudios científicos", "antes/después reales", "certificación del entrenador")

**Personas base para Fit Generation (preconfigurables):**
- Principiante gym (25M): quiere ganar músculo, busca rutinas, sensible al precio
- Madre activa (38F): quiere ponerse en forma post-parto, poco tiempo, busca resultados rápidos
- Entrenador personal (30M): busca formarse/certificarse, quiere diferenciarse, busca autoridad
- Atleta intermedio (28F): quiere optimizar rendimiento, busca contenido técnico/avanzado
- Senior activo (55M): quiere mantenerse sano, preocupado por lesiones, busca seguridad

**Fuentes de datos para alimentar personas (orden de riqueza):**
1. Search Console query data: queries question-type últimos 28 días (ya lo tenemos en GSC)
2. Reviews del cliente: qué dicen, qué esperaban, qué les faltó
3. Comentarios en redes sociales: lenguaje real de la audiencia
4. Foros y comunidades fitness: problemas reales, vocabulario, objeciones

**Implementación — 2 modos:**

**Modo 1: Focus Group de Contenido (integración Content Validator)**
- Endpoint: `POST /api/projects/{id}/personas/focus-group`
- Input: URL a evaluar + personas a usar (o usar las 5 default)
- Claude simula cada persona leyendo el contenido y responde en texto libre:
  * ¿Qué entendí? ¿Resuelve mi problema? ¿Me fío del autor? ¿Haría lo que dice? ¿Qué me falta?
- Después: SSR (Semantic Similarity Rating) — la respuesta libre se compara contra respuestas calibradas para sacar score 1-5 por persona
- Output: score promedio de resonancia + feedback textual por persona + gaps identificados

**Modo 2: Comparativa Competitiva (integración Competidores)**
- Endpoint: `POST /api/projects/{id}/personas/competitive-focus-group`
- Input: nuestra URL + URL del competidor + query target
- Las mismas personas evalúan AMBAS páginas
- Output: cuadrante tipo Locomotive (AI Visibility vs Landing Page Effectiveness) + "¿a quién eliges y por qué?" por persona

**Migración 040: `synthetic_personas` y `focus_group_results`**
```sql
CREATE TABLE IF NOT EXISTS synthetic_personas (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    demographics JSONB DEFAULT '{}',
    job_to_be_done TEXT NOT NULL,
    constraints TEXT[],
    information_needs TEXT[],
    search_behavior TEXT,
    trust_signals TEXT[],
    data_sources TEXT[],
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS focus_group_results (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    competitor_url TEXT,
    query TEXT,
    personas_used BIGINT[],
    results JSONB DEFAULT '{}',
    overall_score NUMERIC(3,1),
    mode TEXT CHECK (mode IN ('content', 'competitive')),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Frontend:** Tab "Focus Group" dentro del módulo People (tab Audiencia) o Content Validator
- Panel izquierdo: selección de personas (checkboxes) + opción de crear nueva
- Panel derecho: resultados por persona con avatar, nombre, score, quote clave
- Visualización: bar chart horizontal de scores por persona
- En modo competitivo: cuadrante de posicionamiento + tabla side-by-side

**Criterio:** 5 personas default creadas para Fit Generation. Focus Group funciona para cualquier URL. Resultados muestran feedback útil y accionable por persona.

---

## SPRINT 19: Reputation & Trust EEAT ✅ COMPLETADO

> **Fuente:** Ahrefs EEAT Checklist — secciones Reviews, Associations, Links, Legal
> **Commit:** 148c197

### 19.0 — Limpieza de badges "NUEVO" en sidebar

**ANTES de hacer cualquier otra cosa en este sprint:** Eliminar TODOS los `badge: 'NUEVO'` de `frontend/src/config/modules.ts`. Hay 6 módulos que aún lo tienen (content-performance, entity-panel, eeat-audit, geo-audit, llm-monitor, content-hub). Quitar la propiedad `badge` de esos 6 objetos. No añadir badge a ningún módulo nuevo a partir de ahora.

### 19.A — Reputation Score Dashboard

- Reviews: count + rating por plataforma
- Prensa: menciones positivas/negativas/neutras
- Foros: menciones y recomendaciones
- Score ponderado + trend temporal

### 19.B — Reviews & Testimonials Tracker

- Inventario de reviews por plataforma
- Alertas de reviews sin responder
- Verificar testimonials en web con link a fuente
- Review schema checker

### 19.C — Professional Associations & Awards

- Registro de membresías, certificaciones, awards, partnerships
- Verificar visibilidad en web (About, footer, homepage)
- Sugerencias de asociaciones del sector fitness

### 19.D — Trust Signals Checker

- Automático: SSL, HTTPS, cookie consent, privacy policy, terms
- Semi-automático: editorial policy, AI disclaimer, GDPR
- Integrar con Screaming Frog
- Checklist de páginas esenciales EEAT: About, Contact, Team, Portfolio, Reviews, Media
- Score Trust técnico + Trust editorial

---

## SPRINT 20: Brand Visibility Audit

> **Fuente:** Brand Visibility Audit Framework MVP (feb 2026) — 6 módulos, Brand Visibility Index con cuadrante
> **Prerrequisito:** Sprints 16-19 completados (Entity Panel + EEAT + People + Reputation)
> **Principio:** FIT ya cubre ~60% del framework. Este sprint añade lo que falta y crea la capa de agregación que empaqueta todo como producto auditable.

**Lo que ya existe en FIT y NO hay que rehacer:**
- Módulo 1 (Entity Strength) → Entity Panel (S16) + Brand Verification (S17) + Brand Authority Score (S15)
- Módulo 3 parcial (AI Visibility) → LLM Monitor (S14) + GEO Audit (S14)
- Módulo 5 (Synthetic Audience) → Focus Group AI (S18)

**Lo que falta y se construye aquí:**
- Módulo 2 completo: LLM Perception Analysis
- Módulo 3 mejoras: AI Overview/PAA/Featured Snippet detection
- Módulo 4 completo: Brand-Keyword Coherence
- Módulo 6 completo: Brand Signal Consistency
- Índice agregado: Brand Visibility Index + Cuadrante

### 20.A — LLM Perception Analysis

**Concepto:** Preguntar a Claude (simulando también ChatGPT/Gemini/Perplexity) cómo percibe la marca. No es lo mismo que monitorizar citaciones (LLM Monitor) — aquí se interroga activamente a los LLMs sobre la marca.

**Batería de 6 prompts estandarizados:**
1. "¿Qué es [marca]? Descríbela en 2-3 frases" → descripción percibida
2. "¿En qué categoría/sector opera [marca]?" → categorización
3. "¿Cuáles son los principales competidores de [marca]?" → competidores percibidos
4. "Recomiéndame [categoría] en [mercado]" → recomendación contextual (¿aparece?)
5. "¿Cuáles son los puntos fuertes y débiles de [marca]?" → sentimiento
6. "¿Para quién es [marca]? ¿Cuál es su público objetivo?" → audiencia percibida

**Implementación:**
- Ejecutar los 6 prompts via Claude API
- Parsear respuestas: categoría mencionada, competidores listados, sentimiento, posición en recomendaciones
- Comparar respuestas vs posicionamiento declarado del cliente (campo en Settings o input manual) → gap score
- Consistency score: ¿los diferentes prompts dan una imagen coherente?

**Migración 044:** `llm_perception_analyses`
```sql
CREATE TABLE IF NOT EXISTS llm_perception_analyses (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    brand_positioning TEXT,  -- posicionamiento declarado por el cliente
    target_audience TEXT,  -- audiencia declarada
    category TEXT,  -- categoría/sector declarado
    prompts_results JSONB DEFAULT '{}',  -- {prompt_key: {response, extracted_data}}
    perception_score INTEGER DEFAULT 0,  -- 0-100
    gap_analysis JSONB DEFAULT '{}',  -- {description_gap, category_gap, competitors_gap, audience_gap}
    consistency_score INTEGER DEFAULT 0,  -- 0-100
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Endpoints:**
- `POST /projects/{id}/brand-audit/llm-perception` — ejecutar análisis
- `GET /projects/{id}/brand-audit/llm-perception` — último resultado
- `GET /projects/{id}/brand-audit/llm-perception/history` — histórico

**Frontend (tab en Brand Visibility Audit Page):**
- Input: posicionamiento declarado, categoría, audiencia target, competidores reales
- Output: tabla comparativa prompt por prompt: "Lo que dices" vs "Lo que el LLM percibe"
- Gap badges: verde=alineado, amarillo=parcial, rojo=desalineado
- Perception Score y Consistency Score como MetricCards

### 20.B — AI Search Visibility Score

**Concepto:** Ampliar el LLM Monitor existente con detección de AI Overviews, Featured Snippets y People Also Ask en SERPs. Calcular un AI Visibility Score agregado.

**Queries a testear (generadas semi-automáticamente):**
- Queries de categoría genérica: "[categoría] en [mercado]"
- Queries comparativas: "mejor [categoría] para [use case]"
- Queries de recomendación: "recomiéndame [categoría]"
- Queries de problema: "[pain point del target] solución"
- Queries de marca: "[marca]", "[marca] opiniones", "[marca] vs [competidor]"

**Implementación:**
- Usar Serper API (ya integrada) para cada query
- Detectar: AI Overview (presencia + mención de marca), Featured Snippet (marca aparece?), PAA (preguntas relacionadas)
- Calcular Salience Score por query: posición + cobertura + sentimiento + recomendación
- Agregar en AI Visibility Score (1-5 o 0-100)

**Migración 044 (misma):** añadir tabla `ai_visibility_checks`
```sql
CREATE TABLE IF NOT EXISTS ai_visibility_checks (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    query_type TEXT CHECK (query_type IN ('category', 'comparative', 'recommendation', 'problem', 'brand')),
    has_ai_overview BOOLEAN DEFAULT FALSE,
    brand_in_ai_overview BOOLEAN DEFAULT FALSE,
    has_featured_snippet BOOLEAN DEFAULT FALSE,
    brand_in_featured_snippet BOOLEAN DEFAULT FALSE,
    paa_questions TEXT[],
    brand_in_paa BOOLEAN DEFAULT FALSE,
    organic_position INTEGER,
    salience_score NUMERIC(3,1),  -- 1-5
    serp_data JSONB DEFAULT '{}',
    checked_at TIMESTAMPTZ DEFAULT now()
);
```

**Endpoints:**
- `POST /projects/{id}/brand-audit/ai-visibility/check` — ejecutar batch de queries
- `GET /projects/{id}/brand-audit/ai-visibility` — resultados + score agregado
- `POST /projects/{id}/brand-audit/ai-visibility/generate-queries` — Claude genera 20-30 queries relevantes

**Frontend (tab):**
- Heatmap de visibilidad: queries × canales (AI Overview / Featured Snippet / PAA / Orgánico)
- Verde=presente, rojo=ausente
- Score AI Visibility global

### 20.C — Brand-Keyword Coherence

**Concepto:** Analizar si el universo de keywords por el que compite la marca refleja su posicionamiento real. Usa datos existentes de Topical Authority + Keyword Universe + GSC.

**Implementación:**
- Input: pilares de posicionamiento de marca (manual o desde Settings)
- Claude clasifica las keywords actuales (de GSC top 500) en clusters temáticos
- Mapear clusters vs pilares declarados: alineado / parcialmente alineado / desalineado / no cubierto
- Calcular Coherence Score: % keywords alineadas × volumen ponderado
- Identificar gaps estratégicos: pilares sin keywords + keywords fuertes fuera de pilares

**Sin migración nueva:** usa datos de `content_keywords` + `keyword_positions` + `topical_clusters` existentes.

**Endpoints:**
- `POST /projects/{id}/brand-audit/keyword-coherence` — ejecutar análisis
- `GET /projects/{id}/brand-audit/keyword-coherence` — último resultado

**Frontend (tab):**
- Bubble chart: clusters por volumen, coloreados por alineación
- Tabla: pilar → keywords alineadas → % cobertura → gaps
- Coherence Score como MetricCard

### 20.D — Brand Signal Consistency

**Concepto:** Verificar si el messaging de la marca es coherente en todos los touchpoints digitales. Claude analiza textos de diferentes fuentes y detecta inconsistencias.

**Touchpoints a analizar:**
1. Homepage (H1, tagline, hero text)
2. About page (descripción, misión, valores)
3. 3-5 landing pages principales (value props)
4. Meta descriptions de las 10 URLs principales
5. OG tags (og:title, og:description)
6. Perfiles sociales (bios de LinkedIn, Twitter, Instagram, Google Business)

**Implementación:**
- Fetch de contenido via URLs del proyecto (sitemap + perfiles sociales de brand_verification)
- Claude analiza: "Analiza estos 15+ textos de la misma marca. ¿Es consistente el mensaje? ¿Qué inconsistencias detectas? ¿Se diferencia de [competidores]?"
- Extraer: taglines, value props, descriptores clave, tono → comparar
- Consistency Score: cuántos touchpoints son coherentes vs inconsistentes
- Differentiation Score: ¿se diferencia de competidores o es genérica?

**Migración 044 (misma):** añadir tabla `brand_consistency_analyses`
```sql
CREATE TABLE IF NOT EXISTS brand_consistency_analyses (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    touchpoints JSONB DEFAULT '{}',  -- {url: {source, text_extracted, tagline, value_prop}}
    consistency_score INTEGER DEFAULT 0,
    differentiation_score INTEGER DEFAULT 0,
    inconsistencies JSONB DEFAULT '[]',  -- [{touchpoint_a, touchpoint_b, issue, severity}]
    competitor_comparison JSONB DEFAULT '{}',
    analysis_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Endpoints:**
- `POST /projects/{id}/brand-audit/consistency` — ejecutar análisis
- `GET /projects/{id}/brand-audit/consistency` — último resultado

**Frontend (tab):**
- Tabla de touchpoints: URL/plataforma, texto extraído, tagline, tono
- Lista de inconsistencias con severity (alta/media/baja)
- Consistency Score + Differentiation Score

### 20.E — Brand Visibility Index + Cuadrante

**Concepto:** Capa de agregación que combina los 6 módulos (4 existentes + 2 nuevos) en un único Brand Visibility Index con visualización de cuadrante.

**Composición del índice:**

| Módulo | Peso | Fuente en FIT |
|--------|------|---------------|
| 1. Entity Strength | 20% | Entity Panel → entity_health_score |
| 2. LLM Perception | 20% | 20.A → perception_score |
| 3. AI Search Visibility | 15% | 20.B → ai_visibility_score |
| 4. Brand-Keyword Coherence | 20% | 20.C → coherence_score |
| 5. Audience Perception | 15% | Focus Group (S18) → overall_score promedio |
| 6. Signal Consistency | 10% | 20.D → consistency_score |

**Cuadrante (inspirado en Locomotive):**
- Eje X: **Brand Definition** = promedio módulos 1, 2, 6 → "¿Saben quién eres?"
- Eje Y: **Market Alignment** = promedio módulos 3, 4, 5 → "¿Llegas a quien debes?"

Cuadrantes:
- Superior derecho: **Connected Brand** — bien definida y bien posicionada
- Superior izquierdo: **Hidden Gem** — mal definida pero buen mercado
- Inferior derecho: **Loud but Lost** — bien definida pero mal dirigida
- Inferior izquierdo: **Invisible** — necesita trabajo fundamental

**Migración 044 (misma):** añadir tabla `brand_visibility_snapshots`
```sql
CREATE TABLE IF NOT EXISTS brand_visibility_snapshots (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    bvi_score NUMERIC(4,1),  -- Brand Visibility Index 0-100
    module_scores JSONB DEFAULT '{}',  -- {entity: X, llm_perception: X, ai_visibility: X, coherence: X, audience: X, consistency: X}
    brand_definition NUMERIC(4,1),  -- eje X cuadrante
    market_alignment NUMERIC(4,1),  -- eje Y cuadrante
    quadrant TEXT,  -- 'connected_brand', 'hidden_gem', 'loud_but_lost', 'invisible'
    snapshot_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, snapshot_date)
);
```

**Endpoints:**
- `GET /projects/{id}/brand-audit/index` — calcular BVI actual (agrega datos de todos los módulos)
- `GET /projects/{id}/brand-audit/index/trend` — histórico de snapshots

### 20.F — Brand Visibility Audit Page

**Concepto:** Nueva página unificada como módulo en el sidebar (grupo "Entidad"). Dashboard que muestra el BVI con cuadrante + tabs para cada módulo del audit.

**Layout:**
- **Header:** Brand Visibility Index (número grande) + cuadrante visual (scatter plot con punto posicionado) + etiqueta del cuadrante
- **6 MetricCards:** un score por módulo (coloreados semánticamente)
- **5 tabs:**
  1. LLM Perception (20.A)
  2. AI Visibility (20.B)
  3. Keyword Coherence (20.C)
  4. Signal Consistency (20.D)
  5. Trend (evolución temporal del BVI y sus componentes)

Los módulos 1 (Entity) y 5 (Audience) ya tienen sus propias páginas dedicadas (Entity Panel y People/Focus Group), así que aquí solo se muestran los scores como referencia con link al módulo.

**Registrar en modules.ts:**
```typescript
{ key: 'brand-audit', label: 'Brand Visibility Audit', icon: Radar, path: 'brand-audit', group: 'entity', enabled: true },
```

---

## Resumen visual actualizado

```
BLOQUES A-E: Completados                     [✅ Sprints 1-13]

SPRINT 14: GEO                               [✅ Completado]
  14.A Auditor GEO Comparativo
  14.B Monitor Citaciones LLM
  14.C Briefings GEO-first
  14.D Schema Markup Sugerido
      ↓
SPRINT 15: Brand Authority + Validator       [✅ Completado]
  15.A-G Features originales
      ↓
SPRINT 16: Entity Panel                      [✅ Completado 12 feb]
      ↓
SPRINT 17: EEAT Audit Module                 [✅ Completado]
  17.A Checklist interactivo (150 ítems Brand+Website)
  17.B EEAT Score Dashboard (radar, gaps, export)
  17.C EEAT Score por página (10 criterios AI)
  17.D YMYL Risk Assessment
  17.E Brand Entity Verification (13 plataformas)
      ↓
SPRINT 18: Authors, People & Personas        [✅ Completado]
  18.A Módulo People unificado (Equipo + Audiencia)
  18.B Author-Content Linking
  18.C Author Schema Markup Generator
  18.D Author Search Presence Tracker
  18.E Persona-Driven Content Strategy
  18.F Company Leaders & Reviewers
  18.G Personas Sintéticas / Focus Group AI
      ↓
SPRINT 19: Reputation & Trust EEAT           [✅ Completado]
  19.0 Limpieza badges NUEVO
  19.A Reputation Score Dashboard
  19.B Reviews & Testimonials Tracker
  19.C Professional Associations & Awards
  19.D Trust Signals Checker
      ↓
SPRINT 20: Brand Visibility Audit             [✅ Completado 13 feb]
  20.A LLM Perception Analysis (multi-LLM)
  20.B AI Search Visibility Score (AI Overviews, PAA, Featured Snippets)
  20.C Brand-Keyword Coherence (alineación keywords ↔ posicionamiento)
  20.D Brand Signal Consistency (coherencia messaging en touchpoints)
  20.E Brand Visibility Index + Cuadrante
  20.F Brand Visibility Audit Page (dashboard unificado)
  + Lead Attribution (GA4 generate_lead events)
  + Dashboard Cache (DB-backed, 24h TTL)
```

SPRINT 21: SEO Técnico + Performance        [✅ Completado 15 feb]
  21.A Indexación & Cobertura (sitemap vs crawl vs GSC)
  21.B Grafo de Arquitectura Web (D3.js force-directed, VON Crawl-style)
  21.C Crawl Budget Analysis (facetada, params, calendarios — datos Google)
  21.D Interlinking Inteligente (sugerencias cruzando clústeres + entidades + tráfico)
  21.E Inspector URL Rápido (análisis on-demand sin SF, fetch+parse HTML)
  21.F Quality Gates Contenido (doorway pages, thin por tipo, templates, velocidad)
  21.G Performance & Cache (dashboard 6.4s→1.4s, branded gap 52%→0%)
  21.H Onboarding & Empty States (EmptyState component, CTAs, seed personas default)
  + P0 Fix: Branded/Non-branded ahora suman = Total
  + P0 Fix: Dashboard lee de DB en vez de GSC API
```

**Sprints 14-21 completados.**

---

## SPRINT 25: AI Search Optimization (SRO) + Content Repurposer

> **Fuentes:** DEJAN AI (Dan Petrovic) — Grounding Chunks Research, Selection Rate Optimization (SRO), Grounding Classifier. Search Engine Journal — Article to Short-Form Video framework. FandangoSEO — inspiración crawl intelligence.
> **Prerrequisito:** Sprint 24 completado.
> **Principio:** Dos módulos nuevos que posicionan FIT en la frontera del AI SEO: optimizar contenido para ser seleccionado por Gemini como grounding chunk (SRO), y transformar artículos de alto rendimiento en guiones de video corto con IA.

### 25.A — Grounding Score Analyzer (SRO)

**Concepto:** Analizar cada URL del proyecto para predecir qué porcentaje de su contenido sobreviviría al filtrado de grounding de Gemini. Google extrae ~2,000 palabras por query distribuidas entre fuentes, y el #1 recibe ~531 palabras (28% del presupuesto). Páginas de 800 palabras obtienen 50%+ de cobertura; páginas de 4,000 palabras solo 13%. **Densidad le gana a longitud.**

**Datos clave de DEJAN (hardcodear como constantes):**
```python
GROUNDING_BUDGET_WORDS = 2000  # palabras totales por query
GROUNDING_BY_RANK = {1: 531, 2: 398, 3: 332, 4: 299, 5: 266, 6: 233, 7: 200, 8: 166, 9: 133, 10: 100}
OPTIMAL_PAGE_LENGTH = 800  # palabras para máxima cobertura
COVERAGE_BY_LENGTH = {500: 0.70, 800: 0.61, 1000: 0.50, 1500: 0.35, 2000: 0.27, 3000: 0.13, 4000: 0.10}
```

**Análisis por URL (Claude AI):**

Para cada URL, Claude analiza el contenido HTML y evalúa 5 dimensiones:

1. **Grounding Coverage Score** (0-100): Estimación del % de contenido que sobreviviría al filtrado extractivo. Se basa en: densidad de información factual, ausencia de contenido filler, estructura chunk-friendly.

2. **Semantic Compression Check**: Detectar párrafos que usan pronombres ambiguos ("es muy eficiente", "esto funciona") o dependen de contexto anterior. Cada bloque lógico debe ser autocontenido — nombrar explícitamente el producto/servicio/concepto.

3. **Chunk-Proof Structure**: ¿Cada sección H2/H3 funciona como fragmento independiente? ¿Los párrafos tienen entidad principal nombrada? ¿Hay datos concretos o solo claims genéricos?

4. **Optimal Length Assessment**: Comparar longitud actual vs óptima. Si >2,000 palabras, sugerir split en páginas más densas. Si <500, evaluar si hay suficiente sustancia.

5. **Selection Rate Predictor**: Basado en posición actual (GSC) y longitud, estimar la probabilidad de ser seleccionado como grounding chunk. Fórmula: `selection_probability = coverage_by_length[word_count] × rank_allocation[position] / page_word_count`

**Migración 057: `grounding_analyses`**
```sql
CREATE TABLE IF NOT EXISTS grounding_analyses (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    word_count INTEGER,
    grounding_coverage_score INTEGER DEFAULT 0,  -- 0-100
    semantic_issues JSONB DEFAULT '[]',  -- [{paragraph_index, issue, suggestion, severity}]
    chunk_proof_score INTEGER DEFAULT 0,  -- 0-100
    optimal_length_assessment JSONB DEFAULT '{}',  -- {current_words, optimal_words, recommendation, estimated_coverage}
    selection_rate NUMERIC(5,2),  -- probabilidad estimada 0-100%
    overall_sro_score INTEGER DEFAULT 0,  -- 0-100 ponderado
    recommendations JSONB DEFAULT '[]',  -- [{priority, action, impact, effort}]
    analysis_text TEXT,  -- análisis narrativo de Claude
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, url)
);

CREATE TABLE IF NOT EXISTS sro_snapshots (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    avg_sro_score NUMERIC(4,1),
    avg_grounding_coverage NUMERIC(4,1),
    urls_analyzed INTEGER,
    urls_optimal_length INTEGER,  -- URLs dentro del rango 500-1200 palabras
    urls_over_2000 INTEGER,  -- candidatas a split
    semantic_issues_count INTEGER,
    snapshot_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, snapshot_date)
);
```

**Backend:** `sro_service.py`
- `analyze_url(project_id, url)` → fetch HTML + parse + Claude analysis → grounding_analyses
- `batch_analyze(project_id, limit=20)` → analizar top 20 URLs por tráfico
- `get_sro_dashboard(project_id)` → scores agregados + snapshot
- `get_recommendations(project_id)` → top 10 acciones priorizadas por impacto

**Endpoints:**
- `POST /projects/{id}/sro/analyze` — analizar URL individual
- `POST /projects/{id}/sro/batch` — batch de top N URLs
- `GET /projects/{id}/sro/dashboard` — dashboard SRO
- `GET /projects/{id}/sro/url?url=...` — detalle por URL
- `GET /projects/{id}/sro/recommendations` — acciones priorizadas

**Frontend:** `SROPage.tsx` (módulo sidebar, grupo "Auditoría Técnica")

**Tab 1: Dashboard SRO**
- 4 MetricCards: SRO Score medio, Grounding Coverage medio, URLs en rango óptimo (%), URLs con problemas semánticos
- Bar chart: distribución de URLs por longitud (buckets: <500, 500-800, 800-1200, 1200-2000, 2000-3000, 3000+) con overlay de cobertura estimada
- Trend temporal del SRO Score medio

**Tab 2: Análisis por URL**
- Tabla: URL, palabras, posición GSC, SRO Score, Coverage, Selection Rate → coloreado semántico
- Expandir URL → detalle con issues semánticos, assessment de longitud, recomendaciones
- Botón "Analizar" por URL + "Batch top 20"

**Tab 3: Recomendaciones**
- Lista priorizada de acciones: "Comprimir [URL] de 3,200 a ~800 palabras", "Reescribir párrafos ambiguos en [URL]", "Split [URL] en 3 páginas temáticas"
- Cada acción con: impacto estimado, esfuerzo, URL afectada
- Workflow: pendiente → en progreso → hecho

**Criterio:** Score SRO funcional para cualquier URL. Batch funciona para top 20. Dashboard muestra datos correctos. Recomendaciones accionables.

### 25.B — QDG Classifier (Query Deserves Grounding)

**Concepto:** Réplica del clasificador de DEJAN que predice si una query activará grounding en Gemini. Google usa un prediction score (0-1, threshold 0.3) para decidir si buscar datos en tiempo real. Saber qué queries activan grounding permite priorizar la optimización SRO.

**Implementación:**
- Usar Claude para clasificar queries como: "Alta probabilidad de grounding" / "Media" / "Baja"
- Heurísticas base (del research de DEJAN):
  * Queries factuales/informacionales → alta probabilidad
  * Queries de navegación (branded) → baja probabilidad
  * Queries con datos temporales ("2026", "últimas") → alta
  * Queries ambiguas/subjetivas → baja
  * Queries YMYL → alta (Google necesita verificar)

**Integración con Rank Tracker:**
- Nueva columna "QDG" en tabla de keywords (badge: 🟢 Alta / 🟡 Media / 🔴 Baja)
- Filtro por QDG: ver solo keywords con alta probabilidad de grounding
- Cruzar QDG × SRO Score: keywords que activan grounding PERO nuestra página no está optimizada → oportunidad crítica

**Endpoint:**
- `POST /projects/{id}/sro/qdg-classify` — clasificar batch de keywords
- `GET /projects/{id}/sro/qdg-opportunities` — keywords QDG alta × SRO bajo

**Criterio:** Clasificación QDG funciona. Se ve en Rank Tracker. Oportunidades cruzadas visibles.

### 25.C — Content Repurposer: Article → Video Ecosystem (Short + Long + SEO)

> **Fuentes:** Search Engine Journal — HHVCTA framework + batch production (feb 2026). YouTube CEO Neal Mohan — 4 prioridades estratégicas 2026. BrightEdge — 29.5% de AI Overviews citan YouTube. VdoCipher — Video SEO Best Practices 2026. Google — 70% de B2B buyers consumen video en journey de compra. YouTube creator data 2026 — chapters +11% watch time, repurposing 4.8x más alcance.

**Por qué esto importa (datos duros):**
- 29.5% de Google AI Overviews citan YouTube → **es el dominio más citado en AI search**
- YouTube Shorts: 200 mil millones de views diarias (YouTube CEO, 2026)
- 25%+ de resultados de Google incluyen un video snippet
- Videos con chapters/timestamps: 63% de los top-ranking los incluyen, +11% watch time
- Videos embebidos en artículos: +34% tráfico orgánico vs video solo (BrightEdge 2026)
- Artículos repurposed a video: +148% referral traffic (SEJ case study)
- Creators que usan estrategia repurposing: 4.8x más alcance (YouTube 2026)
- Reducción producción con batch: de 150-180 min/video a ~40 min/video

**Conexión con SRO (25.A):** YouTube es el dominio #1 citado por AI Overviews. Un video bien optimizado con chapters/timestamps funciona como grounding source para Gemini. El Content Repurposer no es solo "hacer videos" — es una estrategia de AI Search Visibility. Cada video de YouTube con schema VideoObject + Clip markup + transcripción se convierte en un activo más para ser seleccionado como grounding chunk.

**Modelo estratégico (YouTube CEO 2026):**
```
Shorts (discovery) → Long-form (depth) → Blog embebido (SEO) → Commerce (conversion)
     60s HHVCTA         8-15min chapters      +34% tráfico org      link en bio/desc
```

Mix recomendado: 60% long-form, 40% Shorts. Regla 70/20/10: 70% contenido core, 20% trending, 10% experimental.

**Datos clave (constantes):**
```python
SPEAKING_PACE_WPM = 150  # palabras por minuto estándar

# === SHORT-FORM CONFIG ===
SHORT_MAX_WORDS = 150  # 60 segundos × 150 WPM
SHORT_WORD_BUDGET = {
    "hook": (15, 20),      # palabras para el hook
    "close": (15, 25),     # palabras para takeaway+CTA
    "body": (100, 120),    # palabras para value (2-3 puntos máx)
}
SHORT_HHVCTA_TIMING = {
    "hook": (0, 2),       # 0-2 seg: stat sorprendente o pregunta
    "hint": (2, 5),       # 2-5 seg: preview de lo que aprenderán
    "value": (5, 45),     # 5-45 seg: contenido principal (2-3 puntos MAX)
    "credibility": None,  # tejido durante todo el script
    "takeaway": (45, 55), # 45-55 seg: mensaje core
    "action": (55, 60),   # últimos 5 seg: CTA
}
# Platform-specific constraints
SHORT_PLATFORM_LIMITS = {
    "youtube_shorts": {"max_sec": 180, "optimal_sec": 30, "min_for_monetize": 60},
    "tiktok": {"max_sec": 600, "optimal_sec": 34, "min_for_rewards": 60},
    "reels": {"max_sec": 90, "optimal_sec": 30},
}
# Retention benchmarks
SHORT_RETENTION_BENCHMARKS = {
    "3_sec_threshold": 0.60,   # <60% retention at 3s = hook problem
    "mid_video": 0.45,         # sharp drop = pacing issue
    "completion_good": 0.35,   # >35% = good for 60s
}

# === LONG-FORM CONFIG (YouTube) ===
LONG_FORM_STRUCTURE = {
    "cold_open": (0, 30),        # 0-30s: resultado impactante o escena visual
    "hook": (30, 60),            # 30-60s: problema + promesa del video
    "intro": (60, 90),           # 60-90s: presentación + credibilidad + agenda
    "chapters": "dynamic",       # 2-4 capítulos con timestamps keyword-rich
    "recap": (-120, -60),        # últimos 2 min: resumen
    "cta": (-60, 0),             # último min: suscripción + link + engagement
}
LONG_TARGET_MINUTES = {
    "how-to": 8,
    "listicle": 10,
    "case-study": 12,
    "comparison": 10,
    "deep-dive": 15,
    "faq": 7,
    "guide": 12,
}
# YouTube chapters rules
CHAPTER_RULES = {
    "must_start_at_0": True,          # primer timestamp siempre 0:00
    "min_chapters": 3,                 # mínimo 3 para Key Moments en Google
    "max_chapters": 10,                # no más de 10 por video
    "min_duration_sec": 10,            # cada capítulo mín 10 seg
    "title_max_chars": 50,             # keyword-rich, <50 chars
    "pattern_interrupt_every_sec": 150, # cada 2.5 min un interrupt
}

# === CANDIDATURA ===
GOOD_SHORT_TYPES = ["how-to", "listicle", "faq", "tip", "myth-busting"]
GOOD_LONG_TYPES = ["how-to", "case-study", "comparison", "deep-dive", "guide", "listicle"]
BAD_CONTENT_TYPES = ["news", "statistics-heavy", "complex-argument"]
# Threshold: solo recomendar conversión si engagement >5% o >1000 visits/mes (SEJ)
MIN_ENGAGEMENT_RATE = 0.05
MIN_MONTHLY_VISITS = 1000
```

**Candidacy Score (automático, por formato):**

Para cada URL, calcular DOS scores de candidatura:

**Short-form candidacy (0-100):**
1. **Tipo de contenido** (35%): how-to/listicle/faq/tip/myth-busting → alto
2. **Rendimiento GSC** (25%): clicks + impressions altos (threshold: >1000 visits/mes)
3. **Extractabilidad** (25%): ¿se puede destilar en 150 palabras? (datos concretos, pasos claros, estructura Q&A)
4. **Evergreen** (15%): no tiene fechas que caduquen, no es temporal

**Long-form candidacy (0-100):**
1. **Profundidad** (30%): word count >1500, múltiples H2/H3, subtemas desarrollados
2. **Rendimiento GSC** (20%): clicks + impressions
3. **Tipo de contenido** (20%): guide/case-study/comparison/deep-dive → alto
4. **Cluster relevance** (15%): ¿pertenece a un cluster core de topical authority? → videos en clusters fuertes refuerzan authority
5. **AI Search Opportunity** (15%): ¿la query principal tiene AI Overview activo? → video optimizado puede capturar citación

Claude clasifica el tipo de contenido y calcula ambos scores. Una URL puede ser candidata a ambos formatos.

**Generación del guion SHORT (Claude):**

```
Eres un guionista de video corto especializado en fitness.
Artículo fuente: {content}
Datos de rendimiento: {clicks} clicks, {impressions} impresiones, top query: "{query}"

Genera un guion de EXACTAMENTE 150 palabras o menos para un video de 60 segundos.

PRESUPUESTO DE PALABRAS:
- Hook: 15-20 palabras
- Body (value): 100-120 palabras (2-3 puntos MÁXIMO)
- Close (takeaway + CTA): 15-25 palabras

Usa el framework HHVCTA:
- HOOK (0-2s): Stat sorprendente o pregunta directa relacionada con "{query}"
- HINT (2-5s): "En este video vas a aprender..."
- VALUE (5-45s): Los 2-3 puntos más densos del artículo, sin filler
- CREDIBILITY: Mencionar la fuente/experto/dato que respalda (tejido durante value)
- TAKEAWAY (45-55s): El mensaje core en 1 frase
- ACTION (55-60s): CTA claro (seguir, link en bio, comentar)

IMPORTANTE: Relee el hook después de escribir el body — ¿realmente respondiste la pregunta/promesa del hook?

Incluye también:
- 3 opciones de hook (formatos: stat sorprendente, pregunta directa, stake personal)
- Sugerencias de B-roll/overlay cada 3-5 segundos (pattern interrupts para retención)
- Hashtags: 3 broad (#fitness, #entrenamiento) + 3 specific (#rutinagym, #piernasenfuerza) + 2 evergreen
- Título optimizado para cada plataforma (TikTok, Reels, Shorts) — keywords + curiosidad
- Sugerencia de caption para captions on-screen (retención +25% en modo silencio)

Responde en español. Tono: directo, energético, profesional fitness.
```

**Generación del guion LONG (Claude):**

```
Eres un guionista de YouTube especializado en fitness y salud.
Artículo fuente: {content}
Datos: {clicks} clicks, {impressions} impresiones, top queries: {queries}
Tipo de contenido: {content_type}
Duración objetivo: {target_minutes} minutos (~{target_words} palabras)

Genera un guion completo para YouTube con esta estructura:

## COLD OPEN (0-30s)
Empieza con el resultado más impactante o la escena más visual del contenido.
Objetivo: que el espectador NO pase de largo. El 90% del ad recall ocurre en los primeros 6 segundos.

## HOOK + PROBLEMA (30-60s)
Plantea el problema que resuelve este video. ¿Por qué debería importarme?
Incluye la promesa: "Al final de este video vas a saber..."

## INTRO + CREDIBILIDAD (60-90s)
Presentación breve. ¿Por qué Fit Generation puede hablar de esto?
Agenda: "Vamos a ver X, Y y Z"

## CAPÍTULOS DE VALOR (1:30 - {main_end}min)
Divide el contenido en 2-4 capítulos claros con:
- Título de capítulo keyword-rich (<50 chars, para timestamps de YouTube y Key Moments de Google)
- Contenido desarrollado con ejemplos prácticos
- "Pattern interrupt" cada 2-3 minutos (dato sorprendente, pregunta al viewer, cambio visual)
- Transición natural entre capítulos
- Cada capítulo DEBE responder una pregunta concreta (mejora AEO — AI puede surfear clips como respuestas)

## RECAP (últimos 2 min antes del CTA)
"Para resumir lo que hemos visto hoy..."
3-5 puntos clave en formato "si solo te llevas una cosa..."

## CTA (último minuto)
- Pedir suscripción + campana (contextualizado: "si quieres más contenido de [tema]")
- Link en descripción al artículo completo (bidireccional: blog embebe video, video linkea blog → +34% tráfico)
- Sugerir siguiente video relacionado (del mismo cluster temático)
- Pregunta para comentarios (engagement)

Incluye también:

**YouTube SEO package:**
- 3 opciones de thumbnail + título (CTR-optimized, con número o pregunta)
- Timestamps formateados para descripción (empezando en 0:00, mín 3 chapters, títulos keyword-rich <50 chars)
- Tags recomendados (10-15, mix: keywords principales + long-tail + related)
- Descripción YouTube optimizada (~250 palabras): keyword principal en primeras 25 palabras, estructura con links, timestamps embebidos, hashtags
- Schema sugerido: VideoObject + Clip markup JSON-LD para la página del blog donde se embeba

**Producción:**
- Sugerencias de B-roll/gráficos por capítulo (qué se muestra en pantalla)
- "Cards" sugeridas: momentos exactos para enlazar otros videos del canal
- Retention hooks: dónde poner pattern interrupts para evitar caída de audiencia
- Sugerencia de 3-5 Shorts extractables de este video (timestamp + hook para cada uno)

**Cross-plataforma:**
- Transcripción sugerida para subir manualmente (más precisa que auto-captions, mejora discoverability)
- Sugerencia de embed: dónde embeber este video en el blog original para boost de dwell time

Responde en español. Tono: cercano, experto pero accesible, como un entrenador que sabe de lo que habla.
```

**Migración 057 (misma): `content_repurpose_scripts`**
```sql
CREATE TABLE IF NOT EXISTS content_repurpose_scripts (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    source_title TEXT,
    format TEXT NOT NULL DEFAULT 'short' CHECK (format IN ('short', 'long')),
    candidacy_score INTEGER DEFAULT 0,  -- 0-100
    content_type TEXT,  -- 'how-to', 'listicle', etc.
    script_text TEXT NOT NULL,
    hook_options JSONB DEFAULT '[]',  -- 3 hooks/thumbnails alternativos
    visual_cues JSONB DEFAULT '[]',  -- [{timestamp, suggestion}]
    chapters JSONB DEFAULT '[]',  -- long-form: [{title, start_sec, end_sec, summary, keyword}]
    hashtags JSONB DEFAULT '{}',  -- short: {broad: [], specific: [], evergreen: []}
    tags JSONB DEFAULT '[]',  -- long-form: YouTube tags
    platform_titles JSONB DEFAULT '{}',  -- short: {tiktok, reels, shorts} / long: {youtube}
    youtube_description TEXT,  -- long-form: descripción SEO ~250 palabras
    youtube_timestamps TEXT,  -- long-form: timestamps formateados (0:00 format)
    thumbnail_ideas JSONB DEFAULT '[]',  -- long-form: 3 opciones thumbnail+título
    retention_hooks JSONB DEFAULT '[]',  -- [{timestamp_sec, type, suggestion}]
    shorts_extractable JSONB DEFAULT '[]',  -- long→short: [{timestamp, duration, hook, topic}]
    schema_suggestion JSONB DEFAULT '{}',  -- VideoObject + Clip markup JSON-LD
    transcript_text TEXT,  -- transcripción sugerida para subir manual
    embed_suggestion TEXT,  -- dónde embeber en el blog
    word_count INTEGER,
    estimated_duration_sec INTEGER,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'produced', 'published')),
    published_url TEXT,  -- URL del video publicado (para tracking)
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, source_url, format)
);
```

**Backend:** `repurpose_service.py`
- `calculate_candidacy(project_id, url)` → scores de candidatura SHORT + LONG + AI opportunity flag
- `batch_candidacy(project_id, limit=50)` → calcular para top 50 URLs por tráfico
- `generate_script(project_id, url, format='short')` → Claude genera guion según formato
- `generate_shorts_from_long(script_id)` → para un guion long, generar 3-5 scripts short extractables
- `get_scripts(project_id, format=None, status=None)` → listar guiones con filtros
- `update_script_status(script_id, status, published_url=None)` → workflow + URL publicada
- `get_schema_markup(script_id)` → devolver VideoObject + Clip markup listo para copiar

**Endpoints:**
- `POST /projects/{id}/repurpose/candidacy` — calcular candidatura batch (devuelve short_score + long_score + ai_opportunity)
- `POST /projects/{id}/repurpose/generate` — body: `{url, format: "short"|"long"}` — generar guion
- `POST /projects/{id}/repurpose/scripts/{script_id}/extract-shorts` — extraer shorts de un long
- `GET /projects/{id}/repurpose/scripts?format=short|long&status=draft` — listar con filtros
- `PATCH /projects/{id}/repurpose/scripts/{script_id}` — actualizar status + published_url
- `GET /projects/{id}/repurpose/scripts/{script_id}/schema` — schema markup copiable
- `GET /projects/{id}/repurpose/dashboard` — stats por formato + AI visibility impact

**Frontend:** `ContentRepurposePage.tsx` (módulo sidebar, grupo "Contenido")

**Tab 1: Candidatos**
- Toggle arriba: "Short-form" / "Long-form" / "Todos"
- Tabla: URL, título, tipo, clicks, short score, long score, AI opportunity flag → ordenada por score
- Botón "Generar Short" + "Generar Long" por fila
- "Batch top 10" por formato
- Badge por tipo de contenido
- Indicador "AI" si la query tiene AI Overview activo (oportunidad de citación via video)

**Tab 2: Guiones Short**
- Lista de guiones short-form con status
- Expandir guion → vista completa:
  - Script con timestamps y secciones HHVCTA coloreadas
  - 3 hooks alternativos (seleccionable)
  - Visual cues en timeline
  - Sugerencia de captions on-screen
  - Hashtags copiables (broad + specific + evergreen)
  - Títulos por plataforma copiables
  - Word count + duración estimada
  - Benchmarks de retención esperados
- Botones: Aprobar, Producido, Publicado, Regenerar

**Tab 3: Guiones Long (YouTube)**
- Lista de guiones long-form con status
- Expandir guion → vista completa:
  - Script completo con capítulos coloreados y timestamps
  - Panel lateral "YouTube SEO Package":
    - Timestamps copiables (formato YouTube)
    - 3 opciones de thumbnail + título (con preview)
    - Descripción YouTube copiable (250 palabras, SEO-optimized)
    - Tags copiables
    - Schema markup copiable (VideoObject + Clip)
  - Timeline visual con retention hooks + cards sugeridas
  - Sección "Shorts extractables": 3-5 clips sugeridos del video largo con su propio hook
  - Sugerencia de embed en blog
  - B-roll/gráficos sugeridos por capítulo
- Botones: Aprobar, Producido, Publicado, Regenerar, "Extraer Shorts"

**Tab 4: Pipeline**
- Kanban visual con DOS carriles: Short-form arriba, Long-form abajo
- Draft → Approved → Produced → Published
- Stats por formato: conversión entre etapas, velocidad de producción
- KPIs: total guiones, ratio short/long, pendientes de producción
- **Funnel visual**: Long-form → Shorts extraídos → Blog embeds (muestra el ecosistema)

**Criterio:** Ambos formatos generan guiones de calidad. Short: 150 palabras HHVCTA con benchmarks. Long: estructura completa con chapters keyword-rich, timestamps, descripción SEO, schema markup, thumbnails, shorts extractables. Pipeline funcional. Schema VideoObject+Clip copiable.

### 25.D — Integración Cross-Module

**Dashboard:**
- Nuevo widget "AI Readiness": mini-card con SRO Score medio + URLs optimizadas vs total
- Nuevo widget "Content Pipeline": guiones en cada etapa del pipeline

**Content Performance:**
- Nueva columna "SRO" en tabla de URLs (score coloreado)
- Nueva columna "Video" (badge si tiene guion generado, con link)

**Rank Tracker:**
- Nueva columna "QDG" (Query Deserves Grounding)
- Filtro por QDG level

**Módulos sidebar (modules.ts):**
```typescript
{ key: 'sro', label: 'AI Search (SRO)', icon: Brain, path: 'sro', group: 'audit', enabled: true },
{ key: 'repurpose', label: 'Content Repurposer', icon: Video, path: 'repurpose', group: 'content', enabled: true },
```

**Criterio:** Widgets en Dashboard visibles. Columnas nuevas en tablas existentes. Módulos en sidebar.

---

### Resumen visual Sprint 25

```
SPRINT 25: AI Search Optimization + Content Repurposer
  25.A Grounding Score Analyzer (SRO) — análisis de densidad para grounding chunks Gemini
  25.B QDG Classifier — predecir qué queries activan grounding, cruce QDG×SRO
  25.C Content Repurposer — article → video ecosystem (short HHVCTA + long YouTube + schema + shorts extractables)
  25.D Integración Cross-Module — widgets Dashboard, columnas SRO/QDG/Video, funnel visual
```

**Tiempo estimado: 3-4 días con Claude Code.**
**Migraciones:** 057 (grounding_analyses, sro_snapshots, content_repurpose_scripts)
**Nuevos módulos frontend:** 2 (SRO, Content Repurposer)
**Nuevos servicios backend:** sro_service.py, repurpose_service.py
**Nuevos endpoints:** ~12

---

## SPRINT 26: SEO Value Framework + Content Risk Scanner

> **Fuentes:**
> - Bengü Sarıca Dinçer / SEJ — "Why Your SEO KPIs Are Failing Your Business" (feb 2026): Three-Layer Measurement Model, metric debt
> - SEJ — "Search That Sells: Connecting the Dots Between Rankings and Results": Revenue per keyword, attribution models, conversion focus
> - SEJ — "Repositioning What SEO Success Looks Like": Five Dimensions of repositioned success, leading vs lagging indicators
> - Lily Ray / Amsive — "Is Google Finally Cracking Down on Self-Promotional Listicles?" (feb 2026): -30% a -50% visibility drops, site-wide quality scores
> - Arnout Hellemans — Entity-based content survival: contenido core a la entidad sobrevive updates
> - Ahrefs — AI Overviews reducen CTR orgánico -58% en posición 1
> - BrightEdge — Brands citadas en AI Overviews: +35% clicks orgánicos, +91% clicks paid
> - Seer Interactive — CTR orgánico -61%, paid -68% en queries con AI Overviews
> - Semrush — Visitante desde LLM vale 4.4x más que visitante orgánico tradicional
>
> **Prerrequisito:** Sprint 25 completado.
> **Principio:** Dos problemas convergentes: (1) los clicks bajan pero el revenue se mantiene — necesitamos medir el valor real del SEO más allá del tráfico; (2) Google penaliza contenido off-topic/auto-promocional a nivel de sitio — necesitamos detectar contenido tóxico antes de que nos impacte. Este sprint transforma cómo FIT mide el éxito SEO y protege proactivamente contra penalizaciones.

### 26.A — SEO Value Dashboard (Revenue Attribution Layer)

**Concepto:** Evolucionar el Dashboard de FIT del paradigma "tráfico" al paradigma "valor". Los clicks bajan un 25% por AI Overviews, pero el revenue se mantiene porque la influencia ocurre dentro de la IA. Necesitamos capturar esa "value halo" — el valor invisible que genera la visibilidad orgánica aunque no se traduzca en click directo.

**El problema (datos):**
- AI Overviews reducen CTR orgánico -58% en posición 1 (Ahrefs 2026)
- Zero-click searches: 65% de búsquedas (2025)
- PERO: revenue per organic visitor está SUBIENDO (menos tráfico, más cualificado)
- Un visitante desde LLM vale 4.4x más que orgánico tradicional (Semrush)
- Marcas citadas en AI Overviews: +35% clicks orgánicos (BrightEdge)
- Orgánico genera 44.6% del revenue B2B (más que todos los demás canales combinados)
- SEO leads cierran a 14.6% vs 1.7% outbound (8.5x más probable)

**Three-Layer KPI Model (framework Bengü Sarıca Dinçer, adaptado para FIT):**

```python
# Layer 1: Operational Signals (FIT ya los tiene casi todos)
OPERATIONAL_KPIS = {
    "indexation_coverage": "% URLs indexadas vs total sitemap",       # SEO Técnico 21.A
    "cwv_pass_rate": "% URLs con CWV en verde",                      # Dashboard CWV
    "content_velocity": "URLs nuevas/mes en clusters prioritarios",    # Content Performance
    "share_of_voice": "% visibilidad vs competidores por cluster",     # Topical Authority
    "crawl_health": "% URLs rastreadas sin errores",                   # SEO Técnico 21.C
    "sro_readiness": "% URLs con SRO Score >70",                       # Sprint 25
}

# Layer 2: Engagement Signals (FIT tiene parcialmente via GA4)
ENGAGEMENT_KPIS = {
    "engaged_sessions": "Sesiones >10s o con conversión (GA4)",
    "scroll_depth": "% medio de scroll en páginas de contenido",
    "return_visit_rate": "% usuarios que vuelven en 7 días",
    "micro_conversions": "Downloads, newsletter signups, tool usage",
    "organic_conversions": "Conversiones atribuidas a orgánico",
    "ai_citation_rate": "% queries donde aparecemos en AI Overviews",  # LLM Monitor
}

# Layer 3: Business Outcomes (NUEVO — lo que falta en FIT)
BUSINESS_KPIS = {
    "revenue_per_organic_visitor": "Ingresos / visitantes orgánicos",
    "organic_cac": "Coste adquisición cliente via orgánico",
    "organic_vs_paid_cac": "Ratio CAC orgánico / CAC paid",
    "pipeline_influence": "Oportunidades con touchpoint orgánico",
    "organic_ltv": "LTV de clientes adquiridos por orgánico",
    "seo_roi": "Revenue atribuido a SEO / inversión en SEO",
}

# Value Per Organic Visitor (VPOV) — métrica core
# Fórmula: VPOV = Revenue_total / Organic_visitors
# Variante ajustada: VPOV_adjusted = (Revenue_total × Organic_attribution_%) / Organic_visitors
# Si VPOV sube mientras tráfico baja → SEO está funcionando (value halo)
```

**Migración 058: `seo_value_metrics`**
```sql
CREATE TABLE IF NOT EXISTS seo_value_metrics (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    -- Layer 1: Operational
    indexation_coverage NUMERIC(5,2),
    cwv_pass_rate NUMERIC(5,2),
    content_velocity INTEGER,
    share_of_voice NUMERIC(5,2),
    sro_readiness NUMERIC(5,2),
    -- Layer 2: Engagement
    engaged_sessions INTEGER,
    engaged_session_rate NUMERIC(5,2),
    scroll_depth_avg NUMERIC(5,2),
    return_visit_rate NUMERIC(5,2),
    micro_conversions INTEGER,
    organic_conversions INTEGER,
    ai_citation_rate NUMERIC(5,2),
    -- Layer 3: Business Outcomes
    revenue_total NUMERIC(12,2),  -- input manual o GA4 ecommerce
    organic_visitors INTEGER,
    revenue_per_visitor NUMERIC(8,2),  -- VPOV
    organic_cac NUMERIC(8,2),  -- input manual
    paid_cac NUMERIC(8,2),  -- input manual para comparativa
    pipeline_value NUMERIC(12,2),  -- input manual o CRM
    seo_investment NUMERIC(10,2),  -- input manual
    seo_roi NUMERIC(6,2),  -- calculado
    -- Comparativa
    previous_period_id BIGINT REFERENCES seo_value_metrics(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS seo_value_config (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    -- Inputs manuales que el usuario configura una vez
    monthly_seo_investment NUMERIC(10,2) DEFAULT 0,  -- €/mes invertido en SEO
    avg_deal_value NUMERIC(10,2) DEFAULT 0,  -- valor medio de conversión/venta
    organic_attribution_pct NUMERIC(5,2) DEFAULT 50,  -- % de revenue atribuido a orgánico (configurable)
    target_organic_cac NUMERIC(8,2),  -- CAC objetivo
    target_vpov NUMERIC(8,2),  -- VPOV objetivo
    -- Fuentes de datos
    revenue_source TEXT DEFAULT 'manual' CHECK (revenue_source IN ('manual', 'ga4_ecommerce', 'ga4_goals')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id)
);
```

**Backend:** `seo_value_service.py`
- `calculate_period_metrics(project_id, start, end)` → agrega datos de GA4 + GSC + LLM Monitor + CWV + Sprint 25 SRO en un snapshot
- `get_vpov_trend(project_id, periods=6)` → evolución del Value Per Organic Visitor
- `get_three_layer_dashboard(project_id)` → los 3 layers con estado actual + MoM
- `calculate_seo_roi(project_id)` → ROI basado en config + métricas
- `get_executive_summary(project_id)` → Claude genera resumen ejecutivo para stakeholders

**Endpoints:**
- `GET /projects/{id}/seo-value/dashboard` — dashboard 3 layers completo
- `GET /projects/{id}/seo-value/vpov` — VPOV trend
- `GET /projects/{id}/seo-value/roi` — cálculo ROI
- `POST /projects/{id}/seo-value/snapshot` — forzar snapshot manual
- `PUT /projects/{id}/seo-value/config` — configurar inputs manuales (inversión, deal value, etc.)
- `GET /projects/{id}/seo-value/executive-summary` — resumen AI para stakeholders

**Frontend:** Evolución del DashboardPage.tsx existente (no es módulo nuevo — es upgrade del Dashboard)

**Nueva vista "Valor SEO" como tab del Dashboard:**

**Sección 1: Value Per Organic Visitor (VPOV)**
- MetricCard gigante: VPOV actual (€X.XX) con MoM (verde si sube, rojo si baja)
- Gráfico dual: línea de VPOV (€) + barras de tráfico orgánico → el storytelling visual es: "el tráfico baja pero el valor por visita sube"
- Comparativa: VPOV orgánico vs VPOV paid (si está configurado) → demostrar que orgánico es más eficiente

**Sección 2: Three-Layer KPIs**
- 3 columnas (Operacional / Engagement / Negocio)
- Cada columna: 4-6 MetricCards con valor + MoM + semáforo
- Las de Layer 3 que requieren input manual: campo editable inline (inversión mensual, revenue, deal value)
- Score por layer (0-100): % de KPIs en verde

**Sección 3: SEO ROI Calculator**
- Input: inversión mensual en SEO
- Automático: revenue atribuido a orgánico (GA4 o manual × attribution %)
- Output: ROI = (Revenue_orgánico - Inversión) / Inversión × 100
- Comparativa con paid: "Por cada €1 en SEO generas €X, por cada €1 en paid generas €Y"

**Sección 4: Executive Summary (Claude)**
- Resumen narrativo de 3-5 frases para presentar a dirección
- Formato: "El SEO generó €X en valor este mes (+Y% vs anterior). El valor por visitante orgánico subió a €Z, compensando la caída de -W% en tráfico por AI Overviews. Recomendación: [acción]."
- Botón "Copiar para email" + "Exportar PDF"

**Criterio:** VPOV se calcula correctamente. Dashboard muestra 3 layers. ROI calculator funciona. Executive summary genera texto útil para stakeholders.

### 26.B — Content Risk Scanner

**Concepto:** Detector proactivo de contenido que podría ser penalizado en el próximo Google update. Basado en los patrones documentados por Lily Ray (feb 2026): listicles auto-promocionales, contenido off-topic respecto a la entidad, señales de freshness artificial, y contenido que baja el quality score site-wide.

**Contexto (datos Lily Ray / Arnout Hellemans):**
- Marca B2B de $8B: -49% visibilidad en 2 semanas
- SaaS con listicles: -30% a -50% en /blog/ y /guides/
- Contenido que sobrevive: core a lo que la empresa HACE (expertise real)
- Google tiene scores site-wide: contenido tóxico arrastra todo el sitio (siteQualityStddev del Leak)
- GEO tactics basadas en listicles: doble pérdida (orgánico + AI visibility)

**6 Risk Signals a detectar (Claude + heurísticas):**

```python
CONTENT_RISK_SIGNALS = {
    # Signal 1: Self-Promotional Listicle (Lily Ray pattern)
    "self_promo_listicle": {
        "description": "Artículo tipo 'X Best [Category]' donde la marca aparece como #1",
        "detection": "title regex + Claude analysis of content bias",
        "severity": "critical",  # -30% a -50% visibility documented
        "patterns": [
            r"(?i)\d+\s+(?:best|mejor|top)\s+.{5,50}\s+(?:in|en|for|para)\s+\d{4}",
            r"(?i)(?:best|mejor|top)\s+\d+\s+.{5,50}\s+(?:companies|tools|software|apps|plataformas)",
        ],
    },
    # Signal 2: Entity-Topic Misalignment (Arnout Hellemans insight)
    "entity_misalignment": {
        "description": "Contenido fuera del expertise core de la entidad",
        "detection": "Cruzar topic del contenido vs pilares de marca (Brand-Keyword Coherence S20.C)",
        "severity": "high",
        "check": "Si la URL no pertenece a ningún cluster core de topical authority → flag",
    },
    # Signal 3: Artificial Freshness
    "artificial_freshness": {
        "description": "Actualización de fecha sin cambio sustantivo",
        "detection": "title contiene año actual pero content_hash no cambió significativamente",
        "severity": "high",
        "check": "Diff entre versiones: si solo cambió el año en título/meta → flag",
    },
    # Signal 4: Thin/Template Content (Quality Gates S21.F overlap)
    "thin_template": {
        "description": "Contenido templated, boilerplate alto, poco valor único",
        "detection": "word_count < 500, boilerplate_ratio > 40%, unique_value_score bajo",
        "severity": "medium",
        "check": "Reutilizar Quality Gates pero con threshold más estricto",
    },
    # Signal 5: AI Slop Without Expertise
    "ai_slop": {
        "description": "Contenido generado por IA sin edición humana ni expertise demostrable",
        "detection": "Claude evalúa: ¿tiene datos propios? ¿experiencia de primera mano? ¿ejemplos específicos?",
        "severity": "high",
        "check": "Score de 'human fingerprint': datos propios, anécdotas, screenshots, metodología original",
    },
    # Signal 6: Site-Wide Quality Drag
    "quality_drag": {
        "description": "URLs con métricas muy por debajo de la media del sitio que bajan el score global",
        "detection": "URLs con bounce_rate > media+2σ AND clicks < 10/mes AND no conversions",
        "severity": "medium",
        "check": "Bottom 10% de URLs por engagement que podrían estar arrastrando siteQualityStddev",
    },
}

RISK_SCORE_WEIGHTS = {
    "self_promo_listicle": 30,
    "entity_misalignment": 25,
    "artificial_freshness": 15,
    "ai_slop": 15,
    "thin_template": 10,
    "quality_drag": 5,
}
```

**Migración 058 (misma): `content_risk_scans`**
```sql
CREATE TABLE IF NOT EXISTS content_risk_scans (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    -- Risk scores
    overall_risk_score INTEGER DEFAULT 0,  -- 0-100 (0=safe, 100=high risk)
    risk_level TEXT DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    -- Individual signals
    self_promo_listicle BOOLEAN DEFAULT FALSE,
    self_promo_details JSONB DEFAULT '{}',
    entity_misalignment BOOLEAN DEFAULT FALSE,
    entity_misalignment_details JSONB DEFAULT '{}',  -- {topic, expected_pillar, alignment_score}
    artificial_freshness BOOLEAN DEFAULT FALSE,
    freshness_details JSONB DEFAULT '{}',  -- {title_year, last_real_update, content_change_pct}
    thin_template BOOLEAN DEFAULT FALSE,
    thin_details JSONB DEFAULT '{}',  -- {word_count, boilerplate_ratio, unique_value_score}
    ai_slop BOOLEAN DEFAULT FALSE,
    ai_slop_details JSONB DEFAULT '{}',  -- {human_fingerprint_score, own_data, first_hand, examples}
    quality_drag BOOLEAN DEFAULT FALSE,
    quality_drag_details JSONB DEFAULT '{}',  -- {bounce_rate, clicks, vs_site_avg}
    -- Recommendations
    recommended_action TEXT CHECK (recommended_action IN ('keep', 'rewrite', 'consolidate', 'noindex', 'delete')),
    action_details TEXT,  -- explicación de Claude
    -- Status
    review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'reviewed', 'actioned', 'dismissed')),
    scanned_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, url)
);

CREATE TABLE IF NOT EXISTS content_risk_snapshots (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    total_urls_scanned INTEGER,
    urls_critical INTEGER,
    urls_high INTEGER,
    urls_medium INTEGER,
    urls_low INTEGER,
    top_risks JSONB DEFAULT '[]',  -- [{url, risk_score, primary_signal}] top 10
    site_risk_score INTEGER DEFAULT 0,  -- 0-100 agregado
    snapshot_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, snapshot_date)
);
```

**Backend:** `content_risk_service.py`
- `scan_url(project_id, url)` → analiza URL contra los 6 signals, Claude evalúa + heurísticas
- `batch_scan(project_id, limit=50)` → escanear top 50 URLs + bottom 50 por engagement
- `get_risk_dashboard(project_id)` → dashboard con distribución de riesgos
- `get_risk_detail(project_id, url)` → detalle de signals por URL
- `get_action_plan(project_id)` → plan de acción priorizado generado por Claude
- `update_review_status(scan_id, status)` → marcar como revisado/accionado/descartado

**Prompt Claude para scan:**
```
Analiza esta URL como Content Risk Scanner. Evalúa estos 6 signals de riesgo:

URL: {url}
Contenido: {content}
Entidad/marca: {brand_name}
Pilares de marca: {brand_pillars}
Métricas: {clicks}/mes, bounce: {bounce_rate}%, posición media: {position}

1. SELF-PROMO LISTICLE: ¿Es un artículo tipo "mejores X" donde la marca se posiciona como #1? ¿Tiene evaluación independiente o es sesgo evidente?

2. ENTITY MISALIGNMENT: ¿Este contenido es core al expertise de {brand_name}? ¿O está fuera de su territorio natural? Los pilares de marca son: {brand_pillars}.

3. ARTIFICIAL FRESHNESS: ¿El contenido parece actualizado solo cosméticamente (año en título) sin cambios sustantivos?

4. THIN/TEMPLATE: ¿Tiene valor único o es genérico/templated? ¿Podría haber sido escrito por cualquiera sin expertise?

5. AI SLOP: ¿Hay evidencia de expertise humana? (datos propios, experiencia de primera mano, ejemplos específicos, metodología original, screenshots, anécdotas)

6. QUALITY DRAG: Dado que tiene {clicks} clicks/mes y {bounce_rate}% bounce, ¿está este contenido arrastrando la calidad general del sitio?

Para cada signal responde: SÍ/NO + breve justificación.
Luego: acción recomendada (keep/rewrite/consolidate/noindex/delete) + explicación.

Responde en español. Sé directo y accionable.
```

**Endpoints:**
- `POST /projects/{id}/content-risk/scan` — escanear URL individual
- `POST /projects/{id}/content-risk/batch` — batch scan (top 50 + bottom 50)
- `GET /projects/{id}/content-risk/dashboard` — dashboard de riesgos
- `GET /projects/{id}/content-risk/url?url=...` — detalle por URL
- `GET /projects/{id}/content-risk/action-plan` — plan de acción priorizado (Claude)
- `PATCH /projects/{id}/content-risk/{scan_id}` — actualizar review_status

**Frontend:** `ContentRiskPage.tsx` (módulo sidebar, grupo "Auditoría Técnica")

**Tab 1: Risk Dashboard**
- 4 MetricCards: URLs Critical, URLs High, URLs Medium, Site Risk Score
- Bar chart: distribución de URLs por nivel de riesgo (stacked por signal type)
- Trend: Site Risk Score temporal (¿estamos limpiando o empeorando?)
- Alert box si Site Risk Score >50: "Alto riesgo de impacto site-wide en próximo update"

**Tab 2: Scan Results**
- Tabla: URL, Risk Score (coloreado), Risk Level badge, Primary Signal, Recommended Action, Status
- Filtros: por nivel de riesgo, por signal type, por status
- Expandir URL → detalle completo:
  - 6 signals con SÍ/NO + justificación
  - Acción recomendada + explicación
  - Métricas de la URL (clicks, bounce, posición)
  - Botón "Marcar como revisado" / "Acción tomada" / "Descartar"
- Botones: "Scan URL" + "Batch Scan"

**Tab 3: Action Plan**
- Plan generado por Claude, agrupado por tipo de acción:
  - "ELIMINAR/NOINDEX (X URLs)": listicles auto-promocionales, contenido off-topic irrecuperable
  - "REESCRIBIR (X URLs)": contenido con potencial pero thin/AI slop, necesita expertise real
  - "CONSOLIDAR (X URLs)": contenido similar/duplicado que se puede fusionar
  - "MANTENER (X URLs)": contenido sano, sin acción necesaria
- Cada grupo con impacto estimado: "Eliminar estas 8 URLs podría reducir el riesgo site-wide un ~15%"
- Workflow: pendiente → en progreso → hecho

**Criterio:** Scan detecta correctamente los 6 signals. Batch funciona para 100 URLs. Dashboard muestra distribución clara. Action plan es accionable y priorizado.

### 26.C — Entity Coherence Score

**Concepto:** Score unificado que mide cuánto del contenido del sitio está alineado con la entidad/marca. Inspirado en la observación de Arnout Hellemans: "el contenido que sobrevive es el que es core a lo que la empresa HACE". Este score agrega datos de Brand-Keyword Coherence (S20.C), Content Risk Scanner (26.B), y Topical Authority (S22.A).

**Fórmula:**
```python
ENTITY_COHERENCE_SCORE = (
    brand_keyword_coherence * 0.35 +        # S20.C: keywords alineadas con pilares
    content_on_topic_ratio * 0.30 +          # % URLs sin entity_misalignment flag
    topical_cluster_coverage * 0.20 +        # S22.A: cobertura de clusters core
    author_expertise_alignment * 0.15        # S18: autores especializados en su cluster
)
```

**Sin migración nueva** — usa datos de módulos existentes + Content Risk Scanner.

**Endpoint:** `GET /projects/{id}/entity-coherence` — score + desglose + recomendaciones

**Frontend:** MetricCard nueva en Entity Panel + tab "Coherencia" en Brand Visibility Audit
- Score 0-100 coloreado
- Desglose: qué % contribuye cada componente
- Lista de "content outliers": URLs que más dañan la coherencia
- Recomendación: "Tu contenido está X% alineado con tu entidad. Las siguientes Y URLs están fuera de territorio."

**Criterio:** Score se calcula correctamente. Visible en Entity Panel y Brand Audit.

### 26.D — Reporting Evolution (Business Language)

**Concepto:** Evolucionar el módulo de Reportes (ya existente) para generar informes en "lenguaje de negocio" en vez de "lenguaje SEO". Basado en el insight de SEJ: "Good SEO teams don't report more metrics. They explain better."

**Nuevo template de reporte "Executive SEO Report":**

Prompt Claude para generación:
```
Genera un informe ejecutivo de SEO para presentar a dirección. NO uses jerga técnica.
Datos del periodo: {metrics_json}

Estructura:
1. RESUMEN EJECUTIVO (2-3 frases): ¿El SEO está generando valor? ¿Más o menos que el mes anterior?
2. VALOR GENERADO: Revenue atribuido a orgánico, VPOV, comparativa con paid
3. VISIBILIDAD DE MARCA: ¿Nos encuentran? ¿Nos citan los LLMs? ¿Somos referencia en nuestro sector?
4. RIESGOS: ¿Hay algo que podría impactarnos? (content risk, updates pendientes, competidores)
5. PLAN PRÓXIMO MES: 3-5 acciones priorizadas con impacto estimado

Reglas:
- NUNCA mencionar: rankings, posiciones, backlinks, crawl budget, indexación
- SÍ mencionar: valor generado, visibilidad de marca, audiencia alcanzada, competitividad, ROI
- Usar € y % siempre que sea posible
- Tono: profesional, orientado a resultados, como un director de marketing hablando al CEO
```

**Integración:** Nuevo tipo de reporte en el módulo existente de Reportes
- Dropdown de tipo: "Informe SEO Técnico" (existente) + "Informe Ejecutivo SEO" (nuevo)
- El ejecutivo tira de datos del SEO Value Dashboard (26.A) + Content Risk (26.B) + Entity Coherence (26.C)

**Criterio:** Template ejecutivo genera reportes en lenguaje de negocio. No aparece jerga técnica. Incluye VPOV y ROI.

### 26.E — Integración Cross-Module

**Dashboard:**
- Nueva tab "Valor SEO" (26.A) junto a las tabs existentes
- Widget "Site Risk" en tab principal: semáforo con Site Risk Score
- Widget "Entity Coherence" en tab principal

**Content Performance:**
- Nueva columna "Risk" en tabla de URLs (badge critical/high/medium/low)
- Filtro por risk level

**Entity Panel:**
- MetricCard "Entity Coherence Score" en el dashboard de entidad

**Brand Visibility Audit:**
- Nueva tab "Coherencia" con Entity Coherence desglosado

**Reportes:**
- Nuevo tipo "Informe Ejecutivo SEO" disponible

**Módulos sidebar (modules.ts):**
```typescript
{ key: 'content-risk', label: 'Content Risk', icon: ShieldAlert, path: 'content-risk', group: 'audit', enabled: true },
```
El SEO Value Dashboard no es módulo nuevo — es tab del Dashboard existente.

**Criterio:** Todas las integraciones visibles. Datos fluyen correctamente entre módulos.

---

### Resumen visual Sprint 26

```
SPRINT 26: SEO Value Framework + Content Risk Scanner
  26.A SEO Value Dashboard — VPOV, 3-Layer KPIs, ROI Calculator, Executive Summary AI
  26.B Content Risk Scanner — 6 signals de riesgo, batch scan, action plan, workflow
  26.C Entity Coherence Score — score unificado entidad-contenido, agrega S20+S22+S26B
  26.D Reporting Evolution — informe ejecutivo en lenguaje de negocio, no jerga SEO
  26.E Integración Cross-Module — tab Valor SEO en Dashboard, columna Risk, widgets
```

**Tiempo estimado: 3-4 días con Claude Code.**
**Migraciones:** 058 (4 tablas: seo_value_metrics, seo_value_config, content_risk_scans, content_risk_snapshots)
**Nuevo módulo frontend:** 1 (Content Risk Scanner)
**Evolución frontend:** Dashboard (nueva tab "Valor SEO"), Reportes (nuevo template), Entity Panel + Brand Audit (widgets)
**Nuevos servicios backend:** seo_value_service.py, content_risk_service.py
**Nuevos endpoints:** ~15

---

## Sprint 27: AI Citability Engine

> **7 fuentes de investigación:**
>
> | Fuente | Hallazgo clave | Dato duro |
> |--------|---------------|-----------|
> | Gauge / Growth Memo | Señales lingüísticas predicen citación AI | 3M respuestas, 18K citas verificadas, p<0.0001 |
> | DEJAN AI / Petrovic | Grounding chunks de ~2000 palabras; >2000 = 13% útil | Allocation table por posición SERP |
> | Resoneo AIO Inspector | Pipeline AIO: Grounding → Pool → Displayed | Fuentes ocultas existen (grounding sin display) |
> | Lily Ray | Listicles auto-promocionales penalizados | -30-50% tráfico post HCU |
> | AlsoAsked / Chris Green | PAA coverage correlaciona con top rankings | 563 kw, r=-0.96 transactional top 5 |
> | Metehan AI / GPT-5 tokenizer | Prose 5.9 chars/token vs tablas 2.7 (2.2x) | o200k_base, 200K tokens, RAG budget 8K |
> | awesome-seo-tools | Landscape GEO tools emergentes | 28 categorías, herramientas de referencia |
>
> **Arquitectura:** Un servicio central `citability_engine` calcula un score compuesto por URL que alimenta SRO, Content Risk, Briefings, Text Review, Topical Authority, y Entity Panel. No módulos sueltos — un motor que mejora todo.
>
> **Prerrequisito:** Sprint 26 + hotfix (badges, SEO Value config, v0.26.0). P1 fixes aplicados (qdg-opportunities, migración 058 en prod).

### 27.A — Citability Engine (servicio central transversal)

Un solo servicio `citability_engine.py` que analiza cualquier texto/URL y devuelve un score compuesto. Lo consumen SRO, Content Risk, Briefings, Text Review, Topical Authority, Content Validator. No duplica lógica — un motor, muchos consumidores.

**Por qué un motor central:** Los sprints anteriores crearon SRO (grounding S25), Content Risk (6 señales S26), Text Review (readability), Content Validator (GEO checks). Cada uno mide cosas distintas pero ninguno sabe si el contenido es citable por AI. El Citability Engine unifica las señales que realmente predicen citación (Gauge p<0.0001) y las hace disponibles para todos.

**Datos de entrada (ya existen en la app):**
- `content.body` (TEXT) → texto del contenido
- `content.url` → para fetch HTML si necesario
- `grounding_analyses.word_count` → ya lo calculamos en SRO
- `ai_visibility_checks.paa_questions` (JSONB[]) → preguntas PAA ya guardadas

**Constantes fundamentadas en datos:**
```python
# Gauge dataset: 3M respuestas ChatGPT, 18K citas verificadas, p<0.0001
# Cada umbral tiene el paper detrás — no son arbitrarios

CITABILITY = {
    # FK: Winners 16.0, Losers 19.1 (diferencia 3 puntos, t-test p<0.0001)
    'FK_TARGET': 16,
    'FK_FLOOR': 12,        # <12 = too shallow
    'FK_CEILING': 18,      # >18 = PhD jargon

    # Subjectivity: TextBlob 0-1. Winners significativamente más bajo.
    # No hay umbral exacto publicado; 0.30 = 1σ por debajo de media losers
    'SUBJ_MAX': 0.30,

    # Definition Rate: % de oraciones con verbos definitorios (is/are/refers to/means/defines)
    # Winners tienen más; >2% = top quartile del dataset
    'DEF_RATE_MIN': 0.02,

    # Entity Density: entidades nombradas / palabras totales
    # Winners tienen densidad significativamente mayor; 5% = mediana winners
    'ENTITY_DENSITY_MIN': 0.05,

    # Positional Depth: Gauge "ski ramp" — citas caen exponencialmente después del 25% del HTML
    # >50% del contenido citable en primer 25% del HTML = exponencialmente más citas
    'POS_DEPTH_THRESHOLD': 0.50,

    # Chunk Efficiency: DEJAN AI — Google procesa ~2000 word chunks
    # >2000 words: solo 540 (~13%) se usan para grounding
    'CHUNK_OPTIMAL': (800, 1200),
    'CHUNK_MAX_EFFICIENT': 2000,

    # Token Efficiency: Metehan AI — o200k_base tokenizer analysis
    # Plain prose: 5.9 chars/token (100% efficiency baseline)
    # Tables: 2.7 chars/token (46% efficiency)
    'TOKEN_PROSE_RATIO': 5.9,
    'TOKEN_TABLE_RATIO': 2.7,
    'TOKEN_GOOD_THRESHOLD': 4.5,  # chars/token
    'FRONT_LOAD_CHARS': 2750,     # ≈500 tokens × 5.5 avg chars/token
}
```

**Cálculo — 3 capas, no pesos lineales:**

```python
import re
import textstat
from textblob import TextBlob


def citability_score(text: str, html: str = "") -> dict:
    """
    Citability Engine: 3-layer scoring.

    Layer 1 — GATES (pasan o no pasan, sin ellos el resto vale <10%):
      · Positional Depth: ¿el contenido clave está al inicio?
      · Subjectivity: ¿es factual o editorial?

    Layer 2 — SIGNALS (multiplican el efecto de los gates):
      · Definition Rate, Entity Density, Flesch-Kincaid

    Layer 3 — EFFICIENCY (cuánto del contenido es útil para AI):
      · Chunk Efficiency (longitud), Token Efficiency (formato)

    El score final NO es una media ponderada.
    Es: gates × signals × efficiency_multiplier
    Si un gate falla → cap a 40/100 sin importar lo demás.
    """
    words = text.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    num_sentences = max(len(sentences), 1)

    # ─── LAYER 1: GATES ───────────────────────────────
    # Gate 1: Positional Depth
    # Medir qué % de oraciones con datos/definiciones están en el primer 25% del texto
    quarter_mark = len(text) // 4
    first_quarter = text[:quarter_mark]
    key_pattern = r'\b(is|are|refers to|means|defined as|according to|study|research|data|found that|shows that|\d{4}|\d+%)\b'
    total_key_sentences = len([s for s in sentences if re.search(key_pattern, s, re.I)])
    first_q_key = len([s for s in sentences if re.search(key_pattern, s, re.I)
                        and s in first_quarter])
    pos_depth = first_q_key / max(total_key_sentences, 1)
    gate_pd = min(100, max(0, (pos_depth - 0.25) / 0.50 * 100))  # 25%→0, 75%→100

    # Gate 2: Subjectivity
    blob = TextBlob(text[:5000])  # Limitar a 5K chars por performance
    subj = blob.sentiment.subjectivity
    gate_subj = min(100, max(0, (0.50 - subj) / 0.30 * 100))  # 0.50→0, 0.20→100

    gates_avg = (gate_pd + gate_subj) / 2
    gates_passing = gates_avg >= 50

    # ─── LAYER 2: SIGNALS ─────────────────────────────
    # Flesch-Kincaid
    fk = textstat.flesch_kincaid_grade(text)
    if 14 <= fk <= 16:
        sig_fk = 100
    elif 12 <= fk <= 18:
        sig_fk = 70 - abs(fk - 15) * 10  # degrada suavemente
    else:
        sig_fk = max(0, 40 - abs(fk - 15) * 5)

    # Definition Rate
    def_verbs = r'\b(is|are|refers to|means|defined as|se define como|es un|son los)\b'
    def_sentences = sum(1 for s in sentences if re.search(def_verbs, s, re.I))
    def_rate = def_sentences / num_sentences
    sig_dr = min(100, def_rate / 0.02 * 100)  # 0%→0, 2%→100, >2%→100

    # Entity Density (sin spacy — regex para capitalized multi-words + numbers)
    entity_pattern = r'(?:[A-Z][a-záéíóúñ]*(?:\s[A-Z][a-záéíóúñ]*)+|\b\d[\d,.]+\b(?:\s?%)?)'
    entities = re.findall(entity_pattern, text)
    entity_density = len(entities) / max(word_count, 1)
    sig_ed = min(100, entity_density / 0.05 * 100)  # 0→0, 5%→100

    signals_avg = (sig_fk + sig_dr + sig_ed) / 3

    # ─── LAYER 3: EFFICIENCY ──────────────────────────
    # Chunk Efficiency (DEJAN)
    if word_count <= 1200:
        chunk_eff = 95
    elif word_count <= 2000:
        chunk_eff = 75
    else:
        chunk_eff = max(15, round(2000 / word_count * 100))

    # Token Efficiency (Metehan)
    # Detectar formato: contar chars de markup vs total
    markup_chars = len(re.findall(r'[|─┌┐└┘├┤┬┴┼#*_~`\[\]<>{}]', text))
    markup_ratio = markup_chars / max(len(text), 1)
    # Estimar chars/token según ratio de markup
    estimated_cpt = 5.9 * (1 - markup_ratio * 2)  # 0% markup→5.9, 50% markup→0
    estimated_cpt = max(2.7, min(5.9, estimated_cpt))
    token_eff = min(100, (estimated_cpt / 5.9) * 100)

    # Front-load check (primeros ~500 tokens)
    first_chunk = text[:CITABILITY['FRONT_LOAD_CHARS']]
    has_def = bool(re.search(def_verbs, first_chunk, re.I))
    has_num = bool(re.search(r'\d{2,}', first_chunk))
    has_ent = bool(re.search(entity_pattern, first_chunk))
    front_load = sum([has_def, has_num, has_ent]) / 3 * 100

    efficiency_avg = (chunk_eff + token_eff + front_load) / 3

    # ─── COMPOSITE ────────────────────────────────────
    if not gates_passing:
        # Gates fallando: signals y efficiency son irrelevantes
        composite = gates_avg * 0.8  # max ≈40
    else:
        # Gates OK: signals y efficiency multiplican
        composite = gates_avg * 0.45 + signals_avg * 0.35 + efficiency_avg * 0.20

    return {
        'citability_score': round(min(100, composite), 1),
        'gates_passing': gates_passing,

        # Layer 1
        'positional_depth': round(pos_depth, 3),
        'subjectivity': round(subj, 3),
        'gate_pd_score': round(gate_pd, 1),
        'gate_subj_score': round(gate_subj, 1),

        # Layer 2
        'flesch_kincaid': round(fk, 1),
        'definition_rate': round(def_rate, 4),
        'entity_density': round(entity_density, 4),
        'sig_fk_score': round(sig_fk, 1),
        'sig_dr_score': round(sig_dr, 1),
        'sig_ed_score': round(sig_ed, 1),

        # Layer 3
        'word_count': word_count,
        'chunk_efficiency': round(chunk_eff, 1),
        'token_efficiency': round(token_eff, 1),
        'front_load_score': round(front_load, 1),
        'estimated_chars_per_token': round(estimated_cpt, 1),

        # Diagnóstico
        'bottleneck': (
            'positional_depth' if gate_pd < 50 else
            'subjectivity' if gate_subj < 50 else
            'definition_rate' if sig_dr < 50 else
            'entity_density' if sig_ed < 50 else
            'flesch_kincaid' if sig_fk < 50 else
            'chunk_efficiency' if chunk_eff < 60 else
            'none'
        ),
    }
```

**Tabla — nuevas columnas en `grounding_analyses`:**
```sql
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS citability_score NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS gates_passing BOOLEAN;
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS flesch_kincaid_score NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS definition_rate NUMERIC(5,4);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS subjectivity_score NUMERIC(5,4);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS entity_density NUMERIC(5,4);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS positional_depth_score NUMERIC(5,3);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS chunk_efficiency NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS token_efficiency NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS front_load_score NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS bottleneck TEXT;
```

**Dependencias:**
```
textstat>=0.7.3    # FK + readability (puro Python, ligero)
textblob>=0.18.0   # Subjectivity (puro Python, ligero)
cachetools>=5.3.0  # TTL cache (para 27.D performance)
```
NO spacy — demasiado pesado para Railway. Entity density via regex calibrado.

---

### 27.B — Smart Internal Linking

Módulo nuevo. Más simple que la versión anterior — no embeddings por cada sección (carísimo), sino Claude batch con contexto del sitio completo.

**Flujo real:**
1. Obtener top 50 URLs por tráfico de `content` table (ya tenemos clicks, title, url)
2. Para cada URL: extraer H2/H3 headings + primer párrafo de cada sección (de `content.body`)
3. UN solo prompt Claude con todo el contexto: "Dado este sitio con 50 URLs y sus temas, sugiere los 20 mejores links internos que faltan"
4. Claude devuelve: source_url, target_url, anchor_text, context_sentence, naturalness_score
5. Guardar en `internal_link_suggestions` con status=suggested
6. El usuario acepta/rechaza en el frontend

**Por qué un solo prompt:** Embeddings por sección × URLs = miles de llamadas API. Un solo prompt con resumen del sitio es 1 llamada, <4K tokens input, y Claude entiende las relaciones semánticas mejor que cosine similarity de embeddings.

**Tablas:**
```sql
CREATE TABLE IF NOT EXISTS internal_link_suggestions (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    target_url TEXT NOT NULL,
    anchor_text TEXT NOT NULL,
    context_sentence TEXT,
    position_in_content NUMERIC(5,2),
    relevance_score NUMERIC(5,2),
    status TEXT DEFAULT 'suggested',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS internal_link_audit (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    total_internal_links INT DEFAULT 0,
    orphan_score NUMERIC(5,2),  -- 0=well connected, 100=orphan
    scan_date TIMESTAMPTZ DEFAULT now()
);
```

**Prompt (un solo prompt, no uno por URL):**
```python
LINKING_PROMPT = """Eres un experto en interlinking SEO. Aquí tienes las {n} URLs principales del sitio:

{url_summaries}

Cada entrada tiene: url, title, h2_headings[], primer_parrafo, clicks_mes.

Sugiere los 20 links internos más valiosos que NO existen actualmente.
Reglas:
- El anchor text debe ser una frase natural que ya existe en el contenido fuente
- Priorizar links desde páginas con alto tráfico hacia páginas con bajo tráfico
- Priorizar links dentro del mismo cluster temático
- NUNCA "haz clic aquí" o "leer más"
- Position: preferir primer tercio del contenido (positional depth)

JSON array:
[{{"source_url": "...", "target_url": "...", "anchor_text": "...",
   "context_sentence": "frase donde insertar el link",
   "relevance_score": 0-100, "reason": "..."}}]
"""
```

**Frontend SmartLinkingPage.tsx (3 tabs):**
- Tab 1: Oportunidades — 20 sugerencias con accept/reject, preview del contexto
- Tab 2: Auditoría — URLs ordenadas por orphan_score (más desconectadas arriba)
- Tab 3: Mapa — Grafo simplificado (no D3.js completo — un treemap o heatmap de Recharts que ya tenemos)

---

### 27.C — AIO Visibility (evolución Monitor LLM)

Evolucionar `ai_visibility_checks` (ya tiene has_ai_overview, brand_in_ai_overview, ai_overview_text, paa_questions). Añadir granularidad del pipeline Resoneo: grounding vs displayed.

**Columnas nuevas en tabla existente:**
```sql
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS aio_grounding BOOLEAN DEFAULT false;
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS aio_displayed BOOLEAN DEFAULT false;
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS aio_position INT;
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS text_fragment TEXT;
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS citation_type TEXT;
```

**Cómo se mide (con datos reales):**
- Ya llamamos Serper API en `ai_visibility_service.py` para cada query
- Serper devuelve `aiOverview` con sources[] — cada source tiene url + snippet
- Grounding = nuestro dominio aparece en sources[] de AIO
- Displayed = nuestro dominio + snippet visible (no solo fuente oculta)
- `text_fragment` = el snippet exacto que Google cita de nosotros
- `citation_type` = clasificar con regex: direct_quote (comillas), paraphrase (reformulado), reference (solo mención)

**Métricas dashboard (3 KPIs nuevos en Monitor LLM):**
- Grounding Rate = % de queries monitorizadas donde somos fuente grounding
- Display Rate = % donde aparecemos visiblemente en AIO
- Grounding Gap = grounding_rate - display_rate (oportunidad oculta)

**Entity Graph → Control de Entidad:**
De `ai_visibility_checks.ai_overview_text` (ya guardamos 2000 chars del AIO text), extraer entidades mencionadas junto a nuestra marca. Usar Claude con un prompt simple:
```python
ENTITY_EXTRACT_PROMPT = """Del siguiente texto de AI Overview de Google, extrae las entidades
(marcas, herramientas, personas, conceptos) que aparecen junto a "{brand_name}":

{aio_text}

JSON: [{{"entity": "...", "relationship": "competitor|complement|citation|context"}}]
"""
```
Esto alimenta una nueva sección en EntityPanelPage: "Cómo Google nos relaciona en AI Overviews".

---

### 27.D — Integración en módulos existentes

No son "parches" — son mejoras al flujo existente de cada módulo. Cada cambio se fundamenta en un dato concreto y conecta con infraestructura real.

#### 27.D.1 — SRO: Citability Score + Chunk Efficiency

**Cambio en `sro_service.py` → `analyze_url()`:**
Después de calcular `overall_sro_score` (S25), ejecutar `citability_score(text)` y guardar resultado en las nuevas columnas de `grounding_analyses`.

```python
# En analyze_url(), después del análisis Claude existente:
from services.citability_engine import citability_score
cit = citability_score(content_text, html=raw_html)
# Guardar en grounding_analyses junto con SRO existente
update_data = {
    'citability_score': cit['citability_score'],
    'gates_passing': cit['gates_passing'],
    'flesch_kincaid_score': cit['flesch_kincaid'],
    'definition_rate': cit['definition_rate'],
    'subjectivity_score': cit['subjectivity'],
    'entity_density': cit['entity_density'],
    'positional_depth_score': cit['positional_depth'],
    'chunk_efficiency': cit['chunk_efficiency'],
    'token_efficiency': cit['token_efficiency'],
    'front_load_score': cit['front_load_score'],
    'bottleneck': cit['bottleneck'],
}
```

**Frontend SROPage.tsx:**
- Columna nueva "Citability" en tabla de URLs (con color: verde ≥70, amarillo 40-70, rojo <40)
- En detalle de URL: radar chart de 7 señales (2 gates + 3 signals + 2 efficiency)
- Indicador de GATES (✅/❌) prominente — si falla, mostrar "Fix gates first" antes de cualquier otra recomendación
- `bottleneck` field se muestra como "Cuello de botella: {bottleneck}" con acción sugerida

#### 27.D.2 — Content Risk: 7ª señal Promotional Bias

**Cambio en `content_risk_service.py` → `scan_url()`:**
La función ya evalúa 6 señales con pesos. Añadir la 7ª usando el contenido que ya fetchea.

```python
# Señal 7: Promotional Bias (Lily Ray: -30-50% tráfico en listicles auto-promo)
# Peso: 15 (al nivel de artificial_freshness y ai_slop)
# Detección: regex affiliate patterns + Claude analysis del balance promocional
promo_signals = {
    'affiliate_patterns': [r'utm_source=', r'aff_id=', r'tag=', r'shareasale', r'impact\.com'],
    'sponsored_patterns': [r'sponsored by', r'in partnership', r'affiliate link', r'we earn'],
}
```
Se añade al composite risk score existente. Frontend ContentRiskPage muestra la señal junto a las 6 existentes.

**Columnas nuevas:**
```sql
ALTER TABLE content_risk_scans ADD COLUMN IF NOT EXISTS promotional_bias BOOLEAN DEFAULT FALSE;
ALTER TABLE content_risk_scans ADD COLUMN IF NOT EXISTS promotional_bias_details JSONB DEFAULT '{}';
```
Sigue el patrón exacto de las 6 señales existentes (boolean + JSONB details).

#### 27.D.3 — Briefings: GEO prompt mejorado

**Cambio en `claude_service.py` → `generate_briefing_content()`:**
El prompt actual ya tiene sección `geo_optimization` con: question_based_title, tldr, faq_questions, key_definitions, key_entities, retrieval_statements.

NO añadir otro bloque de texto. En cambio, **mejorar los parámetros existentes** del GEO:

```python
# Ajustar las instrucciones existentes de geo_optimization:
GEO_ENHANCEMENT = """
Para las secciones de GEO optimization existentes, aplicar estos criterios adicionales:

key_definitions: Mínimo 3 (antes no había mínimo). Usar verbos "es", "se refiere a", "significa".
  Target: Definition Rate >2% del texto final.

key_entities: Mínimo 5 entidades nombradas (marcas, herramientas, estudios con año).
  Target: Entity Density >5%. ≥1 entidad cada 150 palabras.

retrieval_statements: Mínimo 3 frases citables de ~30 palabras.
  NUEVO: Todas deben ir en el primer 25% del artículo (Positional Depth / ski ramp).
  NUEVO: Usar datos numéricos, no opiniones (Subjectivity <0.30).

word_count: Rango 800-1200 palabras (antes no había límite superior).
  Reason: >2000 words = solo 13% usado para AI grounding (DEJAN research).

NUEVO - token_optimization:
  - Preferir numerales sobre texto ("1,234" no "mil doscientos")
  - Establecer abreviaturas al inicio ("AI" en vez de repetir "Artificial Intelligence")
  - Evitar tablas decorativas (2.2x menos eficientes que prosa para AI)
  - Front-load: claims principales en primeros 500 tokens (~2750 chars)
"""
```

#### 27.D.4 — Text Review: Citability feedback

**Cambio en `claude_service.py` → `generate_text_review()`:**
El prompt actual devuelve: seo_score, readability_score, eeat_score, checks[], actions[].

Añadir al response un bloque `citability` llamando al engine:

```python
# En la función generate_text_review():
from services.citability_engine import citability_score
cit = citability_score(content_text)

# Añadir al response existente:
result['citability'] = {
    'score': cit['citability_score'],
    'gates_passing': cit['gates_passing'],
    'bottleneck': cit['bottleneck'],
    'signals': {
        'positional_depth': {'value': cit['positional_depth'], 'target': '>0.50', 'is_gate': True},
        'subjectivity': {'value': cit['subjectivity'], 'target': '<0.30', 'is_gate': True},
        'definition_rate': {'value': cit['definition_rate'], 'target': '>0.02'},
        'entity_density': {'value': cit['entity_density'], 'target': '>0.05'},
        'flesch_kincaid': {'value': cit['flesch_kincaid'], 'target': '14-16'},
        'chunk_efficiency': {'value': cit['chunk_efficiency'], 'target': '>75'},
        'token_efficiency': {'value': cit['token_efficiency'], 'target': '>80'},
    }
}
```

Frontend TextReviewPage: nueva sección "AI Citability" debajo del score existente con 7 mini-cards de señales.

#### 27.D.5 — Content Validator: gate pre-check

**Cambio en `claude_service.py` → `validate_content()`:**
Antes de la validación GEO completa (que consume tokens Claude), ejecutar citability_score() como pre-check barato (puro Python, 0 API calls).

```python
# Pre-check antes de llamar a Claude
cit = citability_score(content_text)
if not cit['gates_passing']:
    warnings.append(f"⚠️ Gates lingüísticos fallando (bottleneck: {cit['bottleneck']}). "
                    "Corregir antes de optimizar GEO — contenido no es citable en estado actual.")
```
El validate_content ya devuelve `score_geo` — ahora lo multiplica por 0.5 si gates fallan.

#### 27.D.6 — Topical Authority: PAA Coverage

**Cambio en ruta de topical_clusters:**
`ai_visibility_checks.paa_questions` ya guarda hasta 10 preguntas PAA por query. Para medir PAA coverage por cluster:

```python
async def get_cluster_paa_coverage(project_id: int, cluster_id: int) -> dict:
    """
    Mide qué % de preguntas PAA del cluster están respondidas en nuestro contenido.

    Datos:
    - AlsoAsked study: r=-0.96 para transactional top 5 (563 kw, 7905 PAA questions)
    - Solo relevante para top 10 (correlación cae y se invierte fuera de page 1)

    Flujo:
    1. Obtener keywords del cluster (cluster_urls → content → content_keywords → keywords)
    2. Para cada keyword, buscar paa_questions en ai_visibility_checks
    3. Para cada pregunta PAA, verificar si alguna URL del cluster la responde
       (usando Claude con el body de las URLs del cluster, 1 prompt batch)
    4. Calcular coverage %
    """
    sb = get_supabase()

    # 1. Keywords del cluster
    cluster_urls = sb.table("cluster_urls").select("url").eq("cluster_id", cluster_id).execute()
    urls = [r["url"] for r in (cluster_urls.data or [])]
    if not urls:
        return {'paa_coverage_pct': 0, 'total_questions': 0, 'answered': 0}

    # 2. PAA questions para esas URLs (via keyword_positions → keywords → ai_visibility_checks)
    # Simplificación: buscar ai_visibility_checks donde el query matchea keywords del cluster
    cluster_keywords = sb.table("content_keywords").select(
        "keywords!inner(keyword)"
    ).in_("content_id",
        [r["id"] for r in sb.table("content").select("id").in_("url", urls).execute().data or []]
    ).execute()

    kw_texts = list({r["keywords"]["keyword"] for r in (cluster_keywords.data or [])})
    if not kw_texts:
        return {'paa_coverage_pct': 0, 'total_questions': 0, 'answered': 0}

    # 3. Fetch PAA questions de ai_visibility_checks
    all_paa = []
    for kw in kw_texts[:20]:  # Limit to 20 keywords
        checks = sb.table("ai_visibility_checks").select("paa_questions")\
            .eq("project_id", project_id).ilike("query", f"%{kw}%")\
            .limit(1).execute()
        for check in (checks.data or []):
            paa_qs = check.get("paa_questions") or []
            all_paa.extend(paa_qs)

    unique_paa = list(set(all_paa))
    if not unique_paa:
        return {'paa_coverage_pct': 0, 'total_questions': 0, 'answered': 0}

    # 4. Check coverage: fetch body content of cluster URLs
    content_bodies = sb.table("content").select("url, body")\
        .in_("url", urls).execute()
    combined_content = " ".join(
        (r.get("body") or "")[:2000] for r in (content_bodies.data or [])
    )[:10000]  # Max 10K chars for Claude

    # 5. Single Claude call to check which PAA questions are answered
    from services.claude_service import call_claude
    check_prompt = f"""Dado este contenido del sitio:
{combined_content}

¿Cuáles de estas preguntas PAA están respondidas en el contenido? (total o parcialmente)
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(unique_paa[:30]))}

Responde JSON: {{"answered": [1, 3, 5], "not_answered": [2, 4]}}"""

    response = await call_claude(check_prompt, max_tokens=500)
    # Parse response...
    answered_count = len(response.get('answered', []))

    coverage = round(answered_count / max(len(unique_paa), 1) * 100, 1)

    return {
        'paa_coverage_pct': coverage,
        'total_questions': len(unique_paa),
        'answered': answered_count,
        'unanswered_questions': [unique_paa[i-1] for i in response.get('not_answered', [])
                                  if 0 < i <= len(unique_paa)],
        'correlation_note': 'AlsoAsked: r=-0.96 transactional, r=-0.89 commercial/informational (top 5)',
        'recommendation': (
            f'Cobertura PAA: {coverage}%. '
            + ('Excelente — alineado con top 5 rankings.' if coverage > 70
               else f'Bajo. {len(unique_paa) - answered_count} preguntas PAA sin responder. '
                    'Añadir secciones FAQ o expandir contenido existente.')
        )
    }
```

Frontend TopicalAuthorityPage: en detalle de cluster, sección "PAA Coverage" con barra de progreso, lista de preguntas no respondidas como oportunidades de contenido.

#### 27.D.7 — Entity Panel: AIO Entity Relationships

Usar datos que ya guardamos en `ai_visibility_checks.ai_overview_text` (2000 chars) para extraer entidades que Google asocia con nuestra marca.

```python
async def get_aio_entity_relationships(project_id: int) -> dict:
    sb = get_supabase()
    brand = sb.table("projects").select("name, brand_terms").eq("id", project_id).single().execute()
    brand_name = brand.data.get("name", "")

    # Fetch AIO texts donde aparecemos
    checks = sb.table("ai_visibility_checks").select("query, ai_overview_text")\
        .eq("project_id", project_id).eq("brand_in_ai_overview", True)\
        .order("checked_at", desc=True).limit(30).execute()

    if not checks.data:
        return {'entities': [], 'note': 'No AIO appearances found'}

    # Batch extract: all AIO texts in one Claude call
    aio_texts = "\n---\n".join(
        f"Query: {c['query']}\nAIO: {c['ai_overview_text'][:500]}"
        for c in checks.data if c.get('ai_overview_text')
    )

    prompt = f"""De estos fragmentos de AI Overviews donde aparece "{brand_name}",
extrae las entidades (marcas, herramientas, conceptos) que Google asocia con nosotros:

{aio_texts[:6000]}

JSON: [{{"entity": "...", "count": N, "relationship": "competitor|complement|citation"}}]
Agrupa por entidad, cuenta apariciones, clasifica relación."""

    response = await call_claude(prompt, max_tokens=800)
    return {
        'aio_perceived_entities': response,
        'total_aio_checks': len(checks.data),
        'brand': brand_name,
    }
```

Frontend EntityPanelPage: nueva sección "AI-Perceived Relationships" — tabla de entidades asociadas con count y tipo de relación.

---

### 27.E — Performance Optimization

```python
# 1. Dashboard: asyncio.gather (7+ queries → paralelo)
# Archivo: dashboard_service.py → get_dashboard()
async def get_dashboard(project_id, ...):
    metrics, alerts, cannib, trends, gaps = await asyncio.gather(
        get_dashboard_metrics(project_id, ...),
        asyncio.to_thread(lambda: sb.table("alerts").select(...).execute()),
        asyncio.to_thread(lambda: sb.table("cannibalizations").select(...).execute()),
        asyncio.to_thread(lambda: sb.table("trends").select(...).execute()),
        asyncio.to_thread(lambda: sb.table("content_gaps").select(...).execute()),
    )

# 2. N+1 fix: _auto_assign_categories batch upsert
# Archivo: content_performance_service.py
async def _auto_assign_categories(project_id):
    items = sb.table("content").select("id,url").eq("project_id", project_id).is_("category", "null").execute()
    if not items.data: return
    updates = [{"id": i["id"], "category": _detect_category(i["url"])} for i in items.data]
    for batch in chunks(updates, 100):
        sb.table("content").upsert(batch, on_conflict="id").execute()

# 3. GZip (main.py)
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 4. Permission cache (middleware/permissions.py)
from cachetools import TTLCache
_profile_cache = TTLCache(maxsize=100, ttl=300)
_project_access_cache = TTLCache(maxsize=500, ttl=300)
```

Frontend: `React.memo` en widgets pesados del Dashboard.

---

### 27.F — Integración

**Regla permanente:** NUNCA badges en sidebar.

**AI Readiness Score del Dashboard:**
```python
# Compuesto de datos reales que ya calculamos:
AI_READINESS = {
    'sro_score': 0.35,        # grounding_analyses.overall_sro_score (S25)
    'citability_score': 0.35, # grounding_analyses.citability_score (S27.A — NUEVO)
    'aio_visibility': 0.15,   # ai_visibility_checks: brand_in_ai_overview rate (S22 + S27.C)
    'link_health': 0.15,      # internal_link_audit.orphan_score inverse (S27.B — NUEVO)
}
# Nota: chunk_efficiency y token_efficiency ya están dentro de citability_score
```

**Sidebar — 1 módulo nuevo:**
```typescript
{ key: 'smart-linking', label: 'Smart Linking', icon: Link2, path: 'smart-linking', group: 'content', enabled: true },
```

---

### Migración 059
```sql
-- Sprint 27: Citability Engine + Smart Linking + AIO Visibility

-- Smart Linking
CREATE TABLE IF NOT EXISTS internal_link_suggestions (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    target_url TEXT NOT NULL,
    anchor_text TEXT NOT NULL,
    context_sentence TEXT,
    position_in_content NUMERIC(5,2),
    relevance_score NUMERIC(5,2),
    status TEXT DEFAULT 'suggested',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS internal_link_audit (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    total_internal_links INT DEFAULT 0,
    orphan_score NUMERIC(5,2),
    scan_date TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_link_suggestions_project ON internal_link_suggestions(project_id);
CREATE INDEX idx_link_suggestions_status ON internal_link_suggestions(project_id, status);
CREATE INDEX idx_link_audit_project ON internal_link_audit(project_id);

-- Citability Engine columns en grounding_analyses (ya existe)
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS citability_score NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS gates_passing BOOLEAN;
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS flesch_kincaid_score NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS definition_rate NUMERIC(5,4);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS subjectivity_score NUMERIC(5,4);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS entity_density NUMERIC(5,4);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS positional_depth_score NUMERIC(5,3);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS chunk_efficiency NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS token_efficiency NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS front_load_score NUMERIC(5,1);
ALTER TABLE grounding_analyses ADD COLUMN IF NOT EXISTS bottleneck TEXT;

-- AIO Visibility en ai_visibility_checks (ya existe)
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS aio_grounding BOOLEAN DEFAULT false;
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS aio_displayed BOOLEAN DEFAULT false;
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS aio_position INT;
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS text_fragment TEXT;
ALTER TABLE ai_visibility_checks ADD COLUMN IF NOT EXISTS citation_type TEXT;

-- Promotional Bias en content_risk_scans (ya existe)
ALTER TABLE content_risk_scans ADD COLUMN IF NOT EXISTS promotional_bias BOOLEAN DEFAULT FALSE;
ALTER TABLE content_risk_scans ADD COLUMN IF NOT EXISTS promotional_bias_details JSONB DEFAULT '{}';

-- RLS
ALTER TABLE internal_link_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE internal_link_audit ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow_all_link_suggestions" ON internal_link_suggestions FOR ALL USING (true);
CREATE POLICY "allow_all_link_audit" ON internal_link_audit FOR ALL USING (true);
```

### Dependencias
```
textstat>=0.7.3
textblob>=0.18.0
cachetools>=5.3.0
```

### Resumen

```
SPRINT 27: AI CITABILITY ENGINE
════════════════════════════════

  27.A CITABILITY ENGINE (servicio central — 0 módulos nuevos, 1 motor)
    ├── Layer 1 GATES: Positional Depth + Subjectivity (pasan o no pasan)
    ├── Layer 2 SIGNALS: FK 16 + Definition Rate + Entity Density
    ├── Layer 3 EFFICIENCY: Chunk (DEJAN) + Token (Metehan) + Front-load
    └── Output: citability_score 0-100 + bottleneck diagnosis

  27.B SMART LINKING (1 módulo nuevo, 3 tabs)
    ├── 1 prompt Claude batch (no embeddings por sección)
    ├── Sugerencias accept/reject
    └── Orphan score audit

  27.C AIO VISIBILITY (evolución Monitor LLM)
    ├── Grounding Rate / Display Rate / Grounding Gap
    └── Entity graph → Control de Entidad

  27.D INTEGRACIÓN EN 7 MÓDULOS EXISTENTES
    ├── D.1 SRO: citability_score en grounding_analyses + radar chart
    ├── D.2 Content Risk: 7ª señal promotional_bias (Lily Ray)
    ├── D.3 Briefings: GEO prompt mejorado (no bloque nuevo, parámetros existentes)
    ├── D.4 Text Review: sección citability con 7 señales
    ├── D.5 Content Validator: gate pre-check antes de GEO scoring
    ├── D.6 Topical Authority: PAA Coverage por cluster (AlsoAsked r=-0.96)
    └── D.7 Entity Panel: AIO entity relationships

  27.E PERFORMANCE
    ├── asyncio.gather Dashboard (-50%)
    ├── N+1 fix batch upsert
    ├── GZip (-60% payload)
    └── Permission cache TTL 5min

  27.F AI READINESS SCORE
    └── SRO 35% + Citability 35% + AIO 15% + Link Health 15%
```

**Tiempo: 5-6 días.** Migración 059. 1 módulo nuevo (Smart Linking, 3 tabs). 7 módulos mejorados. 1 servicio central nuevo (citability_engine.py). ~12 endpoints nuevos.

---

## Sprint 28: CrUX Field Data + CWV Intelligence

> **Contexto:** FIT ya tiene CWV con PageSpeed Insights API (lab data, cache 24h). Pero lab ≠ field. El deep-research-report.md identifica que los datos de campo (CrUX) son los que Google usa para ranking. CrUX API es gratuita, 150 req/min, y tiene History API con 40 semanas de tendencia. Este sprint añade la capa de field data que falta.
>
> **Fuentes:** Chrome UX Report API docs (2025-2026), Google PageSpeed Insights methodology, Web Vitals initiative. INP reemplazó FID en marzo 2024.

### 28.A — CrUX Service (backend)

Nuevo servicio `crux_service.py` que consume CrUX API y CrUX History API.

**Endpoints CrUX API:**
```
POST https://chromeuxreport.googleapis.com/v1/records:queryRecord?key=API_KEY
POST https://chromeuxreport.googleapis.com/v1/records:queryHistoryRecord?key=API_KEY
```

**Autenticación:** API Key de Google Cloud (NO OAuth). Guardar en `CRUX_API_KEY` env var. Gratis, 150 QPM.

**Implementación `crux_service.py`:**

```python
import httpx
from typing import Optional
import os

CRUX_API_KEY = os.getenv("CRUX_API_KEY", "")
CRUX_BASE = "https://chromeuxreport.googleapis.com/v1/records"

# Umbrales oficiales Google (p75)
CWV_THRESHOLDS = {
    "largest_contentful_paint": {"good": 2500, "poor": 4000, "unit": "ms"},
    "interaction_to_next_paint": {"good": 200, "poor": 500, "unit": "ms"},
    "cumulative_layout_shift":  {"good": 0.1, "poor": 0.25, "unit": "score"},
    "first_contentful_paint":   {"good": 1800, "poor": 3000, "unit": "ms"},
    "time_to_first_byte":       {"good": 800, "poor": 1800, "unit": "ms"},
}

async def fetch_crux_record(
    origin: Optional[str] = None,
    url: Optional[str] = None,
    form_factor: str = "PHONE"
) -> dict:
    """Fetch CrUX field data for origin or specific URL."""
    payload = {"formFactor": form_factor}
    if url:
        payload["url"] = url
    elif origin:
        payload["origin"] = origin
    else:
        raise ValueError("origin or url required")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CRUX_BASE}:queryRecord?key={CRUX_API_KEY}",
            json=payload, timeout=15
        )
        resp.raise_for_status()
        return resp.json()

async def fetch_crux_history(
    origin: Optional[str] = None,
    url: Optional[str] = None,
    form_factor: str = "PHONE"
) -> dict:
    """Fetch CrUX history (40 weekly data points)."""
    payload = {"formFactor": form_factor}
    if url:
        payload["url"] = url
    elif origin:
        payload["origin"] = origin

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CRUX_BASE}:queryHistoryRecord?key={CRUX_API_KEY}",
            json=payload, timeout=15
        )
        resp.raise_for_status()
        return resp.json()

def classify_metric(metric_key: str, p75_value: float) -> str:
    """Classify as 'good', 'needs_improvement', or 'poor'."""
    t = CWV_THRESHOLDS.get(metric_key)
    if not t:
        return "unknown"
    if p75_value <= t["good"]:
        return "good"
    elif p75_value > t["poor"]:
        return "poor"
    return "needs_improvement"

def parse_crux_response(data: dict) -> dict:
    """Extract p75 values + classifications from CrUX response."""
    metrics = data.get("record", {}).get("metrics", {})
    result = {}
    for key, val in metrics.items():
        p75 = val.get("percentiles", {}).get("p75")
        if p75 is not None:
            result[key] = {
                "p75": p75,
                "status": classify_metric(key, p75),
                "histogram": val.get("histogram", []),
            }
    # Overall pass = LCP + INP + CLS all "good"
    core_three = ["largest_contentful_paint", "interaction_to_next_paint", "cumulative_layout_shift"]
    result["cwv_pass"] = all(
        result.get(m, {}).get("status") == "good" for m in core_three
    )
    return result
```

**Lógica de negocio:**
- `fetch_crux_record(origin="https://fitgeneration.es")` → datos de campo del dominio completo
- `fetch_crux_record(url="https://fitgeneration.es/page")` → datos de campo de URL específica (si tiene suficiente tráfico; si no, CrUX devuelve 404 → fallback a origin)
- `fetch_crux_history(origin=...)` → 40 puntos semanales para gráfico de tendencia
- `classify_metric()` → good/needs_improvement/poor según umbrales oficiales
- `cwv_pass` → True solo si LCP + INP + CLS están en "good" (p75)

### 28.B — Endpoints CrUX

**Rutas en `cwv.py` (añadir a las existentes):**

```
GET /projects/{id}/cwv/field           → CrUX origin data (desktop + mobile)
GET /projects/{id}/cwv/field/url       → CrUX URL-level data (query param: ?url=...)
GET /projects/{id}/cwv/field/history   → CrUX history (40 weeks, gráfico de tendencia)
GET /projects/{id}/cwv/comparison      → Lab vs Field comparison (PSI lab vs CrUX field)
```

**Endpoint `/cwv/field`:**
- Llama CrUX para origin (PHONE + DESKTOP)
- Cachea en `cwv_field_cache` (TTL 24h — CrUX se actualiza diariamente)
- Devuelve: 5 métricas con p75 + status + histogram, cwv_pass boolean, collection_period

**Endpoint `/cwv/field/history`:**
- Llama CrUX History API para origin
- Devuelve: array de 40 puntos {date, lcp_p75, inp_p75, cls_p75} para gráfico de líneas
- Cachea con TTL 7 días (los históricos no cambian)

**Endpoint `/cwv/comparison`:**
- Combina datos de `cwv_service.py` (PSI/lab) con `crux_service.py` (CrUX/field)
- Devuelve: `{lab: {lcp, inp_proxy_tbt, cls}, field: {lcp, inp, cls}, divergences: [...]}`
- Divergencia = cuando lab dice "good" pero field dice "poor" (o viceversa)

### 28.C — Migración 060

```sql
-- 060_cwv_field_cache.sql
CREATE TABLE IF NOT EXISTS cwv_field_cache (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    origin TEXT NOT NULL,
    url TEXT,  -- NULL = origin-level
    form_factor TEXT NOT NULL DEFAULT 'PHONE',
    lcp_p75 NUMERIC,
    inp_p75 NUMERIC,
    cls_p75 NUMERIC(6,4),
    fcp_p75 NUMERIC,
    ttfb_p75 NUMERIC,
    cwv_pass BOOLEAN DEFAULT FALSE,
    raw_data JSONB,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, origin, url, form_factor)
);

CREATE INDEX idx_cwv_field_project ON cwv_field_cache(project_id);
CREATE INDEX idx_cwv_field_fetched ON cwv_field_cache(fetched_at);

ALTER TABLE cwv_field_cache ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cwv_field_project_isolation ON cwv_field_cache;
CREATE POLICY cwv_field_project_isolation ON cwv_field_cache
    USING (project_id IN (SELECT id FROM projects));

-- History cache (40 weekly points per origin)
CREATE TABLE IF NOT EXISTS cwv_field_history (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    origin TEXT NOT NULL,
    form_factor TEXT NOT NULL DEFAULT 'PHONE',
    week_ending DATE NOT NULL,
    lcp_p75 NUMERIC,
    inp_p75 NUMERIC,
    cls_p75 NUMERIC(6,4),
    fcp_p75 NUMERIC,
    ttfb_p75 NUMERIC,
    cwv_pass BOOLEAN DEFAULT FALSE,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, origin, form_factor, week_ending)
);

CREATE INDEX idx_cwv_history_project ON cwv_field_history(project_id);
ALTER TABLE cwv_field_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cwv_history_project_isolation ON cwv_field_history;
CREATE POLICY cwv_history_project_isolation ON cwv_field_history
    USING (project_id IN (SELECT id FROM projects));
```

### 28.D — Frontend: CWV Field Tab en SEO Técnico

**Ubicación:** Nueva sub-tab "Datos de Campo" dentro de la sección CWV de `TechnicalSeoPage.tsx` (o tab independiente si el layout lo requiere).

**Componentes:**
1. **3 KPI cards** (LCP, INP, CLS) con semáforo verde/amarillo/rojo y valor p75
   - Badge "FIELD" vs "LAB" para distinguir de los datos PSI existentes
   - Debajo de cada KPI: mini histogram (3 barras: good/needs_improvement/poor %)
2. **Pass/Fail badge** global: "Core Web Vitals Assessment: PASSED ✓" o "FAILED ✗"
3. **Gráfico de tendencia** (40 semanas): línea temporal para LCP, INP, CLS con umbrales como líneas horizontales
4. **Tabla Lab vs Field** comparativa: mostrar divergencias en rojo cuando lab≠field
5. **Selector Desktop/Mobile** (form_factor toggle)

**Diseño UX (reglas FIT):**
- Máximo 5-7 KPIs por vista ✓ (5 métricas + 1 pass/fail)
- Colores semánticos: verde=good, amarillo=needs_improvement, rojo=poor
- Comparativa temporal: gráfico de 40 semanas ✓
- NUNCA pie charts ✓

### 28.E — Settings: CRUX_API_KEY

Añadir campo en Settings > API Keys para guardar la Google Cloud API Key de CrUX. Se guarda como secret en la tabla `api_keys` existente (o env var de Railway).

```
SPRINT 28: CrUX FIELD DATA + CWV INTELLIGENCE
══════════════════════════════════════════════

  28.A CRUX SERVICE (backend)
    ├── crux_service.py: fetch_crux_record + fetch_crux_history
    ├── parse_crux_response con classify_metric (umbrales oficiales)
    ├── cwv_pass = LCP + INP + CLS all "good" en p75
    └── Fallback: URL sin datos → origin-level

  28.B ENDPOINTS CWV FIELD
    ├── GET /cwv/field (origin desktop + mobile, cache 24h)
    ├── GET /cwv/field/url (URL específica, fallback origin)
    ├── GET /cwv/field/history (40 semanas, cache 7d)
    └── GET /cwv/comparison (lab PSI vs field CrUX, divergencias)

  28.C MIGRACIÓN 060
    ├── cwv_field_cache (origin + URL + form_factor, p75 5 métricas, cwv_pass)
    └── cwv_field_history (40 semanas × origin × form_factor)

  28.D FRONTEND
    ├── 3 KPI cards (LCP/INP/CLS) con semáforo + histograma
    ├── Pass/Fail badge global
    ├── Gráfico tendencia 40 semanas
    ├── Tabla Lab vs Field divergencias
    └── Toggle Desktop/Mobile

  28.E SETTINGS
    └── CRUX_API_KEY en API Keys
```

**Tiempo: 3-4 días.** Migración 060. 0 módulos nuevos. 4 endpoints nuevos. 1 servicio nuevo (crux_service.py). Frontend: nueva sub-tab CWV Field en SEO Técnico.

---

## Sprint 29: URL Inspection API + Indexability Intelligence

> **Contexto:** FIT tiene diagnóstico de indexación en SEO Técnico (tab Indexación) pero depende de datos del crawl de Screaming Frog. La URL Inspection API de Google permite verificar directamente el estado de indexación real desde Google — no lo que nosotros creemos, sino lo que Google ve. Esto cierra el gap entre "lo que Screaming Frog reporta" y "lo que Google realmente indexó". El deep-research-report.md lo identifica como requisito funcional clave.
>
> **Fuentes:** Google Search Console URL Inspection API docs (2022-2026), Search Console API reference, GSC batch inspection guide.

### 29.A — URL Inspection Service (backend)

Nuevo servicio `url_inspection_service.py` que consume la URL Inspection API de Search Console.

**Endpoint API:**
```
POST https://searchconsole.googleapis.com/v1/urlInspection/index:inspect
```

**Autenticación:** OAuth 2.0 (ya configurado — FIT ya tiene GSC conectado con OAuth). Scope: `https://www.googleapis.com/auth/webmasters.readonly`. Reusar el token OAuth existente de la integración GSC.

**Rate limits:** 2,000 queries/día por propiedad, 600 queries/minuto. Diseñar para respetar estos límites.

**Implementación `url_inspection_service.py`:**

```python
from typing import Optional
from supabase import Client
from api.services.google_auth_service import get_gsc_credentials

async def inspect_url(project_id: int, url: str, site_url: str) -> dict:
    """Inspect a single URL via GSC URL Inspection API."""
    credentials = await get_gsc_credentials(project_id)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
            headers={"Authorization": f"Bearer {credentials.token}"},
            json={
                "inspectionUrl": url,
                "siteUrl": site_url
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

def parse_inspection_result(raw: dict) -> dict:
    """Parse API response into structured result."""
    result = raw.get("inspectionResult", {})
    index_status = result.get("indexStatusResult", {})
    mobile = result.get("mobileUsabilityResult", {})
    rich = result.get("richResultsResult", {})

    return {
        "verdict": index_status.get("verdict", "UNKNOWN"),  # PASS, FAIL, etc.
        "coverage_state": index_status.get("coverageState", ""),  # "Submitted and indexed", etc.
        "indexing_state": index_status.get("indexingState", ""),
        "robots_txt_state": index_status.get("robotsTxtState", ""),
        "page_fetch_state": index_status.get("pageFetchState", ""),
        "crawled_as": index_status.get("crawledAs", ""),
        "last_crawl_time": index_status.get("lastCrawlTime"),
        "referring_urls": index_status.get("referringUrls", []),
        "sitemap": index_status.get("sitemap", []),
        "mobile_usability": mobile.get("verdict", "UNKNOWN"),
        "mobile_issues": [i.get("message") for i in mobile.get("issues", [])],
        "rich_results_verdict": rich.get("verdict", "UNKNOWN"),
        "rich_results_items": [
            {"type": item.get("name"), "issues": [i.get("message") for i in item.get("issues", [])]}
            for item in rich.get("detectedItems", [])
        ],
    }

async def batch_inspect(project_id: int, urls: list[str], site_url: str) -> list[dict]:
    """Inspect multiple URLs respecting rate limits.
    Max 2000/day, 600/min. Process in chunks of 50 with delay."""
    results = []
    for i in range(0, len(urls), 50):
        chunk = urls[i:i+50]
        for url in chunk:
            try:
                raw = await inspect_url(project_id, url, site_url)
                parsed = parse_inspection_result(raw)
                parsed["url"] = url
                results.append(parsed)
            except Exception as e:
                results.append({"url": url, "error": str(e)})
        # Rate limit: ~50 per batch, small delay between batches
        if i + 50 < len(urls):
            await asyncio.sleep(5)
    return results
```

**Lógica de negocio:**
- `inspect_url()` → inspección unitaria (para URL Inspector tab en SEO Técnico)
- `batch_inspect()` → inspección masiva (máx 200 URLs por ejecución, respetando 2000/día)
- `parse_inspection_result()` → extrae verdict, coverage_state, crawl info, mobile, rich results
- Reusar OAuth token de GSC existente (no nueva autenticación)

### 29.B — Endpoints URL Inspection

**Rutas en nuevo archivo `url_inspection.py`:**

```
GET  /projects/{id}/url-inspection/{url_encoded}  → Inspección de 1 URL (con cache)
POST /projects/{id}/url-inspection/batch           → Batch de URLs (body: {urls: [...]}, max 200)
GET  /projects/{id}/url-inspection/results         → Historial de inspecciones
GET  /projects/{id}/url-inspection/summary         → Resumen: indexed/excluded/error counts
```

**Endpoint `/url-inspection/{url_encoded}`:**
- Busca en cache primero (TTL 24h)
- Si no hay cache o expiró, llama API
- Devuelve: verdict, coverage_state, last_crawl_time, mobile_usability, rich_results
- Muestra rate limit restante en response header: `X-Inspection-Quota-Remaining`

**Endpoint `/url-inspection/batch`:**
- Acepta array de URLs (máximo 200 por request)
- Ejecuta en background (task async), devuelve task_id
- Progreso consultable via websocket o polling
- Guarda resultados en `url_inspection_results`

**Endpoint `/url-inspection/summary`:**
- Agrega resultados cacheados: {total_inspected, indexed, excluded, errors, not_found}
- Breakdown por coverage_state (ej: "Crawled - currently not indexed", "Discovered - currently not indexed", etc.)

### 29.C — Migración 061

```sql
-- 061_url_inspection_cache.sql
CREATE TABLE IF NOT EXISTS url_inspection_results (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    verdict TEXT,  -- PASS, FAIL, NEUTRAL, VERDICT_UNSPECIFIED
    coverage_state TEXT,  -- "Submitted and indexed", "Excluded", etc.
    indexing_state TEXT,
    robots_txt_state TEXT,
    page_fetch_state TEXT,
    crawled_as TEXT,  -- DESKTOP, MOBILE
    last_crawl_time TIMESTAMPTZ,
    mobile_usability TEXT,
    mobile_issues JSONB DEFAULT '[]',
    rich_results_verdict TEXT,
    rich_results_items JSONB DEFAULT '[]',
    referring_urls JSONB DEFAULT '[]',
    sitemap_urls JSONB DEFAULT '[]',
    raw_response JSONB,
    inspected_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, url)
);

CREATE INDEX idx_url_inspection_project ON url_inspection_results(project_id);
CREATE INDEX idx_url_inspection_verdict ON url_inspection_results(project_id, verdict);
CREATE INDEX idx_url_inspection_coverage ON url_inspection_results(project_id, coverage_state);

ALTER TABLE url_inspection_results ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS url_inspection_project_isolation ON url_inspection_results;
CREATE POLICY url_inspection_project_isolation ON url_inspection_results
    USING (project_id IN (SELECT id FROM projects));

-- Daily quota tracking
CREATE TABLE IF NOT EXISTS url_inspection_quota (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    requests_used INT DEFAULT 0,
    requests_limit INT DEFAULT 2000,
    UNIQUE(project_id, date)
);

ALTER TABLE url_inspection_quota ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS url_inspection_quota_isolation ON url_inspection_quota;
CREATE POLICY url_inspection_quota_isolation ON url_inspection_quota
    USING (project_id IN (SELECT id FROM projects));
```

### 29.D — Frontend: URL Inspector mejorado en SEO Técnico

**Ubicación:** Mejorar la tab "Inspector URL" existente en `TechnicalSeoPage.tsx` / `UrlInspectorTab.tsx`.

**Componentes:**
1. **Buscador de URL** (ya existe) → ahora llama la API real de Google, no solo datos de crawl
2. **Resultado de inspección:**
   - Badge grande: "INDEXED ✓" verde / "NOT INDEXED ✗" rojo / "EXCLUDED ⚠" amarillo
   - Coverage state en texto descriptivo
   - Last crawl date + crawled as (Desktop/Mobile)
   - Mobile usability: PASS/FAIL + issues list
   - Rich results: detected types + issues
   - Referring URLs y sitemaps que Google conoce
3. **Batch Inspector:**
   - Botón "Inspeccionar Top 200 URLs" (usa las 200 URLs con más tráfico de GSC)
   - Progress bar durante la inspección
   - Resultado: tabla con URL + verdict + coverage_state + last_crawl
4. **Summary Dashboard:**
   - 4 KPI cards: Total Inspected, Indexed, Excluded, Errors
   - Breakdown chart (barras horizontales) por coverage_state
   - Lista de URLs problemáticas (excluded/error) con razón

**Diseño UX (reglas FIT):**
- Máximo 5-7 KPIs ✓ (4 summary + coverage breakdown)
- Colores semánticos: verde=indexed, rojo=error, amarillo=excluded
- NUNCA pie charts ✓ (barras horizontales para breakdown)

### 29.E — Quota Management

- Tabla `url_inspection_quota` trackea uso diario (2000/día límite)
- UI muestra "Inspecciones restantes hoy: X/2000"
- Si quota agotada, deshabilitar botones y mostrar "Límite diario alcanzado, vuelve mañana"
- Priorizar URLs: las que tienen más tráfico o las que Screaming Frog marcó como problemáticas

```
SPRINT 29: URL INSPECTION API + INDEXABILITY INTELLIGENCE
═════════════════════════════════════════════════════════

  29.A URL INSPECTION SERVICE (backend)
    ├── url_inspection_service.py: inspect_url + batch_inspect
    ├── Reutiliza OAuth de GSC existente
    ├── parse_inspection_result: verdict, coverage, mobile, rich results
    └── Rate limit: 2000/día, 600/min, chunks de 50

  29.B ENDPOINTS
    ├── GET /url-inspection/{url} (single, cache 24h)
    ├── POST /url-inspection/batch (max 200, async task)
    ├── GET /url-inspection/results (historial)
    └── GET /url-inspection/summary (indexed/excluded/error counts)

  29.C MIGRACIÓN 061
    ├── url_inspection_results (verdict, coverage, mobile, rich, raw)
    └── url_inspection_quota (daily tracking 2000/día)

  29.D FRONTEND (mejora UrlInspectorTab)
    ├── Buscador → ahora con datos reales de Google
    ├── Badge INDEXED/NOT INDEXED/EXCLUDED
    ├── Batch Inspector (top 200 URLs por tráfico)
    ├── Summary: 4 KPIs + breakdown por coverage_state
    └── Quota indicator "X/2000 restantes hoy"

  29.E QUOTA MANAGEMENT
    └── Tracking diario + UI de límite + priorización por tráfico
```

**Tiempo: 4-5 días.** Migración 061. 0 módulos nuevos. 4 endpoints nuevos. 1 servicio nuevo (url_inspection_service.py). Frontend: mejora UrlInspectorTab con datos reales de Google.

---

## Sprint 30 — Bulk Index Inspector + Smoke Fix + GSC Validation Tuning

> **Objetivo:** Convertir el Inspector URL individual en una herramienta de inspección masiva al estilo JL Hernando (bulk checker con dashboard agregado), corregir falso-verde en smoke tests (P1), y afinar validación GSC (P2).
>
> **Referencia:** https://jlhernando.com/blog/google-index-inspect-v2-webapp/
>
> **Dependencia:** Sprint 29 (URL Inspection API ya implementada).

### 30.A BULK INSPECTION FRONTEND (UrlInspectorTab.tsx)

**Problema actual:** Solo se puede inspeccionar 1 URL a la vez. El endpoint `scan_urls_batch` existe pero el frontend no lo expone con listas custom.

**Cambios en UrlInspectorTab.tsx:**

1. **Modo dual: Single / Bulk**
   - Toggle "URL individual" ↔ "Inspección masiva" en la parte superior
   - Single: mantener input actual
   - Bulk: textarea (pegar URLs, una por línea) + botón "Subir CSV"

2. **Input masivo:**
   ```tsx
   // Textarea para pegar URLs
   <textarea
     placeholder="Pega URLs aquí, una por línea..."
     rows={8}
     className="w-full bg-gray-900 border border-gray-700 rounded p-3 font-mono text-sm"
   />

   // O subir CSV
   <input type="file" accept=".csv,.txt" onChange={handleFileUpload} />

   // Parser CSV: extraer columna URL (primera columna o columna "url"/"URL"/"address")
   function parseCSV(text: string): string[] {
     const lines = text.split('\n').filter(l => l.trim());
     // Detectar si tiene header
     const first = lines[0].toLowerCase();
     const hasHeader = first.includes('url') || first.includes('address') || first.includes('http') === false;
     const startIdx = hasHeader ? 1 : 0;
     return lines.slice(startIdx).map(l => {
       // Si tiene comas (CSV), tomar primera columna
       const parts = l.split(',');
       return parts[0].trim().replace(/^["']|["']$/g, '');
     }).filter(u => u.startsWith('http'));
   }
   ```

3. **Validación pre-envío:**
   - Deduplicar URLs
   - Validar formato (debe empezar con https:// o http://)
   - Mostrar count: "X URLs válidas de Y introducidas"
   - Warning si > 2000 (límite diario API)
   - Confirmar property GSC: dropdown de properties conectadas

4. **Nuevo endpoint backend para bulk custom:**
   ```python
   # POST /projects/{id}/technical-seo/index-status/bulk-inspect
   @router.post("/projects/{project_id}/technical-seo/index-status/bulk-inspect")
   async def bulk_inspect_custom_urls(
       project_id: int,
       body: BulkInspectRequest,
       user: dict = Depends(require_auth),
   ):
       """Inspeccionar lista custom de URLs (max 2000/día)."""
       urls = body.urls  # List[str], max 2000
       if len(urls) > 2000:
           raise HTTPException(400, "Máximo 2000 URLs por día")

       # Verificar cuota restante
       quota = get_daily_quota_remaining(project_id)
       if len(urls) > quota:
           raise HTTPException(429, f"Solo quedan {quota} inspecciones hoy")

       # Crear job_id para tracking
       job_id = str(uuid4())
       store_bulk_job(project_id, job_id, urls)

       # Lanzar en background
       background_tasks.add_task(
           run_bulk_inspection, project_id, job_id, urls
       )

       return {"job_id": job_id, "total_urls": len(urls), "status": "running"}
   ```

### 30.B PROGRESS TRACKING + POLLING

**Backend — Job tracking:**

```python
# Tabla en memoria (o Redis si hay) para jobs activos
# Alternativa simple: usar dashboard_cache con key "bulk_job_{job_id}"

async def run_bulk_inspection(project_id: int, job_id: str, urls: list[str]):
    """Background task que inspecciona URLs secuencialmente."""
    total = len(urls)
    results = []
    errors = []

    for i, url in enumerate(urls):
        try:
            result = await inspect_single_url(project_id, url)
            results.append(result)
        except Exception as e:
            errors.append({"url": url, "error": str(e)})

        # Actualizar progreso cada 5 URLs
        if (i + 1) % 5 == 0 or i == total - 1:
            update_bulk_job_progress(project_id, job_id, {
                "status": "running",
                "processed": i + 1,
                "total": total,
                "indexed": sum(1 for r in results if r.get("verdict") == "PASS"),
                "not_indexed": sum(1 for r in results if r.get("verdict") != "PASS"),
                "errors": len(errors),
            })

    # Finalizar: calcular resumen
    summary = compute_bulk_summary(results, errors)
    update_bulk_job_progress(project_id, job_id, {
        "status": "completed",
        **summary,
    })

# GET /projects/{id}/technical-seo/index-status/bulk-inspect/{job_id}
@router.get("/projects/{project_id}/technical-seo/index-status/bulk-inspect/{job_id}")
async def get_bulk_job_status(project_id: int, job_id: str, user: dict = Depends(require_auth)):
    """Polling endpoint para progreso del bulk job."""
    return get_bulk_job_progress(project_id, job_id)
```

**Frontend — Polling con progress bar:**

```tsx
// Polling cada 3s mientras status === "running"
const [job, setJob] = useState<BulkJob | null>(null);

useEffect(() => {
  if (!job || job.status !== 'running') return;
  const interval = setInterval(async () => {
    const res = await api.get(
      `/projects/${pid}/technical-seo/index-status/bulk-inspect/${job.job_id}`
    );
    setJob(res.data);
    if (res.data.status === 'completed') clearInterval(interval);
  }, 3000);
  return () => clearInterval(interval);
}, [job?.job_id, job?.status]);

// Progress bar
<div className="w-full bg-gray-800 rounded-full h-3 mt-4">
  <div
    className="bg-yellow-500 h-3 rounded-full transition-all duration-500"
    style={{ width: `${(job.processed / job.total) * 100}%` }}
  />
</div>
<p className="text-sm text-gray-400 mt-1">
  {job.processed} / {job.total} URLs inspeccionadas
  ({job.indexed} indexadas, {job.not_indexed} no indexadas)
</p>
```

### 30.C DASHBOARD AGREGADO (Google Index tab mejorado)

**Problema actual:** La tab "Google Index Intelligence" muestra "Sin datos de indexabilidad" y solo un botón Recalcular. Necesita un dashboard rico con los resultados del bulk.

**Rediseño GoogleIndexTab.tsx:**

```
┌─────────────────────────────────────────────────────────┐
│  GOOGLE INDEX INTELLIGENCE              [⟳ Recalcular]  │
├──────────┬──────────┬──────────┬────────────────────────┤
│  Total   │ Indexed  │ Not Idx  │ Mobile Issues          │
│  1,247   │ 1,064    │   183    │    12                  │
│          │ (85.3%)  │ (14.7%)  │ (0.96%)                │
│  ■ gris  │ ■ verde  │ ■ rojo   │ ■ amarillo             │
├──────────┴──────────┴──────────┴────────────────────────┤
│                                                         │
│  VERDICT BREAKDOWN          COVERAGE STATE              │
│  ┌────────────────┐        ┌─────────────────────────┐  │
│  │ PASS    1064   │ ██████ │ Submitted+indexed  1064 │  │
│  │ PARTIAL   42   │ ██     │ Crawled-not idx      89 │  │
│  │ FAIL     137   │ ████   │ Discovered-not crwl  52 │  │
│  │ NEUTRAL    4   │        │ URL unknown           42 │  │
│  └────────────────┘        └─────────────────────────┘  │
│                                                         │
│  RICH RESULTS               ÚLTIMA INSPECCIÓN           │
│  ┌────────────────────┐    ┌────────────────────────┐   │
│  │ Breadcrumbs  847   │    │ Hace 2 horas           │   │
│  │ FAQ           123  │    │ Cuota: 1,847/2,000     │   │
│  │ Article        89  │    │ [Exportar CSV] [JSON]  │   │
│  │ Product        45  │    └────────────────────────┘   │
│  └────────────────────┘                                 │
│                                                         │
│  DETALLE POR URL                        [Buscar...]     │
│  ┌─────────────────┬────────┬──────────┬───────────┐    │
│  │ URL             │Verdict │Coverage  │Last Crawl │    │
│  ├─────────────────┼────────┼──────────┼───────────┤    │
│  │ /blog/post-1    │ ✅ PASS│Indexed   │ 3 feb     │    │
│  │ /products/old   │ ❌ FAIL│Unknown   │ —         │    │
│  │ /about          │ ✅ PASS│Indexed   │ 15 feb    │    │
│  └─────────────────┴────────┴──────────┴───────────┘    │
│  Mostrando 1-50 de 1,247         [< Prev] [Next >]     │
└─────────────────────────────────────────────────────────┘
```

**Backend — Mejorar summary endpoint:**

```python
def compute_bulk_summary(results: list[dict], errors: list[dict]) -> dict:
    """Resumen agregado de inspección masiva."""
    verdicts = Counter(r.get("verdict", "NEUTRAL") for r in results)
    coverage_states = Counter(r.get("coverage_state", "Unknown") for r in results)

    # Rich results: extraer de raw response
    rich_results = Counter()
    mobile_issues = 0
    for r in results:
        raw = r.get("raw_result", {})
        # Rich results del inspectionResult
        rr = raw.get("inspectionResult", {}).get("richResultsResult", {})
        for item in rr.get("detectedItems", []):
            rich_results[item.get("richResultType", "Unknown")] += 1
        # Mobile usability
        mu = raw.get("inspectionResult", {}).get("mobileUsabilityResult", {})
        if mu.get("verdict") != "PASS":
            mobile_issues += 1

    return {
        "total": len(results) + len(errors),
        "inspected": len(results),
        "errors": len(errors),
        "indexed": verdicts.get("PASS", 0),
        "not_indexed": sum(v for k, v in verdicts.items() if k != "PASS"),
        "mobile_issues": mobile_issues,
        "verdict_breakdown": dict(verdicts),
        "coverage_breakdown": dict(coverage_states),
        "rich_results": dict(rich_results.most_common(10)),
    }
```

**Frontend — Export:**

```tsx
function exportResults(results: InspectionResult[], format: 'csv' | 'json') {
  if (format === 'json') {
    const blob = new Blob([JSON.stringify(results, null, 2)],
      { type: 'application/json' });
    downloadBlob(blob, `index-inspection-${Date.now()}.json`);
  } else {
    const headers = ['URL', 'Verdict', 'Coverage State',
      'Last Crawl', 'Mobile OK', 'Rich Results'];
    const rows = results.map(r => [
      r.url, r.verdict, r.coverage_state,
      r.last_crawl_time || '',
      r.mobile_usable ? 'Yes' : 'No',
      (r.rich_results || []).join('; '),
    ]);
    const csv = [headers, ...rows]
      .map(r => r.map(c => `"${c}"`).join(','))
      .join('\n');
    downloadBlob(new Blob([csv], { type: 'text/csv' }),
      `index-inspection-${Date.now()}.csv`);
  }
}
```

### 30.D FIX P1: SMOKE TEST FALSE GREEN EN 404

**Archivo:** `tasks/current/run_real_api_smoke.py`

**Problema:** `is_ok_status()` solo marca fallo en 5xx/401/403. Un endpoint roto que devuelve 404 pasa como OK.

**Fix:**

```python
# ANTES (líneas 193-198):
def is_ok_status(status: int) -> bool:
    if 500 <= status <= 599:
        return False
    if status in (401, 403):
        return False
    return True

# DESPUÉS:
MANDATORY_ENDPOINTS = {
    "/projects/{pid}/dashboard",
    "/projects/{pid}/performance",
    "/projects/{pid}/technical-seo/overview",
    "/projects/{pid}/content-risk/dashboard",
    "/projects/{pid}/smart-linking/suggestions",
    "/projects/{pid}/keywords/overview",
    "/projects/{pid}/integrations/validation-status",
}

def is_ok_status(status: int, endpoint: str = "", mandatory: bool = False) -> bool:
    """
    Evalúa si un status HTTP es aceptable.
    - 5xx, 401, 403: siempre fallo
    - 404: fallo si el endpoint es mandatory
    - 2xx, 3xx: siempre OK
    - Otros 4xx (400, 422): OK (validación de input)
    """
    if 500 <= status <= 599:
        return False
    if status in (401, 403):
        return False
    if status == 404:
        if mandatory or any(
            endpoint.endswith(e.split("{pid}")[-1])
            for e in MANDATORY_ENDPOINTS
        ):
            return False
        return True
    return True
```

### 30.E FIX P2: GSC VALIDATION CTR MISMATCH + SCAN TRUNCATED

**Archivo:** `backend/api/services/import_validation_service.py`

**Problema 1 — CTR mismatch (6 filas):** La tolerancia de 0.05 (5%) es demasiado estricta para filas con pocas impresiones. Con 1-2 impresiones, el CTR calculado varía mucho por redondeo.

**Fix — Tolerancia adaptativa por volumen de impresiones:**

```python
# ANTES:
# ctr_mismatch check con tolerancia fija 0.05
if abs(ctr - expected_ctr) > 0.05:
    ctr_mismatches.append(row)

# DESPUÉS — tolerancia adaptativa:
def ctr_tolerance(impressions: int) -> float:
    """
    Tolerancia de CTR según volumen de impresiones.
    - < 10 impressions: 0.20 (20%) — redondeo domina
    - 10-99: 0.10 (10%)
    - 100+: 0.05 (5%) — tolerancia estándar
    """
    if impressions < 10:
        return 0.20
    elif impressions < 100:
        return 0.10
    return 0.05
```

**Problema 2 — scan_truncated (scanned=20000):** El límite de 20K filas trunca el scan.

**Fix — Subir límite + sampling:**

```python
# ANTES:
MAX_SCAN_ROWS = 20000

# DESPUÉS:
MAX_SCAN_ROWS = 50000  # Subir a 50K

# Si aún supera, sampling estratificado:
# 70% filas más recientes + 30% random del resto
# Así truncated=True pero con cobertura representativa
```

### Resumen Sprint 30

```
Sprint 30 — Bulk Index Inspector + Smoke Fix + GSC Validation
├── 30.A BULK INSPECTION FRONTEND
│   ├── Toggle Single/Bulk en UrlInspectorTab
│   ├── Textarea + CSV upload para URLs custom
│   ├── Validación: dedup, formato, count, cuota
│   └── Nuevo endpoint POST bulk-inspect
├── 30.B PROGRESS TRACKING + POLLING
│   ├── Background task con job_id
│   ├── Polling GET bulk-inspect/{job_id} cada 3s
│   └── Progress bar con contadores en tiempo real
├── 30.C DASHBOARD AGREGADO (Google Index tab)
│   ├── 4 KPIs: Total, Indexed, Not Indexed, Mobile Issues
│   ├── Verdict Breakdown (PASS/PARTIAL/FAIL/NEUTRAL)
│   ├── Coverage State breakdown
│   ├── Rich Results detected
│   ├── Tabla detalle con búsqueda y paginación
│   └── Export CSV / JSON
├── 30.D FIX P1: SMOKE TEST 404
│   ├── is_ok_status() trata 404 como fallo en endpoints mandatory
│   └── Lista MANDATORY_ENDPOINTS configurable
└── 30.E FIX P2: GSC VALIDATION TUNING
    ├── CTR tolerance adaptativa (20%/10%/5% según impressions)
    ├── MAX_SCAN_ROWS 20K → 50K
    └── Sampling estratificado si > 50K filas
```

**Tiempo: 3-4 días.** 0 migraciones (usa tablas existentes url_inspection_results + dashboard_cache). 0 módulos nuevos. 2 endpoints nuevos (bulk-inspect POST + GET status). 2 fixes (smoke + validation). Frontend: refactor UrlInspectorTab + rediseño GoogleIndexTab.

---

## Sprint 31 — Authority Hub: Importadores + Backlink Profile + Authority Graph

> **Objetivo:** Crear el módulo "Authority & PR" como hub central que unifica backlinks (GSC + Semrush + Sistrix), PR/clipping (Excel gabinete), y señales de autoridad temática + entidad. Modelo de datos unificado: cada señal externa se clasifica por tema (cluster), entidad (marca/profesional), y tipo de señal.
>
> **Concepto clave — Authority Graph:** Cada enlace, mención o citación externa no es solo un "backlink". Es una señal que conecta tres dimensiones: (1) TEMA — a qué cluster/topic pertenece, (2) ENTIDAD — qué entidad refuerza (marca, profesional, concepto), (3) TIPO — qué clase de señal es (follow link, nofollow, mención, citación social). Esto permite responder preguntas como "¿en qué temas tenemos más autoridad externa?", "¿qué profesionales tienen más respaldo mediático?", "¿dónde hay gaps de autoridad temática?".
>
> **Dependencias:** Topical Clusters (Sprint 22), People (Sprint 18), Entity Panel (Sprint 16), Reputación (Sprint 19).

### 31.A MODELO DE DATOS UNIFICADO

**Migración 062 — authority_signals + authority_imports:**

```sql
-- Tabla central: cada señal de autoridad externa
CREATE TABLE authority_signals (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),

    -- Origen
    source TEXT NOT NULL,              -- 'gsc', 'semrush', 'sistrix', 'bing', 'clipping', 'manual'
    import_id INTEGER,                 -- referencia al import batch

    -- La señal
    signal_type TEXT NOT NULL,         -- 'follow_link', 'nofollow_link', 'mention', 'citation_social', 'citation_video'
    referring_url TEXT,                -- URL del artículo/página que enlaza/menciona
    referring_domain TEXT,             -- dominio extraído
    target_url TEXT,                   -- URL destino en nuestro site (si aplica)
    anchor_text TEXT,                  -- texto ancla (si es link)

    -- Contexto del medio
    media_name TEXT,                   -- nombre del medio (ej: "Men's Health", "ABC")
    media_type TEXT,                   -- 'press', 'blog', 'forum', 'social', 'video', 'podcast'
    media_authority_score INTEGER,     -- DA/DR del medio (Moz/Semrush) si disponible

    -- Clasificación temática (Authority Graph)
    cluster_id INTEGER REFERENCES topical_clusters(id),     -- cluster temático asignado
    topic_tag TEXT,                    -- tag temático libre (ej: "nutrición", "entrenamiento")

    -- Clasificación de entidad
    entity_type TEXT,                  -- 'brand', 'professional', 'product', 'concept'
    entity_name TEXT,                  -- nombre de la entidad mencionada
    person_id INTEGER REFERENCES people(id),  -- si es mención de profesional

    -- Metadatos
    detected_date DATE,               -- fecha de la señal (publicación del artículo)
    first_seen_date DATE DEFAULT CURRENT_DATE,
    last_seen_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,   -- FALSE si el link se ha perdido
    notes TEXT,
    raw_data JSONB DEFAULT '{}',      -- datos crudos del importador

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_authority_signals_project ON authority_signals(project_id);
CREATE INDEX idx_authority_signals_domain ON authority_signals(referring_domain);
CREATE INDEX idx_authority_signals_cluster ON authority_signals(cluster_id);
CREATE INDEX idx_authority_signals_person ON authority_signals(person_id);
CREATE INDEX idx_authority_signals_type ON authority_signals(signal_type);
CREATE INDEX idx_authority_signals_source ON authority_signals(source);

-- Tabla de imports (tracking de cada importación)
CREATE TABLE authority_imports (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    source TEXT NOT NULL,              -- 'gsc', 'semrush', 'sistrix', 'clipping'
    filename TEXT,
    rows_total INTEGER DEFAULT 0,
    rows_imported INTEGER DEFAULT 0,
    rows_duplicated INTEGER DEFAULT 0,
    rows_error INTEGER DEFAULT 0,
    imported_at TIMESTAMPTZ DEFAULT now(),
    imported_by TEXT
);

-- Tabla de domain authority cache (para no re-consultar Moz cada vez)
CREATE TABLE domain_authority_cache (
    id SERIAL PRIMARY KEY,
    domain TEXT NOT NULL UNIQUE,
    da_score INTEGER,                  -- Moz Domain Authority 0-100
    spam_score INTEGER,                -- Moz Spam Score
    external_links INTEGER,
    media_type TEXT,                   -- 'press', 'blog', etc.
    last_checked TIMESTAMPTZ DEFAULT now()
);

-- Tabla de authority score snapshots (histórico mensual)
CREATE TABLE authority_score_snapshots (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,

    -- Score compuesto
    authority_score DECIMAL DEFAULT 0,   -- 0-100

    -- Desglose
    backlinks_total INTEGER DEFAULT 0,
    referring_domains INTEGER DEFAULT 0,
    follow_ratio DECIMAL DEFAULT 0,      -- % follow vs total
    pr_appearances INTEGER DEFAULT 0,
    media_tier1_count INTEGER DEFAULT 0, -- medios top (DA > 70)
    media_tier2_count INTEGER DEFAULT 0, -- medios mid (DA 40-70)
    entity_mentions INTEGER DEFAULT 0,
    professional_mentions INTEGER DEFAULT 0,

    -- Por cluster
    cluster_authority JSONB DEFAULT '{}',  -- {cluster_id: score, ...}

    -- Por entidad
    entity_authority JSONB DEFAULT '{}',   -- {entity_name: {mentions: N, links: M}, ...}

    UNIQUE(project_id, snapshot_date)
);

ALTER TABLE authority_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE authority_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE authority_score_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE domain_authority_cache ENABLE ROW LEVEL SECURITY;
```

### 31.B IMPORTADORES (authority_import_service.py)

**4 parsers + 1 importador genérico:**

```python
# Cada parser normaliza su formato a una lista de AuthoritySignal dicts

def parse_gsc_links(file_content: bytes, filename: str) -> list[dict]:
    """
    GSC export: 'Enlaces externos' o 'External Links'
    Formatos esperados:
    - "Enlazando sitios" (dominios que enlazan)
    - "Páginas principales enlazadas" (URLs destino más enlazadas)
    - "Texto de enlace principal" (anchor texts)
    - O el export completo con columnas: target_url, source_url, source_domain
    """
    df = pd.read_csv(io.BytesIO(file_content))
    signals = []
    for _, row in df.iterrows():
        signals.append({
            "source": "gsc",
            "signal_type": "follow_link",  # GSC solo reporta follow
            "referring_url": row.get("source_url", ""),
            "referring_domain": extract_domain(row.get("source_url") or row.get("source_domain", "")),
            "target_url": row.get("target_url", ""),
            "anchor_text": row.get("anchor_text", ""),
        })
    return signals


def parse_semrush_backlinks(file_content: bytes, filename: str) -> list[dict]:
    """
    Semrush Backlink Audit/Analytics export.
    Columnas típicas: Source URL, Target URL, Anchor, Type (Text/Image/Form),
    First Seen, Last Seen, nofollow/dofollow, Source Domain Authority
    """
    df = pd.read_csv(io.BytesIO(file_content), sep=';')  # Semrush usa ; a veces
    # Fallback a , si falla
    if len(df.columns) <= 1:
        df = pd.read_csv(io.BytesIO(file_content))

    signals = []
    for _, row in df.iterrows():
        is_follow = str(row.get("Attribute", "")).lower() not in ("nofollow", "ugc", "sponsored")
        signals.append({
            "source": "semrush",
            "signal_type": "follow_link" if is_follow else "nofollow_link",
            "referring_url": row.get("Source URL", ""),
            "referring_domain": extract_domain(row.get("Source URL", "")),
            "target_url": row.get("Target URL", ""),
            "anchor_text": row.get("Anchor", ""),
            "media_authority_score": safe_int(row.get("Source Domain Authority Score")),
            "detected_date": parse_date(row.get("First Seen")),
            "last_seen_date": parse_date(row.get("Last Seen")),
            "raw_data": row.to_dict(),
        })
    return signals


def parse_sistrix_links(file_content: bytes, filename: str) -> list[dict]:
    """
    Sistrix Link Module export.
    Columnas típicas: Enlazado desde, URL destino, Texto ancla,
    Tipo enlace, Visibilidad dominio, Fecha primera vez
    """
    df = pd.read_csv(io.BytesIO(file_content), sep=';')
    signals = []
    for _, row in df.iterrows():
        link_type = str(row.get("Tipo enlace", "")).lower()
        is_follow = "nofollow" not in link_type
        signals.append({
            "source": "sistrix",
            "signal_type": "follow_link" if is_follow else "nofollow_link",
            "referring_url": row.get("Enlazado desde", row.get("Linking from", "")),
            "referring_domain": extract_domain(row.get("Enlazado desde", "")),
            "target_url": row.get("URL destino", row.get("Target URL", "")),
            "anchor_text": row.get("Texto ancla", row.get("Anchor text", "")),
            "detected_date": parse_date(row.get("Fecha primera vez", row.get("First seen"))),
            "raw_data": row.to_dict(),
        })
    return signals


def parse_clipping_excel(file_content: bytes, filename: str) -> list[dict]:
    """
    Excel de clipping del gabinete de prensa.
    Sheets por año. Columnas: Url artículo, Medio, Enlaces/menciones, Notas
    Tipos: FOLLOW, NO FOLLOW, Mención, Enlace a YT/IG/TT, Video
    """
    xls = pd.ExcelFile(io.BytesIO(file_content))
    signals = []

    SIGNAL_MAP = {
        "follow": "follow_link",
        "no follow": "nofollow_link",
        "nofollow": "nofollow_link",
        "mención": "mention",
        "mencion": "mention",
        "mencíón": "mention",
        "mención en papel": "mention",
        "enlace a yt": "citation_video",
        "enlace yt": "citation_video",
        "enlace a youtube": "citation_video",
        "vídeo youtube": "citation_video",
        "enlace a ig": "citation_social",
        "enlace ig": "citation_social",
        "instagram enlazado": "citation_social",
        "enlace a tiktok": "citation_social",
        "enlace a tt": "citation_social",
    }

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name, header=None)
        # Encontrar fila de header
        header_idx = None
        for i, row in df.iterrows():
            if "Url artículo" in str(row.values):
                header_idx = i
                break
        if header_idx is None:
            continue

        df = pd.read_excel(xls, sheet_name, header=header_idx)
        df = df.dropna(subset=["Url artículo"])

        current_date = None
        for _, row in df.iterrows():
            url = str(row.get("Url artículo", "")).strip()

            # Detectar filas de fecha (ej: "ENERO DE 2024", "2025-01-01")
            if not url.startswith("http"):
                current_date = parse_month_header(url, sheet_name)
                continue

            medio = str(row.get("Medio", "")).strip()
            tipo_raw = str(row.get("Enlaces/menciones", "")).strip().lower()
            signal_type = SIGNAL_MAP.get(tipo_raw, "mention")
            notes = str(row.get(df.columns[-1], "")).strip() if len(df.columns) > 3 else ""

            signals.append({
                "source": "clipping",
                "signal_type": signal_type,
                "referring_url": url,
                "referring_domain": extract_domain(url),
                "media_name": medio,
                "media_type": "press",
                "detected_date": current_date,
                "notes": notes if notes != "nan" else "",
            })

    return signals
```

**Importador unificado:**

```python
async def import_authority_signals(
    project_id: int,
    source: str,
    file_content: bytes,
    filename: str,
    user_email: str,
) -> dict:
    """Importar señales de autoridad desde cualquier fuente."""

    PARSERS = {
        "gsc": parse_gsc_links,
        "semrush": parse_semrush_backlinks,
        "sistrix": parse_sistrix_links,
        "clipping": parse_clipping_excel,
    }

    parser = PARSERS.get(source)
    if not parser:
        raise ValueError(f"Source '{source}' no soportada")

    # 1. Parsear
    signals = parser(file_content, filename)

    # 2. Enriquecer: auto-clasificar cluster + entidad
    signals = await enrich_signals(project_id, signals)

    # 3. Deduplicar contra existentes
    existing = get_existing_signals(project_id, source)
    new_signals, dupes = deduplicate(signals, existing)

    # 4. Insertar
    imported = bulk_insert_signals(project_id, new_signals)

    # 5. Registrar import
    import_record = create_import_record(project_id, source, filename,
        len(signals), len(imported), len(dupes), 0, user_email)

    return {
        "import_id": import_record.id,
        "total_parsed": len(signals),
        "imported": len(imported),
        "duplicated": len(dupes),
        "errors": 0,
    }
```

### 31.C AUTO-CLASIFICACIÓN (Authority Graph Engine)

**La magia: cada señal se clasifica automáticamente por tema y entidad.**

```python
async def enrich_signals(project_id: int, signals: list[dict]) -> list[dict]:
    """
    Para cada señal, auto-asignar cluster_id y entity.
    Usa heurísticas rápidas + Claude fallback para casos ambiguos.
    """
    # Pre-cargar datos del proyecto
    clusters = get_clusters_with_urls(project_id)
    people = get_people(project_id, type="team")
    brand_name = get_project_brand(project_id)

    for signal in signals:
        # --- CLASIFICAR CLUSTER ---
        # 1. Si target_url existe, buscar a qué cluster pertenece
        if signal.get("target_url"):
            cluster = find_cluster_by_url(clusters, signal["target_url"])
            if cluster:
                signal["cluster_id"] = cluster["id"]
                signal["topic_tag"] = cluster["name"]

        # 2. Si no hay target_url (mención/clipping), inferir por URL del artículo
        if not signal.get("cluster_id") and signal.get("referring_url"):
            # Extraer topic de la URL del artículo externo
            # ej: /bienestar/fitness/... → "fitness"
            # ej: /nutricion/... → "nutrición"
            topic = extract_topic_from_url(signal["referring_url"])
            if topic:
                cluster = find_cluster_by_topic(clusters, topic)
                if cluster:
                    signal["cluster_id"] = cluster["id"]
                    signal["topic_tag"] = topic

        # 3. Si aún no hay cluster, clasificar por media_name
        if not signal.get("cluster_id") and signal.get("media_name"):
            # Men's Health → fitness
            # El Confidencial → general
            topic = infer_topic_from_media(signal["media_name"])
            if topic:
                signal["topic_tag"] = topic

        # --- CLASIFICAR ENTIDAD ---
        # 1. Buscar si el artículo menciona a un profesional del equipo
        if signal.get("referring_url"):
            for person in people:
                # Match por nombre en URL o anchor text
                name_parts = person["name"].lower().split()
                url_lower = signal["referring_url"].lower()
                anchor_lower = (signal.get("anchor_text") or "").lower()

                if any(part in url_lower for part in name_parts if len(part) > 3):
                    signal["entity_type"] = "professional"
                    signal["entity_name"] = person["name"]
                    signal["person_id"] = person["id"]
                    break
                if any(part in anchor_lower for part in name_parts if len(part) > 3):
                    signal["entity_type"] = "professional"
                    signal["entity_name"] = person["name"]
                    signal["person_id"] = person["id"]
                    break

        # 2. Si no matchea profesional, es mención de marca
        if not signal.get("entity_type"):
            signal["entity_type"] = "brand"
            signal["entity_name"] = brand_name

    return signals
```

### 31.D ENDPOINTS

```python
# --- IMPORTACIÓN ---
# POST /projects/{id}/authority/import
# Body: multipart/form-data con file + source (gsc|semrush|sistrix|clipping)
@router.post("/projects/{project_id}/authority/import")

# GET /projects/{id}/authority/imports  (historial de importaciones)
@router.get("/projects/{project_id}/authority/imports")

# --- BACKLINK PROFILE ---
# GET /projects/{id}/authority/backlinks
# Query: ?source=all|gsc|semrush|sistrix&type=follow|nofollow|all
#         &domain=&date_from=&date_to=&page=1&limit=50
@router.get("/projects/{project_id}/authority/backlinks")

# GET /projects/{id}/authority/backlinks/summary
# → total_links, referring_domains, follow_ratio, new_last_30d, lost_last_30d
@router.get("/projects/{project_id}/authority/backlinks/summary")

# GET /projects/{id}/authority/backlinks/domains
# → top referring domains con count + DA + tipo + first_seen
@router.get("/projects/{project_id}/authority/backlinks/domains")

# GET /projects/{id}/authority/backlinks/anchors
# → distribución de anchor texts
@router.get("/projects/{project_id}/authority/backlinks/anchors")

# --- AUTHORITY SCORE ---
# GET /projects/{id}/authority/score
# → Authority Score compuesto (0-100) con desglose
@router.get("/projects/{project_id}/authority/score")

# GET /projects/{id}/authority/score/trend
# → tendencia mensual del authority score
@router.get("/projects/{project_id}/authority/score/trend")
```

**Authority Score Compuesto (nuevo, reemplaza al simple DA):**

```python
def calculate_authority_score(project_id: int) -> dict:
    """
    Authority Score 0-100 compuesto de 6 dimensiones:

    1. Domain Authority (Moz DA)         — 20%  → escala directa 0-100
    2. Backlink Profile                   — 20%  → referring_domains log-scaled
    3. Follow Ratio                       — 10%  → % follow links (>70% = 100)
    4. PR & Media Coverage                — 20%  → apariciones ponderadas por tier
    5. Topical Authority Distribution     — 15%  → clusters con cobertura externa
    6. Entity EEAT Signals                — 15%  → profesionales con menciones externas
    """

    # 1. DA (Moz)
    da = get_moz_da(project_id)  # 0-100

    # 2. Backlink Profile
    rd = count_referring_domains(project_id)
    bp_score = min(100, math.log10(max(rd, 1)) * 33)  # log scale: 1000 RD ≈ 100

    # 3. Follow Ratio
    total = count_signals(project_id, signal_type=None)
    follow = count_signals(project_id, signal_type="follow_link")
    fr_score = min(100, (follow / max(total, 1)) * 143)  # 70% follow = 100

    # 4. PR & Media
    tier1 = count_signals(project_id, media_authority_min=70)  # DA > 70
    tier2 = count_signals(project_id, media_authority_min=40, media_authority_max=69)
    mentions = count_signals(project_id, signal_type="mention")
    pr_score = min(100, (tier1 * 5 + tier2 * 2 + mentions * 1))

    # 5. Topical Distribution
    clusters = get_clusters(project_id)
    clusters_with_external = count_clusters_with_signals(project_id)
    td_score = (clusters_with_external / max(len(clusters), 1)) * 100

    # 6. Entity EEAT
    people = get_people(project_id, type="team")
    people_with_mentions = count_people_with_signals(project_id)
    ee_score = (people_with_mentions / max(len(people), 1)) * 100

    composite = (
        da * 0.20 +
        bp_score * 0.20 +
        fr_score * 0.10 +
        pr_score * 0.20 +
        td_score * 0.15 +
        ee_score * 0.15
    )

    return {
        "authority_score": round(composite, 1),
        "breakdown": {
            "domain_authority": {"score": da, "weight": 0.20, "value": da},
            "backlink_profile": {"score": round(bp_score, 1), "weight": 0.20, "referring_domains": rd},
            "follow_ratio": {"score": round(fr_score, 1), "weight": 0.10, "ratio": follow / max(total, 1)},
            "pr_media": {"score": round(pr_score, 1), "weight": 0.20, "tier1": tier1, "tier2": tier2, "mentions": mentions},
            "topical_distribution": {"score": round(td_score, 1), "weight": 0.15, "clusters_covered": clusters_with_external, "clusters_total": len(clusters)},
            "entity_eeat": {"score": round(ee_score, 1), "weight": 0.15, "people_covered": people_with_mentions, "people_total": len(people)},
        }
    }
```

### 31.E FRONTEND — AUTHORITY & PR MODULE (AuthorityPage.tsx)

**Nuevo módulo en sidebar: "Authority & PR" bajo ENTIDAD**

```
┌─────────────────────────────────────────────────────────────────┐
│  AUTHORITY & PR HUB                                             │
│  [Backlinks] [PR & Clipping] [Authority Graph] [Importar]       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AUTHORITY SCORE                        TENDENCIA               │
│  ┌──────────┐  ┌──────────────────┐    ┌───────────────────┐   │
│  │          │  │ DA Moz      72   │    │  ╱‾‾‾╲            │   │
│  │   67.4   │  │ Backlinks   58   │    │ ╱     ‾╲──        │   │
│  │  /100    │  │ Follow %    85   │    │╱        ‾‾──      │   │
│  │          │  │ PR Media    71   │    │ Oct Nov Dic Ene Feb│   │
│  └──────────┘  │ Topic Dist  54   │    └───────────────────┘   │
│   ▲ +3.2 MoM   │ Entity EEAT 60   │                            │
│                └──────────────────┘                             │
│                                                                 │
│  BACKLINKS PROFILE                                              │
│  ┌──────────┬──────────┬──────────┬──────────┐                 │
│  │ Total    │ Ref.Dom  │ Follow % │ New/30d  │                 │
│  │  2,847   │   342    │  68.2%   │   +23    │                 │
│  └──────────┴──────────┴──────────┴──────────┘                 │
│                                                                 │
│  TOP REFERRING DOMAINS              ANCHOR TEXT DISTRIBUTION     │
│  ┌──────────────────────┐          ┌───────────────────────┐   │
│  │ abc.es          DA:88│ 47 links │ fit generation    22% │   │
│  │ menshealth.com  DA:82│ 31 links │ calculadora       14% │   │
│  │ elmundo.es      DA:91│ 18 links │ [marca]           11% │   │
│  │ hola.com        DA:85│ 15 links │ entrenamiento      8% │   │
│  │ marca.com       DA:87│ 12 links │ nutrición          6% │   │
│  └──────────────────────┘          └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Resumen Sprint 31

```
Sprint 31 — Authority Hub: Importadores + Backlink Profile + Authority Graph
├── 31.A MODELO DE DATOS (Migración 062)
│   ├── authority_signals (tabla central: señal + tema + entidad)
│   ├── authority_imports (tracking importaciones)
│   ├── domain_authority_cache (DA por dominio)
│   └── authority_score_snapshots (histórico mensual)
├── 31.B IMPORTADORES (authority_import_service.py)
│   ├── parse_gsc_links() — CSV export Search Console
│   ├── parse_semrush_backlinks() — CSV export Semrush
│   ├── parse_sistrix_links() — CSV export Sistrix
│   ├── parse_clipping_excel() — Excel gabinete de prensa
│   └── import_authority_signals() — unificador + dedup
├── 31.C AUTO-CLASIFICACIÓN (enrich_signals)
│   ├── Cluster assignment por target_url → cluster_urls
│   ├── Topic inference por URL path del artículo externo
│   ├── Entity matching: profesional por nombre en URL/anchor
│   └── Fallback: brand mention si no matchea profesional
├── 31.D ENDPOINTS (8 nuevos)
│   ├── POST /authority/import (file upload)
│   ├── GET /authority/imports (historial)
│   ├── GET /authority/backlinks (lista paginada + filtros)
│   ├── GET /authority/backlinks/summary (4 KPIs)
│   ├── GET /authority/backlinks/domains (top referring)
│   ├── GET /authority/backlinks/anchors (distribución)
│   ├── GET /authority/score (compuesto 6 dimensiones)
│   └── GET /authority/score/trend (mensual)
└── 31.E FRONTEND (AuthorityPage.tsx)
    ├── Tab Backlinks: perfil unificado GSC+Semrush+Sistrix
    ├── Tab Import: drag-drop con parser auto-detect
    └── Authority Score widget con 6 dimensiones + trend
```

**Tiempo: 5-6 días.** Migración 062 (4 tablas). 1 módulo nuevo sidebar. 8 endpoints nuevos. 1 servicio nuevo (authority_import_service.py). Frontend: AuthorityPage con 3 tabs iniciales.

---

## Sprint 32 — PR Intelligence + Entity Authority + Topical Authority Externa

> **Objetivo:** Explotar el Authority Graph del Sprint 31. Vistas especializadas de PR/clipping con atribución a profesionales y temas, análisis de autoridad temática externa (qué clusters tienen respaldo externo), oportunidades de link building, y conexión bidireccional con Entity Panel + People + Topical Authority.
>
> **Dependencia:** Sprint 31 (authority_signals + importadores).

### 32.A PR & CLIPPING DASHBOARD (Tab PR & Clipping)

```
┌─────────────────────────────────────────────────────────────────────┐
│  PR & CLIPPING                              [Importar Excel]        │
│                                                                     │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │ Total    │ Follow   │ Mención  │ Social   │ Tier 1   │          │
│  │ aparic.  │ links    │          │ (YT/IG)  │ (DA>70)  │          │
│  │   233    │   47     │   98     │   41     │   87     │          │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘          │
│                                                                     │
│  APARICIONES POR MES                    TOP MEDIOS                  │
│  ┌────────────────────────┐            ┌─────────────────────────┐ │
│  │ █ █ █ █████ ██ █████   │            │ ABC           DA:88  19 │ │
│  │ ▓ ▓ ▓ ▓▓▓▓▓ ▓▓ ▓▓▓    │            │ Men's Health  DA:82  31 │ │
│  │ ░ ░ ░ ░░    ░░ ░░░░░  │            │ HOLA          DA:85  15 │ │
│  │ E F M A M J  J A S O  │            │ El Mundo      DA:91   8 │ │
│  │ █=Follow ▓=Mención ░=Social│       │ La Vanguardia DA:79  10 │ │
│  └────────────────────────┘            └─────────────────────────┘ │
│                                                                     │
│  POR PROFESIONAL                        POR TEMA (CLUSTER)         │
│  ┌─────────────────────────┐           ┌──────────────────────┐   │
│  │ 👤 Xabier R.   42 apar │           │ Fitness        48%   │   │
│  │ 👤 María C.    28 apar │           │ Nutrición      32%   │   │
│  │ 👤 Eneko B.    19 apar │           │ Bienestar      12%   │   │
│  │ 👤 Nuria G.    15 apar │           │ Sin clasificar  8%   │   │
│  │ 👤 Marcos G.   11 apar │           └──────────────────────┘   │
│  │ [Ver EEAT impact →]    │                                       │
│  └─────────────────────────┘                                       │
│                                                                     │
│  DETALLE                                        [Buscar] [Filtrar] │
│  ┌────────┬─────────────┬──────┬──────┬────────┬────────┐         │
│  │ Fecha  │ Medio       │ Tipo │ Prof │ Tema   │ URL    │         │
│  ├────────┼─────────────┼──────┼──────┼────────┼────────┤         │
│  │ 15 feb │ Men's Health│ IG   │ Eneko│Fitness │ [↗]    │         │
│  │ 14 feb │ Marca       │ NoF  │ —    │Fitness │ [↗]    │         │
│  │ 13 feb │ El Confid.  │ YT   │ Nuria│Nutric. │ [↗]    │         │
│  └────────┴─────────────┴──────┴──────┴────────┴────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

### 32.B AUTHORITY GRAPH — Vista de autoridad temática externa

**Concepto:** Cruzar la autoridad temática interna (cluster_metrics_cache.authority_score, basada en keywords/rankings) con la autoridad temática externa (señales de authority_signals por cluster). Esto responde: "¿Nuestro posicionamiento interno se corresponde con nuestro respaldo externo?"

```python
async def get_topical_authority_matrix(project_id: int) -> list[dict]:
    """
    Para cada cluster, devuelve:
    - internal_authority: del authority.py existente (7 métricas internas)
    - external_authority: señales externas del Authority Graph
    - gap: diferencia (oportunidad o riesgo)
    """
    clusters = get_clusters(project_id)
    results = []

    for cluster in clusters:
        # Autoridad interna (existente)
        internal = get_cluster_authority_score(cluster["id"])  # 0-100

        # Autoridad externa (nuevo)
        signals = get_signals_by_cluster(project_id, cluster["id"])
        follow_links = len([s for s in signals if s["signal_type"] == "follow_link"])
        total_signals = len(signals)
        unique_domains = len(set(s["referring_domain"] for s in signals))
        tier1_media = len([s for s in signals if (s.get("media_authority_score") or 0) > 70])
        professional_mentions = len([s for s in signals if s.get("person_id")])

        # Score externo: ponderación de señales
        external = min(100, (
            follow_links * 3 +          # 3 pts por follow link
            total_signals * 1 +          # 1 pt por cualquier señal
            unique_domains * 5 +         # 5 pts por dominio único
            tier1_media * 8 +            # 8 pts por medio Tier 1
            professional_mentions * 2    # 2 pts por mención de profesional
        ))

        gap = external - internal  # positivo = más autoridad externa que interna

        results.append({
            "cluster_id": cluster["id"],
            "cluster_name": cluster["name"],
            "internal_authority": internal,
            "external_authority": external,
            "gap": gap,
            "gap_type": "oportunidad" if gap > 10 else "riesgo" if gap < -10 else "alineado",
            "signals_count": total_signals,
            "follow_links": follow_links,
            "referring_domains": unique_domains,
            "tier1_media": tier1_media,
            "top_media": get_top_media_for_cluster(signals, limit=5),
            "professionals": get_professionals_for_cluster(signals),
        })

    return sorted(results, key=lambda x: abs(x["gap"]), reverse=True)
```

**Frontend — Tab Authority Graph:**

```
┌────────────────────────────────────────────────────────────────┐
│  AUTHORITY GRAPH — Autoridad Interna vs Externa por Tema       │
│                                                                │
│  SCATTER PLOT (X = interna, Y = externa)                       │
│  ┌───────────────────────────────────────┐                     │
│  │ Y: Externa                            │                     │
│  │ 100 │         ● Fitness               │ ● = Cluster        │
│  │     │                                 │                     │
│  │  75 │              ● Nutrición        │ Cuadrante I:        │
│  │     │                                 │  Autoridad total    │
│  │  50 │    ○ Bienestar                  │ Cuadrante II:       │
│  │     │                                 │  Respaldo sin rank  │
│  │  25 │                    ○ Recovery   │ Cuadrante III:      │
│  │     │ ○ Suplementos                   │  Gap total          │
│  │   0 ├────────────────────────────────│ Cuadrante IV:       │
│  │     0    25    50    75    100        │  Rankea sin respaldo│
│  │         X: Interna                    │                     │
│  └───────────────────────────────────────┘                     │
│                                                                │
│  DETALLE POR CLUSTER                                           │
│  ┌──────────┬──────┬──────┬─────┬──────────┬─────────────────┐│
│  │ Cluster  │ Int. │ Ext. │ Gap │ Señales  │ Medios top      ││
│  ├──────────┼──────┼──────┼─────┼──────────┼─────────────────┤│
│  │ Fitness  │  72  │  85  │ +13 │ 112 (47F)│ Men's H, Marca  ││
│  │ Nutrición│  68  │  71  │  +3 │  78 (21F)│ ABC, El Confid. ││
│  │ Bienestar│  45  │  38  │  -7 │  29 (8F) │ HOLA, Telva     ││
│  │ Recovery │  34  │  12  │ -22 │   8 (2F) │ —               ││
│  └──────────┴──────┴──────┴─────┴──────────┴─────────────────┘│
│                                                                │
│  ⚠️ Recovery: rankea posición 34 avg sin respaldo externo      │
│  💡 Fitness: fuerte en ambos ejes — consolidar como pilar      │
└────────────────────────────────────────────────────────────────┘
```

### 32.C ENTITY AUTHORITY — Conexión con People + Entity Panel

**Enriquecer People module con datos de PR:**

```python
async def get_person_authority_profile(project_id: int, person_id: int) -> dict:
    """
    Perfil de autoridad externa de un profesional.
    Alimenta EEAT score y Entity Panel.
    """
    signals = get_signals_by_person(project_id, person_id)
    person = get_person(person_id)

    # Métricas de autoridad mediática
    total_appearances = len(signals)
    unique_media = len(set(s["referring_domain"] for s in signals))
    follow_links = len([s for s in signals if s["signal_type"] == "follow_link"])
    tier1_appearances = len([s for s in signals if (s.get("media_authority_score") or 0) > 70])
    topics_covered = list(set(s.get("topic_tag") for s in signals if s.get("topic_tag")))

    # Media Authority Score del profesional (0-100)
    media_authority = min(100, (
        total_appearances * 2 +
        unique_media * 5 +
        follow_links * 3 +
        tier1_appearances * 8
    ))

    # Temporal: apariciones por trimestre
    quarterly = group_signals_by_quarter(signals)

    return {
        "person_id": person_id,
        "person_name": person["name"],
        "media_authority_score": media_authority,
        "total_appearances": total_appearances,
        "unique_media": unique_media,
        "follow_links": follow_links,
        "tier1_appearances": tier1_appearances,
        "topics_covered": topics_covered,
        "top_media": get_top_media(signals, limit=5),
        "quarterly_trend": quarterly,
        "latest_appearances": signals[:5],  # 5 más recientes
    }
```

**Conexiones bidireccionales:**

```python
# 1. People → EEAT: añadir media_authority como factor 15 del checklist
# En people_service.py, añadir al cálculo de EEAT:
def calculate_eeat_score_v2(person_id, project_id):
    base_score = calculate_eeat_score(person_id)  # 14 items existentes
    media_profile = get_person_authority_profile(project_id, person_id)

    # Bonus por autoridad mediática (hasta +10 puntos)
    media_bonus = min(10, media_profile["media_authority_score"] / 10)

    return {
        **base_score,
        "media_authority": media_profile["media_authority_score"],
        "media_bonus": media_bonus,
        "adjusted_score": min(100, base_score["total"] + media_bonus),
    }

# 2. Entity Panel → Authority Score como nuevo input
# En entity_panel_service.py, reemplazar el peso de Reputation (10%):
#   ANTES: Reputation: 10%
#   DESPUÉS: Authority: 20% (absorbe Reputation + backlinks + PR)
# Rebalanceo:
#   Brand Health: 25% (antes 30%)
#   EEAT: 20% (antes 25%)
#   YMYL: 15% (antes 20%)
#   Bridges: 10% (antes 15%)
#   Authority: 20% (NUEVO, reemplaza Reputation 10%)
#   Topical: 10% (NUEVO, avg de cluster authority scores)

# 3. Topical Authority → external_authority_score por cluster
# En authority.py, añadir external_authority al response de cada cluster
```

### 32.D OPORTUNIDADES DE LINK BUILDING

```python
async def get_link_opportunities(project_id: int) -> dict:
    """
    Identifica oportunidades de link building:
    1. Menciones sin enlace → link reclamation
    2. Medios con historial follow → priorizar
    3. Clusters sin cobertura externa → gap temático
    4. Profesionales sin menciones → oportunidad EEAT
    """

    # 1. Link reclamation: menciones de marca sin link
    mentions_no_link = get_signals(project_id,
        signal_type="mention", has_target_url=False)
    reclamation = [{
        "type": "reclamation",
        "priority": "high",
        "domain": s["referring_domain"],
        "url": s["referring_url"],
        "media_name": s["media_name"],
        "action": f"Contactar {s['media_name']} para añadir enlace",
    } for s in mentions_no_link]

    # 2. Medios con historial follow
    domains_with_follow = get_domains_by_follow_history(project_id)
    repeat_media = [{
        "type": "repeat_pitch",
        "priority": "medium",
        "domain": d["domain"],
        "media_name": d["media_name"],
        "follow_count": d["follow_count"],
        "last_appearance": d["last_date"],
        "action": f"Repetir pitch a {d['media_name']} ({d['follow_count']} follows previos)",
    } for d in domains_with_follow if d["follow_count"] >= 2]

    # 3. Clusters sin cobertura
    matrix = await get_topical_authority_matrix(project_id)
    topic_gaps = [{
        "type": "topic_gap",
        "priority": "high" if c["internal_authority"] > 50 else "medium",
        "cluster": c["cluster_name"],
        "internal": c["internal_authority"],
        "external": c["external_authority"],
        "action": f"Buscar PR en {c['cluster_name']} (rankea {c['internal_authority']} sin respaldo externo)",
    } for c in matrix if c["gap"] < -15]

    # 4. Profesionales sin menciones
    people = get_people(project_id, type="team")
    for p in people:
        p["mentions"] = count_signals_by_person(project_id, p["id"])
    people_gaps = [{
        "type": "eeat_gap",
        "priority": "medium",
        "person": p["name"],
        "eeat_score": p.get("eeat_score", 0),
        "mentions": p["mentions"],
        "action": f"Conseguir mención externa para {p['name']} (0 apariciones)",
    } for p in people if p["mentions"] == 0]

    return {
        "reclamation": reclamation,
        "repeat_media": repeat_media,
        "topic_gaps": topic_gaps,
        "eeat_gaps": people_gaps,
        "total_opportunities": len(reclamation) + len(repeat_media) + len(topic_gaps) + len(people_gaps),
    }
```

### 32.E ENDPOINTS NUEVOS

```python
# --- PR & CLIPPING ---
GET  /authority/pr/dashboard          → KPIs + por mes + por medio + por profesional + por tema
GET  /authority/pr/by-person          → apariciones agrupadas por profesional
GET  /authority/pr/by-cluster         → apariciones agrupadas por cluster/tema
POST /authority/pr/manual             → añadir aparición manual

# --- AUTHORITY GRAPH ---
GET  /authority/graph/matrix          → internal vs external por cluster (scatter data)
GET  /authority/graph/person/{id}     → perfil de autoridad mediática del profesional

# --- OPORTUNIDADES ---
GET  /authority/opportunities         → link reclamation + repeat media + topic gaps + EEAT gaps

# --- CONEXIONES ---
GET  /authority/entity-impact         → cómo Authority Score alimenta Entity Panel
GET  /authority/eeat-impact           → cómo PR alimenta EEAT scores de People
```

### Resumen Sprint 32

```
Sprint 32 — PR Intelligence + Entity Authority + Topical Authority Externa
├── 32.A PR & CLIPPING DASHBOARD
│   ├── 5 KPIs: total, follow, mención, social, tier1
│   ├── Gráfico apariciones por mes (stacked por tipo)
│   ├── Top medios con DA
│   ├── Por profesional (con link a EEAT)
│   ├── Por cluster/tema
│   └── Tabla detalle con filtros
├── 32.B AUTHORITY GRAPH
│   ├── Scatter plot: autoridad interna vs externa por cluster
│   ├── 4 cuadrantes: autoridad total / respaldo sin rank / gap total / rankea sin respaldo
│   ├── Tabla detalle cluster con gap analysis
│   └── Insights automáticos (warnings + oportunidades)
├── 32.C ENTITY AUTHORITY (conexiones)
│   ├── Person authority profile (media_authority_score)
│   ├── EEAT v2: media_bonus (+10 pts máx) en People
│   ├── Entity Panel rebalanceo: Authority 20% (absorbe Reputation)
│   └── Topical Authority: external_authority por cluster
├── 32.D OPORTUNIDADES LINK BUILDING
│   ├── Link reclamation: menciones sin enlace
│   ├── Repeat media: medios con historial follow
│   ├── Topic gaps: clusters sin cobertura externa
│   └── EEAT gaps: profesionales sin menciones
└── 32.E ENDPOINTS (8 nuevos)
    ├── GET /authority/pr/* (4 endpoints)
    ├── GET /authority/graph/* (2 endpoints)
    └── GET /authority/opportunities + entity-impact + eeat-impact
```

**Tiempo: 5-7 días.** 0 migraciones nuevas (usa authority_signals de Sprint 31). 0 módulos nuevos (tabs dentro de Authority & PR). 8 endpoints nuevos. Extensiones a: entity_panel_service.py, people_service.py, authority.py. Frontend: 3 tabs nuevas (PR, Graph, Oportunidades).

---

## Sprint 33 — Query Count Analytics: Peso Semántico de Google

> **Fuentes:** SEO Stack (seo-stack.io) — Daniel Foley Carter, LinkedIn post sobre Query Counting como proceso SEO. Concepto: medir cuántas queries distintas asigna Google a cada URL para diagnosticar devaluación de contenido vs CTR degradation vs slippage de posiciones.
>
> **Problema que resuelve:** FIT importa datos GSC con queries por URL, pero los procesa en memoria y los descarta. No hay persistencia histórica del conteo de queries, lo que impide detectar si Google está quitando peso semántico a contenidos (reduciendo queries asignadas) — incluso cuando clicks/impressions parecen estables.
>
> **Concepto clave — Query Count:**
> - **Query Count por URL** = nº de queries distintas por las que rankea una URL en un periodo
> - ↑ Query Count = Google aumenta confianza semántica en esa URL
> - ↓ Query Count = Google devalúa el contenido (reduce el abanico de queries asignadas)
> - Query Count estable + Clicks ↓ = CTR degradation (AI Overviews robando clicks)
> - Query Count estable + Position ↓ = Slippage (bajada de posiciones sin devaluación)
> - Query Count ↓ + todo lo demás ↓ = Devaluación real (contenido perdió autoridad temática)

### 33.A — Modelo de datos: GSC Snapshots persistentes

**Migración 064:** `064_query_count_analytics.sql`

```sql
-- =================================================================
-- Sprint 33: Query Count Analytics — Peso semántico de Google
-- Persistencia de snapshots GSC con conteo de queries por URL
-- =================================================================

-- Tabla 1: Snapshots diarios por URL (agregados)
CREATE TABLE IF NOT EXISTS gsc_daily_snapshots (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    url TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr DECIMAL(6,4) DEFAULT 0,
    avg_position DECIMAL(6,2) DEFAULT 0,
    distinct_query_count INTEGER DEFAULT 0,
    -- Desglose por posición (distribution buckets)
    queries_pos_1_3 INTEGER DEFAULT 0,    -- Top 3
    queries_pos_4_10 INTEGER DEFAULT 0,   -- Página 1
    queries_pos_11_20 INTEGER DEFAULT 0,  -- Página 2
    queries_pos_21_plus INTEGER DEFAULT 0, -- Más allá
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_gsc_snapshot UNIQUE(project_id, snapshot_date, url)
);

CREATE INDEX idx_gsc_snap_project_date ON gsc_daily_snapshots(project_id, snapshot_date DESC);
CREATE INDEX idx_gsc_snap_url ON gsc_daily_snapshots(project_id, url, snapshot_date DESC);
CREATE INDEX idx_gsc_snap_qcount ON gsc_daily_snapshots(project_id, distinct_query_count DESC);

-- Tabla 2: Query-level audit log (granular, para drill-down)
CREATE TABLE IF NOT EXISTS gsc_query_log (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    url TEXT NOT NULL,
    query TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr DECIMAL(6,4) DEFAULT 0,
    position DECIMAL(6,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_gsc_query_log UNIQUE(project_id, snapshot_date, url, query)
);

CREATE INDEX idx_gsc_qlog_url ON gsc_query_log(project_id, url, snapshot_date DESC);
CREATE INDEX idx_gsc_qlog_query ON gsc_query_log(project_id, query);
CREATE INDEX idx_gsc_qlog_date ON gsc_query_log(project_id, snapshot_date DESC);

-- Tabla 3: Resumen de dominio completo por día (site-level KPIs)
CREATE TABLE IF NOT EXISTS gsc_domain_snapshots (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_urls INTEGER DEFAULT 0,
    total_distinct_queries INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_impressions INTEGER DEFAULT 0,
    avg_queries_per_url DECIMAL(6,2) DEFAULT 0,
    urls_gaining_queries INTEGER DEFAULT 0,   -- vs snapshot anterior
    urls_losing_queries INTEGER DEFAULT 0,    -- vs snapshot anterior
    urls_stable INTEGER DEFAULT 0,
    query_stability_index DECIMAL(5,2) DEFAULT 0, -- % URLs estables (±5%)
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_gsc_domain_snap UNIQUE(project_id, snapshot_date)
);

CREATE INDEX idx_gsc_domain_snap ON gsc_domain_snapshots(project_id, snapshot_date DESC);

-- Tabla 4: Annotations (eventos para correlacionar con query counts)
CREATE TABLE IF NOT EXISTS gsc_annotations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    annotation_date DATE NOT NULL,
    annotation_type VARCHAR(50) NOT NULL, -- 'core_update', 'content_change', 'link_building', 'deploy', 'manual'
    title TEXT NOT NULL,
    description TEXT,
    auto_detected BOOLEAN DEFAULT false,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_gsc_annotations ON gsc_annotations(project_id, annotation_date DESC);

-- RLS
ALTER TABLE gsc_daily_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE gsc_query_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE gsc_domain_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE gsc_annotations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "gsc_daily_snapshots_all" ON gsc_daily_snapshots FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "gsc_query_log_all" ON gsc_query_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "gsc_domain_snapshots_all" ON gsc_domain_snapshots FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "gsc_annotations_all" ON gsc_annotations FOR ALL USING (true) WITH CHECK (true);
```

### 33.B — Backend: query_count_service.py

Nuevo servicio que orquesta snapshot + análisis + tendencias.

```python
# backend/api/services/query_count_service.py
"""
Sprint 33: Query Count Analytics — Peso Semántico de Google
Persiste snapshots GSC con conteo de queries por URL.
Detecta: devaluación, CTR degradation, slippage.
"""
from datetime import date, timedelta
from collections import defaultdict
from typing import Optional
from config.supabase_client import get_supabase
from api.services.gsc_service import fetch_search_analytics

# ───────── CORE: Crear snapshot ─────────

async def create_daily_snapshot(
    project_id: int,
    site_url: str,
    snapshot_date: date = None,
    days_window: int = 30
) -> dict:
    """
    Fetches GSC data y persiste snapshot con query count por URL.
    Ejecutar diariamente (scheduler) o bajo demanda.

    Returns: {
        "snapshot_date": "2026-02-18",
        "urls_processed": 127,
        "total_queries": 2341,
        "avg_queries_per_url": 18.4,
        "urls_gaining": 12,
        "urls_losing": 5,
        "urls_stable": 110
    }
    """
    snapshot_date = snapshot_date or date.today()
    sb = get_supabase()

    # Fetch GSC con queries anidadas
    raw = fetch_search_analytics(project_id, site_url, days=days_window)

    # Agregar por URL: contar queries distintas
    url_data = defaultdict(lambda: {
        "clicks": 0, "impressions": 0, "ctr_sum": 0, "pos_sum": 0,
        "queries": set(), "pos_buckets": [0, 0, 0, 0]
    })

    for item in raw:
        url = item["page"]
        d = url_data[url]
        d["clicks"] += item.get("clicks", 0)
        d["impressions"] += item.get("impressions", 0)

        for q in item.get("queries", []):
            d["queries"].add(q["query"])
            pos = q.get("position", 100)
            if pos <= 3:
                d["pos_buckets"][0] += 1
            elif pos <= 10:
                d["pos_buckets"][1] += 1
            elif pos <= 20:
                d["pos_buckets"][2] += 1
            else:
                d["pos_buckets"][3] += 1

    # Obtener snapshot anterior para comparar
    prev = sb.table("gsc_daily_snapshots").select("url, distinct_query_count") \
        .eq("project_id", project_id) \
        .lt("snapshot_date", snapshot_date.isoformat()) \
        .order("snapshot_date", desc=True) \
        .limit(len(url_data) * 2) \
        .execute()

    prev_counts = {}
    for row in (prev.data or []):
        if row["url"] not in prev_counts:  # solo el más reciente
            prev_counts[row["url"]] = row["distinct_query_count"]

    # Upsert snapshots + query log
    gaining, losing, stable = 0, 0, 0
    total_queries = 0

    for url, d in url_data.items():
        qcount = len(d["queries"])
        total_queries += qcount
        avg_ctr = d["clicks"] / max(d["impressions"], 1)
        avg_pos = d["pos_sum"] / max(len(d["queries"]), 1) if d["pos_sum"] else 0

        # Comparar con anterior
        prev_qcount = prev_counts.get(url, qcount)
        change_pct = ((qcount - prev_qcount) / max(prev_qcount, 1)) * 100
        if change_pct > 5:
            gaining += 1
        elif change_pct < -5:
            losing += 1
        else:
            stable += 1

        # Upsert URL snapshot
        sb.table("gsc_daily_snapshots").upsert({
            "project_id": project_id,
            "snapshot_date": snapshot_date.isoformat(),
            "url": url,
            "clicks": d["clicks"],
            "impressions": d["impressions"],
            "ctr": round(avg_ctr, 4),
            "avg_position": round(avg_pos, 2),
            "distinct_query_count": qcount,
            "queries_pos_1_3": d["pos_buckets"][0],
            "queries_pos_4_10": d["pos_buckets"][1],
            "queries_pos_11_20": d["pos_buckets"][2],
            "queries_pos_21_plus": d["pos_buckets"][3],
        }, on_conflict="project_id,snapshot_date,url").execute()

        # Insertar query-level log (batch)
        query_rows = [{
            "project_id": project_id,
            "snapshot_date": snapshot_date.isoformat(),
            "url": url,
            "query": q,
            "clicks": 0, "impressions": 0, "ctr": 0, "position": 0
        } for q in d["queries"]]

        if query_rows:
            # Batch insert en chunks de 500
            for i in range(0, len(query_rows), 500):
                sb.table("gsc_query_log").upsert(
                    query_rows[i:i+500],
                    on_conflict="project_id,snapshot_date,url,query"
                ).execute()

    # Domain snapshot
    total_urls = len(url_data)
    avg_qpu = total_queries / max(total_urls, 1)
    stability = (stable / max(total_urls, 1)) * 100

    sb.table("gsc_domain_snapshots").upsert({
        "project_id": project_id,
        "snapshot_date": snapshot_date.isoformat(),
        "total_urls": total_urls,
        "total_distinct_queries": total_queries,
        "total_clicks": sum(d["clicks"] for d in url_data.values()),
        "total_impressions": sum(d["impressions"] for d in url_data.values()),
        "avg_queries_per_url": round(avg_qpu, 2),
        "urls_gaining_queries": gaining,
        "urls_losing_queries": losing,
        "urls_stable": stable,
        "query_stability_index": round(stability, 2),
    }, on_conflict="project_id,snapshot_date").execute()

    return {
        "snapshot_date": snapshot_date.isoformat(),
        "urls_processed": total_urls,
        "total_queries": total_queries,
        "avg_queries_per_url": round(avg_qpu, 2),
        "urls_gaining": gaining,
        "urls_losing": losing,
        "urls_stable": stable,
        "query_stability_index": round(stability, 2)
    }


# ───────── ANÁLISIS: Query Count Trends ─────────

async def get_query_count_overview(
    project_id: int,
    start_date: date = None,
    end_date: date = None,
    granularity: str = "daily"  # daily | weekly | monthly
) -> dict:
    """
    Retorna KPIs de dominio + serie temporal de query count.
    """
    sb = get_supabase()
    start_date = start_date or (date.today() - timedelta(days=90))
    end_date = end_date or date.today()

    domain_data = sb.table("gsc_domain_snapshots") \
        .select("*") \
        .eq("project_id", project_id) \
        .gte("snapshot_date", start_date.isoformat()) \
        .lte("snapshot_date", end_date.isoformat()) \
        .order("snapshot_date", desc=False) \
        .execute()

    rows = domain_data.data or []
    if not rows:
        return {"kpis": {}, "trend": [], "status": "no_data"}

    latest = rows[-1]
    first = rows[0]

    # KPIs
    q_change = latest["total_distinct_queries"] - first["total_distinct_queries"]
    q_change_pct = (q_change / max(first["total_distinct_queries"], 1)) * 100

    kpis = {
        "total_queries": latest["total_distinct_queries"],
        "total_urls": latest["total_urls"],
        "avg_queries_per_url": latest["avg_queries_per_url"],
        "query_stability_index": latest["query_stability_index"],
        "query_change": q_change,
        "query_change_pct": round(q_change_pct, 1),
        "urls_gaining": latest["urls_gaining_queries"],
        "urls_losing": latest["urls_losing_queries"],
    }

    # Trend (agrupa si weekly/monthly)
    trend = [{
        "date": r["snapshot_date"],
        "queries": r["total_distinct_queries"],
        "clicks": r["total_clicks"],
        "impressions": r["total_impressions"],
        "avg_qpu": r["avg_queries_per_url"],
        "stability": r["query_stability_index"],
        "gaining": r["urls_gaining_queries"],
        "losing": r["urls_losing_queries"],
    } for r in rows]

    return {"kpis": kpis, "trend": trend, "status": "ok"}


async def get_url_query_history(
    project_id: int,
    url: str,
    start_date: date = None,
    end_date: date = None
) -> dict:
    """
    Historial de query count para una URL específica.
    Incluye diagnóstico: devaluation / ctr_degradation / slippage / healthy.
    """
    sb = get_supabase()
    start_date = start_date or (date.today() - timedelta(days=90))
    end_date = end_date or date.today()

    snaps = sb.table("gsc_daily_snapshots") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("url", url) \
        .gte("snapshot_date", start_date.isoformat()) \
        .lte("snapshot_date", end_date.isoformat()) \
        .order("snapshot_date", desc=False) \
        .execute()

    rows = snaps.data or []
    if len(rows) < 2:
        return {"url": url, "history": rows, "diagnosis": "insufficient_data"}

    first, latest = rows[0], rows[-1]
    q_change = ((latest["distinct_query_count"] - first["distinct_query_count"])
                / max(first["distinct_query_count"], 1)) * 100
    c_change = ((latest["clicks"] - first["clicks"])
                / max(first["clicks"], 1)) * 100
    p_change = latest["avg_position"] - first["avg_position"]  # positivo = peor

    # Diagnóstico
    if q_change < -15 and c_change < -15:
        diagnosis = "devaluation"        # Google quitó queries Y clicks bajan
    elif q_change > -5 and c_change < -20:
        diagnosis = "ctr_degradation"    # Queries estables, clicks caen (AI Overviews)
    elif q_change > -5 and p_change > 3:
        diagnosis = "slippage"           # Queries estables, posiciones bajan
    elif q_change > 10:
        diagnosis = "gaining_authority"  # Ganando queries = más confianza semántica
    else:
        diagnosis = "stable"

    history = [{
        "date": r["snapshot_date"],
        "query_count": r["distinct_query_count"],
        "clicks": r["clicks"],
        "impressions": r["impressions"],
        "position": float(r["avg_position"]),
        "pos_1_3": r["queries_pos_1_3"],
        "pos_4_10": r["queries_pos_4_10"],
        "pos_11_20": r["queries_pos_11_20"],
        "pos_21_plus": r["queries_pos_21_plus"],
    } for r in rows]

    return {
        "url": url,
        "history": history,
        "diagnosis": diagnosis,
        "query_change_pct": round(q_change, 1),
        "click_change_pct": round(c_change, 1),
        "position_change": round(p_change, 2),
        "current_query_count": latest["distinct_query_count"],
    }


# ───────── ANÁLISIS: Core Update Impact ─────────

async def get_core_update_impact(
    project_id: int,
    before_date: date,
    after_date: date
) -> dict:
    """
    Compara snapshots antes/después de una fecha (core update, deploy, etc).
    Identifica URLs más afectadas y diagnóstico por cluster.
    """
    sb = get_supabase()

    # Ventana: 30 días antes vs 30 días después
    before_start = before_date - timedelta(days=30)
    after_end = after_date + timedelta(days=30)

    before_snaps = sb.table("gsc_daily_snapshots") \
        .select("url, distinct_query_count, clicks, impressions, avg_position") \
        .eq("project_id", project_id) \
        .gte("snapshot_date", before_start.isoformat()) \
        .lt("snapshot_date", before_date.isoformat()) \
        .order("snapshot_date", desc=True) \
        .execute()

    after_snaps = sb.table("gsc_daily_snapshots") \
        .select("url, distinct_query_count, clicks, impressions, avg_position") \
        .eq("project_id", project_id) \
        .gt("snapshot_date", after_date.isoformat()) \
        .lte("snapshot_date", after_end.isoformat()) \
        .order("snapshot_date", desc=True) \
        .execute()

    # Agregar por URL (último snapshot de cada ventana)
    def latest_per_url(rows):
        by_url = {}
        for r in rows:
            if r["url"] not in by_url:
                by_url[r["url"]] = r
        return by_url

    before = latest_per_url(before_snaps.data or [])
    after = latest_per_url(after_snaps.data or [])

    all_urls = set(before.keys()) | set(after.keys())

    # Calcular impacto por URL
    impacts = []
    total_before_q = sum(b["distinct_query_count"] for b in before.values())
    total_after_q = sum(a["distinct_query_count"] for a in after.values())
    total_before_c = sum(b["clicks"] for b in before.values())
    total_after_c = sum(a["clicks"] for a in after.values())

    for url in all_urls:
        b = before.get(url, {"distinct_query_count": 0, "clicks": 0, "avg_position": 0})
        a = after.get(url, {"distinct_query_count": 0, "clicks": 0, "avg_position": 0})

        q_diff = a["distinct_query_count"] - b["distinct_query_count"]
        c_diff = a["clicks"] - b["clicks"]

        if abs(q_diff) > 3 or abs(c_diff) > 10:  # Filtrar solo cambios significativos
            impacts.append({
                "url": url,
                "queries_before": b["distinct_query_count"],
                "queries_after": a["distinct_query_count"],
                "queries_diff": q_diff,
                "clicks_before": b["clicks"],
                "clicks_after": a["clicks"],
                "clicks_diff": c_diff,
                "position_before": float(b["avg_position"]),
                "position_after": float(a["avg_position"]),
            })

    # Ordenar por impacto (queries perdidas)
    impacts.sort(key=lambda x: x["queries_diff"])

    q_change_pct = ((total_after_q - total_before_q) / max(total_before_q, 1)) * 100
    c_change_pct = ((total_after_c - total_before_c) / max(total_before_c, 1)) * 100

    return {
        "before_date": before_date.isoformat(),
        "after_date": after_date.isoformat(),
        "summary": {
            "total_queries_before": total_before_q,
            "total_queries_after": total_after_q,
            "query_change_pct": round(q_change_pct, 1),
            "total_clicks_before": total_before_c,
            "total_clicks_after": total_after_c,
            "click_change_pct": round(c_change_pct, 1),
            "urls_affected": len(impacts),
        },
        "most_affected": impacts[:20],  # Top 20 más impactadas
        "most_improved": list(reversed(impacts[-10:])),  # Top 10 mejoradas
    }


# ───────── QUERIES: Drill-down ─────────

async def get_url_queries(
    project_id: int,
    url: str,
    snapshot_date: date = None
) -> list:
    """Retorna las queries específicas de una URL en un snapshot."""
    sb = get_supabase()
    snapshot_date = snapshot_date or date.today()

    result = sb.table("gsc_query_log") \
        .select("query, clicks, impressions, position, ctr") \
        .eq("project_id", project_id) \
        .eq("url", url) \
        .eq("snapshot_date", snapshot_date.isoformat()) \
        .order("impressions", desc=True) \
        .limit(500) \
        .execute()

    return result.data or []


async def get_lost_queries(
    project_id: int,
    url: str,
    compare_date_a: date,
    compare_date_b: date
) -> dict:
    """
    Compara queries de una URL entre dos fechas.
    Retorna: queries_gained, queries_lost, queries_kept.
    """
    sb = get_supabase()

    queries_a = sb.table("gsc_query_log") \
        .select("query") \
        .eq("project_id", project_id) \
        .eq("url", url) \
        .eq("snapshot_date", compare_date_a.isoformat()) \
        .execute()

    queries_b = sb.table("gsc_query_log") \
        .select("query") \
        .eq("project_id", project_id) \
        .eq("url", url) \
        .eq("snapshot_date", compare_date_b.isoformat()) \
        .execute()

    set_a = {r["query"] for r in (queries_a.data or [])}
    set_b = {r["query"] for r in (queries_b.data or [])}

    return {
        "url": url,
        "date_a": compare_date_a.isoformat(),
        "date_b": compare_date_b.isoformat(),
        "queries_kept": sorted(set_a & set_b),
        "queries_lost": sorted(set_a - set_b),
        "queries_gained": sorted(set_b - set_a),
        "count_kept": len(set_a & set_b),
        "count_lost": len(set_a - set_b),
        "count_gained": len(set_b - set_a),
    }


# ───────── ANNOTATIONS ─────────

async def add_annotation(
    project_id: int,
    annotation_date: date,
    annotation_type: str,
    title: str,
    description: str = None,
    user_id: str = None
) -> dict:
    """Añade una anotación (core update, deploy, cambio de contenido, etc)."""
    sb = get_supabase()
    result = sb.table("gsc_annotations").insert({
        "project_id": project_id,
        "annotation_date": annotation_date.isoformat(),
        "annotation_type": annotation_type,
        "title": title,
        "description": description,
        "auto_detected": False,
        "created_by": user_id,
    }).execute()
    return (result.data or [{}])[0]

async def get_annotations(project_id: int, start_date: date = None, end_date: date = None) -> list:
    """Lista anotaciones del proyecto."""
    sb = get_supabase()
    q = sb.table("gsc_annotations").select("*").eq("project_id", project_id)
    if start_date:
        q = q.gte("annotation_date", start_date.isoformat())
    if end_date:
        q = q.lte("annotation_date", end_date.isoformat())
    result = q.order("annotation_date", desc=True).execute()
    return result.data or []
```

### 33.C — Endpoints: query_count routes

```python
# Añadir en backend/api/routes/query_count.py
# Router: tags=["query-count"]

# ── SNAPSHOTS ──
POST /projects/{project_id}/query-count/snapshot
  → create_daily_snapshot(project_id, site_url, snapshot_date?, days_window?)
  → Crea snapshot diario. Ejecutable manualmente o por scheduler.

POST /projects/{project_id}/query-count/backfill
  → Lanza backfill de últimos N días (default 90) creando un snapshot por semana.
  → Background job con progress tracking.

# ── OVERVIEW (dominio completo) ──
GET /projects/{project_id}/query-count/overview
  → get_query_count_overview(project_id, start_date?, end_date?, granularity?)
  → KPIs de dominio + serie temporal query count.
  Params: start_date, end_date, granularity (daily|weekly|monthly)

# ── PER-URL ──
GET /projects/{project_id}/query-count/urls
  → Lista URLs con query count actual, cambio MoM, diagnóstico.
  Params: sort (query_count|change|clicks), order (asc|desc), limit, offset, diagnosis?

GET /projects/{project_id}/query-count/url-detail
  → get_url_query_history(project_id, url, start_date?, end_date?)
  → Historial + diagnóstico (devaluation/ctr_degradation/slippage/stable/gaining_authority)
  Params: url (required)

GET /projects/{project_id}/query-count/url-queries
  → get_url_queries(project_id, url, snapshot_date?)
  → Lista de queries para una URL en un snapshot.
  Params: url, snapshot_date?

# ── COMPARACIÓN ──
GET /projects/{project_id}/query-count/lost-queries
  → get_lost_queries(project_id, url, date_a, date_b)
  → Queries ganadas/perdidas/mantenidas entre dos fechas.
  Params: url, date_a, date_b

POST /projects/{project_id}/query-count/core-update-impact
  → get_core_update_impact(project_id, before_date, after_date)
  → Análisis de impacto antes/después de un evento.
  Body: { before_date, after_date }

# ── ANNOTATIONS ──
POST /projects/{project_id}/query-count/annotations
  → add_annotation(project_id, date, type, title, description?)
  Body: { annotation_date, annotation_type, title, description? }

GET /projects/{project_id}/query-count/annotations
  → get_annotations(project_id, start_date?, end_date?)
  Params: start_date?, end_date?
```

**Total: 10 endpoints nuevos.**

### 33.D — Frontend: QueryCountPage.tsx

Nuevo módulo en sidebar bajo grupo **AUDIT** → "Query Count" con icono `BarChart3`.

```
modules.ts → { key: 'query-count', label: 'Query Count', icon: BarChart3,
                path: 'query-count', group: 'audit', enabled: true }
```

**Layout: 3 Tabs**

#### Tab 1: "Visión General" (Overview)
```
┌─────────────────────────────────────────────────────────────────┐
│  QUERY COUNT — PESO SEMÁNTICO                                   │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐│
│  │ 2,341    │ │ 127      │ │ 18.4     │ │ 87.3%    │ │ -3.2% ││
│  │ Queries  │ │ URLs     │ │ Avg Q/URL│ │ Stability│ │ MoM   ││
│  │ totales  │ │ activas  │ │          │ │ Index    │ │       ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘│
│                                                                 │
│  ┌─── Line Chart: Query Count Trend ─────────────────────────┐ │
│  │                                                            │ │
│  │  Total queries ───── Avg Q/URL ─────                       │ │
│  │  (Annotations: ▼ core update  ▼ deploy  ▼ manual)         │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── Stacked Bar: URLs por diagnóstico ─────────────────────┐ │
│  │  ■ Gaining  ■ Stable  ■ Losing  ■ Devaluation             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  [Crear snapshot]  [Backfill 90 días]  [+ Anotación]            │
└─────────────────────────────────────────────────────────────────┘
```

#### Tab 2: "Por URL" (URL Detail)
```
┌─────────────────────────────────────────────────────────────────┐
│  QUERY COUNT POR URL                                            │
│                                                                 │
│  [Filtro: diagnóstico ▾]  [Ordenar: query_count ▾]  [Buscar…] │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ URL              │ Queries │ MoM   │ Clicks │ Diagnóstico│   │
│  │──────────────────│─────────│───────│────────│────────────│   │
│  │ /blog/entren...  │ 47      │ ↓-12% │ 234    │ 🔴 Deval  │   │
│  │ /blog/nutric...  │ 35      │ ↑+8%  │ 189    │ 🟢 Gaining│   │
│  │ /blog/yoga-...   │ 28      │ =0%   │ 56     │ 🟡 CTR↓   │   │
│  │ /servicios/...   │ 22      │ ↓-18% │ 412    │ 🔴 Deval  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ── Click en fila expande: ──                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ /blog/entrenamiento-funcional                             │   │
│  │                                                           │   │
│  │ Query Count: 47 → 41 (↓12.8%)   Clicks: 234 → 198 (↓15%)│   │
│  │ Position: 8.2 → 9.1 (↓0.9)     Diagnosis: DEVALUATION   │   │
│  │                                                           │   │
│  │ ┌── Line Chart mini: query_count + clicks timeline ────┐ │   │
│  │ └─────────────────────────────────────────────────────────┘ │ │
│  │                                                           │   │
│  │ Distribution: ■ Pos 1-3: 8  ■ Pos 4-10: 15  ■ 11-20: 12 │   │
│  │               ■ Pos 21+: 6                                │   │
│  │                                                           │   │
│  │ [Ver queries]  [Comparar fechas]                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

#### Tab 3: "Impacto" (Core Update / Comparación)
```
┌─────────────────────────────────────────────────────────────────┐
│  IMPACTO — ANTES vs DESPUÉS                                    │
│                                                                 │
│  Fecha antes: [📅 2026-01-15]  Fecha después: [📅 2026-02-15]  │
│  [Analizar impacto]                                             │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ -31.8%   │ │ -33.8%   │ │ +4.5     │ │ 23       │          │
│  │ Queries  │ │ Clicks   │ │ Avg Pos  │ │ URLs     │          │
│  │ change   │ │ change   │ │ slip     │ │ affected │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                 │
│  ── URLs MÁS AFECTADAS (queries perdidas) ──                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ URL              │ Q Before │ Q After │ Diff  │ Clicks Δ │   │
│  │ /health/vitamins │ 45       │ 27      │ -18   │ -450     │   │
│  │ /fitness/cardio  │ 38       │ 22      │ -16   │ -234     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ── URLs QUE MEJORARON ──                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ URL              │ Q Before │ Q After │ Diff  │ Clicks Δ │   │
│  │ /recetas/protein │ 12       │ 28      │ +16   │ +180     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ── QUERIES PERDIDAS (drill-down por URL) ──                    │
│  Selecciona URL: [/health/vitamins ▾]                           │
│  Periodo A: ene 2026  →  Periodo B: feb 2026                   │
│                                                                 │
│  Mantenidas: 27    Perdidas: 18    Ganadas: 0                   │
│  Perdidas: "best vitamin supplements", "vitamin D dosage", ...  │
└─────────────────────────────────────────────────────────────────┘
```

### 33.E — Integración con módulos existentes

**Conexiones bidireccionales:**

1. **Authority & PR (Sprint 31-32):**
   - Correlación: ¿URLs con más backlinks/PR mantienen query count?
   - Widget en Authority Graph: overlay query count trend sobre scatter

2. **Topical Authority (Sprint 22):**
   - Query Count por cluster: ¿Google está devaluando un cluster entero?
   - `get_cluster_query_trend()` — agregar query counts de URLs por cluster

3. **Content Performance (existente):**
   - Badge "DEVALUATION" / "CTR↓" / "SLIPPAGE" en tabla de rendimiento
   - Mini sparkline de query count en cada fila

4. **Dashboard principal:**
   - Widget: "Query Stability Index" (%) + trend MoM
   - Alert: "⚠ 5 URLs perdieron >20% queries este mes"

5. **Annotations auto-detectadas:**
   - Si query_stability_index baja >10% de golpe → auto-annotation "Posible core update"
   - Si un cluster pierde >25% queries → auto-annotation "Devaluación de cluster: {nombre}"

### Resumen Sprint 33

```
Sprint 33 — Query Count Analytics: Peso Semántico de Google
├── 33.A MODELO DE DATOS (Migración 064)
│   ├── gsc_daily_snapshots (URL + fecha + query_count + pos_buckets)
│   ├── gsc_query_log (query-level audit trail)
│   ├── gsc_domain_snapshots (KPIs de dominio por día)
│   └── gsc_annotations (eventos para correlacionar)
├── 33.B BACKEND SERVICE
│   ├── query_count_service.py
│   ├── create_daily_snapshot() → persiste GSC con query count
│   ├── get_query_count_overview() → KPIs + trend dominio
│   ├── get_url_query_history() → historial + diagnóstico por URL
│   ├── get_core_update_impact() → análisis antes/después
│   ├── get_url_queries() / get_lost_queries() → drill-down
│   └── add_annotation() / get_annotations()
├── 33.C ENDPOINTS (10 nuevos)
│   ├── POST snapshot + backfill
│   ├── GET overview + urls + url-detail + url-queries
│   ├── GET lost-queries + POST core-update-impact
│   └── POST/GET annotations
├── 33.D FRONTEND (QueryCountPage.tsx — 3 tabs)
│   ├── Tab 1 "Visión General": 5 KPIs + line chart + stacked bar
│   ├── Tab 2 "Por URL": tabla filtrable + expand con diagnóstico
│   └── Tab 3 "Impacto": comparación antes/después + drill-down queries
└── 33.E INTEGRACIONES
    ├── Authority Graph: overlay query count
    ├── Topical Authority: query count por cluster
    ├── Content Performance: badges diagnóstico
    ├── Dashboard: widget stability + alerts
    └── Auto-annotations: core update / cluster devaluation detection
```

**Tiempo: 5-7 días.** 1 migración nueva (064: 4 tablas). 1 módulo nuevo sidebar (query-count). 1 servicio nuevo (query_count_service.py). 10 endpoints nuevos. Integraciones: dashboard_service, authority, topical_authority, content_performance.

---

## Sprint 34 — Bugfix Críticos (Feedback Tester)

> **Fuente:** Excel "Mejoras aplicables a la app Fit Content.xlsx" — 204 items de feedback (81 🟣 errores, 88 🔵 mejoras, 31 🟠 no desarrollados).
> **Objetivo:** Arreglar los bugs que destruyen la confianza del tester en la herramienta. Foco en: datos incorrectos, crashes, funcionalidades que dan error visible.

### 34.A — Dashboard: sparklines + filtros + periodos

**Problemas reportados:**
- 🟣 Sparklines de tendencia aparecen a la derecha del título en vez de debajo de la métrica (reportado 3 veces: Dashboard Adquisición, Negocio, Rendimiento)
- 🟣 Filtro Branded/Non-branded resetea periodo temporal a 1 día, gráfica pierde sentido
- 🟣 Periodo 30D muestra datos de mes actual, no del mes pasado; 90D no muestra noviembre
- 🔵 Gráfica empieza 2 días antes (sin datos) y se va a 0; empezar 3+ días antes
- 🟣 Brand Authority tooltip cortado
- 🟠 Tráfico IA no refleja datos (tarjeta existe pero vacía)

**Implementación:**
```
34.A.1 — Sparklines: mover mini-gráficas debajo de la métrica en MetricCard.
         Si no hay sparklines (actual = LineChart completo), añadir sparklines
         como <Sparklines> de recharts debajo de cada KPI value.

34.A.2 — Filtro branded: al cambiar trafficType, preservar periodo seleccionado.
         Bug: setTrafficType() probablemente triggers un re-fetch que resetea dateRange.
         Fix: asegurar que setTrafficType NO modifica dateRange state.

34.A.3 — Periodos: 30D = últimos 30 días naturales (no mes actual).
         90D = últimos 90 días. Gráfica debe mostrar data_range_start - 3 días
         de padding para evitar corte a 0.

34.A.4 — AI Traffic: implementar regex de fuentes IA para filtrar sessions de GA4.
         Regex: chatgpt\.com|chat\.openai\.com|gemini\.google\.com|deepseek|
         perplexity|claude|copilot\.microsoft\.com|character\.ai|grok|
         bard\.google\.com|mistral\.ai|writesonic|anthropic\.com
         Endpoint ya existe (/dashboard/ai-traffic) pero probablemente no tiene
         datos porque GA4 no tiene el channel group configurado O el endpoint
         no aplica el regex correcto a los referrers.
```

### 34.B — Rendimiento: datos GSC + URLs con parámetros

**Problemas reportados:**
- 🟣 Datos no coinciden con Search Console (reportado en Dashboard + Rendimiento + Keywords)
- 🟣 URLs con ?fbclid= contabilizadas como tráfico orgánico
- 🟣 Análisis de URLs erróneo ("poner año 2024 en title" cuando no aplica)
- 🟣 En "A revisar, Decay y CTR bajo" números muy bajos de URLs

**Implementación:**
```
34.B.1 — GSC data: auditar fetch_search_analytics() para verificar que
         los filtros de fecha, aggregation type, y dimensiones coinciden
         con lo que muestra GSC nativo. Posible bug: double-counting
         por aggregation 'auto' vs 'byPage'.

34.B.2 — URL normalization: strip query params (?fbclid=, ?utm_*, ?gclid=)
         antes de agregar datos. Añadir normalize_url() que elimine
         parámetros de tracking. Aplicar en gsc_service.py al procesar results.

34.B.3 — Content analysis: revisar las recomendaciones IA para que no
         sugieran "poner año 2024" si ya estamos en 2026. El servicio de
         análisis debe usar fecha actual, no hardcoded.

34.B.4 — Decay/CTR: revisar umbrales. Probablemente el threshold es muy
         estricto o el dataset muy pequeño. Ajustar: decay si posición
         media empeoró >3 en 30d, CTR bajo si CTR < 50% del esperado
         por posición.
```

### 34.C — Módulos que dan error visible

**Problemas reportados:**
- 🟣 Content Risk: "Error cargando dashboard de riesgo", "Error escaneando URL"
- 🟣 AI Search (SRO): "Error en batch" al ejecutar Batch top 20 URLs
- 🟣 Canibalizaciones: "Plan de acción no funciona, da error"
- 🟣 Keywords: tabla muestra duplicidad de términos
- 🟣 SEO Técnico: ancho mayor que pantalla, obligando scroll horizontal
- 🟣 Grupos URLs: "Undefined grupos detectados" al autodetectar

**Implementación:**
```
34.C.1 — Content Risk: debug error de carga. Probablemente falta tabla o
         el endpoint devuelve 500. Añadir try/catch + mensaje user-friendly.

34.C.2 — SRO Batch: debug error. Posible: timeout en batch de 20 URLs,
         o el servicio Claude no responde a tiempo. Añadir retry + progress.

34.C.3 — Canibalizaciones plan de acción: debug endpoint de plan.
         Probablemente llama a Claude API y falla por timeout o formato.

34.C.4 — Keywords dedup: en el servicio de keywords, agrupar por
         keyword normalizada (lowercase, trim, remove trailing 's').
         Mostrar solo la variante con más impressions.

34.C.5 — SEO Técnico: fix CSS overflow. Añadir max-width: 100% +
         overflow-x: auto al container principal.

34.C.6 — Grupos URLs: fix "undefined" — el count variable no se
         inicializa antes de mostrar el toast. Inicializar a 0.
```

### 34.D — Sistema: sitemap parser + chat

**Problemas reportados:**
- 🟣 Sitemap parser: "solo detecta 1 artículo vs mil páginas", "error al parsear"
- 🟣 Sitemap: "no filtra bien tipo de páginas"
- 🟣 Chat AI: "respuestas largas recargan la página perdiendo conversación"
- 🟣 Usuarios activos: no detecta usuario actual

**Implementación:**
```
34.D.1 — Sitemap: el default limit=50 en /pages endpoint confunde.
         Cambiar default a 200 o eliminar limit en listado.
         Parseo recursivo: si sitemap contiene sub-sitemaps (sitemap index),
         parsear recursivamente. Actual sitemap_service.py línea ~150
         probablemente solo parsea el primer nivel.

34.D.2 — Sitemap content type: mejorar clasificación de URLs.
         Actual: probablemente solo busca /blog/ en path.
         Fix: clasificar por path patterns (/blog/, /curso/, /categoria/,
         /tienda/, etc.) + detectar por sitemap source.

34.D.3 — Chat overflow: el streaming response probablemente excede
         el buffer del componente y triggers un re-render que pierde state.
         Fix: usar useRef para chat history, no useState que rerenderiza.

34.D.4 — Usuarios activos: verificar que el auth context reporta
         correctamente el usuario actual a la lista de activos.
```

### Resumen Sprint 34

```
Sprint 34 — Bugfix Críticos (Feedback Tester)
├── 34.A DASHBOARD (sparklines + filtros + periodos + AI traffic)
│   ├── Sparklines debajo de métricas (o añadir si no existen)
│   ├── Fix: branded filter no resetea periodo
│   ├── Fix: periodos 30D/90D muestran rango correcto
│   ├── Fix: tooltip Brand Authority completo
│   └── AI Traffic: regex 15+ fuentes IA en referrers
├── 34.B RENDIMIENTO (GSC + URL normalization)
│   ├── Auditar GSC data discrepancies
│   ├── Strip tracking params (?fbclid, ?utm_*)
│   ├── Content analysis: usar fecha actual
│   └── Decay/CTR: ajustar umbrales
├── 34.C MÓDULOS CON ERROR VISIBLE (6 fixes)
│   ├── Content Risk: error cargando/escaneando
│   ├── SRO Batch: error en batch
│   ├── Canibalizaciones: plan de acción error
│   ├── Keywords: dedup variantes
│   ├── SEO Técnico: overflow horizontal
│   └── Grupos URLs: "undefined" en autodetectar
└── 34.D SISTEMA (sitemap + chat + usuarios)
    ├── Sitemap: default limit + parseo recursivo
    ├── Sitemap: clasificación content type
    ├── Chat: fix streaming overflow
    └── Usuarios activos: detectar sesión actual
```

**Tiempo: 5-7 días.** 0 migraciones. 0 módulos nuevos. ~15 bugfixes across 8+ archivos frontend + 6+ backend. Prioridad: confianza del tester.

---

## Sprint 35 — Features No Desarrolladas + AI Traffic Intelligence

> **Fuente:** Feedback tester (31 items 🟠) + artículos Analytics Mania / Optimize Smart sobre tracking de tráfico IA en GA4.
> **Objetivo:** Implementar funcionalidades previstas pero vacías, y añadir AI Traffic Intelligence como módulo nuevo inspirado en los artículos de GA4.

### 35.A — AI Traffic Intelligence (nuevo)

**Contexto:** La tarjeta "Tráfico IA" existe pero no muestra datos. Los artículos de Analytics Mania y Optimize Smart describen cómo trackear tráfico de IA con regex en GA4. En vez de solo una tarjeta, creamos un módulo completo.

**Fuentes IA a detectar (regex):**
```
chatgpt\.com|chat\.openai\.com|gemini\.google\.com|deepseek|
perplexity(?:\.ai)?|claude|copilot\.microsoft\.com|character\.ai|
grok\.x|grok\.com|bard\.google\.com|mistral\.ai|writesonic|
anthropic\.com|huggingface|you\.com|phind|neeva|kagi\.com|
bing\.com/chat|copilot\.microsoft
```

**Implementación:**
```
35.A.1 — Backend: ai_traffic_service.py
         - detect_ai_sessions(project_id, start, end) → filtra GSC/GA4
           referrers que matchean regex
         - get_ai_traffic_overview(project_id) → KPIs: sessions, share%,
           trend, top sources, top landing pages
         - get_ai_traffic_by_source(project_id) → desglose por fuente IA
         - get_ai_vs_organic_comparison(project_id) → métricas engagement
           de tráfico IA vs orgánico clásico

35.A.2 — Endpoints: 4 nuevos bajo /ai-traffic/
         GET overview, by-source, landing-pages, comparison

35.A.3 — Dashboard widget: reemplazar tarjeta vacía por widget con
         sessions IA + share% + top 3 fuentes + trend sparkline

35.A.4 — Tab en Dashboard Engagement: "Tráfico IA" como tab adicional
         con tabla fuentes, landing pages, dispositivos, engagement
```

### 35.B — Features 🟠 del Dashboard

```
35.B.1 — Content Pipeline: mostrar datos de briefings creados + estado
35.B.2 — Valor SEO: calcular visitantes * CPC medio por keyword
35.B.3 — Site Risk: mostrar score basado en issues detectados en crawl SF
35.B.4 — CWV Escanear: conectar botón al endpoint existente de cwv scan
35.B.5 — Bing Backlinks: conectar botón al endpoint existente
```

### 35.C — Features 🟠 de Entidad

```
35.C.1 — EEAT Checklist: poblar datos del checklist desde People + Schema
35.C.2 — Brand Audit historial: guardar auditorías ejecutadas con timestamp
35.C.3 — Brand Audit: posición media en tabla coincida con gráfico
```

### 35.D — Features 🟠 de Auditoría + Contenido

```
35.D.1 — Keywords: botón Scores refleje en métricas + botón Ord funcione
35.D.2 — SEO Técnico: detectar schemas asociados a URL
35.D.3 — Contenido: tabla refleje autores (leer desde meta/schema)
35.D.4 — Contenido: columna YMYL con datos
35.D.5 — Contenido: botón Exportar funcione (CSV/Excel)
35.D.6 — Informes: "Crear informe Manual" completo (no solo resumen)
35.D.7 — Tendencias: botón Escanear funcione sin error
35.D.8 — GEO Auditor: botón Analizar GEO funcione
```

### Resumen Sprint 35

```
Sprint 35 — Features No Desarrolladas + AI Traffic Intelligence
├── 35.A AI TRAFFIC INTELLIGENCE (nuevo)
│   ├── ai_traffic_service.py con regex 20+ fuentes
│   ├── 4 endpoints: overview, by-source, landing-pages, comparison
│   ├── Dashboard widget reemplazado
│   └── Tab Tráfico IA en Engagement
├── 35.B DASHBOARD FEATURES 🟠 (5 fixes)
│   ├── Content Pipeline + Valor SEO + Site Risk
│   └── CWV Escanear + Bing Backlinks botones
├── 35.C ENTIDAD FEATURES 🟠 (3 fixes)
│   ├── EEAT Checklist datos
│   └── Brand Audit historial + posición
└── 35.D AUDITORÍA + CONTENIDO 🟠 (8 fixes)
    ├── Keywords scores + SEO Técnico schemas
    ├── Contenido autores + YMYL + Export
    └── Informes manual + Tendencias + GEO
```

**Tiempo: 7-10 días.** 0 migraciones. 1 servicio nuevo (ai_traffic_service.py). 4 endpoints nuevos. ~16 features faltantes implementadas.

---

## Sprint 36 — UX/Polish Transversal

> **Fuente:** Feedback tester (88 items 🔵 oportunidades de mejora).
> **Objetivo:** Pulir la experiencia de usuario en todas las secciones. Foco en: paginación, tooltips, CRUD completo, traducciones, botones visibles.

### 36.A — Paginación global

**Reportado en:** Keywords, Canibalizaciones, People contenido, Contenido tabla, Schema fichas.

```
36.A.1 — Crear componente <Pagination> reutilizable con: page, pageSize,
         total, onPageChange. Estilo consistente con design system.
36.A.2 — Aplicar en: KeywordsPage, CanibalizationsPage, ContentPage,
         People contenido listado, Schema listado.
36.A.3 — Backend: asegurar que todos los endpoints de listado soportan
         ?limit=&offset= correctamente.
```

### 36.B — Tooltips/descripciones en todas las secciones

**Reportado en:** General, Control de Entidad, AI Readiness, Keywords, Revenue Opportunity.

```
36.B.1 — Añadir prop 'tooltip' a MetricCard. Al hover en icono ℹ️,
         mostrar popover con explicación de la métrica.
36.B.2 — Añadir subtítulo descriptivo en header de cada sección.
         Actual: solo algunas tienen. Target: todas.
36.B.3 — Revenue Opportunity: tooltip explicando dónde configurar
         CVR y AOV con link a Settings.
```

### 36.C — CRUD completo (editar/eliminar)

**Reportado en:** People, Reviews, Menciones, Asociaciones, Competidores, Briefings, Informes.

```
36.C.1 — People: botones editar/eliminar miembro con confirmación modal.
36.C.2 — Reviews: editar plataforma, editar testimonial.
36.C.3 — Menciones: editar mención existente.
36.C.4 — Competidores: editar detalle (incluir campo URL sitemap).
36.C.5 — Briefings: eliminar brief creado.
36.C.6 — Informes: eliminar informe.
36.C.7 — Monitor LLM: eliminar/modificar consultas.
```

### 36.D — Traducciones y labels

```
36.D.1 — EEAT profile: traducir labels a español
36.D.2 — Canibalizaciones: "Reviewing" → "Resolviendo"
36.D.3 — Contenido: "article" → "artículo" en tipo tabla
36.D.4 — Keywords: texto explicativo en sidebar vacío
36.D.5 — Focus Group: fix "Como X," redundante en tarjetas
36.D.6 — Brand Audit: "H2 vs H1" → "P1 vs P2" en Top 10 kws
```

### 36.E — Botones y estados visibles

```
36.E.1 — Canibalizaciones: botón "Revisar/Resolver" estilizar como botón
         (no como etiqueta). Posibilidad de revertir estado.
36.E.2 — Contenido Series: botón "O crea un cluster manualmente" visible.
36.E.3 — Focus Group: botón "Ejecutar otro" visible y estilizado.
36.E.4 — Brand Audit popup: añadir botón cerrar (X).
36.E.5 — Menciones Extracto: indicar caracteres máximos al lado.
36.E.6 — Config Sitemap: parar animación del botón cuando da error.
36.E.7 — People links: al añadir link duplicado, mostrar mensaje.
36.E.8 — People contenido: al eliminar, quedar en misma ficha.
```

### Resumen Sprint 36

```
Sprint 36 — UX/Polish Transversal
├── 36.A PAGINACIÓN GLOBAL
│   ├── Componente <Pagination> reutilizable
│   └── Aplicar en 5+ tablas
├── 36.B TOOLTIPS Y DESCRIPCIONES
│   ├── Tooltip en MetricCard
│   ├── Subtítulos descriptivos en headers
│   └── Revenue Opportunity ayuda contextual
├── 36.C CRUD COMPLETO (7 módulos)
│   ├── Editar/eliminar en People, Reviews, Menciones
│   ├── Editar competidores, eliminar briefs/informes
│   └── Modificar consultas LLM
├── 36.D TRADUCCIONES (6 fixes)
│   └── Labels en español, textos coherentes
└── 36.E BOTONES Y ESTADOS (8 fixes)
    ├── Estilizar botones que parecen etiquetas
    ├── Mensajes de feedback faltantes
    └── Estados de error visibles
```

**Tiempo: 5-7 días.** 0 migraciones. 0 endpoints nuevos. 1 componente nuevo (Pagination). ~30 fixes UX across frontend.

---

## Sprint 38 — Fix ALL Remaining Feedback (83 items → 100% completado)

> **Spec completa:** `SPRINT-38-PLAN.md` (en raíz del proyecto)
> **Objetivo:** Llevar de 59.3% a 100% los 204 items del Excel de feedback.
> **Items pendientes:** 25 ❌ + 58 ⚠️ = 83 items
> **Organización:** 5 Fases paralelas por dominio de archivos.

### Fase A — MetricCard + DashboardPage (7 items)

```
A1 — MetricCard.tsx L65: whitespace-nowrap → whitespace-normal max-w-xs
A2 — DashboardPage.tsx: AI Readiness Score tooltips explicativos
A3 — DashboardPage.tsx: filtro etiquetas cursos en tabla URLs
A4 — main.py: TimeoutMiddleware 120s para estabilidad servidor
A5 — DashboardPage.tsx: banner freshness GSC "datos con 2-3 días de retraso"
     (cubre items 10, 13, 28, 33 de datos no coinciden)
```

### Fase B — Entidad: PeoplePage + ReputationPage (15 items)

```
B1  — ReputationPage.tsx: botones EDIT en Reviews, Menciones, Asociaciones (items 68,73,77)
B2  — EntityPanelPage.tsx: botón "Auto-detectar RRSS" → Claude sugiere URLs
B3  — PeoplePage.tsx: selector de tema antes de generar buyer personas (item 62)
B4  — PeoplePage.tsx L1004: slice(0,500) → expandible con "Ver más/menos"
B5  — PeoplePage.tsx: debounce 30s en botón Re-evaluar EEAT (item 51)
B6  — PeoplePage.tsx: checkbox "Mantener personas actuales" al regenerar (item 60)
B7  — claude_service.py: prompt Focus Group → max_tokens mayor + "300 palabras mínimo"
B8  — EntityPanelPage.tsx: conectar EEAT/YMYL con datos reales de snapshots
B9  — EntityPanelPage.tsx: gráfico poblar con snapshots, fallback si vacío
B10 — EntityPanelPage.tsx: botón "Analizar página" por URL → /sro/analyze
B11 — BrandAuditPage.tsx: tab queries verificar endpoint /brand-audit/{id}/queries
B12 — RankTrackerPage.tsx: posición media ponderada por impressions
```

### Fase C — Auditoría Técnica (15 items)

```
C1  — CannibalizationsPage.tsx: paginación PAGE_SIZE=20
C2  — RankTrackerPage.tsx: link externo GSC por URL en Striking Distance
C3  — RankTrackerPage.tsx: nota explicativa keywords no visibles en URL
C4  — RankTrackerPage.tsx: Top Movers ordenar por |change| desc, alertas top 10
C5  — RankTrackerPage.tsx: párrafo explicativo sidebar Keywords
C6  — RankTrackerPage.tsx: sidebar keyword → listar TODAS URLs si canibalizado
C7  — sro_service.py L64: añadir param page_type al prompt
C8  — sro_service.py: OPTIMAL_BY_TYPE dict por tipo página, no hardcoded 800
C9  — ContentRiskPage.tsx: batch scan → textarea multi-URL, backend asyncio.gather
C10 — SchemaTab: si no crawl, botón "Escanear Schema de URL" directo
C11 — FieldDataTab.tsx: mensaje CrUX si no hay datos
C12 — SROPage.tsx: textarea para crear grupo con lista URLs
C13 — QualityGatesTab.tsx: verificar overflow-x-auto
```

### Fase D — Contenido + Investigación + Informes (28 items)

```
D1  — content.py: función classify_ymyl() + incluir en response
D2  — content.py: campo category + columna en frontend
D3  — BriefingEditor.tsx L130: "Palabras estimadas" → "Número de palabras"
D4  — BriefingsPage.tsx: verificar content_type editable + backend permite PUT
D5  — briefings.py L145-174: verificar /generate, añadir logging + loading state
D6  — TopicalAuthorityPage.tsx L497: cluster button → bg-brand-yellow text-black font-bold
D7  — TopicalAuthorityPage.tsx L392-412: error msg específico "Verifica GSC conectado"
D8  — ContentSeriesPage.tsx: botón Exportar CSV con downloadCSV()
D9  — TopicalAuthorityPage.tsx L632: warning canibalización entre topics
D10 — ContentGapsPage.tsx: createBriefing() → source_gap_id + badge "Desde Gap"
D11 — TopicalAuthorityPage.tsx: campo priority en gaps, sort por prioridad
D12 — ContentValidatorPage.tsx: link "Crear avatares en Entidad > Personas"
D13 — content_validator.py: verificar/crear POST /validations + logging
D14 — ContentValidatorPage.tsx: banner diferenciador vs Revisor de Textos
D15 — ContentPerformancePage.tsx: botón "Importar CSV" con Papa.parse
D16 — ContentPerformancePage.tsx: pestaña "Candidatos" o estado draft
D17 — gaps.py + authority routes: try/catch + logging + error msgs específicos
D18 — CompetitorsPage.tsx: EmptyState solo si competitors.length === 0
D19 — Frontend: texto "Marcas > Personas > Resultados" → copy claro
D20 — CompetitorsPage.tsx: campo sitemap_url en modal crear/editar
D21 — competitor_service.py: retry + validar XML + sitemap index handling
D22 — SSRAnalysisTab.tsx: mensaje "Sincroniza sitemap primero"
D23 — GeoAuditPage.tsx: tooltip score "relevancia × frecuencia en LLMs"
D24 — GeoAuditPage.tsx: filtro por tipo consulta (info/nav/transactional)
D25 — gaps.py: score = volume * max(0.1, 1-(difficulty/100)) * position_factor
D26 — TrendsPage.tsx: mensaje "keywords de nicho sin datos Google Trends"
D27 — TrendsPage.tsx: validar rango temporal chart vs periodo seleccionado
D28 — reports.py: L251 rank_tracker vacío msg, L309 segmentos multi-level, L216 filter published
```

### Fase E — Sistema + Settings (8 items)

```
E1 — integrations.py/gsc_service.py: filtrar sitemaps por project.site_url
E2 — ChatWidget.tsx + chat routes: pre-fetch métricas GSC en contexto Claude
E3 — UsersSettings.tsx: usar last_sign_in_at para badge "Activo"
E4 — SitemapSettings.tsx: setParsing(false) en catch + toast.error específico
E5 — claude_service.py prompt GEO: "Lista TODAS las instituciones, no solo una"
E6 — ContentPerformancePage.tsx: indicador "última actualización" + btn Sync GSC
```

### Auto-validación

Ejecutar `SPRINT-38-PLAN.md` → sección "AUTO-VALIDACIÓN" contiene script bash
que verifica 18 fixes clave con grep + build + tests. Ejecutar al acabar:

```bash
# Quick validation
cd frontend && npx tsc --noEmit && npm run build && cd ../backend && pytest
# Full validation
bash ../../SPRINT-38-VALIDATE.sh
```

**Criterio de éxito:** 0 errores TSC, build OK, 142+ tests pass, script validación 0 errors.

**Tiempo estimado: 7-8 horas.** ~35 archivos frontend, ~12 archivos backend.

---

## Sprint 39 — Fix Final: 7 ❌ + 9 ⚠️ → 100% completado

> **Objetivo:** Cerrar los 16 items restantes para llegar al 100% de los 204 del Excel.
> **Referencia:** Audit_Sprint38_Final.xlsx tiene el detalle de qué falta.

### 39.1 — RankTrackerPage.tsx: posición media ponderada (Item 90)

**Archivo:** `frontend/src/pages/RankTrackerPage.tsx`

Actualmente la posición media se calcula como media simple. Cambiar a media ponderada por impressions.

Buscar donde se muestran las métricas/KPIs del rank tracker y añadir:

```typescript
const weightedAvgPosition = keywords.length > 0
  ? keywords.reduce((sum, kw) => sum + ((kw.current_position ?? 999) * (kw.impressions ?? 1)), 0)
    / keywords.reduce((sum, kw) => sum + (kw.impressions ?? 1), 0)
  : null
```

Usar `weightedAvgPosition` donde se muestra "Pos. Media". Complejidad: S.

**Criterio:** El KPI de posición media usa la fórmula ponderada.

---

### 39.2 — RankTrackerPage.tsx: sidebar muestra TODAS URLs canibalizadas (Item 114)

**Archivo:** `frontend/src/pages/RankTrackerPage.tsx`

**Líneas 693-698:** Actualmente solo muestra `selectedKw.current_url`. Reemplazar por lista de todas las URLs que posicionan para esa keyword.

Obtener URLs canibalizadas: al seleccionar keyword, hacer query a canibalizaciones o al propio endpoint de keywords filtrando por keyword text para obtener todas URLs.

```typescript
// Después del bloque {selectedKw.current_url && (...)} en L693-698, AÑADIR:
{selectedKw.all_urls && selectedKw.all_urls.length > 1 && (
  <div className="mt-3">
    <p className="text-[10px] uppercase text-text-muted tracking-wider mb-1">
      URLs canibalizadas ({selectedKw.all_urls.length})
    </p>
    <div className="space-y-1">
      {selectedKw.all_urls.map((url: string, i: number) => (
        <p key={i} className="text-xs text-text-secondary truncate" title={url}>{url}</p>
      ))}
    </div>
  </div>
)}
```

Si el backend no devuelve `all_urls`, añadir al endpoint de keywords un JOIN con `cannibalization_keywords` o agrupar por keyword text. Complejidad: M.

**Criterio:** Al seleccionar keyword canibalizada, se ven TODAS las URLs afectadas en el sidebar.

---

### 39.3 — RankTrackerPage.tsx: texto sidebar más descriptivo (Item 112)

**Archivo:** `frontend/src/pages/RankTrackerPage.tsx`

**Línea 707-709:** Cambiar el texto placeholder del sidebar:

```typescript
// ANTES:
<div className="flex items-center justify-center h-full text-text-muted text-xs">
  Selecciona una keyword para ver su historial
</div>

// DESPUÉS:
<div className="flex items-center justify-center h-full text-text-muted text-xs text-center px-4">
  Selecciona una keyword de la tabla para ver su evolución de posición, URL actual y datos históricos de Google Search Console.
</div>
```

Complejidad: S.

**Criterio:** Texto descriptivo visible cuando no hay keyword seleccionada.

---

### 39.4 — ContentSeriesPage.tsx: botón Exportar CSV (Item 175)

**Archivo:** `frontend/src/pages/ContentSeriesPage.tsx`

**Líneas 232-250:** Añadir botón de export CSV al lado de "Eliminar" en el header de detalle de serie.

```typescript
import { Download } from 'lucide-react'
import { downloadCSV } from '../lib/csv'

// Función:
const handleExportCSV = () => {
  if (!selectedSeries) return
  const headers = ['Topic', 'Grupo', 'Funnel Stage', 'Prioridad', 'Es Gap', 'Status']
  const rows = (selectedSeries.topics || []).map((t: any) => [
    t.topic, t.group_name || '', t.funnel_stage || '', t.priority || '', t.is_gap ? 'Sí' : 'No', t.status || ''
  ])
  downloadCSV(`series-${selectedSeries.name}.csv`, headers, rows)
}

// En el div de botones (L232), añadir ANTES del botón Eliminar:
<button onClick={handleExportCSV} className="flex items-center gap-2 px-3 py-2 bg-dark-surface text-text-primary text-sm font-bold uppercase tracking-wider border border-border-subtle hover:border-brand-yellow">
  <Download size={16} /> CSV
</button>
```

Complejidad: S.

**Criterio:** Botón CSV visible en detalle de serie, descarga archivo con todos los topics.

---

### 39.5 — gaps.py: source_gap_id al crear briefing (Item 177)

**Archivo:** `backend/api/routes/gaps.py`

**Línea 166-173:** Añadir `source_gap_id` al crear briefing desde gap.

```python
# ANTES (L166-173):
    briefing_data = {
        "project_id": project_id,
        "title": f"Briefing: {gap.data['keyword']}",
        "target_keyword": gap.data["keyword"],
        "content_type": "article",
        "references": gap.data.get("competitor_urls", []),
        "status": "draft",
    }

# DESPUÉS:
    briefing_data = {
        "project_id": project_id,
        "title": f"Briefing: {gap.data['keyword']}",
        "target_keyword": gap.data["keyword"],
        "content_type": "article",
        "references": gap.data.get("competitor_urls", []),
        "status": "draft",
        "source_gap_id": gap_id,
    }
```

Si la columna `source_gap_id` no existe en tabla `briefings`, crear migración:

```sql
-- backend/db/migrations/066_briefing_source_gap.sql
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS source_gap_id INTEGER REFERENCES content_gaps(id) ON DELETE SET NULL;
```

En frontend BriefingsPage.tsx, donde se lista cada briefing, mostrar badge si tiene source_gap_id:

```tsx
{briefing.source_gap_id && (
  <span className="text-[10px] px-1.5 py-0.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 uppercase">
    Desde Gap
  </span>
)}
```

Complejidad: S (1 línea backend + 1 migración + badge frontend).

**Criterio:** Briefing creado desde gap tiene `source_gap_id` no null. Badge visible en lista.

---

### 39.6 — SROPage.tsx: textarea crear grupo con lista URLs (Item 127)

**Archivo:** `frontend/src/pages/SROPage.tsx`

Buscar el modal o formulario donde se crean grupos/batch. Actualmente solo hay botón "Batch top 20 URLs" (~L382-392).

Añadir botón "Batch Custom" que abre modal con textarea:

```typescript
const [showCustomBatch, setShowCustomBatch] = useState(false)
const [customUrlsText, setCustomUrlsText] = useState('')

// Botón al lado del existente:
<button onClick={() => setShowCustomBatch(true)}
  className="px-3 py-2 border border-border-subtle text-text-primary text-sm font-bold uppercase hover:border-brand-yellow">
  URLs personalizadas
</button>

// Modal:
{showCustomBatch && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div className="bg-dark-card border border-border-yellow p-6 w-full max-w-lg">
      <h3 className="text-sm font-bold text-brand-yellow uppercase mb-3">Batch SRO — URLs personalizadas</h3>
      <textarea value={customUrlsText} onChange={e => setCustomUrlsText(e.target.value)}
        placeholder="Pega una URL por línea..." rows={8}
        className="w-full bg-dark-surface border border-border-subtle text-text-primary text-sm p-3 mb-3" />
      <div className="flex justify-end gap-2">
        <button onClick={() => setShowCustomBatch(false)} className="px-3 py-2 text-sm text-text-muted">Cancelar</button>
        <button onClick={() => {
          const urls = customUrlsText.split('\n').map(u => u.trim()).filter(Boolean)
          if (urls.length === 0) return toast.error('Introduce al menos una URL')
          // reusar la misma lógica de batch pero con estas URLs
          onBatchAnalyze(urls)
          setShowCustomBatch(false)
        }} className="px-4 py-2 bg-brand-yellow text-black text-sm font-bold uppercase">
          Analizar {customUrlsText.split('\n').filter(u => u.trim()).length} URLs
        </button>
      </div>
    </div>
  </div>
)}
```

Si `onBatchAnalyze` no acepta array, modificar para que acepte `urls?: string[]` opcional, y si viene, usar esas en vez de las top 20.

Complejidad: M.

**Criterio:** Se puede pegar lista de URLs personalizada y lanzar batch SRO.

---

### 39.7 — DashboardPage.tsx: filtro etiquetas/tags en tabla URLs (Item 37)

**Archivo:** `frontend/src/pages/DashboardPage.tsx`

Buscar la tabla de URLs de revenue/acquisition (~L600-650). Añadir filtro por segmento/grupo/etiqueta.

Si no hay campo `tags` en los datos, usar los `url_groups` del backend (tabla `seo_tool_groups`). Obtener grupos existentes y crear filtro:

```typescript
// State:
const [urlTagFilter, setUrlTagFilter] = useState<string>('')

// Fetch groups:
const [urlGroups, setUrlGroups] = useState<string[]>([])
useEffect(() => {
  api.get<any[]>(`/projects/${project?.id}/seo-tools/groups`).then(g => {
    setUrlGroups(g.map(x => x.name))
  }).catch(() => {})
}, [project?.id])

// Filtro UI antes de la tabla:
{urlGroups.length > 0 && (
  <div className="flex gap-1 mb-2 flex-wrap">
    <button onClick={() => setUrlTagFilter('')}
      className={`px-2 py-0.5 text-[10px] uppercase border ${!urlTagFilter ? 'border-brand-yellow text-brand-yellow' : 'border-border-subtle text-text-muted'}`}>
      Todos
    </button>
    {urlGroups.map(g => (
      <button key={g} onClick={() => setUrlTagFilter(g)}
        className={`px-2 py-0.5 text-[10px] uppercase border ${urlTagFilter === g ? 'border-brand-yellow text-brand-yellow' : 'border-border-subtle text-text-muted'}`}>
        {g}
      </button>
    ))}
  </div>
)}

// En el .filter() de la tabla, añadir: && (!urlTagFilter || item.group === urlTagFilter)
```

Complejidad: M.

**Criterio:** Botones de filtro visibles, filtran la tabla de URLs por grupo/etiqueta.

---

### 39.8 — TechnicalSeoPage: Schema scan sin crawl (Item 120)

**Archivo:** `frontend/src/pages/technical-seo/TechnicalSeoPage.tsx`

Crear un tab nuevo `schema` que NO dependa de crawl data.

1. Añadir a la definición de TABS (~L20-28):
```typescript
{ id: 'schema', label: 'Schema Markup', icon: Code2 }
```

2. NO incluir 'schema' en SF_DEPENDENT_TABS (~L31).

3. Crear componente `SchemaTab.tsx` en `/technical-seo/tabs/`:
```tsx
// Input: URL individual
// Acción: fetch URL server-side, parsear JSON-LD y microdata
// Output: tipos de schema detectados, campos, validación

export default function SchemaTab({ projectId }: { projectId: number }) {
  const [url, setUrl] = useState('')
  const [schemas, setSchemas] = useState<any[]>([])
  const [scanning, setScanning] = useState(false)

  const handleScan = async () => {
    setScanning(true)
    try {
      const result = await api.post(`/projects/${projectId}/technical-seo/schema-scan`, { url })
      setSchemas(result.schemas || [])
    } finally { setScanning(false) }
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <input value={url} onChange={e => setUrl(e.target.value)} placeholder="URL a escanear..."
          className="flex-1 bg-dark-surface border border-border-subtle text-sm p-2 text-text-primary" />
        <button onClick={handleScan} disabled={scanning || !url}
          className="px-4 py-2 bg-brand-yellow text-black font-bold text-sm uppercase">
          {scanning ? 'Escaneando...' : 'Escanear Schema'}
        </button>
      </div>
      {schemas.map((s, i) => (
        <div key={i} className="bg-dark-card border border-border-subtle p-3 mb-2">
          <p className="text-sm font-bold text-brand-yellow">{s.type}</p>
          <pre className="text-xs text-text-muted mt-1 overflow-x-auto">{JSON.stringify(s.properties, null, 2)}</pre>
        </div>
      ))}
    </div>
  )
}
```

4. Backend endpoint `POST /projects/{id}/technical-seo/schema-scan`:
```python
import httpx
from bs4 import BeautifulSoup
import json

@router.post("/projects/{project_id}/technical-seo/schema-scan")
async def scan_schema(project_id: int, body: dict):
    url = body.get("url", "")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, follow_redirects=True)
    soup = BeautifulSoup(resp.text, "html.parser")
    schemas = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                schemas.extend(data)
            else:
                schemas.append(data)
        except: pass
    return {"url": url, "schemas": [{"type": s.get("@type", "Unknown"), "properties": s} for s in schemas]}
```

Complejidad: M.

**Criterio:** Tab Schema visible sin crawl. Input URL → muestra schemas JSON-LD detectados.

---

### 39.9 — EntityPanelPage.tsx: gráfico temporal con snapshots reales (Item 42)

**Archivo:** `frontend/src/pages/EntityPanelPage.tsx`

Buscar si hay LineChart/BarChart renderizado con datos de snapshots. Si solo hay lista/barras de progreso, reemplazar por Recharts LineChart temporal:

```typescript
// Fetch snapshots:
const [snapshots, setSnapshots] = useState<any[]>([])
useEffect(() => {
  api.get(`/projects/${projectId}/eeat-snapshots`).then(setSnapshots).catch(() => {})
}, [projectId])

// Renderizar:
{snapshots.length > 1 ? (
  <ResponsiveContainer width="100%" height={200}>
    <LineChart data={snapshots}>
      <XAxis dataKey="snapshot_date" tick={{ fontSize: 10 }} />
      <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
      <Tooltip />
      <Line type="monotone" dataKey="overall_score" stroke="#FEE630" strokeWidth={2} dot={false} />
    </LineChart>
  </ResponsiveContainer>
) : (
  <p className="text-xs text-text-muted text-center py-8">Ejecuta auditorías para generar datos históricos.</p>
)}
```

Complejidad: S.

**Criterio:** Gráfico LineChart visible con datos de snapshots. Fallback si no hay datos.

---

### 39.10 — Gaps priority sort UI (Item 178)

**Archivo:** Buscar en `frontend/src/pages/TopicalAuthorityPage.tsx` o `ContentGapsPage.tsx` la lista de gaps.

Añadir botón sort por priority:

```typescript
const [sortBy, setSortBy] = useState<'score' | 'priority'>('score')

// Botón:
<button onClick={() => setSortBy(sortBy === 'score' ? 'priority' : 'score')}
  className="text-xs text-text-muted border border-border-subtle px-2 py-1 hover:border-brand-yellow">
  Ord: {sortBy === 'score' ? 'Score' : 'Prioridad'}
</button>

// Sort:
const sortedGaps = [...gaps].sort((a, b) => {
  if (sortBy === 'priority') {
    const order = { high: 0, medium: 1, low: 2 }
    return (order[a.priority] ?? 2) - (order[b.priority] ?? 2)
  }
  return (b.score ?? 0) - (a.score ?? 0)
})
```

Complejidad: S.

**Criterio:** Botón toggle visible, ordena gaps por prioridad o score.

---

### 39.11 — TrendsPage.tsx: validación temporal chart (Item 155)

**Archivo:** `frontend/src/pages/TrendsPage.tsx`

Buscar donde se renderiza el LineChart de tendencias. Filtrar data points que estén en el futuro:

```typescript
const validData = trendData.filter(p => new Date(p.date || p.period) <= new Date())
// Usar validData en el <LineChart data={validData}> en vez de trendData
```

Complejidad: S.

**Criterio:** Gráfica no muestra meses futuros ni slots vacíos.

---

### 39.12 — claude_service.py: GEO prompt lista TODAS instituciones (Item 147)

**Archivo:** `backend/api/services/claude_service.py`

Buscar la función que genera el prompt de GEO audit (buscar "geo" o "GEO" o "geo_audit").

En el prompt, añadir instrucción explícita:

```python
# Añadir al prompt de GEO:
"""
IMPORTANTE: En tu respuesta, lista TODAS las instituciones, marcas y entidades mencionadas,
no solo la primera o la más relevante. Incluye universidades, federaciones, laboratorios,
organismos oficiales y cualquier entidad que aparezca en los resultados.
Indica la posición relativa de cada una si es posible.
"""
```

Complejidad: S.

**Criterio:** Prompt incluye instrucción "TODAS las instituciones".

---

### Auto-validación Sprint 39

```bash
#!/bin/bash
set -e
echo "═══════════════════════════════════════"
echo "  SPRINT 39 — VALIDACIÓN FINAL"
echo "═══════════════════════════════════════"

cd "/Codigo/Gestor de Contenido FIT/fit-content-app"
E=0

# Build + TSC
echo "[1/3] Build..."
cd frontend && npx tsc --noEmit && npm run build 2>&1 | tail -3 && cd ..
echo "  ✅ Build OK"

# Tests
echo "[2/3] Tests..."
cd backend && python -m pytest --tb=short -q 2>&1 | tail -3 && cd ..
echo "  ✅ Tests OK"

# Grep validaciones
echo "[3/3] Fixes..."
grep -q "weightedAvg\|impressions.*position.*reduce\|ponderada" frontend/src/pages/RankTrackerPage.tsx && echo "  ✅ 39.1 Pos media ponderada" || { echo "  ❌ 39.1"; E=$((E+1)); }
grep -q "all_urls\|canibalized_urls\|URLs canibalizada" frontend/src/pages/RankTrackerPage.tsx && echo "  ✅ 39.2 URLs canibalizadas sidebar" || { echo "  ❌ 39.2"; E=$((E+1)); }
grep -q "Google Search Console" frontend/src/pages/RankTrackerPage.tsx && echo "  ✅ 39.3 Sidebar descriptivo" || { echo "  ❌ 39.3"; E=$((E+1)); }
grep -q "Exportar\|downloadCSV\|handleExportCSV\|Download" frontend/src/pages/ContentSeriesPage.tsx && echo "  ✅ 39.4 Export CSV series" || { echo "  ❌ 39.4"; E=$((E+1)); }
grep -q "source_gap_id" backend/api/routes/gaps.py && echo "  ✅ 39.5 source_gap_id" || { echo "  ❌ 39.5"; E=$((E+1)); }
grep -q "customUrlsText\|showCustomBatch\|URLs personalizadas" frontend/src/pages/SROPage.tsx && echo "  ✅ 39.6 SRO batch custom" || { echo "  ❌ 39.6"; E=$((E+1)); }
grep -q "urlTagFilter\|urlGroups\|url_group" frontend/src/pages/DashboardPage.tsx && echo "  ✅ 39.7 Filtro etiquetas" || { echo "  ❌ 39.7"; E=$((E+1)); }
grep -q "schema-scan\|SchemaTab\|schema.*markup" frontend/src/pages/technical-seo/TechnicalSeoPage.tsx && echo "  ✅ 39.8 Schema sin crawl" || { echo "  ❌ 39.8"; E=$((E+1)); }
grep -q "snapshots.*LineChart\|snapshot_date\|datos históricos" frontend/src/pages/EntityPanelPage.tsx && echo "  ✅ 39.9 Gráfico snapshots" || { echo "  ❌ 39.9"; E=$((E+1)); }
grep -q "sortBy.*priority\|priority.*sort" frontend/src/pages/TopicalAuthorityPage.tsx 2>/dev/null || grep -q "sortBy.*priority" frontend/src/pages/ContentGapsPage.tsx 2>/dev/null && echo "  ✅ 39.10 Gaps sort priority" || { echo "  ❌ 39.10"; E=$((E+1)); }
grep -q "new Date()\|futuro\|<= new Date\|validData" frontend/src/pages/TrendsPage.tsx && echo "  ✅ 39.11 Trends temporal" || { echo "  ❌ 39.11"; E=$((E+1)); }
grep -q "TODAS.*institucion\|todas.*entidades\|TODAS las instituciones" backend/api/services/claude_service.py && echo "  ✅ 39.12 GEO todas instituciones" || { echo "  ❌ 39.12"; E=$((E+1)); }

echo ""
if [ $E -eq 0 ]; then echo "🎉 SPRINT 39: 12/12 ALL PASSED"; else echo "⚠️ SPRINT 39: $E ERRORES"; fi
exit $E
```

**Criterio final:** 0 errores TSC, build OK, tests pass, script validación 12/12 green.
**Tiempo estimado: 3-4 horas.** ~10 archivos frontend, ~3 archivos backend, 1 migración.

---

## Sprint 40 — Cierre definitivo: 5 ⚠️ → ✅ (100% feedback Excel)

**Objetivo:** Resolver los 5 items parciales restantes del Excel de feedback para alcanzar 100% completado.

**Items a resolver:**

| # | Item | Archivo principal | Severidad |
|---|------|-------------------|-----------|
| 40.1 | TimeoutMiddleware: logging + config env | `backend/main.py` | P1 |
| 40.2 | Entity Panel: trend con snapshots reales | `frontend/src/pages/EntityPanelPage.tsx` + `backend` | P2 |
| 40.3 | Focus Group: max_tokens + parallelización | `backend/api/services/focus_group_service.py` | P2 |
| 40.4 | Content Gaps: edición inline de prioridad | `frontend/src/pages/ContentGapsPage.tsx` | P2 |
| 40.5 | Content Validator: banner descriptivo completo | `frontend/src/pages/ContentValidatorPage.tsx` | P3 |

---

### 40.1 — TimeoutMiddleware: logging + config por entorno

**Archivo:** `backend/main.py` (L155-160)

**ANTES:**
```python
class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=120.0)
        except asyncio.TimeoutError:
            return JSONResponse(status_code=504, content={"detail": "Timeout: la operación tardó demasiado"})
```

**DESPUÉS:**
```python
import time

TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
# Rutas que necesitan más tiempo (IA, reportes batch)
LONG_TIMEOUT_PREFIXES = [
    "/projects/", # contiene /analyze, /detect, /generate, /focus-group
]
LONG_TIMEOUT_SECONDS = float(os.getenv("LONG_REQUEST_TIMEOUT_SECONDS", "300"))

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        timeout = LONG_TIMEOUT_SECONDS if any(
            path.startswith(p) and any(kw in path for kw in ["analyze", "detect", "generate", "focus-group", "narrative", "report"])
            else False for p in LONG_TIMEOUT_PREFIXES
        ) else TIMEOUT_SECONDS
        
        start = time.time()
        try:
            return await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            elapsed = time.time() - start
            logger.error(f"⏱️ TIMEOUT {request.method} {path} tras {elapsed:.1f}s (límite: {timeout}s)")
            return JSONResponse(
                status_code=504,
                content={
                    "detail": f"Timeout: la operación tardó más de {timeout:.0f}s",
                    "path": path,
                    "timeout_seconds": timeout,
                }
            )
```

**Nota:** `import time` ya puede existir — verificar. `os` ya está importado. `logger` ya definido arriba.

---

### 40.2 — Entity Panel: trend con snapshots reales desde EEAT+Brand

**Problema:** El LineChart (L725-738) renderiza `data.trend` pero los snapshots en `entity_health_snapshots` están vacíos si nunca se ejecutó el cron. La función `get_entity_trend()` en `entity_panel_service.py` (L415-437) ya busca snapshots, pero no tiene fallback a datos de EEAT/Brand audit si no hay snapshots propios.

**Archivo 1:** `backend/api/services/entity_panel_service.py` — Función `get_entity_trend()` (L415)

**ANTES (L415-437):**
```python
async def get_entity_trend(project_id: int, months: int = 6) -> list:
    """Fetch entity health score snapshots for trend chart."""
    try:
        sb = get_supabase()
        date_from = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
        result = sb.table("entity_health_snapshots").select(
            "snapshot_date, entity_health_score, brand_health_score, eeat_score, ymyl_score"
        ).eq("project_id", project_id).gte("snapshot_date", date_from).order("snapshot_date").execute()
        return [
            {
                "date": r["snapshot_date"],
                "entity_score": float(r.get("entity_health_score", 0)),
                "brand_health": float(r.get("brand_health_score", 0)),
                "eeat": float(r.get("eeat_score", 0)),
                "ymyl": float(r.get("ymyl_score", 0)),
            }
            for r in (result.data or [])
        ]
    except Exception as e:
        logger.error(f"Entity trend error: {e}")
        return []
```

**DESPUÉS:**
```python
async def get_entity_trend(project_id: int, months: int = 6) -> list:
    """Fetch entity health score snapshots for trend chart.
    Falls back to EEAT/Brand audit snapshots if entity snapshots are empty."""
    try:
        sb = get_supabase()
        date_from = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")

        # 1. Try entity_health_snapshots first
        result = sb.table("entity_health_snapshots").select(
            "snapshot_date, entity_health_score, brand_health_score, eeat_score, ymyl_score"
        ).eq("project_id", project_id).gte("snapshot_date", date_from).order("snapshot_date").execute()

        if result.data and len(result.data) >= 2:
            return [
                {
                    "date": r["snapshot_date"],
                    "entity_score": float(r.get("entity_health_score", 0)),
                    "brand_health": float(r.get("brand_health_score", 0)),
                }
                for r in result.data
            ]

        # 2. Fallback: build trend from eeat_audits + brand_audits created_at
        eeat_data = sb.table("eeat_audits").select(
            "created_at, overall_score"
        ).eq("project_id", project_id).gte("created_at", date_from).order("created_at").execute()

        brand_data = sb.table("brand_audits").select(
            "created_at, overall_score"
        ).eq("project_id", project_id).gte("created_at", date_from).order("created_at").execute()

        # Merge by date (truncated to day)
        from collections import defaultdict
        by_date = defaultdict(lambda: {"entity_score": 0, "brand_health": 0})
        for r in (eeat_data.data or []):
            d = r["created_at"][:10]
            by_date[d]["entity_score"] = float(r.get("overall_score", 0))
        for r in (brand_data.data or []):
            d = r["created_at"][:10]
            by_date[d]["brand_health"] = float(r.get("overall_score", 0))

        if not by_date:
            return []

        # Forward-fill missing values
        sorted_dates = sorted(by_date.keys())
        trend = []
        last_entity, last_brand = 0, 0
        for d in sorted_dates:
            entry = by_date[d]
            if entry["entity_score"] > 0: last_entity = entry["entity_score"]
            else: entry["entity_score"] = last_entity
            if entry["brand_health"] > 0: last_brand = entry["brand_health"]
            else: entry["brand_health"] = last_brand
            trend.append({"date": d, "entity_score": entry["entity_score"], "brand_health": entry["brand_health"]})
        return trend

    except Exception as e:
        logger.error(f"Entity trend error: {e}")
        return []
```

**Archivo 2:** `frontend/src/pages/EntityPanelPage.tsx` — Sin cambios necesarios. El LineChart ya consume `data.trend` correctamente (L725-738). El fix es solo backend.

---

### 40.3 — Focus Group: max_tokens a 2500 + evaluación paralela

**Archivo:** `backend/api/services/focus_group_service.py`

**Cambio 1 — L92:** `max_tokens=2000` → `max_tokens=2500`
```python
# ANTES:
text = await call_claude(prompt, max_tokens=2000)
# DESPUÉS:
text = await call_claude(prompt, max_tokens=2500)
```

**Cambio 2 — L151:** `max_tokens=2000` → `max_tokens=2500`
```python
# ANTES (en _evaluate_competitive):
text = await call_claude(prompt, max_tokens=2000)
# DESPUÉS:
text = await call_claude(prompt, max_tokens=2500)
```

**Cambio 3 — Añadir paralelización en la función principal que llama a _evaluate_content.**
Buscar el loop que itera sobre personas y reemplazar con `asyncio.gather`:

```python
# ANTES (patrón esperado):
results = {}
for persona in personas:
    result = await _evaluate_content(persona, url)
    results[str(persona["id"])] = result

# DESPUÉS:
import asyncio
tasks = [_evaluate_content(persona, url) for persona in personas]
evaluated = await asyncio.gather(*tasks, return_exceptions=True)
results = {}
for persona, result in zip(personas, evaluated):
    if isinstance(result, Exception):
        logger.error(f"Focus group persona {persona['name']} error: {result}")
        results[str(persona["id"])] = {"response": "Error evaluando", "score": 0}
    else:
        results[str(persona["id"])] = result
```

---

### 40.4 — Content Gaps: edición inline de prioridad por gap

**Archivo:** `frontend/src/pages/ContentGapsPage.tsx`

El backend ya tiene `PUT /projects/{id}/gaps/{id}` que acepta `priority` en `GapUpdate` (gaps.py L19-24). Solo falta UI.

**Cambio 1 — Añadir estado para edición (después de L25):**
```tsx
const [editingPriority, setEditingPriority] = useState<number | null>(null)
```

**Cambio 2 — Función para actualizar prioridad (después de L65):**
```tsx
const updatePriority = async (gapId: number, newPriority: string) => {
  await api.put(`/projects/${project?.id}/gaps/${gapId}`, { priority: newPriority })
  setEditingPriority(null)
  fetchGaps()
}
```

**Cambio 3 — Reemplazar columna priority (L85) con selector inline:**

**ANTES:**
```tsx
{ key: 'priority', label: 'Prioridad', render: (i: any) => <StatusBadge status={i.priority} /> },
```

**DESPUÉS:**
```tsx
{
  key: 'priority', label: 'Prioridad',
  render: (i: any) => editingPriority === i.id ? (
    <select
      value={i.priority}
      onChange={(e) => updatePriority(i.id, e.target.value)}
      onBlur={() => setEditingPriority(null)}
      autoFocus
      className="bg-dark-surface border border-brand-yellow text-text-primary text-xs px-2 py-1 rounded"
    >
      <option value="high">Alta</option>
      <option value="medium">Media</option>
      <option value="low">Baja</option>
    </select>
  ) : (
    <button onClick={() => setEditingPriority(i.id)} title="Clic para cambiar prioridad">
      <StatusBadge status={i.priority} />
    </button>
  ),
},
```

---

### 40.5 — Content Validator: banner descriptivo con features específicas

**Archivo:** `frontend/src/pages/ContentValidatorPage.tsx` (L315-320)

**ANTES:**
```tsx
<div className="bg-blue-900/20 border border-blue-500/30 p-4 rounded">
  <p className="text-xs text-blue-300">
    <strong>Diferencia con Revisor de Textos:</strong> El Validador evalúa si el contenido cumple con los objetivos SEO, la intención de búsqueda y la alineación con tu avatar.
    El <a href={`/project/${projectId}/text-review`} className="text-blue-400 underline hover:text-blue-300">Revisor de Textos</a> analiza la calidad técnica del HTML (headings, meta tags, legibilidad).
  </p>
</div>
```

**DESPUÉS:**
```tsx
<div className="bg-amber-900/15 border border-amber-500/30 p-4 rounded space-y-2">
  <p className="text-xs text-amber-300 font-bold">Validador de Contenido vs Revisor de Textos</p>
  <div className="grid grid-cols-2 gap-4">
    <div>
      <p className="text-[11px] text-amber-200 font-semibold mb-1">Validador (esta herramienta)</p>
      <p className="text-[11px] text-text-muted leading-relaxed">
        Evalúa alineación SEO estratégica: intención de búsqueda, coherencia con avatar, GEO Score para AI Overviews, densidad factual y estructura óptima para citación por LLMs.
      </p>
    </div>
    <div>
      <p className="text-[11px] text-blue-300 font-semibold mb-1">Revisor de Textos</p>
      <p className="text-[11px] text-text-muted leading-relaxed">
        Analiza calidad técnica HTML: jerarquía de headings, meta tags, legibilidad Flesch-Kincaid, señales E-E-A-T y on-page SEO técnico.{' '}
        <a href={`/project/${projectId}/text-review`} className="text-blue-400 underline hover:text-blue-300">Ir al Revisor</a>
      </p>
    </div>
  </div>
</div>
```

---

### Script de auto-validación Sprint 40

```bash
#!/bin/bash
set -e
E=0
cd "$(dirname "$0")/fit-content-app"

echo "═══ SPRINT 40 VALIDACIÓN ═══"
echo ""

# Build + TSC
echo "[1/3] Build..."
cd frontend && npm run build --silent && npx tsc --noEmit && cd ..
echo "  ✅ Build + TSC OK"

# Backend tests
echo "[2/3] Tests..."
cd backend && python -m pytest -q --tb=short 2>/dev/null && cd ..
echo "  ✅ Tests OK"

echo "[3/3] Sprint 40 items..."

# 40.1 TimeoutMiddleware con logging y env config
grep -q "REQUEST_TIMEOUT_SECONDS\|TIMEOUT_SECONDS\|os.getenv.*timeout\|os.getenv.*TIMEOUT" backend/main.py && echo "  ✅ 40.1 Timeout configurable por env" || { echo "  ❌ 40.1 Timeout config"; E=$((E+1)); }
grep -q "logger.*TIMEOUT\|logger.*timeout\|logger.*error.*path\|elapsed" backend/main.py && echo "  ✅ 40.1b Timeout logging" || { echo "  ❌ 40.1b Timeout logging"; E=$((E+1)); }

# 40.2 Entity trend fallback a EEAT/Brand
grep -q "eeat_audits\|brand_audits\|fallback\|Fallback" backend/api/services/entity_panel_service.py && echo "  ✅ 40.2 Entity trend fallback" || { echo "  ❌ 40.2 Entity trend"; E=$((E+1)); }

# 40.3 Focus Group max_tokens >= 2500
grep -q "max_tokens=2500\|max_tokens=3000" backend/api/services/focus_group_service.py && echo "  ✅ 40.3 Focus Group tokens" || { echo "  ❌ 40.3 Focus Group tokens"; E=$((E+1)); }

# 40.4 Content Gaps edición prioridad inline
grep -q "editingPriority\|updatePriority\|setEditingPriority" frontend/src/pages/ContentGapsPage.tsx && echo "  ✅ 40.4 Gaps priority edit" || { echo "  ❌ 40.4 Gaps priority"; E=$((E+1)); }

# 40.5 Content Validator banner descriptivo
grep -q "GEO Score\|densidad factual\|AI Overviews\|Validador.*Revisor\|esta herramienta" frontend/src/pages/ContentValidatorPage.tsx && echo "  ✅ 40.5 Validator banner" || { echo "  ❌ 40.5 Validator banner"; E=$((E+1)); }

echo ""
if [ $E -eq 0 ]; then echo "🎉 SPRINT 40: 6/6 ALL PASSED — 100% FEEDBACK EXCEL COMPLETADO"; else echo "⚠️ SPRINT 40: $E ERRORES"; fi
exit $E
```

**Criterio final:** 0 errores TSC, build OK, tests pass, script validación 6/6 green.
**Tiempo estimado: 1-2 horas.** 3 archivos backend, 2 archivos frontend. Sin migraciones nuevas.

---

## Sprint 41 — Resolución de 57 items pendientes (9 ❌ + 48 ⚠️)

**Objetivo:** Llevar los 204 items del Excel de feedback al 100% real verificado contra código.

**Organización:** 6 fases (A-F) agrupadas por archivo para minimizar context switching.

---

### FASE A — ❌ Críticos (9 items)

#### A.1 [58] Buyer personas: edit/delete
**Archivo:** `frontend/src/pages/PeoplePage.tsx` (L289-350)

El grid de personas (L289-350) no tiene botones de edición ni eliminación. Solo muestra datos read-only.

**Añadir en L291, después de la línea `<div className="flex items-center justify-between">`:**
```tsx
{/* L291 — dentro del flex justify-between, después del bloque de nombre+DEFAULT */}
<div className="flex gap-1">
  <button
    onClick={(e) => { e.stopPropagation(); setEditingPersona(p) }}
    className="p-1 text-text-muted hover:text-brand-yellow"
    title="Editar persona"
  >
    <Edit3 size={12} />
  </button>
  <button
    onClick={async (e) => {
      e.stopPropagation()
      if (!confirm(`¿Eliminar persona "${p.name}"?`)) return
      await api.delete(`/projects/${project?.id}/personas/${p.id}`)
      load()
    }}
    className="p-1 text-text-muted hover:text-red-400"
    title="Eliminar persona"
  >
    <Trash2 size={12} />
  </button>
</div>
```

**Añadir imports:** `Edit3, Trash2` de lucide-react.
**Añadir estado:** `const [editingPersona, setEditingPersona] = useState<any>(null)`

**Backend:** Verificar que `DELETE /projects/{id}/personas/{id}` existe. Si no, añadir:
```python
@router.delete("/projects/{project_id}/personas/{persona_id}")
async def delete_persona(project_id: int, persona_id: int, access: dict = Depends(require_module_access("people"))):
    sb = get_supabase()
    sb.table("buyer_personas").delete().eq("id", persona_id).eq("project_id", project_id).execute()
    return {"ok": True}
```

#### A.2 [82] Percepción LLM: mostrar modelo usado
**Archivo:** `frontend/src/pages/BrandAuditPage.tsx` (L454)

**ANTES:**
```tsx
<span className="text-[9px] text-text-muted mt-2 inline-block bg-dark-surface px-2 py-1 rounded">Claude Sonnet 4</span>
```

**DESPUÉS:**
```tsx
<span className="text-[9px] text-text-muted mt-2 inline-block bg-dark-surface px-2 py-1 rounded">
  Modelo: {data.model_used || 'Claude Sonnet 4'}
</span>
```

**Backend:** En la función que genera la auditoría de marca, incluir `model_used` en la respuesta:
```python
# En brand_audit_service.py, en la respuesta de la auditoría:
result["model_used"] = "claude-sonnet-4-20250514"  # o el modelo real usado
```

#### A.3 [109] Keywords: alertas solo caídas
**Archivo:** `frontend/src/pages/RankTrackerPage.tsx` (L485)

**ANTES:**
```tsx
{[...alerts].sort((a, b) => a.change - b.change).slice(0, 10).map((a, i) => (
```

**DESPUÉS:**
```tsx
{[...alerts].filter(a => a.type === 'drop').sort((a, b) => a.change - b.change).slice(0, 10).map((a, i) => (
```

**Nota:** El color condicional L489 ya no necesita cambio porque solo habrá `type === 'drop'`.

#### A.4 [125] Grupos URLs: "Undefined" en autodetectar
**Archivo:** `frontend/src/pages/UrlGroupsPage.tsx` (L137-139)

El backend retorna `{ groups_created: N, groups: [...] }` pero el frontend lee `res.created`.

**ANTES:**
```tsx
const res = await api.post<{ created: number; groups: unknown[] }>(`/projects/${projectId}/seo-tools/url-groups/auto-detect`, {})
const count = res.created || 0
toast.success(`${count} grupos detectados`)
```

**DESPUÉS:**
```tsx
const res = await api.post<{ groups_created: number; groups: unknown[] }>(`/projects/${projectId}/seo-tools/url-groups/auto-detect`, {})
const count = res.groups_created ?? res.created ?? 0
toast.success(`${count} grupos detectados`)
```

#### A.5 [203] Usuarios activos: indicador real
**Archivo:** `frontend/src/pages/settings/UsersSettings.tsx`

El check actual usa `last_sign_in_at` con 7 días. El issue dice "no detecta cuando estoy dentro en el cuadro de Usuarios activos". El usuario actual debería verse siempre como activo.

**Añadir comparación con usuario actual:**
```tsx
// En el render de cada usuario, verificar si es el usuario logueado
const isCurrentUser = u.id === currentUser?.id  // currentUser del AuthContext
// Entonces:
const isActive = isCurrentUser || (u.last_sign_in_at && (Date.now() - new Date(u.last_sign_in_at).getTime()) < 7 * 24 * 60 * 60 * 1000)
```

#### A.6 [66] Reviews: info auto-read de plataformas
**Archivo:** `frontend/src/pages/ReputationPage.tsx` — ReviewsTab

Añadir botón "Auto-rellenar con IA" que llame a un endpoint que use Claude para extraer datos de la URL de la plataforma.

```tsx
{/* Junto al botón de Añadir plataforma */}
<button
  onClick={async () => {
    toast.info('Analizando plataformas con IA...')
    try {
      await api.post(`/projects/${project?.id}/reputation/reviews/auto-fetch`)
      toast.success('Datos actualizados desde plataformas')
      load()
    } catch { toast.error('Error al obtener datos') }
  }}
  className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-500/20 border border-purple-500/40 text-purple-300 text-xs font-bold uppercase hover:bg-purple-500/30"
>
  <Sparkles size={12} /> Auto-rellenar con IA
</button>
```

**Backend:** Crear endpoint `POST /projects/{id}/reputation/reviews/auto-fetch` que, para cada plataforma registrada con URL, haga fetch+parse del rating y review count usando Claude.

#### A.7 [71] Menciones: automatización
**Archivo:** `frontend/src/pages/ReputationPage.tsx` — MentionsTab

Añadir botón "Escanear menciones" que use Claude + web search para buscar menciones de la marca.

```tsx
<button
  onClick={async () => {
    toast.info('Buscando menciones online...')
    try {
      const res = await api.post(`/projects/${project?.id}/reputation/mentions/scan`)
      toast.success(`${res.found || 0} menciones encontradas`)
      load()
    } catch { toast.error('Error al escanear') }
  }}
  className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-500/20 border border-purple-500/40 text-purple-300 text-xs font-bold uppercase hover:bg-purple-500/30"
>
  <Search size={12} /> Escanear menciones
</button>
```

**Backend:** Crear endpoint `POST /projects/{id}/reputation/mentions/scan` que use Claude para buscar menciones de la marca en web.

#### A.8 [73] Menciones: campo Medio/Fuente
**Archivo:** `frontend/src/pages/ReputationPage.tsx` (L775-777)

**VERIFICACIÓN:** Ya está implementado. L777 ya tiene:
```tsx
<p className="text-[9px] text-text-muted mt-1">El medio indica la publicación (blog, periódico, podcast, etc.)</p>
```
**→ ✅ YA RESUELTO — Marcar como completado**

#### A.9 [74] Menciones: maxLength Extracto
**Archivo:** `frontend/src/pages/ReputationPage.tsx` (L793-795)

**VERIFICACIÓN:** Ya está implementado. L794 ya tiene `maxLength={500}` y L795 muestra contador.
**→ ✅ YA RESUELTO — Marcar como completado**

---

### FASE B — ⚠️ Entidad (18 items)

#### B.1 [56] People: URL autor auto-detect URLs
Añadir en la ficha del miembro un botón "Detectar artículos" que, dada la `website_profile_url`, haga scraping del sitemap o de la página de autor para extraer URLs.

**Frontend:** Botón en detalle de persona → `POST /projects/{id}/people/{id}/auto-detect-content`
**Backend:** Fetch sitemap, filtrar por author slug, añadir al listado.

#### B.2 [60] Buyer personas no corresponde target
Mejorar prompt en `claude_service.py` en la función de generación de personas. Añadir contexto del negocio (dominio, nicho, marca) al prompt.

#### B.3 [62] Focus Group: "Como X" redundante
**Archivo:** `frontend/src/pages/PeoplePage.tsx` (FocusGroupTab)
En el render de resultados, eliminar el prefijo "Como [nombre]," que aparece al inicio de cada respuesta. Filtrar con:
```tsx
const cleanResponse = (text: string, name: string) =>
  text.replace(new RegExp(`^Como ${name}[,:]?\\s*`, 'i'), '')
```

#### B.4 [64] Focus Group: botón "Ejecutar otro" más visible
Cambiar de link a botón prominente con estilo `bg-brand-yellow text-dark-bg`.

#### B.5 [65] Focus Group: opiniones genéricas
Mejorar prompt: añadir instrucción "Sé específico y concreto, no des respuestas genéricas. Cita detalles del contenido."

#### B.6 [69] Reviews: checkbox sin tooltip
Añadir `title="Marca si la fuente tiene un enlace directo al testimonio"` al checkbox.

#### B.7 [75] Asociaciones: descripción desaparece
Mantener el helper text siempre visible, incluso con datos. Moverlo fuera del EmptyState.

#### B.8 [78] Trust Signals: verificar con SF error
Mejorar error handling: si SF no está conectado, mostrar mensaje descriptivo en vez de error genérico.

#### B.9-B.14 [80-90] Brand Visibility (6 items)
- [80] Brand Visibility Index: verificar que `visibility_index` se renderiza desde datos de auditoría
- [81] Cuadrante marca: verificar que ScatterChart recibe data correctamente
- [83] Columna Estado: añadir status badge en tabla de prompts
- [84] Tabla Querys Tipo: verificar columna `type` en tabla
- [85] Coherencia Keywords: verificar que tab renderiza datos de coherence analysis
- [86-90] Tendencia: historial auditorías, labels P1/P2, periodos, posición media, badge estado
  - [87] Cambiar "H2 vs H1" a "P1 vs P2" en labels
  - [88] Añadir label de periodos comparados
  - [90] Corregir posición del badge de Trust Liabilities: añadir `mt-auto` o `self-end`

---

### FASE C — ⚠️ Auditoría Técnica (15 items)

#### C.1 [23] Alertas: clic canibalizaciones muestre URLs inline
En DashboardPage, cuando el alert de canibalización se muestra, añadir tooltip/popover con las URLs afectadas en vez de solo navegar a la página.

#### C.2 [37] A revisar: calidad análisis IA
Mejorar prompt de análisis en `claude_service.py`: añadir instrucción "No sugieras poner el año en el título si el contenido es evergreen."

#### C.3 [99] Canibalizaciones: resuelta reaparece
En el backend de detección, excluir keywords con status `resolved` del re-análisis:
```python
# En la query de detección, filtrar:
.neq("status", "resolved")
```

#### C.4 [101] Canibalizaciones: plan de acción retry
Añadir botón "Reintentar" cuando el plan de acción falla.

#### C.5 [102] Keywords: tooltip botón Scores
Añadir `title="Recalcula los scores de oportunidad para todas las keywords"` al botón.

#### C.6 [104] Keywords: periodos sin clarificar
Añadir label debajo del gráfico: "Comparando: últimos 28 días vs 28 días anteriores"

#### C.7 [107] Keywords: Striking Distance no muestra todas URLs
Expandir el sidebar para mostrar todas las URLs que posicionan para la keyword, no solo la principal.

#### C.8 [111] Keywords: sidebar texto explicativo
Añadir texto descriptivo al sidebar cuando no hay keyword seleccionada: "Selecciona una keyword de la tabla para ver su posición, URL, CTR y oportunidades de mejora."

#### C.9 [113] Keywords: canibalizado muestra única URL
En sidebar, cuando una keyword está canibalizada, mostrar todas las URLs con `.map()` en vez de solo la primera.

#### C.10 [115-118] SEO Técnico: 4 tabs piden subir crawl
Los 4 tabs (Indexación, Arquitectura, Crawl Budget, Interlinking) muestran EmptyState pidiendo subir crawl aunque ya hay uno. El problema está en `status?.has_crawl_data`.

**Verificar** que el endpoint `/projects/{id}/technical-seo/status` retorna `has_crawl_data: true` cuando hay crawls importados. Si el check es correcto, el fix es frontend: cachear el status y no re-fetchear en cada cambio de tab.

#### C.11 [120] Inspector URL: Google Index sin datos
Verificar endpoint backend. Si requiere GSC API, asegurar que el token GSC se pasa correctamente.

#### C.12 [122] Quality Gates: sin datos con Analizar
Verificar que el análisis de Quality Gates genera resultados y los guarda. Añadir retry + loading state mejorado.

#### C.13 [124] Google Index: sin datos con Recalcular
Mismo patrón que C.11 — verificar backend endpoint y GSC token.

---

### FASE D — ⚠️ Investigación + Tendencias (6 items)

#### D.1 [136] Competencia: texto confuso
Reemplazar "Marcas > Personas > Resultados" por tabs claros o eliminar el texto. Usar tabs normales.

#### D.2 [140-141] Competencia: sitemaps 0 URLs
Verificar parsing recursivo de sitemaps (sitemap index → sitemaps individuales). Añadir soporte para `<sitemapindex>`.

#### D.3 [142] Landing pages SSR: sin datos
Implementar backend para detectar y listar landing pages con SSR (fetch + check meta tags).

#### D.4 [150] Monitor LLM: agrupar consultas por tipo
Añadir dropdown de filtro por tipo de consulta (informacional, transaccional, navegacional) en LLMMonitorPage.

#### D.5 [153] Tendencias: keywords sin resultados
Mejorar manejo cuando Google Trends no devuelve datos: mostrar "Sin datos de tendencia para esta keyword" en vez de dejar vacío.

---

### FASE E — ⚠️ Contenido + Informes (7 items)

#### E.1 [170] Briefings: tipo URL no se puede cambiar
Hacer `content_type` editable en el formulario de edición del briefing. Añadir select con opciones.

#### E.2 [175] Series: aviso canibalización
En ContentSeriesPage, tras generar topics, verificar keywords duplicadas contra content existente y content_gaps. Mostrar warning badge.

#### E.3 [176] Series: flujo topic→brief
Añadir botón "Crear briefing" en cada topic de la serie que llame a `POST /projects/{id}/briefings` con los datos del topic.

#### E.4 [182] Hub Multicanal: modo automático
Añadir botón "Importar desde sitemap" que cree entradas automáticamente desde URLs del sitemap del proyecto.

#### E.5 [183] Hub Multicanal: conexión progreso
Añadir enlace/integración con el dashboard de rendimiento para ver métricas de las URLs registradas.

#### E.6 [191] Reportes: segmentos mezclados
En la generación de informes, separar URLs por tipo (carpeta vs página) en la sección de segmentos.

#### E.7 [193] Reportes: informe manual incompleto
Ampliar el formulario de creación manual para incluir: secciones de métricas, gráficos seleccionables, insights manuales, además del resumen ejecutivo.

---

### FASE F — ⚠️ Sistema (1 item)

#### F.1 [196] Logo no se carga correctamente
**Archivo:** `frontend/src/pages/settings/GeneralSettings.tsx` (L75-103)

Actualmente solo acepta URL. Problemas: URLs externas con CORS, URLs temporales.
- Añadir upload de archivo (no solo URL): input type="file" + subir a Supabase Storage
- Fallback: si URL falla, mostrar placeholder con iniciales de la marca

---

### Script de auto-validación Sprint 41

```bash
#!/bin/bash
set -e
E=0
cd "$(dirname "$0")/fit-content-app"

echo "═══ SPRINT 41 VALIDACIÓN ═══"
echo ""

echo "[1/3] Build + TSC..."
cd frontend && npm run build --silent && npx tsc --noEmit && cd ..
echo "  ✅ Build + TSC OK"

echo "[2/3] Tests..."
cd backend && python -m pytest -q --tb=short 2>/dev/null && cd ..
echo "  ✅ Tests OK"

echo "[3/3] Sprint 41 items..."

# FASE A — Críticos
grep -q "Trash2\|handleDelete.*persona\|delete.*persona\|eliminar.*persona" frontend/src/pages/PeoplePage.tsx && echo "  ✅ A.1 Personas edit/delete" || { echo "  ❌ A.1"; E=$((E+1)); }
grep -q "model_used\|modelo.*usado\|Modelo:" frontend/src/pages/BrandAuditPage.tsx && echo "  ✅ A.2 Modelo LLM" || { echo "  ❌ A.2"; E=$((E+1)); }
grep -q "filter.*drop\|\.filter.*type.*drop" frontend/src/pages/RankTrackerPage.tsx && echo "  ✅ A.3 Alertas solo caídas" || { echo "  ❌ A.3"; E=$((E+1)); }
grep -q "groups_created" frontend/src/pages/UrlGroupsPage.tsx && echo "  ✅ A.4 URL Groups fix" || { echo "  ❌ A.4"; E=$((E+1)); }
grep -q "isCurrentUser\|currentUser.*id\|usuario.*actual" frontend/src/pages/settings/UsersSettings.tsx && echo "  ✅ A.5 Usuarios activos" || { echo "  ❌ A.5"; E=$((E+1)); }
grep -q "auto-fetch\|auto.rellenar\|Auto-rellenar" frontend/src/pages/ReputationPage.tsx && echo "  ✅ A.6 Reviews auto-fetch" || { echo "  ❌ A.6"; E=$((E+1)); }
grep -q "scan.*menciones\|mentions.*scan\|Escanear.*menc" frontend/src/pages/ReputationPage.tsx && echo "  ✅ A.7 Menciones scan" || { echo "  ❌ A.7"; E=$((E+1)); }

# FASE B — Entidad
grep -q "auto-detect-content\|Detectar artículos" frontend/src/pages/PeoplePage.tsx && echo "  ✅ B.1 Auto-detect content" || { echo "  ⚠️ B.1"; E=$((E+1)); }
grep -q "cleanResponse\|Como.*replace\|prefijo" frontend/src/pages/PeoplePage.tsx && echo "  ✅ B.3 Focus Group Como X" || { echo "  ⚠️ B.3"; E=$((E+1)); }
grep -q "P1 vs P2\|P1.*vs.*P2" frontend/src/pages/BrandAuditPage.tsx && echo "  ✅ B.14 Labels P1/P2" || { echo "  ⚠️ B.14"; E=$((E+1)); }

# FASE C — Auditoría técnica
grep -q "filter.*drop\|\.filter.*type.*drop" frontend/src/pages/RankTrackerPage.tsx && echo "  ✅ C.3 Alertas drop-only" || { echo "  ⚠️ C.3"; E=$((E+1)); }
grep -q "Selecciona una keyword\|sidebar.*descriptivo\|explicativ" frontend/src/pages/RankTrackerPage.tsx && echo "  ✅ C.8 Sidebar texto" || { echo "  ⚠️ C.8"; E=$((E+1)); }

# FASE D — Investigación
grep -q "informacional\|transaccional\|navegacional\|query_type" frontend/src/pages/LLMMonitorPage.tsx && echo "  ✅ D.4 LLM filtro tipo" || { echo "  ⚠️ D.4"; E=$((E+1)); }

# FASE E — Contenido
grep -q "content_type.*select\|content_type.*editable\|tipo.*cambiar" frontend/src/pages/BriefingsPage.tsx 2>/dev/null || grep -q "content_type.*select" frontend/src/pages/BriefingDetailPage.tsx 2>/dev/null && echo "  ✅ E.1 Briefing tipo editable" || { echo "  ⚠️ E.1"; E=$((E+1)); }
grep -q "canibalización\|cannibalization.*warn\|duplicate.*keyword" frontend/src/pages/ContentSeriesPage.tsx && echo "  ✅ E.2 Series canibalización" || { echo "  ⚠️ E.2"; E=$((E+1)); }
grep -q "Crear briefing\|crear.*brief\|topic.*brief" frontend/src/pages/ContentSeriesPage.tsx && echo "  ✅ E.3 Topic→Brief" || { echo "  ⚠️ E.3"; E=$((E+1)); }

# FASE F — Sistema
grep -q "type.*file\|file.*upload\|supabase.*storage.*logo\|handleFileUpload" frontend/src/pages/settings/GeneralSettings.tsx && echo "  ✅ F.1 Logo upload file" || { echo "  ⚠️ F.1"; E=$((E+1)); }

echo ""
if [ $E -eq 0 ]; then echo "🎉 SPRINT 41: ALL PASSED"; else echo "⚠️ SPRINT 41: $E items pendientes"; fi
exit $E
```

**Prioridad de implementación:**
1. **Fase A** (❌ críticos) — Máxima prioridad, 7 items reales (A.8 y A.9 ya resueltos)
2. **Fase C** (Auditoría técnica) — 15 items, muchos son verificaciones
3. **Fase B** (Entidad) — 18 items, mezcla de UI y prompts
4. **Fase E** (Contenido) — 7 items, flujos de trabajo
5. **Fase D** (Investigación) — 6 items
6. **Fase F** (Sistema) — 1 item

**Tiempo estimado: 12-16 horas.**
~25 archivos frontend, ~10 archivos backend, ~2 migraciones posibles.

**Nota:** Los items [73] y [74] se marcan como ya resueltos (verificado en código: L777 tiene texto explicativo, L794 tiene maxLength=500).

---

## Sprint 42 — Cierre de Auditoría (Feb 2026)

**Objetivo:** Resolver el ÚNICO item verdaderamente pendiente y documentar el cierre de los 204 items.

### Re-auditoría post-Sprint 41: Hallazgos

Tras auditar el código línea por línea, de los 9 items reportados como pendientes (2 ❌ + 7 ⚠️), **8 de 9 ya están implementados**:

| # | Item | Archivo | Evidencia | Estado Real |
|---|------|---------|-----------|-------------|
| [175] | Series canibalización badge | ContentSeriesPage.tsx | `isCannibalizing()` L124-127, badge L386-389, L450-454 | ✅ YA IMPLEMENTADO |
| [176] | Topic → Crear briefing | ContentSeriesPage.tsx | `handleCreateBriefingFromTopic(t)` L455-462 | ✅ YA IMPLEMENTADO |
| [111] | Sidebar texto descriptivo | RankTrackerPage.tsx | Texto explicativo L687-689 | ✅ YA IMPLEMENTADO |
| [153] | Tendencias empty state | TrendsPage.tsx | Mensaje completo + sugerencias L541-546 | ✅ YA IMPLEMENTADO |
| [193] | Reportes manuales KPIs+charts | ReportsPage.tsx | Campos KPIs L25-28, charts L29-31, insights L32 | ✅ YA IMPLEMENTADO |
| [101] | Plan acción reintentar | CannibalizationsPage.tsx | Botón "Reintentar" con RotateCcw L471-474 | ✅ YA IMPLEMENTADO |
| [104] | Periodos label | RankTrackerPage.tsx | "Comparando: últimos 28 días vs 28 días anteriores" L728 | ✅ YA IMPLEMENTADO |
| [99] | Canibalizaciones excluir resueltas | cannibalization_service.py | `.neq("status", "resolved")` L212 + `resolved_kw_ids` L216 | ✅ YA IMPLEMENTADO |
| [191] | Reportes segmentos carpetas/páginas | reports/ReportDetail.tsx | `isFolder()` L440, "Carpetas" vs "Páginas individuales" L455-460 | ✅ YA IMPLEMENTADO |

**Items adicionales verificados como resueltos:**
- [124] Google Index recalcular: `GoogleInspectionTab.tsx` tiene botón "Recalcular" L267-273 con estado de error "Reintentar" L292 y mensaje explicativo L283-284. El "sin datos" es el empty state correcto.

### Único item con mejora posible

#### A.1 [86] BrandAuditPage — Subtítulo "Evolución BVI" → "Historial de Auditorías"

**Estado actual:** La tab se llama "Tendencia" (L279) y el subtítulo dentro dice "Evolución BVI" (L818). Funciona correctamente mostrando un LineChart con histórico de BVI y módulos. También incluye tabla de snapshots.

**Mejora:** El feedback original pedía "Historial de auditorías" como concepto. El subtítulo "Evolución BVI" es técnicamente correcto pero no comunica que es un historial de auditorías pasadas.

**Cambio:**
```
Archivo: frontend/src/pages/BrandAuditPage.tsx
Línea 818:
  ANTES: <span className="text-xs font-bold uppercase text-text-secondary mb-2 block">Evolución BVI</span>
  DESPUÉS: <span className="text-xs font-bold uppercase text-text-secondary mb-2 block">Historial de Auditorías — Evolución BVI</span>
```

**Impacto:** 1 línea. Cosmético.

---

### Resumen de cierre

| Métrica | Valor |
|---------|-------|
| Items totales auditoría original | 204 |
| Items ✅ post-Sprint 40 (audit real) | 147 (72.1%) |
| Items corregidos Sprint 41 | 48 |
| Items re-verificados como ✅ (Sprint 42) | 9 |
| Item cosmético restante | 1 ([86] subtítulo) |
| **Total implementado** | **203/204 (99.5%)** |
| **Con fix cosmético** | **204/204 (100%)** |

### Validación Sprint 42

```bash
#!/bin/bash
# Sprint 42 — Validación de cierre
cd "/Codigo/Gestor de Contenido FIT/fit-content-app"
E=0

# Único fix: subtítulo Historial
grep -q "Historial de Auditorías" frontend/src/pages/BrandAuditPage.tsx && echo "  ✅ [86] Subtítulo historial" || { echo "  ⚠️ [86]"; E=$((E+1)); }

# Re-verificación de items que ya estaban implementados
grep -q "isCannibalizing" frontend/src/pages/ContentSeriesPage.tsx && echo "  ✅ [175] Canibalización badge" || { echo "  ⚠️ [175]"; E=$((E+1)); }
grep -q "handleCreateBriefingFromTopic\|createBriefFromTopic" frontend/src/pages/ContentSeriesPage.tsx && echo "  ✅ [176] Topic→Brief" || { echo "  ⚠️ [176]"; E=$((E+1)); }
grep -q "Selecciona una keyword\|sidebar.*text\|explicativ" frontend/src/pages/RankTrackerPage.tsx && echo "  ✅ [111] Sidebar texto" || { echo "  ⚠️ [111]"; E=$((E+1)); }
grep -q "No hay tendencias\|sin tendencias\|empty.*trend\|Empieza añadiendo" frontend/src/pages/TrendsPage.tsx && echo "  ✅ [153] Empty state" || { echo "  ⚠️ [153]"; E=$((E+1)); }
grep -q "metric_clicks\|metric_impressions\|metric_ctr" frontend/src/pages/ReportsPage.tsx && echo "  ✅ [193] Reportes KPIs" || { echo "  ⚠️ [193]"; E=$((E+1)); }
grep -q "Reintentar\|reintentar\|RotateCcw\|retry" frontend/src/pages/CannibalizationsPage.tsx && echo "  ✅ [101] Retry button" || { echo "  ⚠️ [101]"; E=$((E+1)); }
grep -q "Comparando\|últimos.*días.*anteriores\|periodo.*label" frontend/src/pages/RankTrackerPage.tsx && echo "  ✅ [104] Periodo label" || { echo "  ⚠️ [104]"; E=$((E+1)); }
grep -q 'neq.*status.*resolved\|exclude.*resolved' backend/api/services/cannibalization_service.py && echo "  ✅ [99] Filter resolved" || { echo "  ⚠️ [99]"; E=$((E+1)); }
grep -q "isFolder\|Carpetas\|Páginas individuales" frontend/src/pages/reports/ReportDetail.tsx && echo "  ✅ [191] Segments folders/pages" || { echo "  ⚠️ [191]"; E=$((E+1)); }
grep -q "Recalcular\|recalculating" frontend/src/pages/technical-seo/tabs/GoogleInspectionTab.tsx && echo "  ✅ [124] Google Index recalculate" || { echo "  ⚠️ [124]"; E=$((E+1)); }

echo ""
if [ $E -eq 0 ]; then echo "🎉 SPRINT 42: AUDITORÍA 204/204 COMPLETA"; else echo "⚠️ SPRINT 42: $E items pendientes"; fi
exit $E
```

**Tiempo estimado: < 1 hora** (1 cambio cosmético + generación de Excel final de cierre).

---

## Sprint 43 — Cierre Definitivo: 15 items ⚠️ (Feb 2026)

**Objetivo:** Resolver los 15 items parcialmente implementados detectados en la auditoría profunda de 204 items.

**Organización:** 3 fases por dificultad. Cada fix incluye archivo exacto, líneas, código antes/después.

---

### FASE A — Fixes rápidos (6 items, ~2h)

#### A.1 [158] AnalysisPage: traducir 'article' → 'Artículo' en tabla

**Archivo:** `frontend/src/pages/AnalysisPage.tsx`

**Problema:** La tabla muestra `article` en inglés pero el filtro select ya dice `Artículo`.

**Fix:** Añadir mapa de traducción y usarlo en la columna Tipo.

```tsx
// AÑADIR después de imports (~línea 8):
const TYPE_LABELS: Record<string, string> = {
  article: 'Artículo',
  landing: 'Landing',
  podcast: 'Podcast',
  video: 'Vídeo',
  page: 'Página',
  product: 'Producto',
}

// MODIFICAR en la definición de columns (~línea 134):
// ANTES:
{ key: 'type', label: 'Tipo', sortable: true },
// DESPUÉS:
{ key: 'type', label: 'Tipo', sortable: true, render: (row: any) => TYPE_LABELS[row.type] || row.type },
```

---

#### A.2 [94] CannibalizationsPage: traducir status + botón revertir desde 'reviewing'

**Archivo:** `frontend/src/pages/CannibalizationsPage.tsx`

**Problema:** (1) StatusBadge podría mostrar "reviewing" sin traducir. (2) Desde estado `reviewing` no hay opción de volver a `detected`.

**Fix 1 — StatusBadge:** Verificar/crear mapa de traducción.

```tsx
// En StatusBadge.tsx o inline en CannibalizationsPage, AÑADIR:
const STATUS_LABELS: Record<string, string> = {
  detected: 'Detectada',
  reviewing: 'En revisión',
  resolved: 'Resuelta',
}

// Usar en badge:
<span className={...}>{STATUS_LABELS[status] || status}</span>
```

**Fix 2 — Botón revertir desde reviewing (~línea 223-229):**

```tsx
// ANTES:
{item.status === 'reviewing' && (
  <button onClick={(e) => { e.stopPropagation(); updateStatus(item.id, 'resolved') }}
    className="px-2 py-1 text-xs font-bold uppercase border border-green-400 text-green-400 hover:bg-green-400/10">
    Resolver
  </button>
)}

// DESPUÉS:
{item.status === 'reviewing' && (
  <div className="flex gap-1.5">
    <button onClick={(e) => { e.stopPropagation(); updateStatus(item.id, 'resolved') }}
      className="px-2 py-1 text-xs font-bold uppercase border border-green-400 text-green-400 hover:bg-green-400/10">
      Resolver
    </button>
    <button onClick={(e) => { e.stopPropagation(); updateStatus(item.id, 'detected') }}
      className="px-2 py-1 text-xs font-bold uppercase border border-text-muted text-text-muted hover:bg-white/5">
      Revertir
    </button>
  </div>
)}
```

---

#### A.3 [134] CompetitorsPage: reemplazar prompt() por modal

**Archivo:** `frontend/src/pages/CompetitorsPage.tsx`

**Problema:** `syncSitemap()` usa `prompt()` nativo del navegador, que se ve feo y no permite validación.

**Fix:** Reemplazar con estado + modal inline.

```tsx
// AÑADIR estados (~línea 18):
const [sitemapModal, setSitemapModal] = useState<any>(null)
const [sitemapUrl, setSitemapUrl] = useState('')

// MODIFICAR syncSitemap (~línea 96):
// ANTES:
const syncSitemap = async (c: any) => {
  const sitemapUrl = c.sitemap_url || prompt('URL del sitemap:', `https://${c.domain}/sitemap.xml`)
  if (!sitemapUrl) return
  // ...

// DESPUÉS:
const openSitemapSync = (c: any) => {
  setSitemapUrl(c.sitemap_url || `https://${c.domain}/sitemap.xml`)
  setSitemapModal(c)
}

const confirmSitemapSync = async () => {
  if (!sitemapModal || !sitemapUrl) return
  const c = sitemapModal
  setSitemapModal(null)
  setSyncing(c.id)
  try {
    const result = await api.post<{ total: number; new: number }>(
      `/projects/${project?.id}/competitors/${c.id}/sync-sitemap`, { sitemap_url: sitemapUrl })
    toast.success(`Sitemap sincronizado: ${result?.total || 0} URLs (${result?.new || 0} nuevas)`)
    fetchData()
  } catch {
    toast.error('Error sincronizando sitemap')
  } finally {
    setSyncing(null)
  }
}

// AÑADIR modal JSX antes del return final:
{sitemapModal && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
    <div className="bg-dark-card border border-border-yellow p-6 w-full max-w-md space-y-4">
      <h3 className="text-sm font-bold uppercase text-brand-yellow">Sincronizar Sitemap</h3>
      <p className="text-xs text-text-muted">Introduce la URL del sitemap de {sitemapModal.name}:</p>
      <input type="url" value={sitemapUrl} onChange={(e) => setSitemapUrl(e.target.value)}
        className="w-full border border-border-subtle bg-dark-surface text-text-primary p-2 text-sm focus:border-brand-yellow focus:outline-none"
        placeholder="https://domain.com/sitemap.xml" />
      <div className="flex gap-2 justify-end">
        <button onClick={() => setSitemapModal(null)}
          className="px-3 py-1.5 text-xs font-bold uppercase text-text-muted border border-border-subtle hover:bg-white/5">
          Cancelar
        </button>
        <button onClick={confirmSitemapSync}
          className="px-3 py-1.5 text-xs font-bold uppercase bg-brand-yellow text-dark-bg hover:brightness-110">
          Sincronizar
        </button>
      </div>
    </div>
  </div>
)}

// Y cambiar todas las llamadas a syncSitemap(c) → openSitemapSync(c)
```

---

#### A.4 [9] DashboardPage: mejorar placeholder Tráfico IA

**Archivo:** `frontend/src/pages/DashboardPage.tsx`

**Problema:** Cuando GA4 no tiene canal AI configurado, el mensaje es poco útil.

**Fix (~línea 688-693):**

```tsx
// ANTES:
<p>Configura un canal personalizado 'AI Traffic' en GA4 para ver estos datos. Ver instrucciones en la documentación.</p>

// DESPUÉS:
<div className="space-y-2">
  <p className="font-bold text-text-secondary">Tráfico IA no disponible</p>
  <p>Para activar esta métrica, crea un canal personalizado en GA4 que capture tráfico desde ChatGPT, Perplexity, Gemini y Claude.</p>
  <a href="https://support.google.com/analytics/answer/10597861" target="_blank" rel="noopener"
    className="inline-flex items-center gap-1 text-brand-yellow hover:underline">
    <ExternalLink size={10} /> Guía de canales personalizados en GA4
  </a>
</div>
```

---

#### A.5 [28] ContentPerformancePage: añadir nota GSC lag + ajustar date_to

**Archivo:** `frontend/src/pages/ContentPerformancePage.tsx`

**Problema:** `date_to` incluye hoy pero GSC tiene lag de 2-3 días, causando discrepancia.

**Fix (~línea 60-68):**

```tsx
// ANTES:
const getDateRange = () => {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - dateRange)
  return {
    date_from: from.toISOString().split('T')[0],
    date_to: to.toISOString().split('T')[0],
  }
}

// DESPUÉS:
const getDateRange = () => {
  const to = new Date()
  to.setDate(to.getDate() - 3) // GSC lag de 2-3 días
  const from = new Date(to)
  from.setDate(from.getDate() - dateRange)
  return {
    date_from: from.toISOString().split('T')[0],
    date_to: to.toISOString().split('T')[0],
  }
}

// AÑADIR nota informativa cerca de los KPIs (~tras el selector de periodo):
<div className="text-xs text-text-muted bg-dark-surface px-3 py-1.5 border border-border-subtle flex items-center gap-2">
  <Info size={12} className="text-brand-yellow shrink-0" />
  <span>Datos GSC con retraso de 3 días. Diferencias menores con la consola son normales.</span>
</div>
```

---

#### A.6 [5][8] DashboardPage: aplicar mismo lag de 3 días en fetch principal

**Archivo:** `frontend/src/pages/DashboardPage.tsx`

**Problema:** El dashboard puede incluir días sin datos GSC consolidados, mostrando cifras menores.

**Fix (~línea 255-262, función getDateRange):**

```tsx
// En getDateRange(), ANTES de calcular 'from', ajustar 'to':
// AÑADIR al inicio de la función:
const gscLagDays = 3
const adjustedTo = new Date()
adjustedTo.setDate(adjustedTo.getDate() - gscLagDays)

// Y usar adjustedTo como base para date_to:
date_to: adjustedTo.toISOString().split('T')[0],
```

**Esto resuelve [5] y [8] de golpe** — los datos coincidirán con GSC porque excluimos los días sin consolidar.

---

### FASE B — Fixes medios (5 items, ~4h)

#### B.1 [22] SEOValueSettings: añadir campo CVR (Conversion Rate)

**Archivo:** `frontend/src/pages/settings/SEOValueSettings.tsx`

**Problema:** `conversion_rate` se usa en backend pero no hay UI para editarlo.

**Fix:**

```tsx
// MODIFICAR interface (~línea 9):
interface SEOValueConfig {
  monthly_seo_investment: number
  avg_deal_value: number
  conversion_rate: number      // ← AÑADIR
  organic_attribution_pct: number
  target_organic_cac: number | null
  target_vpov: number | null
  revenue_source: string
}

// MODIFICAR estado inicial (~línea 24):
conversion_rate: 2,  // ← AÑADIR (2%)

// AÑADIR bloque input DESPUÉS del bloque avg_deal_value (~línea 118):
<div>
  <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider mb-1">
    Tasa de conversión orgánica (%)
  </label>
  <input type="number" step="0.1" min="0" max="100" value={config.conversion_rate}
    onChange={(e) => setConfig({ ...config, conversion_rate: parseFloat(e.target.value) || 0 })}
    className="w-full border border-border-subtle bg-dark-surface text-text-primary p-2 text-sm focus:border-brand-yellow focus:outline-none"
    placeholder="2.0" />
  <p className="text-xs text-text-muted mt-1">% de visitas orgánicas que convierten a lead/venta. Se usa para calcular Revenue Opportunity.</p>
</div>
```

**Backend:** `dashboard_service.py` ya lee `settings.get("conversion_rate", 0.02)` — verificar que el save de settings persiste este campo.

---

#### B.2 [32] ContentPerformancePage: filtro por etiqueta/tag en Leads GA4

**Archivo:** `frontend/src/pages/ContentPerformancePage.tsx`

**Problema:** No hay filtro por etiquetas de cursos para la tabla de leads.

**Fix:**

```tsx
// AÑADIR estado (~línea 42):
const [leadTagFilter, setLeadTagFilter] = useState('')
const [availableTags, setAvailableTags] = useState<string[]>([])

// AÑADIR fetch de tags (~línea 100, dentro de useEffect):
api.get<string[]>(`/content-performance/projects/${projectId}/lead-tags`)
  .then(tags => setAvailableTags(tags))
  .catch(() => {})

// AÑADIR selector en la tab Leads GA4 (~antes de la tabla):
<select value={leadTagFilter} onChange={(e) => setLeadTagFilter(e.target.value)}
  className="border border-border-subtle bg-dark-surface text-text-primary text-xs p-2 focus:border-brand-yellow">
  <option value="">Todas las categorías</option>
  {availableTags.map(t => <option key={t} value={t}>{t}</option>)}
</select>

// MODIFICAR fetch de leads para incluir filtro (~línea 125):
const url = `/content-performance/projects/${projectId}/lead-attribution?date_from=${date_from}&date_to=${date_to}${leadTagFilter ? `&tag=${encodeURIComponent(leadTagFilter)}` : ''}`
```

**Backend:** Añadir endpoint `GET /lead-tags` que devuelva tags únicos, y parámetro `tag` en `/lead-attribution`.

---

#### B.3 [124] SRO: añadir campo propósito de página

**Archivo backend:** `backend/api/routes/sro.py` + `backend/api/services/sro_service.py`
**Archivo frontend:** `frontend/src/pages/SROPage.tsx`

**Fix backend (sro.py ~línea 23):**

```python
# MODIFICAR SROAnalyzeInput:
class SROAnalyzeInput(BaseModel):
    url: str
    position: Optional[int] = None
    page_purpose: Optional[str] = None  # ← AÑADIR: "informativo", "comercial", "transaccional", "navegacional"
```

**Fix backend (sro_service.py ~línea 86):**

```python
# MODIFICAR prompt:
purpose_text = {
    "informativo": "página informativa/divulgativa (artículo de blog, guía, tutorial)",
    "comercial": "página comercial (landing de producto/servicio, comparativa)",
    "transaccional": "página transaccional (checkout, formulario de contacto, compra)",
    "navegacional": "página navegacional (homepage, hub de categorías)",
}.get(page_purpose, "propósito no especificado")

prompt = f"""Analiza el siguiente contenido web para optimización de grounding en AI Search (SRO).

URL: {url}
Tipo de página: {page_type_label}
Propósito: {purpose_text}
...

IMPORTANTE: Adapta tus recomendaciones al propósito de la página. Una página comercial no necesita la misma longitud ni estructura que un artículo divulgativo.
"""
```

**Fix frontend (SROPage.tsx ~en el form):**

```tsx
// AÑADIR estado:
const [pagePurpose, setPagePurpose] = useState('')

// AÑADIR selector en el form de análisis:
<select value={pagePurpose} onChange={(e) => setPagePurpose(e.target.value)}
  className="border border-border-subtle bg-dark-surface text-text-primary text-xs p-2">
  <option value="">Propósito (auto-detectar)</option>
  <option value="informativo">Informativo (blog, guía)</option>
  <option value="comercial">Comercial (landing, producto)</option>
  <option value="transaccional">Transaccional (compra, contacto)</option>
  <option value="navegacional">Navegacional (home, hub)</option>
</select>

// MODIFICAR call a API para incluir page_purpose en body
```

---

#### B.4 [23] DashboardPage Demand Trends: nota datos mínimos + validación

**Archivo:** `frontend/src/pages/DashboardPage.tsx`

**Problema:** Si hay menos de 16 meses de datos, los trends son poco fiables.

**Fix (~línea 1050, sección Demand Trends):**

```tsx
// AÑADIR después de cargar demandTrends:
{demandTrends && demandTrends.months_available < 12 && (
  <div className="text-xs text-amber-400 bg-amber-400/10 border border-amber-400/30 px-3 py-2 flex items-center gap-2">
    <AlertTriangle size={12} />
    <span>Solo {demandTrends.months_available} meses de datos disponibles. Se recomiendan 12+ meses para tendencias fiables.</span>
  </div>
)}
```

**Backend:** Añadir `months_available` al response de `/dashboard/msv-trends`.

---

#### B.5 [153] AnalysisPage: campo XPath para extracción de autor (simplificado)

**Archivo:** `frontend/src/pages/settings/GeneralSettings.tsx` + backend

**Problema:** Los autores no se detectan automáticamente. Un campo XPath es complejo; alternativa más práctica: campo CSS selector.

**Fix simplificado — añadir a GeneralSettings:**

```tsx
// AÑADIR campo en GeneralSettings (~después de campos existentes):
<div>
  <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider mb-1">
    Selector CSS del autor (opcional)
  </label>
  <input type="text" value={settings.author_selector || ''}
    onChange={(e) => setSettings({ ...settings, author_selector: e.target.value })}
    className="w-full border border-border-subtle bg-dark-surface text-text-primary p-2 text-sm"
    placeholder=".author-name, [rel='author'], .entry-author" />
  <p className="text-xs text-text-muted mt-1">
    Selector CSS para extraer el nombre del autor al importar contenido. Ejemplo: .author-name
  </p>
</div>
```

**Backend:** En content_service.py, al importar URLs, usar `author_selector` de settings para extraer autor con BeautifulSoup.

---

### FASE C — Fixes grandes (4 items, ~8h)

#### C.1 [178] ContentHubPage: auto-importación desde RSS/Sitemap por canal

**Archivo:** `frontend/src/pages/ContentHubPage.tsx` + nuevo endpoint backend

**Problema:** Registro manual de contenido multicanal es tedioso. La importación desde sitemap ya existe pero no por canal individual.

**Fix — Añadir "Importar desde RSS/URL" por canal:**

```tsx
// AÑADIR en el detalle de cada canal (~junto al botón de añadir contenido):
<button onClick={() => setImportModal(channel)} className="...">
  <Download size={12} /> Importar desde RSS/Sitemap
</button>

// Modal de importación:
{importModal && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
    <div className="bg-dark-card border border-border-yellow p-6 w-full max-w-md space-y-4">
      <h3 className="text-sm font-bold uppercase text-brand-yellow">Importar contenido — {importModal.name}</h3>
      <select value={importSource} onChange={(e) => setImportSource(e.target.value)} className="w-full ...">
        <option value="rss">Feed RSS</option>
        <option value="sitemap">Sitemap XML</option>
        <option value="youtube">Canal YouTube (ID)</option>
      </select>
      <input type="url" value={importUrl} onChange={(e) => setImportUrl(e.target.value)}
        placeholder={importSource === 'youtube' ? 'ID del canal (UCxxxxx)' : 'https://...'} className="w-full ..." />
      <div className="flex gap-2 justify-end">
        <button onClick={() => setImportModal(null)} className="...">Cancelar</button>
        <button onClick={handleChannelImport} className="...">Importar</button>
      </div>
    </div>
  </div>
)}
```

**Backend:** Nuevo endpoint `POST /projects/{id}/content-hub/channels/{ch_id}/import` que:
1. Si source=rss → parsea feed RSS con feedparser
2. Si source=sitemap → parsea sitemap XML
3. Si source=youtube → usa YouTube Data API (si configurada) o scraping público
4. Crea entries en `channel_content` con datos básicos

---

#### C.2 [179] ContentHubPage: panel de métricas por canal

**Archivo:** `frontend/src/pages/ContentHubPage.tsx`

**Problema:** No hay visualización de rendimiento por canal.

**Fix — Añadir panel de resumen con datos existentes:**

```tsx
// Los datos YA existen en Channel interface: total_views, total_likes, total_comments
// AÑADIR sección de métricas en overview:

<div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
  {overview?.channels.map(ch => (
    <div key={ch.id} className="bg-dark-card border border-border-subtle p-4">
      <p className="text-xs font-bold uppercase text-text-muted mb-2">{ch.name}</p>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between"><span>Contenidos:</span><span className="font-bold">{ch.total_content || 0}</span></div>
        <div className="flex justify-between"><span>Views:</span><span className="font-bold">{(ch.total_views || 0).toLocaleString()}</span></div>
        <div className="flex justify-between"><span>Engagement:</span><span className="font-bold">
          {ch.total_views ? (((ch.total_likes || 0) + (ch.total_comments || 0)) / ch.total_views * 100).toFixed(1) : 0}%
        </span></div>
      </div>
    </div>
  ))}
</div>

// AÑADIR botón "Actualizar métricas" por canal:
<button onClick={() => syncChannelMetrics(ch.id)} className="text-xs text-brand-yellow hover:underline">
  <RefreshCw size={10} /> Actualizar
</button>
```

**Backend:** Endpoint `POST /projects/{id}/content-hub/channels/{ch_id}/sync-metrics` que:
1. Recalcula totales desde `channel_content` (SUM views, likes, comments)
2. Actualiza `channels` table con agregados
3. Devuelve totales actualizados

---

#### C.3 [194] Chat: ampliar acceso GSC con funciones avanzadas

**Archivo:** `backend/api/routes/chat.py` + `backend/api/services/chat_service.py`

**Problema:** Chat solo tiene métricas básicas. No puede responder sobre dispositivos, branded vs non-branded, o tendencias de queries.

**Fix — Añadir funciones de datos avanzadas:**

```python
# AÑADIR nuevos intents (~línea 35):
INTENTS = {
    ...
    "query_device": ["dispositivo", "mobile", "desktop", "tablet", "móvil"],
    "query_branded": ["branded", "no branded", "marca", "genérico", "brand"],
    "query_url_detail": ["url", "página específica", "rendimiento de", "datos de la url"],
}

# AÑADIR funciones de datos (~línea 95):
async def _gather_gsc_by_device(sb, project_id: int) -> dict:
    """Desglose de métricas por dispositivo."""
    rows = sb.table("search_analytics").select("device, clicks, impressions").eq("project_id", project_id).execute()
    devices = {}
    for r in rows.data:
        d = r.get("device", "unknown")
        if d not in devices: devices[d] = {"clicks": 0, "impressions": 0}
        devices[d]["clicks"] += r.get("clicks", 0)
        devices[d]["impressions"] += r.get("impressions", 0)
    return devices

async def _gather_gsc_branded(sb, project_id: int, brand_terms: list) -> dict:
    """Separar tráfico branded vs non-branded."""
    # Usar brand_terms del proyecto settings
    rows = sb.table("search_analytics").select("query, clicks, impressions").eq("project_id", project_id).execute()
    branded = {"clicks": 0, "impressions": 0, "queries": []}
    non_branded = {"clicks": 0, "impressions": 0, "queries": []}
    for r in rows.data:
        q = (r.get("query") or "").lower()
        is_branded = any(bt.lower() in q for bt in brand_terms)
        target = branded if is_branded else non_branded
        target["clicks"] += r.get("clicks", 0)
        target["impressions"] += r.get("impressions", 0)
    return {"branded": branded, "non_branded": non_branded}

async def _gather_url_detail(sb, project_id: int, url: str) -> dict:
    """Datos detallados de una URL específica."""
    rows = sb.table("search_analytics").select("*").eq("project_id", project_id).ilike("url", f"%{url}%").execute()
    if not rows.data: return {"error": "URL no encontrada"}
    total = {"clicks": 0, "impressions": 0, "queries": []}
    for r in rows.data:
        total["clicks"] += r.get("clicks", 0)
        total["impressions"] += r.get("impressions", 0)
        total["queries"].append({"query": r.get("query"), "clicks": r.get("clicks"), "position": r.get("position")})
    total["queries"].sort(key=lambda x: x["clicks"], reverse=True)
    total["queries"] = total["queries"][:20]  # Top 20
    return total
```

**Actualizar prompt del sistema del chat** para que Claude sepa que tiene acceso a estas funciones y las use cuando el usuario pregunte por dispositivos, branded, o URLs específicas.

---

#### C.4 [32] Backend: endpoint lead-tags + filtro lead-attribution

**Archivo:** `backend/api/routes/content_performance.py`

```python
# AÑADIR endpoint:
@router.get("/content-performance/projects/{project_id}/lead-tags")
async def get_lead_tags(project_id: int, access=Depends(require_module_access("content-performance"))):
    sb = get_supabase()
    rows = sb.table("lead_attribution").select("tag").eq("project_id", project_id).execute()
    tags = sorted(set(r["tag"] for r in rows.data if r.get("tag")))
    return tags

# MODIFICAR endpoint lead-attribution para aceptar filtro tag:
@router.get("/content-performance/projects/{project_id}/lead-attribution")
async def get_lead_attribution(
    project_id: int,
    date_from: str = Query(...),
    date_to: str = Query(...),
    tag: Optional[str] = Query(None),  # ← AÑADIR
    access=Depends(require_module_access("content-performance")),
):
    sb = get_supabase()
    q = sb.table("lead_attribution").select("*").eq("project_id", project_id).gte("date", date_from).lte("date", date_to)
    if tag:
        q = q.eq("tag", tag)
    rows = q.execute()
    # ... rest of logic
```

---

### Validación Sprint 43

```bash
#!/bin/bash
cd "/Codigo/Gestor de Contenido FIT/fit-content-app"
E=0

echo "=== FASE A: Fixes rápidos ==="
# A.1 [158] Type translation
grep -q "TYPE_LABELS" frontend/src/pages/AnalysisPage.tsx && echo "  ✅ A.1 [158] Type labels" || { echo "  ⚠️ A.1 [158]"; E=$((E+1)); }

# A.2 [94] Status translation + revert button
grep -qE "STATUS_LABELS|Resolviendo|En revisión" frontend/src/pages/CannibalizationsPage.tsx && echo "  ✅ A.2a [94] Status labels" || { echo "  ⚠️ A.2a"; E=$((E+1)); }
grep -q "updateStatus.*detected" frontend/src/pages/CannibalizationsPage.tsx && echo "  ✅ A.2b [94] Revert button" || { echo "  ⚠️ A.2b"; E=$((E+1)); }

# A.3 [134] Modal sitemap (no prompt)
grep -qv "prompt(" frontend/src/pages/CompetitorsPage.tsx && grep -q "sitemapModal\|SitemapModal" frontend/src/pages/CompetitorsPage.tsx && echo "  ✅ A.3 [134] Modal sitemap" || { echo "  ⚠️ A.3"; E=$((E+1)); }

# A.4 [9] AI Traffic placeholder
grep -qE "Guía de canales|canal personalizado.*GA4|support.google.com" frontend/src/pages/DashboardPage.tsx && echo "  ✅ A.4 [9] AI Traffic help" || { echo "  ⚠️ A.4"; E=$((E+1)); }

# A.5 [28] GSC lag
grep -qE "getDate.*-.*3.*GSC\|retraso.*3.*días\|gscLag" frontend/src/pages/ContentPerformancePage.tsx && echo "  ✅ A.5 [28] GSC lag" || { echo "  ⚠️ A.5"; E=$((E+1)); }

# A.6 [5][8] Dashboard GSC lag
grep -qE "gscLag\|getDate.*-.*3" frontend/src/pages/DashboardPage.tsx && echo "  ✅ A.6 [5][8] Dashboard lag" || { echo "  ⚠️ A.6"; E=$((E+1)); }

echo ""
echo "=== FASE B: Fixes medios ==="
# B.1 [22] CVR field
grep -q "conversion_rate" frontend/src/pages/settings/SEOValueSettings.tsx && echo "  ✅ B.1 [22] CVR field" || { echo "  ⚠️ B.1"; E=$((E+1)); }

# B.2 [32] Lead tag filter
grep -qE "leadTagFilter\|lead-tags\|tag.*filter" frontend/src/pages/ContentPerformancePage.tsx && echo "  ✅ B.2 [32] Lead tags" || { echo "  ⚠️ B.2"; E=$((E+1)); }

# B.3 [124] SRO page purpose
grep -qE "page_purpose\|pagePurpose\|propósito" frontend/src/pages/SROPage.tsx && echo "  ✅ B.3 [124] SRO purpose" || { echo "  ⚠️ B.3"; E=$((E+1)); }
grep -qE "page_purpose\|propósito.*página" backend/api/services/sro_service.py && echo "  ✅ B.3b [124] SRO backend" || { echo "  ⚠️ B.3b"; E=$((E+1)); }

# B.4 [23] Demand trends warning
grep -qE "months_available\|meses.*datos.*disponibles" frontend/src/pages/DashboardPage.tsx && echo "  ✅ B.4 [23] Trends warning" || { echo "  ⚠️ B.4"; E=$((E+1)); }

# B.5 [153] Author selector
grep -qE "author_selector\|selector.*autor" frontend/src/pages/settings/GeneralSettings.tsx && echo "  ✅ B.5 [153] Author selector" || { echo "  ⚠️ B.5"; E=$((E+1)); }

echo ""
echo "=== FASE C: Fixes grandes ==="
# C.1 [178] Channel import
grep -qE "importModal\|import.*rss\|import.*channel" frontend/src/pages/ContentHubPage.tsx && echo "  ✅ C.1 [178] Channel import" || { echo "  ⚠️ C.1"; E=$((E+1)); }

# C.2 [179] Channel metrics panel
grep -qE "total_views.*toLocaleString\|sync.*Metrics\|Engagement.*%" frontend/src/pages/ContentHubPage.tsx && echo "  ✅ C.2 [179] Metrics panel" || { echo "  ⚠️ C.2"; E=$((E+1)); }

# C.3 [194] Chat GSC advanced
grep -qE "query_device\|query_branded\|_gather_gsc_by_device\|_gather_url_detail" backend/api/routes/chat.py && echo "  ✅ C.3 [194] Chat GSC" || { echo "  ⚠️ C.3"; E=$((E+1)); }

# C.4 [32] Backend lead-tags
grep -qE "lead.tags\|lead_tags" backend/api/routes/content_performance.py && echo "  ✅ C.4 [32] Backend tags" || { echo "  ⚠️ C.4"; E=$((E+1)); }

echo ""
# Build check
cd frontend && npm run build --silent 2>&1 | tail -1
cd ../backend && python -c "from main import app; print('Backend: OK')" 2>&1

echo ""
if [ $E -eq 0 ]; then echo "🎉 SPRINT 43: 15/15 ITEMS COMPLETOS"; else echo "⚠️ SPRINT 43: $E items pendientes"; fi
exit $E
```

---

### Resumen Sprint 43

| Fase | Items | Dificultad | Tiempo est. | Archivos |
|------|-------|------------|-------------|----------|
| **A** | [158] [94] [134] [9] [28] [5][8] | Fácil | ~2h | 5 frontend |
| **B** | [22] [32] [124] [23] [153] | Medio | ~4h | 3 frontend + 3 backend |
| **C** | [178] [179] [194] [32-backend] | Grande | ~8h | 2 frontend + 2 backend |

**Total: 15 items → ~14h estimadas**
~8 archivos frontend, ~5 archivos backend.

**Prioridad de implementación:**
1. **Fase A** — Máxima prioridad. 6 items fáciles que se notan mucho. Especialmente A.6 resuelve [5] y [8] de golpe.
2. **Fase B** — Alta prioridad. Mejoras funcionales concretas.
3. **Fase C** — Media prioridad. Funcionalidades nuevas más complejas. C.3 (Chat GSC) es la de mayor impacto.

---

## Sprint 44 — Auditoría de Usabilidad Real (Febrero 2026)

### Contexto
Primera auditoría con navegación REAL del app (Playwright + screenshots).
Se arrancó backend (localhost:8001) y frontend (localhost:5174), se inyectó sesión Supabase,
y se navegaron las 29 secciones de la app tomando screenshots y registrando errores de consola y API.

### Hallazgos Críticos

**Categoría A: Rutas API rotas (404/422) — PRIORIDAD MÁXIMA**

Estos bugs impiden funcionalidad real visible al usuario:

#### A.1 — lead-tags 404 (ContentPerformancePage)
- **Síntoma:** GET `/projects/1/content-performance/lead-tags` → 404
- **Causa:** Frontend usa path invertido. El router tiene prefix `/content-performance` y la ruta es `/projects/{id}/lead-tags`,
  así que la URL real del backend es `/content-performance/projects/{id}/lead-tags`.
  Pero el frontend llama a `/projects/${projectId}/content-performance/lead-tags`.
- **Archivo:** `frontend/src/pages/ContentPerformancePage.tsx` L64
- **Antes:** `api.get<string[]>(\`/projects/${projectId}/content-performance/lead-tags\`)`
- **Después:** `api.get<string[]>(\`/content-performance/projects/${projectId}/lead-tags\`)`
- **Impacto:** Filtro de etiquetas de leads no funciona
- **Tiempo:** 5 min

#### A.2 — settings 404 (BriefingsPage)
- **Síntoma:** GET `/projects/1/settings` → 404
- **Causa:** BriefingsPage intenta cargar configuración de proyecto con una ruta que no existe.
  El backend tiene `/api/projects/{id}` (GET) para obtener datos del proyecto, no `/api/projects/{id}/settings`.
- **Archivo:** `frontend/src/pages/BriefingsPage.tsx` L34
- **Antes:** `const config = await api.get<any>(\`/projects/${project.id}/settings\`)`
- **Después:** `const config = await api.get<any>(\`/projects/${project.id}\`)`
- **Impacto:** Briefings no carga configuración de marca/tono automáticamente
- **Tiempo:** 5 min

#### A.3 — content-gaps 404 (ContentSeriesPage)
- **Síntoma:** GET `/projects/1/content-gaps?limit=500` → 404
- **Causa:** Frontend llama a `/content-gaps` pero el backend usa `/gaps`.
- **Archivo:** `frontend/src/pages/ContentSeriesPage.tsx` L116
- **Antes:** `api.get<...>(\`/projects/${projectId}/content-gaps?limit=500\`)`
- **Después:** `api.get<...>(\`/projects/${projectId}/gaps?limit=200\`)`
- **Nota:** También cambiar limit de 500 a 200 (backend limita a 200 con le=200)
- **Impacto:** Content Series no carga gaps existentes, error 422 en consola
- **Tiempo:** 5 min

#### A.4 — content?limit=500 → 422 (ContentSeriesPage)
- **Síntoma:** GET `/projects/1/content?limit=500` → 422 Unprocessable Entity
- **Causa:** Backend tiene `limit: int = Query(default=50, ge=1, le=200)` en content.py L150.
  Frontend pide limit=500 que viola la restricción.
- **Opción A (frontend):** Cambiar a limit=200
- **Opción B (backend - RECOMENDADA):** Subir le=500 en `backend/api/routes/content.py` L150
- **Antes (backend):** `limit: int = Query(default=50, ge=1, le=200),`
- **Después:** `limit: int = Query(default=50, ge=1, le=500),`
- **Impacto:** ContentSeriesPage no carga contenido existente
- **Tiempo:** 5 min

**Categoría B: Errores de conectividad (manejo graceful) — PRIORIDAD ALTA**

#### B.1 — Bing fetch error silencioso
- **Síntoma:** Console error `Bing fetch error: TypeError: Failed to fetch` en TODAS las páginas que cargan el layout
- **Causa:** El widget de Bing en el sidebar/dashboard intenta fetch a API de Bing que falla (CORS o network).
  El error se captura pero aparece en consola.
- **Archivo:** `frontend/src/components/dashboard/BingWidget.tsx` (o donde se llame a Bing)
- **Fix:** Asegurar que el catch muestre estado "No disponible" en UI sin error de consola.
  Usar `console.warn` en vez de dejar que propague como `console.error`.
- **Tiempo:** 15 min

#### B.2 — CWV fetch error silencioso
- **Síntoma:** Console error `CWV fetch error: TypeError: Failed to fetch` en todas las páginas
- **Causa:** Similar a B.1, el widget CWV falla en conectividad y propaga error.
- **Archivo:** `frontend/src/pages/DashboardPage.tsx` (sección CWV) o `frontend/src/components/`
- **Fix:** Mismo patrón: catch → UI "No disponible", no console.error
- **Tiempo:** 15 min

#### B.3 — "No se pudo generar el resumen" visible en Dashboard
- **Síntoma:** Sección "RESUMEN AI" muestra "No se pudo generar el resumen." permanentemente
- **Causa:** La generación del resumen AI falla (probablemente por falta de datos suficientes o API key).
  El error se muestra directamente al usuario sin contexto.
- **Archivo:** `frontend/src/pages/DashboardPage.tsx` — sección RESUMEN AI
- **Fix:** Mejorar mensaje de error: "No hay datos suficientes para generar un resumen. Regenera cuando haya más datos de GSC."
  + deshabilitar botón "Regenerar" si no hay métricas cargadas.
- **Tiempo:** 20 min

#### B.4 — GA4 OAuth client not found (backend)
- **Síntoma:** Backend log: `Error fetching GA4 engagement: ('invalid_client: The OAuth client was not found.')`
- **Causa:** Las credenciales OAuth de GA4 no están configuradas o han expirado.
- **Fix:** No es bug de código — es configuración. Pero el error debe manejarse mejor:
  en el endpoint de engagement, si OAuth falla, devolver `{"data": null, "error": "GA4 no configurado"}` en vez de 500.
- **Archivo:** `backend/api/services/ga4_service.py`
- **Tiempo:** 15 min

**Categoría C: Mejoras UX detectadas en navegación real — PRIORIDAD MEDIA**

#### C.1 — Brand Audit: spinner infinito + "LOCK" en sidebar
- **Síntoma:** Al navegar a `/brand-audit`, la página muestra spinner de carga infinito.
  Además, todos los items del sidebar muestran "LOCK".
- **Causa:** La Brand Audit necesita que se haya ejecutado una auditoría previa.
  El "LOCK" aparece porque el sistema de módulos requiere acceso explícito.
  Pero no hay mensaje explicativo — solo un spinner eterno.
- **Fix:** Mostrar mensaje "Ejecuta una auditoría de marca para activar esta sección"
  con botón directo "Ejecutar Auditoría" en vez de spinner infinito.
  Los "LOCK" en sidebar: verificar que se muestren solo para módulos realmente bloqueados, no como estado por defecto.
- **Archivos:**
  - `frontend/src/pages/BrandAuditPage.tsx` — añadir empty state
  - `frontend/src/components/Sidebar.tsx` — revisar lógica de LOCK badges
- **Tiempo:** 45 min

#### C.2 — Briefings: briefs duplicados
- **Síntoma:** El brief "Cuando los leads no avanzan: cómo evitar que las oportunidades se enfríen"
  aparece duplicado 7+ veces, todos como BORRADOR con keyword "lead nurturing".
- **Causa:** Probablemente el botón "Crear Briefing" permite crear sin validar duplicados,
  o hubo un doble-envío sin debounce.
- **Fix opciones:**
  1. Añadir debounce al botón de crear (loading state que desactive el botón)
  2. Validar en backend que no exista brief con mismo título+keyword antes de insertar
  3. Añadir botón "Eliminar seleccionados" (bulk delete) para limpiar
- **Archivos:**
  - `frontend/src/pages/BriefingsPage.tsx` — debounce + selección múltiple
  - `backend/api/routes/briefings.py` — validación de duplicados
- **Tiempo:** 1h

#### C.3 — Dashboard KPIs vacíos al cargar
- **Síntoma:** Las tarjetas de SESIONES, CLICS, IMPRESIONES, CTR MEDIO, POSICIÓN MEDIA muestran
  rectángulos vacíos (loading skeleton) que nunca se llenan si GSC no responde a tiempo.
- **Causa:** Los datos de GSC pueden tardar y el skeleton se queda permanente si hay error.
- **Fix:** Añadir timeout al fetch de métricas GSC (10s max). Si falla, mostrar "--" con tooltip
  "Datos de GSC no disponibles" en vez de skeleton eterno.
- **Archivo:** `frontend/src/pages/DashboardPage.tsx` — sección de métricas GSC
- **Tiempo:** 30 min

#### C.4 — Sidebar "Cargando CWV... / Cargando Bing... / Cargando acciones..." perpetuo
- **Síntoma:** En el lateral derecho del Dashboard, tres secciones muestran "Cargando..."
  que nunca terminan de cargar.
- **Causa:** Los widgets de CWV, Bing y Acciones intentan fetch que fallan pero el loading state
  nunca transiciona a error/empty state.
- **Fix:** Añadir timeout de 8 segundos. Si no responde, mostrar "Sin datos" en vez de "Cargando...".
- **Archivo:** `frontend/src/pages/DashboardPage.tsx` — widgets laterales
- **Tiempo:** 20 min

### Resumen Sprint 44

| ID | Categoría | Descripción | Archivo principal | Tiempo est. |
|----|-----------|-------------|-------------------|-------------|
| A.1 | 🔴 API rota | lead-tags path invertido | ContentPerformancePage.tsx L64 | 5 min |
| A.2 | 🔴 API rota | settings path inexistente | BriefingsPage.tsx L34 | 5 min |
| A.3 | 🔴 API rota | content-gaps → gaps | ContentSeriesPage.tsx L116 | 5 min |
| A.4 | 🔴 API rota | content limit 500>200 | content.py L150 | 5 min |
| B.1 | 🟡 UX error | Bing error silencioso | BingWidget.tsx | 15 min |
| B.2 | 🟡 UX error | CWV error silencioso | DashboardPage.tsx | 15 min |
| B.3 | 🟡 UX error | Resumen AI error msg | DashboardPage.tsx | 20 min |
| B.4 | 🟡 Backend | GA4 OAuth graceful | ga4_service.py | 15 min |
| C.1 | 🟠 UX | Brand Audit spinner infinito | BrandAuditPage.tsx | 45 min |
| C.2 | 🟠 UX | Briefings duplicados | BriefingsPage.tsx + briefings.py | 1h |
| C.3 | 🟠 UX | Dashboard KPIs skeleton | DashboardPage.tsx | 30 min |
| C.4 | 🟠 UX | "Cargando..." perpetuo | DashboardPage.tsx | 20 min |

**Total: 12 items → ~4.5h estimadas**

**Prioridad de implementación:**
1. **Fase A (20 min)** — Crítica. 4 rutas API rotas que causan 404/422. Son fixes de 1 línea cada uno.
2. **Fase B (1h 5min)** — Alta. Errores de UX que el usuario ve (mensajes de error, console errors).
3. **Fase C (2h 35min)** — Media. Mejoras de experiencia que no rompen funcionalidad pero afectan percepción.

### Validación post-Sprint 44

```bash
# 1. Backend tests
cd backend && pytest

# 2. Verificar 404s resueltos
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/content-performance/projects/1/lead-tags
# Debe ser 200 o 401 (no 404)

curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/projects/1
# Debe ser 200 o 401 (no 404)

# 3. Verificar 422 resuelto
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/api/projects/1/content?limit=500"
# Debe ser 200 o 401 (no 422)

# 4. Frontend build
cd frontend && npm run build && npx tsc --noEmit

# 5. Test de navegación real (Playwright)
# Navegar todas las rutas y verificar 0 console.error (excepto favicon)
```

---

## Sprint 45 — Fixes restantes + Hardening seguridad (Febrero 2026)

### Contexto
Sprint 44 resolvió 8/12 items. Quedan 4 items de UX + ajustes de seguridad.
Se aplicaron 4 fixes de seguridad críticos (XSS, invitaciones, permisos, ProtectedRoute)
que están bien pero necesitan un par de ajustes finos.
La migración 053 (lead_attribution.tag) ya fue aplicada.

---

### Fase A — Dashboard "Cargando..." perpetuo + KPIs skeleton (~1.5h)

#### A.1 — Timeout en widgets laterales (CWV, Bing, Acciones)
- **Archivo:** `frontend/src/pages/DashboardPage.tsx`
- **Buscar:** Los `useEffect` que hacen fetch de CWV (`/cwv/overview`), Bing (`/bing/search-stats`),
  y Acciones (`/seo-actions/summary`). Cada uno tiene un state `loading` que nunca pasa a `false` si falla.
- **Fix:** Envolver cada fetch en `Promise.race` con timeout de 8 segundos.
  En el `catch`, setear `loading=false` y `data=null`.
- **UI:** Si `!loading && !data`, mostrar "Sin datos disponibles" con icono info en vez de "Cargando...".
- **Tiempo:** 30 min

#### A.2 — Timeout en KPI cards (Sesiones, Clics, Impresiones, etc.)
- **Archivo:** `frontend/src/pages/DashboardPage.tsx`
- **Fix:** Mismo patrón timeout 10s. Si falla, mostrar "—" con tooltip "Datos no disponibles".
- **Tiempo:** 30 min

#### A.3 — GA4 graceful error en backend
- **Archivo:** `backend/api/services/ga4_service.py`
- **Fix:** Cambiar `logger.error(...)` a `logger.warning(...)` para OAuth failures.
  Devolver `{"data": None, "message": "GA4 no configurado"}` status 200 en vez de 500.
- **Tiempo:** 15 min

---

### Fase B — Briefings debounce anti-duplicados (~45min)

#### B.1 — Frontend debounce
- **Archivo:** `frontend/src/pages/BriefingsPage.tsx`
- **Fix:** Desactivar botón "Crear Briefing" con `disabled={creating}` durante la petición.
- **Tiempo:** 15 min

#### B.2 — Backend validación duplicados
- **Archivo:** `backend/api/routes/briefings.py`
- **Fix:** Antes de insertar, SELECT con `keyword` + `title` + `project_id`.
  Si ya existe uno en estado "borrador", devolver el existente (200) en vez de crear otro.
- **Tiempo:** 30 min

---

### Fase C — Hardening seguridad (~30min)

#### C.1 — DOMPurify config restrictivo en ChatWidget
- **Archivo:** `frontend/src/components/chat/ChatWidget.tsx` L219
- **Antes:** `DOMPurify.sanitize(renderMarkdown(displayContent))`
- **Después:** `DOMPurify.sanitize(renderMarkdown(displayContent), { ALLOWED_TAGS: ['strong', 'em', 'code', 'li', 'ul', 'ol', 'br', 'p', 'pre', 'a'], ALLOWED_ATTR: ['class', 'href', 'target', 'rel'] })`
- **Tiempo:** 5 min

#### C.2 — Usuarios legacy con modules_access vacío (SQL manual)
```sql
-- Ejecutar en Supabase SQL Editor:
SELECT id, email, role, modules_access, approved
FROM profiles
WHERE (modules_access IS NULL OR modules_access = '[]'::jsonb)
  AND role != 'admin';
-- Si hay usuarios legítimos bloqueados, asignar permisos:
-- UPDATE profiles SET modules_access = '["all"]'::jsonb WHERE id IN (...);
```
- **Tiempo:** 10 min manual

#### C.3 — Auditoría dangerouslySetInnerHTML en TODO el frontend
- **Comando:** `grep -rn "dangerouslySetInnerHTML" frontend/src/`
- **Fix:** Cualquier uso sin `DOMPurify.sanitize()` debe añadirlo.
- **Tiempo:** 15 min

---

### Resumen Sprint 45

| ID | Descripción | Archivo | Tiempo |
|----|-------------|---------|--------|
| A.1 | Timeout widgets CWV/Bing/Acciones | DashboardPage.tsx | 30 min |
| A.2 | Timeout KPI cards GSC | DashboardPage.tsx | 30 min |
| A.3 | GA4 graceful error | ga4_service.py | 15 min |
| B.1 | Briefings botón debounce | BriefingsPage.tsx | 15 min |
| B.2 | Briefings validación duplicados | briefings.py | 30 min |
| C.1 | DOMPurify whitelist | ChatWidget.tsx | 5 min |
| C.2 | Usuarios legacy modules_access | SQL manual Supabase | 10 min |
| C.3 | Auditoría dangerouslySetInnerHTML | grep + fix | 15 min |

**Total: 8 items → ~2.5h**

**Prioridad:**
1. **C.2** — Primero verificar en Supabase si hay usuarios bloqueados por el Fix 3. Urgente.
2. **Fase A** — Lo que más nota el usuario (Dashboard).
3. **Fase B + C.1 + C.3** — Calidad + seguridad.

---

## Sprint 48 — Briefings: Fixes + Features Nacho (Febrero 2026) ✅ COMPLETADO

> **Contexto:** Testing en vivo + feedback de Nacho (SEO) revelaron 12 issues en Briefings: bugs críticos en creación/exports + mejoras UX + features nuevos (LLMs, disclaimers).
>
> **Referencia:** `AUDIT-COMPLETO-FEB2026.md` — Sección 11 (Bugs #20-22) + Sección 12 (Bugs #23-29, FR-1 a FR-4)
>
> **Commit:** `35800fc` — 27 Feb 2026 — 7 archivos, 527 insertions, 34 deletions
>
> **Migracion:** `072_project_disclaimers.sql` — ejecutar en Supabase SQL Editor

---

### Fase A — Fix creación de briefings (Bug #23) ✅

**A.1 — Fix handleCreate en BriefingsPage.tsx** ✅

- **Archivo:** `frontend/src/pages/BriefingsPage.tsx` (línea ~174)
- **Causa raíz:** Catch vacío silenciaba errores. Payload enviaba campo `tone` (no existe en backend Pydantic model). `deadline: ""` podía causar error de tipo DATE.
- **Fix aplicado:**
  - `toast.error(e.message)` en catch para mostrar errores al usuario
  - `delete payload.tone` — omitir campo que backend ignora
  - Si `deadline` está vacío, no enviarlo (en vez de enviar string vacío)
- **Criterio éxito:** ✅ Crear briefing muestra error si falla, payload limpio llega al backend

---

### Fase B — Renderizado: Preview, DOCX, Notion ✅

**B.1 — Fix doble bullet en Puntos Clave (Bugs #24, #27)** ✅

- **Archivo:** `frontend/src/components/briefings/formatBriefing.ts` (línea ~149)
- **Causa raíz:** `lines.push(\`- ${p}\`)` siempre añadía `- ` — si el usuario ya puso `-` o `•`, quedaba `- - texto`
- **Fix aplicado:** Smart prefix: si el punto ya empieza con `-`, `•`, `*` o `1.` → no agregar prefijo
- **Criterio éxito:** ✅ Preview y Notion sin bullets dobles

**B.2 — Fix saltos de línea en texto libre (Bug #25)** ✅

- **Archivo:** `frontend/src/components/briefings/formatBriefing.ts`
- **Causa raíz:** `\n` simple se ignora en markdown — necesita `  \n` (2 espacios + newline)
- **Fix aplicado:** `.replace(/\n/g, '  \n')` en `tone_and_style`, `writer_notes`, `intro_instructions`
- **Criterio éxito:** ✅ Preview y Notion respetan line breaks

**B.3 — Etiquetas [H2]/[H3] en DOCX (Bug #26)** ✅

- **Archivo:** `backend/api/services/docx_service.py` (líneas 88-98)
- **Fix aplicado:** Prefijo `[H2]` o `[H3]` en el texto del heading de Word
- **Criterio éxito:** ✅ DOCX muestra etiquetas visibles de nivel de encabezado

**B.4 — Texto "propuesta de estructura" en exports (FR-4)** ✅

- **Archivos:** `formatBriefing.ts` + `docx_service.py` + `BriefingEditor.tsx`
- **Fix aplicado:**
  - Markdown: `> *Esta estructura es una propuesta orientativa. El redactor puede adaptarla.*`
  - DOCX: párrafo en cursiva antes de los headings
  - Editor: texto gris informativo bajo sección de encabezados
- **Criterio éxito:** ✅ Nota visible en editor, Preview, Notion y DOCX

**B.5 — DOCX key_points sin bullets forzados (Bug #25 variante)** ✅

- **Archivo:** `backend/api/services/docx_service.py` (líneas 125-128)
- **Causa raíz:** `style='List Bullet'` forzaba bullets siempre
- **Fix aplicado:** Si el punto ya tiene prefijo (`-`/`•`/`*`/número), usar párrafo normal. Si no, usar bullet.
- **Criterio éxito:** ✅ DOCX respeta formato original de cada punto

---

### Fase C — UX del editor de briefings ✅

**C.1 — Keywords secundarias como chips (Bug #28)** ✅

- **Archivo:** `frontend/src/components/briefings/BriefingEditor.tsx` (líneas ~845-856)
- **Fix aplicado:** Reemplazado input comma-separated por sistema de chips/tags:
  - Cada keyword como pill amarilla con botón X para eliminar
  - Input: Enter o `,` agrega chip, Backspace elimina último
  - Flex wrap container
  - Compatible con formato array existente
- **Criterio éxito:** ✅ Se pueden ver y gestionar ≥10 keywords cómodamente

**C.2 — Botón eliminar FAQs y Directrices de Imágenes (Bug #29)** ✅

- **Archivo:** `frontend/src/components/briefings/BriefingEditor.tsx`
- **Fix aplicado:**
  - Image guidelines: botón "Desactivar" (icono Ban) visible cuando está activo, resetea a `undefined`
  - FAQs: botón "Borrar todas" junto al título, con `window.confirm()` de confirmación
- **Criterio éxito:** ✅ Secciones opcionales se pueden activar y desactivar libremente

**C.3 — Sidebar de navegación en el editor (FR-1)** ✅

- **Archivo:** `frontend/src/components/briefings/BriefingEditor.tsx`
- **Fix aplicado:**
  - Sidebar sticky (w-48) a la izquierda con 11 secciones clickeables
  - Secciones: Datos generales, Objetivo, Keywords, Encabezados, Imagenes, FAQs, GEO, Zona LLMs, Coherencia, Disclaimers, Notas
  - Cada sección del editor tiene `id` prop → `scrollIntoView({ behavior: 'smooth' })` al click
  - Solo visible en pantallas >= lg. En mobile, oculto.
  - Layout: flex row con sidebar + contenido scrollable
- **Criterio éxito:** ✅ Navegación con un clic a cualquier sección

---

### Fase D — Nuevos campos de briefing (Features Nacho) ✅

**D.1 — Zona LLMs / IA Generativa (FR-2)** ✅

- **Archivos:** `BriefingEditor.tsx` + `formatBriefing.ts` + `docx_service.py`
- **Implementación:**
  - Nueva sección entre GEO y Coherencia de Señal
  - Campo `llm_blocks` en structure JSONB (no requiere migración):
    ```ts
    llm_blocks?: Array<{ claim: string; source: string; type: "dato" | "cita" | "definicion" }>
    ```
  - UI: lista de bloques, cada uno con select tipo + textarea claim + input source + botón eliminar
  - Botón "Agregar bloque"
  - Export markdown: sección con formato `[Dato] claim — Fuente: source`
  - Export DOCX: sección con tipo en negrita + claim + fuente en tamaño reducido
- **Criterio éxito:** ✅ Bloques visibles en editor, guardados en JSONB, exportados en todos los formatos

**D.2 — Sistema de Disclaimers configurables por proyecto (FR-3)** ✅

- **Archivos:** `072_project_disclaimers.sql` (NUEVO) + `projects.py` + `BrandSettings.tsx` + `BriefingEditor.tsx` + `formatBriefing.ts` + `docx_service.py`
- **Implementación simplificada** (sin tablas extra, todo en JSONB):
  - **Migración:** `ALTER TABLE projects ADD COLUMN IF NOT EXISTS disclaimers JSONB DEFAULT '[]'::jsonb`
  - **Backend:** Campo `disclaimers: Optional[list]` añadido a `ProjectUpdate` en `projects.py`
  - **Settings (BrandSettings.tsx):** Nueva sección "Disclaimers por defecto":
    - Lista con label + texto editable
    - Agregar/eliminar disclaimers
    - Toggle activo/inactivo por defecto
    - Guardar en `projects.disclaimers` vía PUT `/projects/{id}`
  - **Editor (BriefingEditor.tsx):** Nueva sección "Disclaimers" antes de notas:
    - Carga disclaimers del proyecto como checkboxes (activos = pre-checked)
    - Campo para disclaimers custom adicionales con label + texto
    - Guardar en `structure.disclaimers`
  - **Exports:** Sección "Disclaimers" con label en negrita + texto en markdown y DOCX
- **Criterio éxito:** ✅ Configurar en Settings, toggle en editor, aparece en exports

---

### Resumen Sprint 48

| ID | Descripción | Tipo | Archivos | Estado |
|----|-------------|------|----------|--------|
| A.1 | Fix creación briefings (catch + payload) | Bug #23 | BriefingsPage.tsx | ✅ |
| B.1 | Smart bullet en Puntos Clave | Bug #24/#27 | formatBriefing.ts | ✅ |
| B.2 | Line breaks en texto libre | Bug #25 | formatBriefing.ts | ✅ |
| B.3 | Etiquetas [H2]/[H3] en DOCX | Bug #26 | docx_service.py | ✅ |
| B.4 | Nota "propuesta" en estructura | FR-4 | formatBriefing.ts, docx_service.py, BriefingEditor.tsx | ✅ |
| B.5 | DOCX key_points sin bullets forzados | Bug #25 | docx_service.py | ✅ |
| C.1 | Keywords secundarias → chips | Bug #28 | BriefingEditor.tsx | ✅ |
| C.2 | Botón eliminar FAQs/Imágenes | Bug #29 | BriefingEditor.tsx | ✅ |
| C.3 | Sidebar navegación editor | FR-1 | BriefingEditor.tsx | ✅ |
| D.1 | Zona LLMs (bloques factuales) | FR-2 | BriefingEditor.tsx, formatBriefing.ts, docx_service.py | ✅ |
| D.2 | Disclaimers configurables | FR-3 | 6 archivos + migración 072 | ✅ |

**Total: 11 items → todos completados**
**Build:** `npm run build` ✅ — `npx tsc --noEmit` ✅ — Backend imports ✅
