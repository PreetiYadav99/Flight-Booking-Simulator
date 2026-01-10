from flask import Flask, request, jsonify, make_response, session
try:
    from flask_cors import CORS
except Exception:
    CORS = None
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
import os
import sqlite3
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timezone, timedelta
from io import BytesIO
import random
import threading
import time
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
# Secret for session cookies (override with SECRET_KEY env var in production)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
# Allow cookies from cross-origin frontend during local development
# Set SameSite=None so browsers send the cookie on cross-site requests from the frontend
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'None')
# In local/dev we don't require secure cookie (set to True in production)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
app.config['SESSION_COOKIE_HTTPONLY'] = True
if CORS:
    # Restrict CORS to the local frontend origins and allow credentials (cookies)
    allowed_origins = [
        os.environ.get('FRONTEND_ORIGIN', 'http://127.0.0.1:5500'),
        'http://localhost:5500',
        # Vite dev server defaults (common local dev ports)
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        # Additional Vite dev ports (automatic increment)
        'http://localhost:5174',
        'http://127.0.0.1:5174',
        'http://localhost:5175',
        'http://127.0.0.1:5175',
        'http://localhost:5176',
        'http://127.0.0.1:5176',
        'http://localhost:5177',
        'http://127.0.0.1:5177',
        'http://localhost:5178',
        'http://127.0.0.1:5178',
        'http://localhost:3000',
        'http://127.0.0.1:3000'
    ]
    CORS(app, supports_credentials=True, origins=allowed_origins)
else:
    # Provide a minimal CORS fallback when flask_cors isn't installed.
    # This allows the frontend dev server to communicate with the API
    # when running in a different origin (Vite localhost ports).
    allowed_origins = [
        os.environ.get('FRONTEND_ORIGIN', 'http://127.0.0.1:5500'),
        'http://localhost:5500',
        'http://localhost:5173', 'http://127.0.0.1:5173',
        'http://localhost:5174', 'http://127.0.0.1:5174',
        'http://localhost:5175', 'http://127.0.0.1:5175',
        'http://localhost:5176', 'http://127.0.0.1:5176',
        'http://localhost:5177', 'http://127.0.0.1:5177',
        'http://localhost:5178', 'http://127.0.0.1:5178',
        'http://localhost:3000', 'http://127.0.0.1:3000'
    ]

    @app.after_request
    def _cors_fallback(response):
        origin = request.headers.get('Origin')
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        return response
DB = "flights.db"


def query_db(query, args=()):
    """Execute database query and return results as list of dictionaries"""
    try:
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(query, args)
        result = [dict(row) for row in cur.fetchall()]
        conn.close()
        return result
    except sqlite3.Error as e:
        raise Exception(f"Database error: {str(e)}")


def execute_db(query, args=()):
    """Execute a write query and commit."""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {str(e)}")


def error_handler(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({"error": str(e), "status": "error"}), 400
        except Exception as e:
            return jsonify({"error": str(e), "status": "error"}), 500
    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({"error": "Authentication required", "status": "error"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['POST'])
def login():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "JSON payload required", "status": "error"}), 400
    # DEBUG: print incoming payload (mask password)
    try:
        pcopy = dict(payload)
        if 'password' in pcopy:
            pcopy['password'] = '***MASKED***'
        print(f"[DEBUG] /login payload: {pcopy}")
    except Exception:
        print("[DEBUG] /login received non-json payload")

    # normalize incoming email to avoid whitespace/case mismatch
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password')
    print(f"[DEBUG] /login normalized_email='{email}'")
    if not email or not password:
        return jsonify({"error": "email and password required", "status": "error"}), 400

    user = query_db("SELECT id, email, name, password_hash, is_admin FROM users WHERE email = ?", (email,))
    if not user:
        return jsonify({"error": "Invalid credentials", "status": "error"}), 401
    else:
        print(f"[DEBUG] /login found_user id={user[0].get('id')} email={user[0].get('email')}")
    u = user[0]
    if not check_password_hash(u.get('password_hash',''), password):
        return jsonify({"error": "Invalid credentials", "status": "error"}), 401

    # set session
    session['user_id'] = u.get('id')
    session['email'] = u.get('email')
    session['name'] = u.get('name')
    session['is_admin'] = bool(u.get('is_admin'))

    return jsonify({"status": "success", "email": session['email'], "name": session.get('name')}), 200


@app.route('/register', methods=['POST'])
@error_handler
def register():
    """Register a new user. Request JSON: { email, name, password }
    Returns 201 on success, 400 for validation errors, 409 if user exists."""
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "JSON payload required", "status": "error"}), 400

    # DEBUG: print incoming payload (mask password)
    try:
        pcopy = dict(payload)
        if 'password' in pcopy:
            pcopy['password'] = '***MASKED***'
        print(f"[DEBUG] /register payload: {pcopy}")
    except Exception:
        print("[DEBUG] /register received non-json payload")

    # normalize email to a canonical form
    email = (payload.get('email') or '').strip().lower()
    name = (payload.get('name') or '').strip()
    password = payload.get('password')
    print(f"[DEBUG] /register normalized_email='{email}' name='{name}'")

    if not email or not password:
        return jsonify({"error": "email and password required", "status": "error"}), 400

    # check existing
    existing = query_db("SELECT id, email, name FROM users WHERE email = ?", (email,))
    if existing:
        print(f"[DEBUG] /register found existing user: {existing}")
        return jsonify({"error": "User already exists", "status": "error"}), 409

    pw_hash = generate_password_hash(password)
    try:
        execute_db("INSERT INTO users (email, name, password_hash, is_admin) VALUES (?, ?, ?, ?)", (email, name, pw_hash, 0))
    except Exception as e:
        return jsonify({"error": f"Failed to create user: {str(e)}", "status": "error"}), 500

    # Enqueue registration email for background delivery
    try:
        subject = 'Welcome to Flight Booking Simulator'
        body = f"Hello {name or ''},\n\nThank you for registering at Flight Booking Simulator. We're glad to have you on board.\n\nBest regards,\nFlightSim Team"
        enqueue_email(email, subject, body)
        queued = True
    except Exception as e:
        queued = False
        print(f"[DEBUG] enqueue_email error: {e}")

    return jsonify({"status": "created", "email": email, "name": name, "email_queued": bool(queued)}), 201


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"}), 200


