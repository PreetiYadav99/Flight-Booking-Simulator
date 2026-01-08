import threading
import sqlite3
import time
from datetime import datetime

DB = 'flights.db'


def booking_worker(flight_id, results, idx):
    try:
        conn = sqlite3.connect(DB, timeout=5)
        cur = conn.cursor()
        cur.execute('BEGIN TRANSACTION')
        # cleanup expired holds
        now_iso = datetime.utcnow().isoformat()
        try:
            cur.execute("DELETE FROM seat_holds WHERE expires_at <= ?", (now_iso,))
        except Exception:
            pass
        cur.execute("SELECT available_seats FROM flights WHERE id = ?", (flight_id,))
        row = cur.fetchone()
        if not row or row[0] <= 0:
            cur.execute('ROLLBACK')
            results[idx] = False
            conn.close()
            return
        cur.execute("UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?", (flight_id,))
        # insert a simple booking record
        pnr = f"TC{int(time.time()*1000)}{idx}"
        booking_date = datetime.utcnow().isoformat()
        cur.execute(
            "INSERT INTO bookings (pnr, flight_id, passenger_name, passenger_email, seat_number, status, booked_price, booking_date, payment_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (pnr, flight_id, f'Test{idx}', f'test{idx}@example.com', f'{idx}A', 'confirmed', 100.0, booking_date, 'success')
        )
        cur.execute('COMMIT')
        results[idx] = True
        conn.close()
    except Exception:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        results[idx] = False


def test_concurrent_bookings():
    # pick a flight with at least 1 seats; create a small-seat test flight if necessary
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, available_seats FROM flights LIMIT 1")
    row = cur.fetchone()
    if not row:
        raise AssertionError('No flights in DB')
    flight_id = row[0]

    # set available seats to 3 for test
    cur.execute("UPDATE flights SET available_seats = ? WHERE id = ?", (3, flight_id))
    conn.commit()
    conn.close()

    threads = []
    results = [False] * 6
    # start 6 threads attempting to book 3 seats
    for i in range(6):
        t = threading.Thread(target=booking_worker, args=(flight_id, results, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # count successes == 3
    success_count = sum(1 for r in results if r)
    assert success_count == 3
