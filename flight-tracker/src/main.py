"""Entrypoint: load config, run all watches, persist prices, send alerts on drops."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path

from .notifier import Alert, send_digest
from .report import generate_report
from .search import search_watch
from .storage import Storage


_EMAIL_ENV_OVERRIDES = {
    "smtp_host": "FT_SMTP_HOST",
    "smtp_port": "FT_SMTP_PORT",
    "username": "FT_SMTP_USERNAME",
    "password": "FT_SMTP_PASSWORD",
    "from_addr": "FT_SMTP_FROM",
    "to_addr": "FT_SMTP_TO",
}


def load_config(path: Path) -> dict:
    with path.open("rb") as f:
        cfg = tomllib.load(f)
    email = cfg.setdefault("email", {})
    for key, env in _EMAIL_ENV_OVERRIDES.items():
        val = os.environ.get(env)
        if val:
            email[key] = val
    return cfg


def evaluate_drop(
    *, current: float, prev_min: float | None, drop_pct: float, target_price: float | None
) -> tuple[bool, float]:
    """Returns (should_alert, observed_drop_pct_vs_min)."""
    if prev_min is None:
        return (False, 0.0)
    observed_drop = (prev_min - current) / prev_min * 100 if prev_min > 0 else 0.0
    if target_price is not None and current <= target_price:
        return (True, observed_drop)
    if observed_drop >= drop_pct:
        return (True, observed_drop)
    return (False, observed_drop)


def passes_cooldown(
    *, current: float, last_notif: tuple[float, str] | None, extra_drop_pct: float
) -> bool:
    if last_notif is None:
        return True
    last_price, _ = last_notif
    if last_price <= 0:
        return True
    drop_since_last = (last_price - current) / last_price * 100
    return drop_since_last >= extra_drop_pct


def run(config_path: Path, *, dry_run: bool, verbose: bool) -> int:
    config = load_config(config_path)
    settings = config.get("settings", {})
    email_cfg = config.get("email", {})
    watches = config.get("watches", [])
    if not watches:
        print("No hay watches configurados.", file=sys.stderr)
        return 1

    db_path = Path(settings.get("db_path", "data/prices.db"))
    if not db_path.is_absolute():
        db_path = config_path.parent / db_path
    storage = Storage(db_path)
    cooldown = float(settings.get("cooldown_extra_drop_pct", 3))
    notify_enabled = bool(settings.get("notify_enabled", True))
    display_currency = settings.get("display_currency")
    usd_to_eur = float(settings.get("usd_to_eur", 0.92))

    exit_code = 0
    pending_alerts: list[Alert] = []
    for w in watches:
        name = w["name"]
        try:
            flight = search_watch(w)
        except Exception as e:
            print(f"[{name}] ERROR: {e}", file=sys.stderr)
            exit_code = 2
            continue

        if flight is None:
            print(f"[{name}] sin resultados.")
            continue

        if display_currency == "EUR" and flight.currency == "USD":
            flight.price = round(flight.price * usd_to_eur, 2)
            flight.currency = "EUR"

        prev_min = storage.min_price(name)
        storage.record_price(
            name,
            flight.price,
            airline=flight.airline,
            flight_number=flight.flight_number,
            departure=flight.departure.isoformat(),
            arrival=flight.arrival.isoformat(),
            duration_min=flight.duration_min,
            layovers=json.dumps(flight.layovers),
        )

        marker = ""
        if prev_min is not None:
            delta = flight.price - prev_min
            marker = f"  (min hist: {prev_min:.2f}, delta {delta:+.2f})"
        print(
            f"[{name}] {flight.airline} {flight.flight_number} "
            f"{flight.departure.strftime('%H:%M')}  {flight.price:.2f} {flight.currency or ''}{marker}"
        )

        target_price = w.get("target_price")
        should_alert, observed = evaluate_drop(
            current=flight.price,
            prev_min=prev_min,
            drop_pct=float(w.get("drop_pct", 5)),
            target_price=target_price,
        )
        if not should_alert:
            if verbose and prev_min is not None:
                print(f"  no-alert (caida {observed:.1f}% < umbral)")
            continue

        if not passes_cooldown(
            current=flight.price,
            last_notif=storage.last_notification(name),
            extra_drop_pct=cooldown,
        ):
            print(f"  alert suprimida por cooldown")
            continue

        if not w.get("notify", True):
            if verbose:
                print(f"  alert suprimida por notify=false")
            continue

        reason = "target" if target_price is not None and flight.price <= target_price else "drop"
        pending_alerts.append(
            Alert(
                watch_name=name,
                flight=flight,
                previous_min=prev_min,
                drop_pct=observed,
                reason=reason,
                seat_class=w.get("seat_class", "ECONOMY"),
            )
        )
        print(f"  alert: {reason} ({observed:.1f}%)")

    if pending_alerts:
        if dry_run:
            print(f"[dry-run] enviaría digest con {len(pending_alerts)} alerta(s)")
        elif not notify_enabled:
            print(f"notify_enabled=false → digest suprimido ({len(pending_alerts)} alerta(s))")
        else:
            try:
                send_digest(
                    smtp_host=email_cfg["smtp_host"],
                    smtp_port=int(email_cfg["smtp_port"]),
                    username=email_cfg["username"],
                    password=email_cfg["password"],
                    from_addr=email_cfg["from_addr"],
                    to_addr=email_cfg["to_addr"],
                    alerts=pending_alerts,
                )
                for a in pending_alerts:
                    storage.mark_notified(a.watch_name, a.flight.price)
                print(f"digest enviado ({len(pending_alerts)} alerta(s))")
            except Exception as e:
                print(f"ERROR enviando digest: {e}", file=sys.stderr)
                exit_code = 3

    report_path = config_path.parent / "report.md"
    try:
        generate_report(watches, storage, report_path)
        print(f"report: {report_path}")
    except Exception as e:
        print(f"ERROR generando report: {e}", file=sys.stderr)

    return exit_code


def main() -> None:
    p = argparse.ArgumentParser(description="Flight price tracker")
    p.add_argument("--config", type=Path, default=Path("config.toml"))
    p.add_argument("--dry-run", action="store_true", help="No envia emails")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    sys.exit(run(args.config, dry_run=args.dry_run, verbose=args.verbose))


if __name__ == "__main__":
    main()