@app.route('/me', methods=['GET'])
def me():
    """Return current session user info if logged in, else anonymous."""
    if session.get('user_id'):
        return jsonify({
            "status": "success",
            "user": {
                "id": session.get('user_id'),
                "email": session.get('email'),
                "name": session.get('name'),
                "is_admin": bool(session.get('is_admin'))
            }
        }), 200
    return jsonify({"status": "anonymous", "user": None}), 200


# ============= API ENDPOINTS =============

@app.route('/', methods=['GET'])
def home():
    """Root endpoint - API documentation"""
    return jsonify({
        "name": "Flight Booking Simulator API",
        "version": "1.0",
        "description": "Milestone 1: Core Flight Search & Data Management",
        "endpoints": {
            "GET /": "API documentation",
            "GET /flights": "Get all available flights",
            "GET /search": "Search flights with filters",
            "GET /flights/<id>": "Get flight details by ID",
            "GET /airlines": "Get all airlines",
            "GET /airports": "Get all airports",
            "GET /stats": "Get flight statistics"
        },
        "search_parameters": {
            "origin": "City name or IATA code (e.g., 'Delhi' or 'DEL')",
            "destination": "City name or IATA code",
            "date": "Departure date (YYYY-MM-DD)",
            "sort": "Sort results by 'price' or 'duration'",
            "min_price": "Minimum price filter",
            "max_price": "Maximum price filter",
            "min_seats": "Minimum available seats"
        }
    })


@app.route('/flights', methods=['GET'])
@error_handler
def all_flights():
    """Get all available flights with basic info"""
    try:
        query = """
            SELECT f.id, f.flight_number, a.name AS airline_name, a.code AS airline_code,
                   o.city AS origin_city, o.iata_code AS origin_iata,
                   d.city AS destination_city, d.iata_code AS destination_iata,
                   f.departure, f.arrival, f.base_price, f.total_seats, 
                   f.available_seats, f.duration_mins
            FROM flights f
            JOIN airlines a ON f.airline_id = a.id
            JOIN airports o ON f.origin_id = o.id
            JOIN airports d ON f.destination_id = d.id
            ORDER BY f.departure ASC
        """
        data = query_db(query)
        
        # Attach dynamic pricing to each flight
        for f in data:
            try:
                f['current_price'] = compute_dynamic_price(f)
                f['demand_level'] = get_demand_for_flight(int(f.get('id')))
            except Exception:
                f['current_price'] = f.get('base_price')
                f['demand_level'] = 1.0

        if not data:
            return jsonify({"message": "No flights found", "flights": []}), 200
        
        return jsonify({
            "status": "success",
            "count": len(data),
            "flights": data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route('/flights/<int:flight_id>', methods=['GET'])
@error_handler
def flight_details(flight_id):
    """Get detailed information about a specific flight"""
    query = """
        SELECT f.*, a.name AS airline_name, a.code AS airline_code,
               o.name AS origin_airport, o.city AS origin_city, o.iata_code AS origin_iata,
               o.country AS origin_country,
               d.name AS destination_airport, d.city AS destination_city, 
               d.iata_code AS destination_iata, d.country AS destination_country
        FROM flights f
        JOIN airlines a ON f.airline_id = a.id
        JOIN airports o ON f.origin_id = o.id
        JOIN airports d ON f.destination_id = d.id
        WHERE f.id = ?
    """
    data = query_db(query, (flight_id,))
    
    if not data:
        return jsonify({"error": f"Flight {flight_id} not found", "status": "error"}), 404
    
    flight = data[0]
    occupied = flight['total_seats'] - flight['available_seats']
    occupancy_rate = (occupied / flight['total_seats'] * 100) if flight['total_seats'] > 0 else 0
    # compute dynamic price and include demand
    try:
        flight['current_price'] = compute_dynamic_price(flight)
        flight['demand_level'] = get_demand_for_flight(int(flight.get('id')))
    except Exception:
        flight['current_price'] = flight.get('base_price')
        flight['demand_level'] = 1.0

    return jsonify({
        "status": "success",
        "flight": {
            **flight,
            "occupied_seats": occupied,
            "occupancy_rate": round(occupancy_rate, 2),
            "booking_status": "available" if flight['available_seats'] > 0 else "full"
        }
    }), 200


@app.route('/search', methods=['GET'])
@error_handler
def search_flights():
    """Search flights with multiple filter options"""
    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    date = request.args.get('date', '').strip()
    sort = request.args.get('sort', 'departure').strip().lower()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_seats = request.args.get('min_seats', type=int)
    
    # Validate inputs
    if not origin or not destination:
        return jsonify({
            "error": "Both 'origin' and 'destination' parameters are required",
            "status": "error"
        }), 400
    
    if date:
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                "error": "Date must be in YYYY-MM-DD format",
                "status": "error"
            }), 400
    
    if sort not in ['departure', 'price', 'duration', 'available_seats']:
        return jsonify({
            "error": "Sort must be one of: departure, price, duration, available_seats",
            "status": "error"
        }), 400
    
    # Build query
    query = """
        SELECT f.id, f.flight_number, a.name AS airline_name, a.code AS airline_code,
               o.city AS origin_city, o.iata_code AS origin_iata,
               d.city AS destination_city, d.iata_code AS destination_iata,
               f.departure, f.arrival, f.base_price, f.total_seats, 
               f.available_seats, f.duration_mins
        FROM flights f
        JOIN airlines a ON f.airline_id = a.id
        JOIN airports o ON f.origin_id = o.id
        JOIN airports d ON f.destination_id = d.id
        WHERE 1=1
    """
    params = []
    
    # Add origin filter
    query += " AND (o.iata_code = ? OR o.city = ?)"
    params.extend([origin.upper(), origin])
    
    # Add destination filter
    query += " AND (d.iata_code = ? OR d.city = ?)"
    params.extend([destination.upper(), destination])
    
    # Add date filter
    if date:
        query += " AND date(f.departure) = ?"
        params.append(date)
    
    # Add price filters
    if min_price is not None:
        query += " AND f.base_price >= ?"
        params.append(min_price)
    
    if max_price is not None:
        query += " AND f.base_price <= ?"
        params.append(max_price)
    
    # Add seats filter
    if min_seats is not None:
        query += " AND f.available_seats >= ?"
        params.append(min_seats)
    
    # Add sorting
    sort_mapping = {
        'departure': 'f.departure ASC',
        'price': 'f.base_price ASC',
        'duration': 'f.duration_mins ASC',
        'available_seats': 'f.available_seats DESC'
    }
    query += f" ORDER BY {sort_mapping[sort]}"
    
    data = query_db(query, tuple(params))
    
    if not data:
        return jsonify({
            "status": "success",
            "count": 0,
            "message": "No flights found matching your criteria",
            "flights": []
        }), 200
    # attach dynamic pricing
    for f in data:
        try:
            f['current_price'] = compute_dynamic_price(f)
            f['demand_level'] = get_demand_for_flight(int(f.get('id')))
        except Exception:
            f['current_price'] = f.get('base_price')
            f['demand_level'] = 1.0

    return jsonify({
        "status": "success",
        "search_criteria": {
            "origin": origin,
            "destination": destination,
            "date": date if date else "Any date",
            "sort": sort
        },
        "count": len(data),
        "flights": data
    }), 200


