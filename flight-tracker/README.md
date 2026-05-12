# flight-tracker

Tracker de precios de vuelos sobre [fli](https://github.com/punitarani/fli) (Google Flights, sin API key). Guarda historico en SQLite y avisa por email cuando el precio baja.

## Estado actual

- Watch precargado: **BCN -> BER, 2026-06-24, Vueling, salida 8-12h, directo**.
- Notificacion por email (SMTP). Recomendado Gmail con App Password.

## Setup (en tu Mac)

```bash
cd flight-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config.example.toml config.toml
# Edita config.toml: rellena seccion [email] con tu SMTP + App Password.
```

### Gmail App Password

1. Cuenta Google -> Seguridad -> 2-Step Verification (debe estar ON)
2. https://myaccount.google.com/apppasswords -> crea uno para "Mail"
3. Pega esos 16 caracteres en `password` dentro de `[email]`

## Uso

```bash
# Comprueba precios. Imprime el mejor match por watch y registra en SQLite.
python -m src.main --config config.toml

# Igual pero sin enviar emails (debug).
python -m src.main --config config.toml --dry-run -v
```

Primera ejecucion: no hay historico, asi que no avisara (no hay "min previo" contra el que comparar). A partir de la segunda corrida ya evalua bajadas.

## Logica de aviso

Por cada watch, en cada ejecucion:

1. Busca vuelos con los filtros (ruta, fecha, ventana horaria, aerolinea, clase, escalas).
2. Coge el mas barato y lo guarda en `data/prices.db`.
3. Avisa por email si:
   - El precio actual baja >= `drop_pct` % vs el minimo historico de ese watch, **o**
   - El precio actual <= `target_price` (si lo defines).
4. Tras avisar, **cooldown**: no vuelve a avisar hasta que el precio baje otro `cooldown_extra_drop_pct` % adicional. Evita spam.

## Automatizar (cron en Mac)

`crontab -e` y anade:

```
# Cada 6 horas
0 */6 * * * cd /ruta/a/flight-tracker && /ruta/a/flight-tracker/.venv/bin/python -m src.main --config /ruta/a/flight-tracker/config.toml >> /ruta/a/flight-tracker/data/run.log 2>&1
```

Ojo: el Mac tiene que estar despierto. Para algo siempre encendido, usar Raspberry Pi o un VPS pequeno.

## Anadir mas vuelos

En `config.toml`, duplica el bloque `[[watches]]`. Ejemplo:

```toml
[[watches]]
name = "MAD-LIS sep"
origin = "MAD"
destination = "LIS"
date = "2026-09-15"
airlines = []
non_stop = false
seat_class = "ECONOMY"
adults = 1
drop_pct = 8
```

## Ver el historico

```bash
sqlite3 data/prices.db "SELECT watch_name, checked_at, price FROM price_history ORDER BY id DESC LIMIT 20;"
```

## Limitaciones conocidas

- Google Flights bloquea IPs de datacenter (403). En tu Mac local va bien.
- No abusar: 2-4 veces al dia por watch es razonable. Cada hora se puede empezar a rate-limitar.
- `airlines` filtra por codigo IATA (ver `python -c "from fli.models import Airline; print([a.name for a in Airline][:30])"`).
