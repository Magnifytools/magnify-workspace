# CLAUDE.md - The Engine

> Extiende `/Codigo/CLAUDE.md` (global). No repetir reglas globales aqui.

## Proyecto

- Plataforma: The Engine (multi-tenant, multi-proyecto)
- Frontend: localhost:5174 (React + TypeScript + Tailwind)
- Backend: localhost:8001 (Python FastAPI)
- DB: Supabase PostgreSQL (zzjesnxinsbzqqjmgcub.supabase.co)
- Auth: Supabase Auth
- IA: Claude API (Anthropic)
- App folder: `engine-app/`

## Comandos

```bash
# Arrancar frontend
cd "/Codigo/the-engine/engine-app/frontend" && npm run dev

# Arrancar backend
cd "/Codigo/the-engine/engine-app/backend" && uvicorn main:app --reload --port 8001

# Verificar build frontend
cd "/Codigo/the-engine/engine-app/frontend" && npm run build

# Verificar tipos TypeScript
cd "/Codigo/the-engine/engine-app/frontend" && npx tsc --noEmit

# Verificar backend arranca sin errores
cd "/Codigo/the-engine/engine-app/backend" && python -c "from main import app; print('OK')"
```

## Testing

**Backend:** 82+ tests con pytest (`cd backend && pytest`). Añadir tests para cada nueva ruta/servicio.

**Frontend:** Verificación mínima obligatoria:
1. `npm run build` pasa sin errores
2. `npx tsc --noEmit` sin errores de tipos
3. Login funciona en http://localhost:5174
4. La funcionalidad modificada funciona end-to-end

Para cambios críticos (auth, base de datos, integraciones API): probar manualmente el flujo completo Y verificar en los logs del backend que no hay errores.

## Plan de mejoras

Ver `HOJA-DE-RUTA.md` para instrucciones detalladas y `SOURCE-OF-TRUTH.md` para estado actual.

**Airtable:** ❌ Descartado — reemplazado por Lead Attribution GA4 (Sprint 20).

**Reglas UX (aplicar SIEMPRE):**
- Máximo 5-7 KPIs por vista
- NUNCA pie charts
- Toda métrica con comparativa temporal (MoM)
- Colores semánticos: verde=mejora, rojo=empeora

## Funcionalidades

**Referencia única:** `SOURCE-OF-TRUTH.md` — Estado de módulos, roadmap, integraciones.

**Config de sidebar:** `frontend/src/config/modules.ts` — Controla qué módulos aparecen.

## Migraciones Supabase

Hay 69 migraciones en `backend/db/migrations/` numeradas 001-069.
Ejecutar en orden si hay problemas con tablas faltantes.

## Errores conocidos

1. Conflicto de puertos: este proyecto usa 5174/8001, NO 5173/8000 (ese es Content Creator)
2. Python 3.9 deprecation warnings con google-auth: ignorar, es esperado
3. Usar `api.delete()` no `api.del()` en el cliente HTTP
4. ProtectedRoute no debe hacer fetch de `/me`: usar AuthContext que ya lo hace
5. Supabase RLS: verificar que las policies estan activas antes de asumir que un query falla por codigo
