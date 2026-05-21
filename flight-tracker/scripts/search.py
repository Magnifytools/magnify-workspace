"""Ad-hoc flight search. CLI args: origins, destinations, date, adults.

Origins/destinations son listas de IATA separadas por coma. Imprime los 30 mas
baratos ordenados por precio (combina todas las combinaciones origen x destino).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from fli.models import (
    Airport,
    FlightSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    SortBy,
)
from fli.search import SearchFlights


def parse_codes(s: str, enum_cls, kind: str) -> list:
    out = []
    for raw in s.split(","):
        code = raw.strip().upper()
        if not code:
            continue
        try:
            out.append(enum_cls[code])
        except KeyError:
            print(f"WARN: {kind} '{code}' desconocido, ignorado.", file=sys.stderr)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--origins", required=True, help="Comma-separated IATA codes")
    p.add_argument("--destinations", required=True)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--adults", type=int, default=1)
    p.add_argument("--non-stop", action="store_true")
    p.add_argument("--top", type=int, default=30)
    args = p.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("ERROR: --date debe ser YYYY-MM-DD", file=sys.stderr)
        return 1

    origins = parse_codes(args.origins, Airport, "Airport")
    dests = parse_codes(args.destinations, Airport, "Airport")
    if not origins or not dests:
        print("ERROR: faltan origenes o destinos validos.", file=sys.stderr)
        return 1

    search = SearchFlights()
    rows = []
    for o in origins:
        for d in dests:
            try:
                filters = FlightSearchFilters(
                    passenger_info=PassengerInfo(adults=args.adults),
                    flight_segments=[
                        FlightSegment(
                            departure_airport=[[o, 0]],
                            arrival_airport=[[d, 0]],
                            travel_date=args.date,
                        )
                    ],
                    seat_type=SeatType.ECONOMY,
                    stops=MaxStops.NON_STOP if args.non_stop else MaxStops.ANY,
                    sort_by=SortBy.CHEAPEST,
                )
                results = search.search(filters) or []
                for r in results[:10]:
                    leg0, legN = r.legs[0], r.legs[-1]
                    rows.append(
                        {
                            "route": f"{o.name}->{d.name}",
                            "price": r.price,
                            "currency": r.currency or "",
                            "stops": r.stops,
                            "airline": leg0.airline.name,
                            "fn": leg0.flight_number,
                            "dep": leg0.departure_datetime.strftime("%a %d %b %H:%M"),
                            "arr": legN.arrival_datetime.strftime("%H:%M"),
                            "duration": r.duration,
                        }
                    )
                print(f"[{o.name}->{d.name}] {len(results)} resultados", file=sys.stderr)
            except Exception as e:
                print(f"[{o.name}->{d.name}] ERROR: {e}", file=sys.stderr)

    rows.sort(key=lambda x: x["price"])
    print()
    print(f"{'route':<12} {'airline':>4} {'flight':<7} {'departure':<18} {'arr':<6} {'dur':>5} {'stops':>5} {'price':>10}")
    print("-" * 80)
    for r in rows[: args.top]:
        print(
            f"{r['route']:<12} {r['airline']:>4} {r['fn']:<7} {r['dep']:<18} "
            f"{r['arr']:<6} {r['duration']:>4}m {r['stops']:>5} {r['price']:>8.2f} {r['currency']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
