"""Markdown report generator: current price matrix + per-watch history."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .storage import Storage


SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _sparkline(values: list[float]) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    if hi == lo:
        return SPARK_CHARS[0] * len(values)
    span = hi - lo
    return "".join(
        SPARK_CHARS[min(len(SPARK_CHARS) - 1, int((v - lo) / span * (len(SPARK_CHARS) - 1)))]
        for v in values
    )


def _trend_arrow(values: list[float]) -> str:
    if len(values) < 2:
        return ""
    delta = values[-1] - values[-2]
    if delta < -0.5:
        return " ↓"
    if delta > 0.5:
        return " ↑"
    return " ="


def generate_report(watches: list[dict], storage: Storage, output_path: Path) -> None:
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append("# Flight prices — auto-generated\n")
    lines.append(f"_Última actualización: {now}_\n")

    origins = sorted({w["origin"] for w in watches})
    dates = sorted({w["date"] for w in watches})
    by_key = {(w["origin"], w["date"]): w["name"] for w in watches}

    lines.append("\n## Precio actual (USD)\n")
    header = "| Origen | " + " | ".join(dates) + " |"
    sep = "|--------|" + "|".join(["----------:" for _ in dates]) + "|"
    lines.append(header)
    lines.append(sep)
    for origin in origins:
        cells = []
        for date in dates:
            name = by_key.get((origin, date))
            hist = storage.history(name) if name else []
            if not hist:
                cells.append("—")
                continue
            last = hist[-1][1]
            arrow = _trend_arrow([p for _, p in hist])
            cells.append(f"{last:.0f}{arrow}")
        lines.append(f"| {origin}    | " + " | ".join(cells) + " |")

    lines.append("\n## Historial por watch\n")
    lines.append("| Watch | Min | Último | Δ vs min | Runs | Tendencia |")
    lines.append("|-------|----:|-------:|---------:|-----:|-----------|")
    for w in watches:
        name = w["name"]
        hist = storage.history(name)
        if not hist:
            lines.append(f"| {name} | — | — | — | 0 | — |")
            continue
        prices = [p for _, p in hist]
        mn, last = min(prices), prices[-1]
        delta_pct = (last - mn) / mn * 100 if mn > 0 else 0
        lines.append(
            f"| {name} | {mn:.0f} | {last:.0f} | {delta_pct:+.1f}% | {len(prices)} | `{_sparkline(prices)}` |"
        )

    lines.append("\n## Lectura\n")
    lines.append("- `↓` = bajó vs lectura anterior, `↑` = subió, `=` = sin cambio.")
    lines.append("- Sparkline muestra todas las lecturas históricas (más antigua → más reciente).")
    lines.append("- Cada bloque más alto = precio más alto en ese momento.")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