@app.route('/airlines', methods=['GET'])
@error_handler
def get_airlines():
    """Get all airlines"""
    query = "SELECT id, name, code FROM airlines ORDER BY name ASC"
    data = query_db(query)
    
    return jsonify({
        "status": "success",
        "count": len(data),
        "airlines": data
    }), 200


@app.route('/airports', methods=['GET'])
@error_handler
def get_airports():
    """Get all airports"""
    query = "SELECT id, name, city, country, iata_code FROM airports ORDER BY city ASC"
    data = query_db(query)
    
    return jsonify({
        "status": "success",
        "count": len(data),
        "airports": data
    }), 200


@app.route('/flights/<int:flight_id>/price', methods=['GET'])
@error_handler
def flight_price(flight_id):
    """Return current dynamic price for a specific flight id."""
    row = query_db("SELECT id, base_price, total_seats, available_seats, departure FROM flights WHERE id = ?", (flight_id,))
    if not row:
        return jsonify({"error": "Flight not found", "status": "error"}), 404
    price = compute_dynamic_price(row[0])
    return jsonify({"status": "success", "flight_id": flight_id, "current_price": price}), 200


@app.route('/flights/<int:flight_id>/seats', methods=['GET'])
@error_handler
def flight_seats(flight_id):
    """Return a generated seat map for a flight with seat statuses: available, booked, held."""
    # fetch flight to get total_seats
    flights = query_db("SELECT id, total_seats FROM flights WHERE id = ?", (flight_id,))
    if not flights:
        return jsonify({"error": "Flight not found", "status": "error"}), 404
    total_seats = int(flights[0].get('total_seats') or 0)

    # generate seat numbers (6 seats per row: A-F)
    letters = ['A','B','C','D','E','F']
    seats = []
    for i in range(1, total_seats + 1):
        row = (i - 1) // 6 + 1
        col = (i - 1) % 6
        seats.append(f"{row}{letters[col]}")

    # booked seats
    booked_rows = query_db("SELECT seat_number FROM bookings WHERE flight_id = ? AND status != 'cancelled'", (flight_id,))
    booked = set([r['seat_number'] for r in booked_rows if r.get('seat_number')])

    # held seats (not expired)
    now_iso = datetime.utcnow().isoformat()
    held_rows = query_db("SELECT seat_number, temp_ref, expires_at FROM seat_holds WHERE flight_id = ?", (flight_id,))
    held = {}
    for r in held_rows:
        seat = r.get('seat_number')
        exp = r.get('expires_at')
        if seat and exp and exp > now_iso:
            held[seat] = {"temp_ref": r.get('temp_ref'), "expires_at": exp}

    seat_map = []
    for s in seats:
        status = 'available'
        meta = {}
        if s in booked:
            status = 'booked'
        elif s in held:
            status = 'held'
            meta = held[s]
        seat_map.append({"seat_number": s, "status": status, **meta})

    return jsonify({"status": "success", "flight_id": flight_id, "seats": seat_map}), 200


@app.route('/stats', methods=['GET'])
@error_handler
def get_stats():
    """Get flight statistics and system overview"""
    stats = {}
    
    # Total flights
    total = query_db("SELECT COUNT(*) as count FROM flights")
    stats['total_flights'] = total[0]['count'] if total else 0
    
    # Total seats
    seats = query_db("SELECT SUM(total_seats) as total, SUM(available_seats) as available FROM flights")
    if seats:
        stats['total_seats'] = seats[0]['total'] or 0
        stats['available_seats'] = seats[0]['available'] or 0
        stats['occupied_seats'] = (stats['total_seats'] - stats['available_seats']) if stats['total_seats'] > 0 else 0
        stats['occupancy_rate'] = round((stats['occupied_seats'] / stats['total_seats'] * 100), 2) if stats['total_seats'] > 0 else 0
    
    # Airlines count
    airlines = query_db("SELECT COUNT(*) as count FROM airlines")
    stats['total_airlines'] = airlines[0]['count'] if airlines else 0
    
    # Airports count
    airports = query_db("SELECT COUNT(*) as count FROM airports")
    stats['total_airports'] = airports[0]['count'] if airports else 0
    
    # Price range
    prices = query_db("SELECT MIN(base_price) as min, MAX(base_price) as max, AVG(base_price) as avg FROM flights")
    if prices:
        stats['price_range'] = {
            'minimum': round(prices[0]['min'], 2) if prices[0]['min'] else 0,
            'maximum': round(prices[0]['max'], 2) if prices[0]['max'] else 0,
            'average': round(prices[0]['avg'], 2) if prices[0]['avg'] else 0
        }
    
    return jsonify({
        "status": "success",
        "statistics": stats
    }), 200


