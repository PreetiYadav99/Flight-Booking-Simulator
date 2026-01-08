"""
Milestone 3 Verification Script
Tests booking workflow: initiate -> confirm -> retrieve -> cancel
"""

import urllib.request
import urllib.error
import json
import sqlite3
import time

BASE = 'http://127.0.0.1:5000'

def post_json(path, payload):
    """POST request with JSON payload"""
    url = BASE + path
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            return resp.getcode(), json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return None, {'error': str(e)}

def get_json(path):
    """GET request"""
    url = BASE + path
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            return resp.getcode(), json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return None, {'error': str(e)}

def delete_json(path):
    """DELETE request"""
    url = BASE + path
    req = urllib.request.Request(url, method='DELETE')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            return resp.getcode(), json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return None, {'error': str(e)}

def db_check():
    """Check bookings table"""
    try:
        conn = sqlite3.connect('flights.db')
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM bookings")
        count = cur.fetchone()[0]
        cur.execute("SELECT pnr, passenger_name, passenger_email, status FROM bookings ORDER BY booking_date DESC LIMIT 5")
        recent = cur.fetchall()
        conn.close()
        return {'bookings_count': count, 'recent_bookings': recent}
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=" * 50)
    print("Milestone 3: Booking Workflow Verification")
    print("=" * 50)

    # Get first flight (for booking)
    code, flights = get_json('/flights')
    if code != 200 or not flights.get('flights'):
        print("ERROR: Could not fetch flights")
        return
    
    flight = flights['flights'][0]
    flight_id = flight['id']
    print(f"\nTest Flight: {flight['flight_number']} (ID: {flight_id})")
    print(f"Available Seats: {flight['available_seats']}")

    # Step 1: Initiate booking
    print("\n[1] Initiating booking...")
    code, resp = post_json('/book/initiate', {
        'flight_id': flight_id,
        'seat_number': '1A'
    })
    print(f"Status: {code}")
    if code == 200:
        print(f"Price: ₹{resp['current_price']}")
        print(f"Temp Ref: {resp['temp_reference']}")
    else:
        print(f"Error: {resp}")
        return

    # Step 2: Confirm booking
    print("\n[2] Confirming booking with passenger info...")
    code, resp = post_json('/book/confirm', {
        'flight_id': flight_id,
        'seat_number': '1A',
        'passenger_name': 'John Doe',
        'passenger_email': 'john@example.com'
    })
    print(f"Status: {code}")
    if code == 201:
        pnr = resp['booking_details'].get('pnr') or resp.get('pnr')
        print(f"PNR: {pnr}")
        print(f"Booked Price: ₹{resp['booking_details']['booked_price']}")
        booking_pnr = pnr
    else:
        print(f"Error: {resp}")
        return

    # Step 3: Retrieve booking
    print("\n[3] Retrieving booking by PNR...")
    code, resp = get_json(f'/bookings/{booking_pnr}')
    print(f"Status: {code}")
    if code == 200:
        booking = resp['booking']
        print(f"Passenger: {booking['passenger_name']}")
        print(f"Seat: {booking['seat_number']}")
        print(f"Status: {booking['status']}")
    else:
        print(f"Error: {resp}")

    # Step 4: Get booking history
    print("\n[4] Retrieving booking history by email...")
    code, resp = get_json('/bookings/history/john@example.com')
    print(f"Status: {code}")
    if code == 200:
        print(f"Bookings found: {resp['count']}")
        for b in resp['bookings']:
            print(f"  - {b['pnr']}: {b['flight_number']} ({b['status']})")
    else:
        print(f"Error: {resp}")

    # Step 5: Cancel booking
    print(f"\n[5] Cancelling booking {booking_pnr}...")
    code, resp = delete_json(f'/bookings/{booking_pnr}')
    print(f"Status: {code}")
    if code == 200:
        print(f"Message: {resp['message']}")
    else:
        print(f"Error: {resp}")

    # Step 6: DB check
    print("\n[6] Database Check...")
    db_stats = db_check()
    print(f"Total bookings in DB: {db_stats.get('bookings_count', 'N/A')}")
    print("Recent bookings:")
    for b in db_stats.get('recent_bookings', []):
        print(f"  - {b[0]}: {b[1]} ({b[3]})")

    print("\n" + "=" * 50)
    print("Verification complete")
    print("=" * 50)

if __name__ == '__main__':
    main()
