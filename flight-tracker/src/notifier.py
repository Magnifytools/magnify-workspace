"""Email notification via SMTP (single digest with all matching watches)."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from .search import BestFlight


@dataclass
class Alert:
    watch_name: str
    flight: BestFlight
    previous_min: float | None
    drop_pct: float
    reason: str  # "target" | "drop"
    seat_class: str = "ECONOMY"


_CLASS_LABELS = {
    "ECONOMY": "Económica",
    "PREMIUM_ECONOMY": "Económica Premium",
    "BUSINESS": "Business",
    "FIRST": "Primera",
}


def _fmt_dur(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m:02d}m"


def _format_stops(layovers: list[tuple[str, int]], stops: int) -> str:
    if not layovers:
        return "directo" if stops == 0 else f"{stops} escala(s)"
    return " · ".join(f"{code} ({_fmt_dur(mins)})" for code, mins in layovers)


def send_digest(
    *,
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    from_addr: str,
    to_addr: str,
    alerts: list[Alert],
) -> None:
    if not alerts:
        return

    cheapest = min(alerts, key=lambda a: a.flight.price)
    currency = cheapest.flight.currency or ""
    subject = (
        f"Vuelos: {len(alerts)} alerta(s) — el más barato "
        f"{cheapest.flight.price:.0f} {currency} ({cheapest.watch_name})"
    )

    lines = [f"{len(alerts)} ruta(s) cumplen el umbral configurado.\n"]
    for cls in ("ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"):
        group = [a for a in alerts if a.seat_class == cls]
        if not group:
            continue
        lines.append(f"\n=== {_CLASS_LABELS.get(cls, cls)} ===\n")
        for i, a in enumerate(sorted(group, key=lambda x: x.flight.price), 1):
            f = a.flight
            reason = (
                f"≤ target ({f.price:.0f} {f.currency or ''})"
                if a.reason == "target"
                else f"-{a.drop_pct:.1f}% vs min previo {a.previous_min:.0f}"
            )
            stops_desc = _format_stops(f.layovers, f.stops)
            lines.append(
                f"{i}. {a.watch_name}\n"
                f"   Precio:   {f.price:.2f} {f.currency or ''}  ({reason})\n"
                f"   Vuelo:    {f.airline} {f.flight_number}\n"
                f"   Salida:   {f.departure.strftime('%Y-%m-%d %H:%M')}\n"
                f"   Llegada:  {f.arrival.strftime('%Y-%m-%d %H:%M')}\n"
                f"   Duración: {_fmt_dur(f.duration_min)}\n"
                f"   Escalas:  {stops_desc}\n"
            )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content("\n".join(lines))

    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.starttls()
        s.login(username, password)
        s.send_message(msg)