@app.route('/admin/demand', methods=['POST'])
@login_required
@error_handler
def admin_set_demand():
    """Admin-only endpoint to set demand level for a flight.
    Request JSON: { "flight_id": int, "demand_level": float }
    """
    # ensure admin
    if not session.get('is_admin'):
        return jsonify({"error": "Admin privileges required", "status": "error"}), 403

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "JSON payload required", "status": "error"}), 400

    flight_id = payload.get('flight_id')
    demand_level = payload.get('demand_level')

    try:
        flight_id = int(flight_id)
    except Exception:
        return jsonify({"error": "Valid 'flight_id' required", "status": "error"}), 400

    try:
        demand_level = float(demand_level)
    except Exception:
        return jsonify({"error": "Valid 'demand_level' required", "status": "error"}), 400

    # clamp demand to safe range
    if demand_level < 0.1 or demand_level > 10.0:
        return jsonify({"error": "'demand_level' must be between 0.1 and 10.0", "status": "error"}), 400

    # ensure flight exists
    exists = query_db("SELECT id FROM flights WHERE id = ?", (flight_id,))
    if not exists:
        return jsonify({"error": f"Flight {flight_id} not found", "status": "error"}), 404

    # set demand and return current computed price for convenience
    set_demand_for_flight(flight_id, demand_level)
    # fetch updated flight and compute price
    row = query_db("SELECT id, base_price, total_seats, available_seats, departure FROM flights WHERE id = ?", (flight_id,))
    price = None
    if row:
        price = compute_dynamic_price(row[0])

    return jsonify({"status": "success", "flight_id": flight_id, "demand_level": demand_level, "current_price": price}), 200


@app.route('/admin/email-queue', methods=['GET'])
@login_required
@error_handler
def admin_email_queue():
    """Admin endpoint to list queued emails."""
    if not session.get('is_admin'):
        return jsonify({"error": "Admin privileges required", "status": "error"}), 403
    rows = query_db("SELECT id, to_email, subject, created_at, sent_at, status, attempts, last_error FROM email_queue ORDER BY created_at DESC LIMIT 500")
    return jsonify({"status": "success", "count": len(rows), "emails": rows}), 200


@app.route('/admin/email-queue/<int:email_id>/retry', methods=['POST'])
@login_required
@error_handler
def admin_email_queue_retry(email_id):
    """Admin endpoint to immediately retry sending a queued email."""
    if not session.get('is_admin'):
        return jsonify({"error": "Admin privileges required", "status": "error"}), 403
    row = query_db("SELECT * FROM email_queue WHERE id = ?", (email_id,))
    if not row:
        return jsonify({"error": "Email not found", "status": "error"}), 404
    r = row[0]
    # attempt immediate send
    ok = send_email_message(r.get('to_email'), r.get('subject'), r.get('body'))
    now = datetime.utcnow().isoformat()
    if ok:
        execute_db("UPDATE email_queue SET status = 'sent', sent_at = ?, attempts = attempts + 1 WHERE id = ?", (now, email_id))
        return jsonify({"status": "success", "email_id": email_id, "sent": True}), 200
    else:
        execute_db("UPDATE email_queue SET attempts = attempts + 1, last_error = ? WHERE id = ?", ("manual_retry_failed", email_id))
        return jsonify({"status": "error", "email_id": email_id, "sent": False}), 500


