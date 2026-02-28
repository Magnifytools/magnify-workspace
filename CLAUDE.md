# CLAUDE.md - Reglas Globales

> Owner: David | PM: Claude | Actualizado: Feb 2026

Reglas para TODOS los proyectos. Cada proyecto tiene su CLAUDE.md que extiende estas.

## Puertos Reservados

| Proyecto | Frontend | Backend |
|----------|----------|---------|
| Content Creator | 5173 | 8000 |
| The Engine | 5174 | 8001 |
| Gestor Financiero | 5175 | 8002 |
| Agency Manager | 5176 | 8003 |

Nuevos proyectos: 5177+/8004+

## Verificacion de Proyecto (OBLIGATORIO)

ANTES de cualquier cambio: `pwd` + `ls`. Confirmar que coincide con el proyecto objetivo.

| Proyecto | Carpeta | App folder |
|----------|---------|------------|
| Content Creator | `/Codigo/Content Creator/` | `content-creator-app/` |
| The Engine | `/Codigo/the-engine/` | `engine-app/` |
| Gestor Financiero | `/Codigo/Gestor financiero/` | TBD |
| Agency Manager | `/Codigo/agency-manager/` | TBD |

Si la carpeta NO coincide: STOP. Cambiar a la correcta.

## Principios

- Simplicity First: cambio minimo necesario. No tocar lo que no hace falta.
- No Laziness: buscar causa raiz. Sin fixes temporales. Estandar senior.
- Verification Before Done: nunca marcar completo sin demostrar que funciona.
- Context Preservation: actualizar archivos de estado tras cambios significativos.

## Workflow: Planning con Archivos

Para tareas no triviales (3+ pasos, bugs, cambios multi-archivo, cambios de arquitectura), crear en `tasks/current/`:

- `task_plan.md` - Que hay que hacer, paso a paso
- `findings.md` - Descubrimientos durante exploracion
- `progress.md` - Estado actual, que falta

Triggers: usuario dice "arregla", "implementa", "anade feature", algo falla sin causa clara.

Durante ejecucion:
1. ANTES de cada cambio: releer plan y progress
2. DESPUES de descubrimiento: actualizar findings
3. DESPUES de paso completado: actualizar progress
4. Si el plan cambia: actualizar task_plan

Al terminar: mover a `tasks/archive/[fecha]-[nombre]/` o borrar si fue simple.

Para tareas simples (1-2 pasos obvios): ejecutar directamente.

## Workflow: Subagentes

- Offload research, exploracion y analisis paralelo a subagentes
- Un task por subagente para ejecucion enfocada
- Usar para: exploracion de codigo, testing, verificacion, research
- Mantener el contexto principal limpio

## Workflow: Testing y Verificacion

### Regla general
Nunca confiar en que "deberia funcionar". Demostrar que funciona:
- UI: verificar visualmente o con screenshot
- API: mostrar curl/response real
- Logica: correr test o demostrar con ejemplo

### Si el proyecto tiene tests configurados
Correr los tests ANTES y DESPUES de cambios. Si un test falla por tu cambio, arreglarlo antes de reportar como completo.

### Si NO hay tests
Para cambios criticos (auth, datos, pagos), escribir al menos un test basico que cubra el happy path antes de marcar como completo. Usar el framework del proyecto (pytest para Python, vitest/jest para TS/JS).

### Verificacion minima aceptable
1. El build compila sin errores
2. La funcionalidad cambiada funciona end-to-end
3. Las funcionalidades adyacentes no se han roto

## Workflow: Auto-mejora

Cuando el usuario corrija un error, INMEDIATAMENTE (sin preguntar):

1. Anadir entrada a `tasks/lessons.md`:
   ```
   #### [FECHA] [PROYECTO] Descripcion breve
   - Error: Que hiciste mal
   - Regla: Que hacer en el futuro
   - Impacto: Consecuencia del error
   ```
2. Si aplica al proyecto, anadirlo a su CLAUDE.md en "Errores conocidos"

Triggers: usuario dice "no", "mal", "error", "eso no", "incorrecto", corrige tu codigo, test/build falla por tu cambio.

## Workflow: Elegancia (con criterio)

Para cambios no triviales: pausar y preguntar "hay una forma mas elegante?"
Si un fix huele a hack: buscar la solucion limpia.
Para fixes simples y obvios: no sobre-disenar.

## Workflow: Bug Fixing Autonomo

Cuando te den un bug: arreglalo. No pidas que te guien. Lee logs, errores, tests fallidos, y resuelve.

## Estructura del Portfolio

```
/Codigo/
├── CLAUDE.md                    <- Este archivo
├── proyecto-estado-global.json
├── tasks/
│   ├── TASKS.md                 <- Now/Next/Later
│   ├── lessons.md               <- Errores -> Reglas
│   ├── current/                 <- Planificacion tarea activa
│   └── archive/                 <- Tareas completadas
├── agency-manager/
├── Content Creator/
├── the-engine/
└── Gestor financiero/
```

## Al Iniciar Sesion

1. Leer este archivo
2. Leer `tasks/lessons.md` (ultimos errores)
3. Si hay tarea activa: leer `tasks/current/`
4. Si trabajas en proyecto especifico: leer su CLAUDE.md local

## Errores Globales Conocidos

1. No asumir estructura de archivos. Siempre verificar con `ls` antes de crear/mover.
2. No hardcodear puertos. Usar config del proyecto.
3. Python 3.9 deprecation warnings con google-auth: esperado, no intentar "arreglar".
4. `api.del` no existe en algunos clientes HTTP. Usar `api.delete`.
5. ProtectedRoute no debe duplicar fetch de `/me`. Usar AuthContext.
