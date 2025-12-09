from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime, timezone
import random
import threading
import time
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
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

    try:
        # Run without debug/reloader to avoid restart races during automated checks
        app.run(debug=False, port=5000, use_reloader=False)
    finally:
        # Stop background worker on shutdown
        stop_simulation()
