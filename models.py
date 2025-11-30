"""
Data models for Flight Booking Simulator
Defines the structure of flights, airlines, and airports
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Airline:
    """Represents an airline operating flights"""
    id: int
    name: str
    code: str

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code
        }


@dataclass
class Airport:
    """Represents an airport with location information"""
    id: int
    name: str
    city: str
    country: str
    iata_code: str

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "country": self.country,
            "iata_code": self.iata_code
        }


@dataclass
class Flight:
    """Represents a flight with comprehensive booking information"""
    id: int
    flight_number: str
    airline_id: int
    origin_id: int
    destination_id: int
    departure: datetime
    arrival: datetime
    base_price: float
    total_seats: int
    available_seats: int
    duration_mins: int
    airline_name: Optional[str] = None
    airline_code: Optional[str] = None
    origin_city: Optional[str] = None
    origin_airport: Optional[str] = None
    origin_iata: Optional[str] = None
    destination_city: Optional[str] = None
    destination_airport: Optional[str] = None
    destination_iata: Optional[str] = None

    def to_dict(self):
        return {
            "id": self.id,
            "flight_number": self.flight_number,
            "airline_id": self.airline_id,
            "airline_name": self.airline_name,
            "airline_code": self.airline_code,
            "origin_id": self.origin_id,
            "origin_city": self.origin_city,
            "origin_airport": self.origin_airport,
            "origin_iata": self.origin_iata,
            "destination_id": self.destination_id,
            "destination_city": self.destination_city,
            "destination_airport": self.destination_airport,
            "destination_iata": self.destination_iata,
            "departure": self.departure,
            "arrival": self.arrival,
            "base_price": self.base_price,
            "total_seats": self.total_seats,
            "available_seats": self.available_seats,
            "occupied_seats": self.total_seats - self.available_seats,
            "occupancy_rate": round((self.total_seats - self.available_seats) / self.total_seats * 100, 2),
            "duration_mins": self.duration_mins
        }

    @property
    def occupancy_percentage(self):
        """Calculate occupancy rate"""
        if self.total_seats == 0:
            return 0
        return round((self.total_seats - self.available_seats) / self.total_seats * 100, 2)

    @property
    def has_seats(self):
        """Check if seats are available"""
        return self.available_seats > 0
