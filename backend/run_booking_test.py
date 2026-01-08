import requests
import time
import sys

BASE = 'http://127.0.0.1:5000'

def abort(msg):
    print(msg)
    sys.exit(1)

sess = requests.Session()
ts = int(time.time())
email = f'testuser{ts}@example.com'
pw = 'TestPass123!'
name = 'Automated Test'

print('Registering user', email)
r = sess.post(f'{BASE}/register', json={'email': email, 'name': name, 'password': pw})
print('->', r.status_code, r.text)
if r.status_code not in (200,201):
    abort('Register failed')

print('Logging in')
r = sess.post(f'{BASE}/login', json={'email': email, 'password': pw})
print('->', r.status_code, r.text)
if r.status_code != 200:
    abort('Login failed')

print('Fetching flights')
r = sess.get(f'{BASE}/flights')
print('->', r.status_code)
data = r.json() if r.ok else {}
flights = data.get('flights', [])
if not flights:
    abort('No flights found')

flight = flights[0]
fid = flight.get('id')
print('Selected flight', fid, flight.get('flight_number'))

print('Loading seat map')
r = sess.get(f'{BASE}/flights/{fid}/seats')
if not r.ok:
    abort('Failed to load seats')
seats = r.json().get('seats', [])
seat = None
for s in seats:
    if s.get('status') == 'available':
        seat = s.get('seat_number')
        break
if not seat:
    abort('No available seat')
print('Chose seat', seat)

print('Initiating hold')
r = sess.post(f'{BASE}/book/initiate', json={'flight_id': fid, 'seat_number': seat})
print('->', r.status_code, r.text)
if r.status_code != 200:
    abort('Initiate hold failed')
temp = r.json().get('temp_reference')

print('Confirming booking')
payload = {'flight_id': fid, 'seat_number': seat, 'passenger_name': name, 'passenger_email': email, 'temp_reference': temp}
r = sess.post(f'{BASE}/book/confirm', json=payload)
print('->', r.status_code, r.text)
if r.status_code not in (200,201):
    abort('Confirm booking failed')
pnr = r.json().get('pnr')
print('Booking succeeded, PNR=', pnr)

print('Downloading PDF receipt')
r = sess.get(f"{BASE}/bookings/{pnr}/receipt?format=pdf")
print('->', r.status_code, r.headers.get('Content-Type'))
if r.status_code == 200 and r.headers.get('Content-Type','').startswith('application/pdf'):
    with open('booking_receipt.pdf', 'wb') as f:
        f.write(r.content)
    print('Saved booking_receipt.pdf')
else:
    print('Failed to fetch PDF receipt', r.status_code, r.text)

print('Smoke test completed')
