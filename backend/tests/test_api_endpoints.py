import json
from app import app
import db_init


def test_full_api_flow():
    """Reset DB and run a full API smoke test using Flask test client."""
    # Reinitialize database to a known state
    db_init.init_database()

    client = app.test_client()

    # 1) Register (idempotent)
    resp = client.post('/register', json={
        'email': 'tester@example.com',
        'name': 'Tester',
        'password': 'secret'
    })
    assert resp.status_code in (201, 409)

    # 2) Login to obtain session cookie
    resp = client.post('/login', json={'email': 'tester@example.com', 'password': 'secret'})
    assert resp.status_code == 200

    # 3) Basic endpoints
    r = client.get('/')
    assert r.status_code == 200

    r = client.get('/airlines')
    assert r.status_code == 200 and 'airlines' in r.get_json()

    r = client.get('/airports')
    assert r.status_code == 200 and 'airports' in r.get_json()

    r = client.get('/stats')
    assert r.status_code == 200 and 'statistics' in r.get_json()

    # 4) Flights listing and search
    r = client.get('/flights')
    assert r.status_code == 200
    data = r.get_json()
    assert data and data.get('count', 0) > 0
    flight = data['flights'][0]
    flight_id = flight['id']

    # search by origin/destination using sample data values
    r = client.get('/search', query_string={'origin': flight.get('origin_city'), 'destination': flight.get('destination_city')})
    assert r.status_code == 200

    # 5) Flight details, price and seats
    r = client.get(f'/flights/{flight_id}')
    assert r.status_code == 200 and 'flight' in r.get_json()

    r = client.get(f'/flights/{flight_id}/price')
    assert r.status_code == 200 and 'current_price' in r.get_json()

    r = client.get(f'/flights/{flight_id}/seats')
    assert r.status_code == 200 and 'seats' in r.get_json()
    seats = r.get_json()['seats']
    available_seat = None
    for s in seats:
        if s.get('status') == 'available':
            available_seat = s['seat_number']
            break
    assert available_seat is not None

    # 6) External schedules endpoints
    r = client.get('/external/schedules', query_string={'airline': 'SW'})
    assert r.status_code == 200

    r = client.post('/external/push_schedule', json={
        'flight_number': 'SW999',
        'airline_code': 'SW',
        'origin_iata': 'DEL',
        'destination_iata': 'BOM',
        'departure': '2025-12-10T08:00:00',
        'arrival': '2025-12-10T10:00:00'
    })
    assert r.status_code == 200

    # 7) Booking workflow: initiate -> confirm -> receipt -> history -> cancel
    r = client.post('/book/initiate', json={'flight_id': flight_id, 'seat_number': available_seat})
    assert r.status_code == 200
    payload = r.get_json()
    temp_ref = payload.get('temp_reference')

    confirm_payload = {
        'flight_id': flight_id,
        'seat_number': available_seat,
        'passenger_name': 'Tester',
        'passenger_email': 'tester@example.com',
        'temp_reference': temp_ref
    }
    r = client.post('/book/confirm', json=confirm_payload)
    assert r.status_code == 201
    pnr = r.get_json().get('pnr')
    assert pnr

    # fetch booking
    r = client.get(f'/bookings/{pnr}')
    assert r.status_code == 200

    # receipt (json)
    r = client.get(f'/bookings/{pnr}/receipt')
    assert r.status_code == 200

    # history (logged-in user)
    r = client.get('/bookings/history/tester@example.com')
    assert r.status_code == 200 and r.get_json().get('count', 0) >= 1

    # cancel booking
    r = client.delete(f'/bookings/{pnr}')
    assert r.status_code == 200

    # verify cancelled
    r = client.get(f'/bookings/{pnr}')
    assert r.status_code == 200
    booking = r.get_json().get('booking')
    assert booking and booking.get('status') == 'cancelled'
