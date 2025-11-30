from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime
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
    
    app.run(debug=True, port=5000)