@app.route('/send-email', methods=['POST'])
@login_required
@error_handler
def send_email():
    """User-facing endpoint to enqueue an email for delivery.
    Request JSON: { to_email?: str, subject: str, body: str }
    If `to_email` omitted, uses session email.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "JSON payload required", "status": "error"}), 400

    to_email = (payload.get('to_email') or session.get('email') or '').strip().lower()
    subject = payload.get('subject') or 'Message from FlightSim'
    body = payload.get('body') or ''

    if not to_email:
        return jsonify({"error": "to_email required or user must be logged in", "status": "error"}), 400

    try:
        enqueue_email(to_email, subject, body)
        return jsonify({"status": "enqueued", "to_email": to_email}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to enqueue: {e}", "status": "error"}), 500



# ============= Dynamic Pricing Engine =============


def setup_dynamic_tables():
    """Ensure required tables for dynamic pricing exist."""
    extra_sql = """
    CREATE TABLE IF NOT EXISTS demand_levels (
        flight_id INTEGER PRIMARY KEY,
        demand_level REAL NOT NULL DEFAULT 1.0,
        last_updated TEXT
    );

    CREATE TABLE IF NOT EXISTS fare_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        old_price REAL,
        new_price REAL,
        demand_level REAL,
        available_seats INTEGER
    );

    CREATE TABLE IF NOT EXISTS seat_holds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INTEGER NOT NULL,
        seat_number TEXT NOT NULL,
        temp_ref TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        expires_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS email_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        sent_at TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT
    );
    """
    try:
        conn = sqlite3.connect(DB)
        conn.executescript(extra_sql)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Failed to ensure dynamic tables: {e}")


def get_demand_for_flight(flight_id):
    res = query_db("SELECT demand_level FROM demand_levels WHERE flight_id = ?", (flight_id,))
    if res:
        return float(res[0]['demand_level'])
    return 1.0


def cleanup_expired_holds():
    """Remove expired seat holds."""
    try:
        now = datetime.utcnow().isoformat()
        execute_db("DELETE FROM seat_holds WHERE expires_at <= ?", (now,))
    except Exception:
        pass


def create_seat_hold(flight_id, seat_number, temp_ref, expires_at_iso):
    execute_db(
        "INSERT OR REPLACE INTO seat_holds (flight_id, seat_number, temp_ref, expires_at) VALUES (?, ?, ?, ?)",
        (flight_id, seat_number, temp_ref, expires_at_iso)
    )


def get_hold_by_tempref(temp_ref):
    res = query_db("SELECT * FROM seat_holds WHERE temp_ref = ?", (temp_ref,))
    return res[0] if res else None


def delete_hold(temp_ref):
    try:
        execute_db("DELETE FROM seat_holds WHERE temp_ref = ?", (temp_ref,))
    except Exception:
        pass


def set_demand_for_flight(flight_id, demand_level):
    now = datetime.utcnow().isoformat()
    execute_db("INSERT OR REPLACE INTO demand_levels (flight_id, demand_level, last_updated) VALUES (?, ?, ?)", (flight_id, demand_level, now))


def record_fare_history(flight_id, old_price, new_price, demand_level, available_seats):
    now = datetime.utcnow().isoformat()
    execute_db(
        "INSERT INTO fare_history (flight_id, timestamp, old_price, new_price, demand_level, available_seats) VALUES (?, ?, ?, ?, ?, ?)",
        (flight_id, now, old_price, new_price, demand_level, available_seats)
    )


def compute_dynamic_price(flight_row):
    """Compute a dynamic price for a flight row (dict) using base fare, seats, time to departure, demand."""
    try:
        base = float(flight_row.get('base_price', 0) or 0)
        total_seats = int(flight_row.get('total_seats', 0) or 0)
        available = int(flight_row.get('available_seats', 0) or 0)
        remaining_pct = (available / total_seats) if total_seats > 0 else 0

        # parse departure
        dep_raw = flight_row.get('departure')
        try:
            dep_dt = datetime.fromisoformat(dep_raw)
        except Exception:
            dep_dt = datetime.utcnow()

        # time until departure in days
        delta_days = max((dep_dt - datetime.utcnow()).total_seconds() / 86400.0, 0.001)

        # demand level from DB
        flight_id = int(flight_row.get('id')) if flight_row.get('id') else None
        demand = get_demand_for_flight(flight_id) if flight_id else 1.0

        # Pricing factors (tunable)
        # - low remaining seats => higher multiplier
        seat_factor = 1 + (1 - remaining_pct) * 0.6
        # - time to departure: prices increase as departure nears
        time_factor = 1 + max(0.0, (30 - min(delta_days, 30)) / 30) * 0.4
        # - demand factor: >1 increases price
        demand_factor = 1 + (demand - 1) * 0.5

        multiplier = seat_factor * time_factor * demand_factor

        # Enforce pricing tiers (min 80% of base, max 400% of base)
        new_price = round(base * multiplier, 2)
        min_price = round(base * 0.8, 2)
        max_price = round(base * 4.0, 2)
        new_price = max(min_price, min(new_price, max_price))

        return new_price
    except Exception as e:
        return float(flight_row.get('base_price', 0) or 0)


def send_registration_email(to_email, name=None):
    """Send a simple confirmation email to newly registered users.
    SMTP settings are read from environment variables:
      - SMTP_HOST (required to send), SMTP_PORT (default 587)
      - SMTP_USER, SMTP_PASS (optional, for auth)
      - EMAIL_FROM (defaults to SMTP_USER or no-reply@localhost)
    This is best-effort and will return False on failure.
    """
    host = os.environ.get('SMTP_HOST')
    if not host:
        print('[INFO] SMTP_HOST not configured; skipping email send')
        return False

    port = int(os.environ.get('SMTP_PORT', 587))
    user = os.environ.get('SMTP_USER')
    password = os.environ.get('SMTP_PASS')
    sender = os.environ.get('EMAIL_FROM') or user or 'no-reply@flightsim.local'

    subject = 'Welcome to Flight Booking Simulator'
    body = f"Hello {name or ''},\n\nThank you for registering at Flight Booking Simulator. We're glad to have you on board.\n\nBest regards,\nFlightSim Team"

    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                try:
                    server.starttls()
                except Exception:
                    pass
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        print(f"[INFO] Sent registration email to {to_email}")
        return True
    except Exception as e:
        print(f"[WARN] Failed to send registration email to {to_email}: {e}")
        return False


def send_email_message(to_email, subject, body):
    """Generic email sending helper used by the background worker."""
    host = os.environ.get('SMTP_HOST')
    if not host:
        print('[INFO] SMTP_HOST not configured; skipping email send')
        return False

    port = int(os.environ.get('SMTP_PORT', 587))
    user = os.environ.get('SMTP_USER')
    password = os.environ.get('SMTP_PASS')
    sender = os.environ.get('EMAIL_FROM') or user or 'no-reply@flightsim.local'

    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                try:
                    server.starttls()
                except Exception:
                    pass
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        print(f"[INFO] Sent email to {to_email}")
        return True
    except Exception as e:
        print(f"[WARN] Failed to send email to {to_email}: {e}")
        return False


# Background simulation worker
_simulation_thread = None
_stop_simulation = threading.Event()


def simulation_worker(interval_seconds=30):
    """Periodically adjust demand levels and simulate bookings.
    - Randomly picks flights, adjusts demand_level slightly
    - Occasionally decrements available_seats to simulate bookings
    - Records fare_history when price changes notably
    """
    print("Dynamic pricing simulation worker started")
    while not _stop_simulation.is_set():
        try:
            # Fetch some flights
            rows = query_db("SELECT id, base_price, total_seats, available_seats, departure FROM flights ORDER BY RANDOM() LIMIT 10")
            for r in rows:
                fid = int(r['id'])
                # random demand tweak between -0.2 and +0.5
                current = get_demand_for_flight(fid)
                tweak = random.uniform(-0.15, 0.5)
                new_demand = max(0.5, round(current + tweak, 2))
                set_demand_for_flight(fid, new_demand)

                # maybe simulate a booking (10% chance)
                if random.random() < 0.10 and int(r['available_seats']) > 0:
                    # decrement available_seats by 1-3
                    dec = random.randint(1, min(3, int(r['available_seats'])))
                    try:
                        execute_db("UPDATE flights SET available_seats = available_seats - ? WHERE id = ?", (dec, fid))
                    except Exception:
                        pass

                # compute price before/after and record if significant change
                try:
                    before_price = compute_dynamic_price(r)
                except Exception:
                    before_price = float(r.get('base_price') or 0)
                # fetch latest flight after potential seat change
                latest = query_db("SELECT id, base_price, total_seats, available_seats, departure FROM flights WHERE id = ?", (fid,))
                if latest:
                    latest = latest[0]
                    new_price = compute_dynamic_price(latest)
                    # record if change > 1% relative
                    if abs(new_price - before_price) / (before_price + 0.01) > 0.01:
                        record_fare_history(fid, before_price, new_price, new_demand, int(latest.get('available_seats', 0)))

            # sleep until next iteration
            _stop_simulation.wait(interval_seconds)
        except Exception as e:
            print(f"Simulation worker error: {e}")
            _stop_simulation.wait(interval_seconds)

    print("Dynamic pricing simulation worker stopped")


def start_simulation(interval_seconds=30):
    global _simulation_thread
    if _simulation_thread and _simulation_thread.is_alive():
        return
    _stop_simulation.clear()
    _simulation_thread = threading.Thread(target=simulation_worker, args=(interval_seconds,), daemon=True)
    _simulation_thread.start()


def stop_simulation():
    _stop_simulation.set()


# ============= Email queue worker =============
_email_thread = None
_stop_email_worker = threading.Event()


def enqueue_email(to_email, subject, body):
    """Insert an email into the queue for background sending."""
    now = datetime.utcnow().isoformat()
    execute_db("INSERT INTO email_queue (to_email, subject, body, created_at, status, attempts) VALUES (?, ?, ?, ?, 'pending', 0)", (to_email, subject, body, now))


def email_worker(poll_interval=5):
    print("Email worker started")
    while not _stop_email_worker.is_set():
        try:
            # fetch pending emails
            rows = query_db("SELECT id, to_email, subject, body, attempts FROM email_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT 10")
            if not rows:
                _stop_email_worker.wait(poll_interval)
                continue

            for r in rows:
                eid = r.get('id')
                to_email = r.get('to_email')
                subject = r.get('subject')
                body = r.get('body')
                attempts = int(r.get('attempts') or 0)

                ok = send_email_message(to_email, subject, body)
                now = datetime.utcnow().isoformat()
                if ok:
                    execute_db("UPDATE email_queue SET status = 'sent', sent_at = ?, attempts = ? WHERE id = ?", (now, attempts + 1, eid))
                else:
                    attempts += 1
                    if attempts >= 5:
                        execute_db("UPDATE email_queue SET status = 'failed', last_error = ?, attempts = ? WHERE id = ?", ("send_failed", attempts, eid))
                    else:
                        execute_db("UPDATE email_queue SET attempts = ?, last_error = ? WHERE id = ?", (attempts, 'retry', eid))

        except Exception as e:
            print(f"Email worker error: {e}")
            _stop_email_worker.wait(poll_interval)

    print("Email worker stopped")


def start_email_worker(poll_interval=5):
    global _email_thread
    if _email_thread and _email_thread.is_alive():
        return
    _stop_email_worker.clear()
    _email_thread = threading.Thread(target=email_worker, args=(poll_interval,), daemon=True)
    _email_thread.start()


def stop_email_worker():
    _stop_email_worker.set()


# ============= MOCK EXTERNAL AIRLINE API SIMULATION =============


@app.route('/external/schedules', methods=['GET'])
@error_handler
def external_schedules():
    """Simulate an external airline schedules API.
    Query params: airline (code), origin, destination, date (YYYY-MM-DD), count
    Returns: list of schedule objects (may be pulled from DB or generated)
    """
    airline = request.args.get('airline', '').strip().upper()
    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    date = request.args.get('date', '').strip()
    count = request.args.get('count', type=int) or 3

    # Basic validation
    if not airline:
        return jsonify({"error": "'airline' parameter is required", "status": "error"}), 400

    # Try to find matching flights from our DB (best-effort)
    query = """
        SELECT f.flight_number, a.code AS airline_code, o.iata_code AS origin_iata,
               d.iata_code AS destination_iata, f.departure, f.arrival, f.base_price, f.available_seats
        FROM flights f
        JOIN airlines a ON f.airline_id = a.id
        JOIN airports o ON f.origin_id = o.id
        JOIN airports d ON f.destination_id = d.id
        WHERE a.code = ?
    """
    params = [airline]
    if origin:
        query += " AND (o.iata_code = ? OR o.city = ?)"
        params.extend([origin.upper(), origin])
    if destination:
        query += " AND (d.iata_code = ? OR d.city = ?)"
        params.extend([destination.upper(), destination])
    if date:
        try:
            datetime.strptime(date, '%Y-%m-%d')
            query += " AND date(f.departure) = ?"
            params.append(date)
        except ValueError:
            return jsonify({"error": "Date must be in YYYY-MM-DD format", "status": "error"}), 400

    query += " ORDER BY f.departure ASC LIMIT ?"
    params.append(count)

    schedules = query_db(query, tuple(params))

    # If no schedules found, generate mock schedules
    if not schedules:
        mock = []
        base_hour = 6
        for i in range(count):
            dep = datetime.utcnow().replace(hour=(base_hour + i) % 24, minute=0, second=0, microsecond=0)
            arr = dep
            mock.append({
                "flight_number": f"{airline}{100 + i}",
                "airline_code": airline,
                "origin_iata": origin.upper() if origin else "XXX",
                "destination_iata": destination.upper() if destination else "YYY",
                "departure": dep.isoformat() + 'Z',
                "arrival": (arr.replace(hour=(arr.hour + 2) % 24)).isoformat() + 'Z',
                "base_price": round(1500 + i * 250, 2),
                "available_seats": 20 - i
            })
        return jsonify({"status": "mock", "count": len(mock), "schedules": mock}), 200

    return jsonify({"status": "success", "count": len(schedules), "schedules": schedules}), 200


@app.route('/external/push_schedule', methods=['POST'])
@error_handler
def external_push_schedule():
    """Accept a schedule POST from an external (simulated) airline API.
    This endpoint doesn't persist by default; it validates payload and returns 200.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "JSON payload required", "status": "error"}), 400

    # Minimal validation
    required = ['flight_number', 'airline_code', 'origin_iata', 'destination_iata', 'departure', 'arrival']
    missing = [r for r in required if r not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}", "status": "error"}), 400

    # Echo back validated payload as acceptance
    return jsonify({"status": "accepted", "received": payload}), 200


