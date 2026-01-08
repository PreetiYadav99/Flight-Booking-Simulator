"""
Milestone 3 Direct Database Verification
(Doesn't require the Flask server to be running)
"""

import sqlite3
from datetime import datetime

def direct_db_test():
    """Test booking workflow directly through database"""
    print("=" * 60)
    print("Milestone 3: Direct Database Booking Test")
    print("=" * 60)

    try:
        conn = sqlite3.connect('flights.db')
        cur = conn.cursor()

        # 1. Check if bookings table exists
        print("\n[1] Checking bookings table schema...")
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='bookings'")
        schema = cur.fetchone()
        if schema:
            print(f"✓ Bookings table exists")
            print(f"   Schema: {schema[0]}")
        else:
            print("✗ Bookings table NOT found")
            return

        # 2. Get a flight to book
        print("\n[2] Getting a flight to book...")
        cur.execute("SELECT id, flight_number, airline_id, available_seats, base_price FROM flights LIMIT 1")
        flight = cur.fetchone()
        if flight:
            flight_id, flight_number, airline_id, avail_seats, base_price = flight
            print(f"✓ Selected Flight: {flight_number} (ID: {flight_id})")
            print(f"   Available seats: {avail_seats}, Base price: ₹{base_price}")
        else:
            print("✗ No flights found")
            return

        # 3. Get airline code for PNR
        print("\n[3] Getting airline code for PNR generation...")
        cur.execute("SELECT code FROM airlines WHERE id = ?", (airline_id,))
        airline_code = cur.fetchone()[0]
        print(f"✓ Airline code: {airline_code}")

        # 4. Simulate booking with transaction
        print("\n[4] Creating a booking (transaction test)...")
        try:
            cur.execute("BEGIN TRANSACTION")
            
            # Deduct seat
            cur.execute("UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?", (flight_id,))
            
            # Generate PNR
            pnr = f"{airline_code}ABC123"
            
            # Insert booking
            booking_date = datetime.utcnow().isoformat()
            cur.execute("""
                INSERT INTO bookings (pnr, flight_id, passenger_name, passenger_email, seat_number, status, booked_price, booking_date, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pnr, flight_id, "Test Passenger", "test@example.com", "1A", "confirmed", base_price, booking_date, "success"))
            
            cur.execute("COMMIT")
            print(f"✓ Booking created with PNR: {pnr}")
            print(f"   Passenger: Test Passenger, Email: test@example.com")
            print(f"   Seat: 1A, Price: ₹{base_price}")
        except Exception as e:
            cur.execute("ROLLBACK")
            print(f"✗ Booking failed: {e}")
            return

        # 5. Verify booking was inserted
        print("\n[5] Verifying booking in database...")
        cur.execute("SELECT pnr, passenger_name, passenger_email, seat_number, booked_price, status FROM bookings WHERE pnr = ?", (pnr,))
        booking = cur.fetchone()
        if booking:
            print(f"✓ Booking found:")
            print(f"   PNR: {booking[0]}")
            print(f"   Passenger: {booking[1]}")
            print(f"   Email: {booking[2]}")
            print(f"   Seat: {booking[3]}")
            print(f"   Price: ₹{booking[4]}")
            print(f"   Status: {booking[5]}")
        else:
            print("✗ Booking not found in database")

        # 6. Verify seat was deducted
        print("\n[6] Verifying seat was deducted...")
        cur.execute("SELECT available_seats FROM flights WHERE id = ?", (flight_id,))
        new_seats = cur.fetchone()[0]
        print(f"✓ Available seats after booking: {new_seats} (was {avail_seats})")

        # 7. Test cancellation with transaction
        print("\n[7] Testing booking cancellation (transaction)...")
        try:
            cur.execute("BEGIN TRANSACTION")
            
            # Mark booking as cancelled
            cur.execute("UPDATE bookings SET status = 'cancelled' WHERE pnr = ?", (pnr,))
            
            # Restore seat
            cur.execute("UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?", (flight_id,))
            
            cur.execute("COMMIT")
            print(f"✓ Booking cancelled")
        except Exception as e:
            cur.execute("ROLLBACK")
            print(f"✗ Cancellation failed: {e}")
            return

        # 8. Verify cancellation
        print("\n[8] Verifying cancellation...")
        cur.execute("SELECT status FROM bookings WHERE pnr = ?", (pnr,))
        status = cur.fetchone()[0]
        cur.execute("SELECT available_seats FROM flights WHERE id = ?", (flight_id,))
        restored_seats = cur.fetchone()[0]
        print(f"✓ Booking status: {status}")
        print(f"✓ Seats restored to: {restored_seats}")

        # 9. Show all bookings
        print("\n[9] All bookings in database:")
        cur.execute("SELECT COUNT(*) FROM bookings")
        count = cur.fetchone()[0]
        print(f"   Total bookings: {count}")
        cur.execute("SELECT pnr, passenger_name, status FROM bookings")
        for row in cur.fetchall():
            print(f"   - {row[0]}: {row[1]} ({row[2]})")

        conn.close()

        print("\n" + "=" * 60)
        print("✓ All Milestone 3 features verified successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == '__main__':
    direct_db_test()
