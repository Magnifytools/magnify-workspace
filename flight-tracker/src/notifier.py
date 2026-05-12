"""Email notification via SMTP."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .search import BestFlight


def send_drop_alert(
    *,
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    from_addr: str,
    to_addr: str,
    watch_name: str,
    flight: BestFlight,
    previous_min: float,
    drop_pct: float,
) -> None:
    subject = f"Precio bajado: {watch_name} -> {flight.price:.0f} {flight.currency or ''} (-{drop_pct:.1f}%)"

    body = f"""\
El precio del vuelo bajo.

Watch:        {watch_name}
Precio actual: {flight.price:.2f} {flight.currency or ''}
Minimo previo: {previous_min:.2f}
Caida:         {drop_pct:.1f}%

Vuelo:    {flight.airline} {flight.flight_number}
Salida:   {flight.departure.isoformat()}
Llegada:  {flight.arrival.isoformat()}
Duracion: {flight.duration_min} min
Escalas:  {flight.stops}
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.starttls()
        s.login(username, password)
        s.send_message(msg)