# ============= BOOKING WORKFLOW (MILESTONE 3) =============

def generate_pnr(airline_code):
    """Generate a unique PNR: AIRLINE_CODE + 6 random alphanumeric chars."""
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    suffix = ''.join(random.choice(chars) for _ in range(6))
    return f"{airline_code}{suffix}"


def simulate_payment(email, amount):
    """Simulate payment processing. 95% success rate."""
    if random.random() < 0.95:
        return True, "Payment successful"
    else:
        return False, "Payment declined"


@app.route('/book/initiate', methods=['POST'])
@login_required
@error_handler
def initiate_booking():
    """Initiate booking: select flight and seat.
    Request: { "flight_id": int, "seat_number": str }
    Response: { "flight_id", "seat_number", "current_price", "booking_reference" (temp) }
    """
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "JSON payload required", "status": "error"}), 400

    flight_id = payload.get('flight_id')
    seat_number = payload.get('seat_number')

    if not flight_id or not seat_number:
        return jsonify({"error": "flight_id and seat_number required", "status": "error"}), 400

    # cleanup expired holds and check if flight exists and has available seats
    cleanup_expired_holds()
    flight_data = query_db("SELECT f.id, f.flight_number, a.code, f.available_seats, f.base_price FROM flights f JOIN airlines a ON f.airline_id = a.id WHERE f.id = ?", (flight_id,))
    if not flight_data:
        return jsonify({"error": f"Flight {flight_id} not found", "status": "error"}), 404

    flight = flight_data[0]
    if int(flight['available_seats']) <= 0:
        return jsonify({"error": "No available seats on this flight", "status": "error"}), 400
    # Ensure seat isn't already booked
    existing = query_db("SELECT 1 FROM bookings WHERE flight_id = ? AND seat_number = ? AND status = 'confirmed'", (flight_id, seat_number))
    if existing:
        return jsonify({"error": "Seat already booked", "status": "error"}), 409

    # Ensure seat isn't held by another temp ref
    held = query_db("SELECT temp_ref, expires_at FROM seat_holds WHERE flight_id = ? AND seat_number = ? AND expires_at > ?", (flight_id, seat_number, datetime.utcnow().isoformat()))
    if held:
        return jsonify({"error": "Seat temporarily on hold by another user", "status": "error"}), 409

    # Compute dynamic price
    price = compute_dynamic_price(flight)

    # Create a short-lived hold (default 5 minutes)
    hold_minutes = int(os.environ.get('HOLD_MINUTES', '5'))
    expires_at = datetime.utcnow() + timedelta(minutes=hold_minutes)
    temp_ref = f"{flight_id}_{seat_number}_{int(time.time())}"
    create_seat_hold(flight_id, seat_number, temp_ref, expires_at.isoformat())

    return jsonify({
        "status": "initiated",
        "flight_id": flight_id,
        "flight_number": flight['flight_number'],
        "seat_number": seat_number,
        "current_price": price,
        "temp_reference": temp_ref,
        "hold_expires_at": expires_at.isoformat()
    }), 200


