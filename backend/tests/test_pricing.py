import sqlite3
from app import compute_dynamic_price, set_demand_for_flight
from datetime import datetime, timedelta


def make_row(base_price=1000, total_seats=100, available_seats=100, departure=None, fid=1):
    if departure is None:
        departure = (datetime.utcnow() + timedelta(days=10)).isoformat()
    return {
        'id': fid,
        'base_price': base_price,
        'total_seats': total_seats,
        'available_seats': available_seats,
        'departure': departure
    }


def test_min_max_price_enforcement():
    row = make_row(base_price=1000, total_seats=100, available_seats=100)
    price = compute_dynamic_price(row)
    assert price >= 800 and price <= 4000


def test_low_seat_multiplier():
    row_full = make_row(base_price=1000, total_seats=100, available_seats=1)
    row_empty = make_row(base_price=1000, total_seats=100, available_seats=100)
    p_full = compute_dynamic_price(row_full)
    p_empty = compute_dynamic_price(row_empty)
    assert p_full >= p_empty


def test_demand_factor_extremes():
    # ensure demand increases price
    # create a temporary demand level in DB for flight id 999
    set_demand_for_flight(999, 2.5)
    row = make_row(base_price=1000, total_seats=100, available_seats=50, fid=999)
    price_high = compute_dynamic_price(row)
    # reset demand lower and compare
    set_demand_for_flight(999, 0.6)
    price_low = compute_dynamic_price(row)
    assert price_high > price_low
