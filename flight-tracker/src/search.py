"""Thin wrapper around `fli` to run a configured watch and return the best match."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fli.models import (
    Airline,
    Airport,
    FlightSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    SortBy,
)
from fli.models.google_flights.base import TimeRestrictions
from fli.search import SearchFlights


@dataclass
class BestFlight:
    price: float
    currency: str | None
    duration_min: int
    airline: str
    flight_number: str
    departure: datetime
    arrival: datetime
    stops: int


def _enum_or_raise(enum_cls, name: str, kind: str):
    try:
        return enum_cls[name]
    except KeyError as e:
        valid = ", ".join(sorted(m.name for m in enum_cls)[:20])
        raise ValueError(f"{kind} '{name}' no encontrado. Ejemplos: {valid}...") from e


def search_watch(watch: dict) -> BestFlight | None:
    """Run a search for one watch config and return the cheapest matching flight."""
    origin = _enum_or_raise(Airport, watch["origin"], "Airport")
    destination = _enum_or_raise(Airport, watch["destination"], "Airport")
    seat_type = _enum_or_raise(SeatType, watch.get("seat_class", "ECONOMY"), "SeatType")

    airlines_cfg = watch.get("airlines") or []
    airlines = [_enum_or_raise(Airline, code, "Airline") for code in airlines_cfg] or None

    time_restrictions = None
    earliest = watch.get("earliest_departure_hour")
    latest = watch.get("latest_departure_hour")
    if earliest is not None or latest is not None:
        time_restrictions = TimeRestrictions(
            earliest_departure=earliest,
            latest_departure=latest,
        )

    filters = FlightSearchFilters(
        passenger_info=PassengerInfo(adults=int(watch.get("adults", 1))),
        flight_segments=[
            FlightSegment(
                departure_airport=[[origin, 0]],
                arrival_airport=[[destination, 0]],
                travel_date=watch["date"],
                time_restrictions=time_restrictions,
            )
        ],
        airlines=airlines,
        seat_type=seat_type,
        stops=MaxStops.NON_STOP if watch.get("non_stop") else MaxStops.ANY,
        sort_by=SortBy.CHEAPEST,
    )

    results = SearchFlights().search(filters) or []
    results = [r for r in results if r.price is not None]
    if not results:
        return None

    best = min(results, key=lambda r: r.price)
    first_leg = best.legs[0]
    return BestFlight(
        price=float(best.price),
        currency=best.currency,
        duration_min=int(best.duration),
        airline=first_leg.airline.name,
        flight_number=first_leg.flight_number,
        departure=first_leg.departure_datetime,
        arrival=best.legs[-1].arrival_datetime,
        stops=int(best.stops),
    )