@app.route('/book/confirm', methods=['POST'])
@login_required
@error_handler
def confirm_booking():
    """Confirm booking: provide passenger info and simulate payment.
    Request: { "flight_id": int, "seat_number": str, "passenger_name": str, "passenger_email": str }
    Response: { "status": "success", "pnr": str, "booking_details" }
    Uses transaction to ensure atomicity: deduct seat, process payment, insert booking.
    """
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "JSON payload required", "status": "error"}), 400

    flight_id = payload.get('flight_id')
    seat_number = payload.get('seat_number')
    passenger_name = payload.get('passenger_name')
    passenger_email = payload.get('passenger_email')

    required = ['flight_id', 'seat_number', 'passenger_name', 'passenger_email']
    missing = [r for r in required if r not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}", "status": "error"}), 400

    temp_reference = payload.get('temp_reference')

    # Fetch flight info
    flight_data = query_db(
        "SELECT f.id, f.flight_number, a.code, f.available_seats, f.base_price FROM flights f JOIN airlines a ON f.airline_id = a.id WHERE f.id = ?",
        (flight_id,)
    )
    if not flight_data:
        return jsonify({"error": f"Flight {flight_id} not found", "status": "error"}), 404

    flight = flight_data[0]
    if int(flight['available_seats']) <= 0:
        return jsonify({"error": "No available seats on this flight", "status": "error"}), 400

    # Compute dynamic price
    booked_price = compute_dynamic_price(flight)

    # Simulate payment
    payment_success, payment_msg = simulate_payment(passenger_email, booked_price)
    if not payment_success:
        return jsonify({"status": "payment_failed", "message": payment_msg}), 400

    # Begin transaction: deduct seat, create booking with unique PNR
    try:
        conn = sqlite3.connect(DB)
        conn.isolation_level = None  # autocommit off
        cur = conn.cursor()

        cur.execute("BEGIN TRANSACTION")

        # Check and deduct available_seats (double-check for concurrency)
        # remove expired holds first
        try:
            now_iso = datetime.utcnow().isoformat()
            cur.execute("DELETE FROM seat_holds WHERE expires_at <= ?", (now_iso,))
        except Exception:
            pass

        # If a hold exists and temp_reference provided, ensure it matches
        if temp_reference:
            cur.execute("SELECT temp_ref FROM seat_holds WHERE flight_id = ? AND seat_number = ? AND temp_ref = ? AND expires_at > ?", (flight_id, seat_number, temp_reference, datetime.utcnow().isoformat()))
            hold_ok = cur.fetchone()
            if not hold_ok:
                cur.execute("ROLLBACK")
                conn.close()
                return jsonify({"error": "Hold not found or expired/invalid", "status": "error"}), 409
        else:
            # If no temp_reference, ensure no active hold by others
            cur.execute("SELECT temp_ref FROM seat_holds WHERE flight_id = ? AND seat_number = ? AND expires_at > ?", (flight_id, seat_number, datetime.utcnow().isoformat()))
            someone = cur.fetchone()
            if someone:
                cur.execute("ROLLBACK")
                conn.close()
                return jsonify({"error": "Seat is on hold by another user", "status": "error"}), 409

        cur.execute("SELECT available_seats FROM flights WHERE id = ?", (flight_id,))
        result = cur.fetchone()
        if result is None or result[0] <= 0:
            cur.execute("ROLLBACK")
            conn.close()
            return jsonify({"error": "Seat not available (concurrent booking)", "status": "error"}), 409

        # Deduct seat
        cur.execute("UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?", (flight_id,))

        # Generate unique PNR
        pnr = generate_pnr(flight['code'])

        # Insert booking
        booking_date = datetime.utcnow().isoformat()
        cur.execute(
            """INSERT INTO bookings (pnr, flight_id, passenger_name, passenger_email, seat_number, status, booked_price, booking_date, payment_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pnr, flight_id, passenger_name, passenger_email, seat_number, 'confirmed', booked_price, booking_date, 'success')
        )

        cur.execute("COMMIT")
        # remove hold after successful booking
        try:
            cur.execute("DELETE FROM seat_holds WHERE flight_id = ? AND seat_number = ?", (flight_id, seat_number))
        except Exception:
            pass

        conn.close()

        return jsonify({
            "status": "success",
            "pnr": pnr,
            "booking_details": {
                "flight_number": flight['flight_number'],
                "passenger_name": passenger_name,
                "passenger_email": passenger_email,
                "seat_number": seat_number,
                "booked_price": booked_price,
                "booking_date": booking_date
            }
        }), 201

    except Exception as e:
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass
        conn.close()
        return jsonify({"error": f"Booking failed: {str(e)}", "status": "error"}), 500


@app.route('/bookings/<pnr>', methods=['GET'])
@error_handler
def get_booking(pnr):
    """Retrieve booking details by PNR."""
    booking_data = query_db(
        """SELECT b.*, f.flight_number, a.name AS airline_name
           FROM bookings b
           JOIN flights f ON b.flight_id = f.id
           JOIN airlines a ON f.airline_id = a.id
           WHERE b.pnr = ?""",
        (pnr,)
    )

    if not booking_data:
        return jsonify({"error": f"Booking {pnr} not found", "status": "error"}), 404

    booking = booking_data[0]
    return jsonify({
        "status": "success",
        "booking": booking
    }), 200


@app.route('/bookings/<pnr>/receipt', methods=['GET'])
@error_handler
def get_booking_receipt(pnr):
    """Return booking receipt as an attachment (JSON) for download."""
    booking_data = query_db(
        """SELECT b.*, f.flight_number, a.name AS airline_name
           FROM bookings b
           JOIN flights f ON b.flight_id = f.id
           JOIN airlines a ON f.airline_id = a.id
           WHERE b.pnr = ?""",
        (pnr,)
    )

    if not booking_data:
        return jsonify({"error": f"Booking {pnr} not found", "status": "error"}), 404
    booking = booking_data[0]
    fmt = request.args.get('format', '').lower()

    payload = {
        "pnr": booking.get('pnr'),
        "flight_number": booking.get('flight_number'),
        "airline": booking.get('airline_name'),
        "passenger_name": booking.get('passenger_name'),
        "passenger_email": booking.get('passenger_email'),
        "seat_number": booking.get('seat_number'),
        "booked_price": booking.get('booked_price'),
        "status": booking.get('status'),
        "booking_date": booking.get('booking_date')
    }

    # If PDF requested, generate a simple PDF using reportlab
    if fmt == 'pdf':
        try:
            from reportlab.pdfgen import canvas
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(595, 842))
            x = 50
            y = 800
            c.setFont('Helvetica-Bold', 16)
            c.drawString(x, y, 'Flight Booking Receipt')
            y -= 30
            c.setFont('Helvetica', 11)
            for key, val in payload.items():
                c.drawString(x, y, f"{key.replace('_',' ').title()}: {val}")
                y -= 18
                if y < 80:
                    c.showPage()
                    y = 800
            c.showPage()
            c.save()
            buffer.seek(0)
            data = buffer.read()
            resp = make_response(data)
            resp.headers['Content-Disposition'] = f'attachment; filename="{pnr}_receipt.pdf"'
            resp.headers['Content-Type'] = 'application/pdf'
            return resp
        except Exception:
            pass

    resp = make_response(jsonify(payload))
    resp.headers['Content-Disposition'] = f'attachment; filename="{pnr}_receipt.json"'
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route('/bookings/history/<email>', methods=['GET'])
@login_required
@error_handler
def get_booking_history(email):
    """Retrieve all bookings for a passenger by email."""
    # only allow user to fetch their own history or admin
    if session.get('email') != email and not session.get('is_admin'):
        return jsonify({"error": "Forbidden", "status": "error"}), 403
    bookings = query_db(
        """SELECT b.*, f.flight_number, a.name AS airline_name
           FROM bookings b
           JOIN flights f ON b.flight_id = f.id
           JOIN airlines a ON f.airline_id = a.id
           WHERE b.passenger_email = ?
           ORDER BY b.booking_date DESC""",
        (email,)
    )

    return jsonify({
        "status": "success",
        "email": email,
        "count": len(bookings),
        "bookings": bookings
    }), 200


@app.route('/bookings/<pnr>', methods=['DELETE'])
@login_required
@error_handler
def cancel_booking(pnr):
    """Cancel a booking and restore available seat.
    Uses transaction to ensure atomicity.
    """
    # Get booking details
    booking_data = query_db("SELECT id, flight_id, status, passenger_email FROM bookings WHERE pnr = ?", (pnr,))

    if not booking_data:
        return jsonify({"error": f"Booking {pnr} not found", "status": "error"}), 404

    booking = booking_data[0]

    # only owner or admin may cancel
    owner_email = booking.get('passenger_email')
    if session.get('email') != owner_email and not session.get('is_admin'):
        return jsonify({"error": "Forbidden", "status": "error"}), 403

    if booking['status'] == 'cancelled':
        return jsonify({"error": "Booking already cancelled", "status": "error"}), 400

    # Begin transaction: mark booking as cancelled, restore seat
    try:
        conn = sqlite3.connect(DB)
        conn.isolation_level = None
        cur = conn.cursor()

        cur.execute("BEGIN TRANSACTION")

        # Update booking status
        cur.execute("UPDATE bookings SET status = 'cancelled' WHERE pnr = ?", (pnr,))

        # Restore available seats
        cur.execute("UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?", (booking['flight_id'],))

        cur.execute("COMMIT")
        conn.close()

        return jsonify({
            "status": "success",
            "message": f"Booking {pnr} cancelled",
            "restored_seat": True
        }), 200

    except Exception as e:
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass
        conn.close()
        return jsonify({"error": f"Cancellation failed: {str(e)}", "status": "error"}), 500


# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested URL was not found on the server",
        "status": "error"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "status": "error"
    }), 500


if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DB):
        print(f"Warning: Database file '{DB}' not found.")
        print("Run 'python db_init.py' to initialize the database.")
    # Ensure dynamic tables exist and start the simulation worker
    setup_dynamic_tables()
    # start simulation with 30s interval (can be tuned via env var)
    try:
        interval = int(os.environ.get('SIMULATION_INTERVAL', '30'))
    except Exception:
        interval = 30
    start_simulation(interval_seconds=interval)
    # start email worker with short poll interval
    try:
        email_interval = int(os.environ.get('EMAIL_POLL_INTERVAL', '5'))
    except Exception:
        email_interval = 5
    start_email_worker(poll_interval=email_interval)

    try:
        # Run without debug/reloader to avoid restart races during automated checks
        app.run(debug=False, port=5000, use_reloader=False)
    finally:
        # Stop background worker on shutdown
        stop_simulation()
