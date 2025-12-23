import sqlite3
import os
import tempfile
from datetime import datetime

DB = 'flights.db'


def test_db_and_booking_flow():
    # Basic smoke test: DB file exists
    assert os.path.exists(DB)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # pick a flight
    cur.execute("SELECT id, available_seats FROM flights LIMIT 1")
    row = cur.fetchone()
    assert row is not None
    flight_id = row[0]
    before = row[1]

    # insert a booking directly
    pnr = 'TST' + datetime.utcnow().strftime('%H%M%S')
    cur.execute("INSERT INTO bookings (pnr, flight_id, passenger_name, passenger_email, seat_number, status, booked_price, booking_date, payment_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pnr, flight_id, 'Pytest User', 'pytest@example.com', '1A', 'confirmed', 100.0, datetime.utcnow().isoformat(), 'success'))
    conn.commit()

    # confirm booking exists
    cur.execute("SELECT COUNT(*) FROM bookings WHERE pnr = ?", (pnr,))
    assert cur.fetchone()[0] == 1

    # cleanup
    cur.execute("DELETE FROM bookings WHERE pnr = ?", (pnr,))
    conn.commit()
    conn.close()
