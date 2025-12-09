"""
Database initialization script
Populates the SQLite database with sample flight data from CSV
"""

import sqlite3
import csv
from datetime import datetime
import os
import random

DB_FILE = 'flights.db'
SCHEMA_FILE = 'schema.sql'
DATA_FILE = 'sample_data.csv'


def init_database():
    """Initialize database with schema and sample data"""
    
    # Remove existing database if present
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed existing database: {DB_FILE}")
    
    # Connect to database
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    print(f"Created database: {DB_FILE}")
    
    # Read and execute schema
    with open(SCHEMA_FILE, 'r') as f:
        schema = f.read()
    
    c.executescript(schema)
    print(f"Applied schema from: {SCHEMA_FILE}")

    # Create additional tables for dynamic pricing simulation
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
    c.executescript(extra_sql)

    # Load sample data from CSV
    load_sample_data(conn)
    
    conn.commit()
    conn.close()
    print("Database initialization complete!")


def load_sample_data(conn):
    """Load flight data from CSV file"""
    
    c = conn.cursor()
    
    # Track unique airlines and airports
    airlines = {}
    airports = {}
    
    # Read CSV and extract unique airlines and airports
    with open(DATA_FILE, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data_rows = list(reader)
    
    # Insert unique airlines
    for row in data_rows:
        airline_code = row['airline_code'].strip()
        airline_name = row['airline_name'].strip()
        
        if airline_code not in airlines:
            c.execute(
                "INSERT INTO airlines (name, code) VALUES (?, ?)",
                (airline_name, airline_code)
            )
            airlines[airline_code] = c.lastrowid
    
    print(f"Inserted {len(airlines)} airlines")
    
    # Insert unique airports
    for row in data_rows:
        # Origin airport
        origin_code = row['iata_code'].strip()
        origin_name = row['airport_name'].strip()
        origin_city = row['city'].strip()
        origin_country = row['country'].strip()
        
        if origin_code not in airports:
            c.execute(
                "INSERT INTO airports (name, city, country, iata_code) VALUES (?, ?, ?, ?)",
                (origin_name, origin_city, origin_country, origin_code)
            )
            airports[origin_code] = c.lastrowid
    
    print(f"Inserted {len(airports)} airports")
    
    # Insert flights
    flight_count = 0
    for row in data_rows:
        try:
            flight_number = row['flight_number'].strip()
            airline_code = row['airline_code'].strip()
            origin_city = row['origin_city'].strip()
            destination_city = row['destination_city'].strip()
            departure = datetime.fromisoformat(row['departure'].strip())
            arrival = datetime.fromisoformat(row['arrival'].strip())
            base_price = float(row['base_price'])
            total_seats = int(row['total_seats'])
            available_seats = int(row['available_seats'])
            duration_mins = int(row['duration_mins'])
            
            # Get airport IDs by city
            origin_id = None
            destination_id = None
            
            for code, airport_id in airports.items():
                # Query to find airport by city
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM airports WHERE city = ? LIMIT 1", (origin_city,))
                result = cursor.fetchone()
                if result:
                    origin_id = result[0]
                    break
            
            for code, airport_id in airports.items():
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM airports WHERE city = ? LIMIT 1", (destination_city,))
                result = cursor.fetchone()
                if result:
                    destination_id = result[0]
                    break
            
            if origin_id and destination_id:
                airline_id = airlines[airline_code]
                
                c.execute("""
                    INSERT INTO flights 
                    (flight_number, airline_id, origin_id, destination_id, departure, 
                     arrival, base_price, total_seats, available_seats, duration_mins)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    flight_number,
                    airline_id,
                    origin_id,
                    destination_id,
                    departure.isoformat(),
                    arrival.isoformat(),
                    base_price,
                    total_seats,
                    available_seats,
                    duration_mins
                ))
                # seed demand_levels for this flight
                fid = c.lastrowid
                try:
                    c.execute(
                        "INSERT OR REPLACE INTO demand_levels (flight_id, demand_level, last_updated) VALUES (?, ?, ?)",
                        (fid, 1.0, datetime.utcnow().isoformat())
                    )
                except Exception:
                    pass
                # initial fare history record
                try:
                    c.execute(
                        "INSERT INTO fare_history (flight_id, timestamp, old_price, new_price, demand_level, available_seats) VALUES (?, ?, ?, ?, ?, ?)",
                        (fid, datetime.utcnow().isoformat(), None, base_price, 1.0, available_seats)
                    )
                except Exception:
                    pass
                flight_count += 1
        
        except Exception as e:
            print(f"Error inserting flight: {e}")
            continue
    
    print(f"Inserted {flight_count} flights")

    # Seed demand_levels and initial fare_history for each flight
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, base_price, available_seats FROM flights")
        flights = cursor.fetchall()
        seeded = 0
        for f in flights:
            flight_id = f[0]
            base_price = float(f[1]) if f[1] is not None else 0.0
            available_seats = int(f[2]) if f[2] is not None else 0

            # Insert default demand level (1.0 = neutral)
            cursor.execute(
                "INSERT OR REPLACE INTO demand_levels (flight_id, demand_level, last_updated) VALUES (?, ?, datetime('now'))",
                (flight_id, 1.0)
            )

            # Insert initial fare history record
            cursor.execute(
                "INSERT INTO fare_history (flight_id, old_price, new_price, demand_level, available_seats, timestamp) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                (flight_id, None, base_price, 1.0, available_seats)
            )
            seeded += 1

        print(f"Seeded demand_levels and fare_history for {seeded} flights")
    except Exception as e:
        print(f"Error seeding demand/fare tables: {e}")

    # Insert initial demand levels and fare history for each flight
    # (Removed duplicate/incorrect seeding that referenced a non-existent `demand` table
    # and mismatched fare_history columns.)

    # Initialize demand_levels for each flight
    c.execute("SELECT id FROM flights")
    flights = c.fetchall()
    now_iso = datetime.utcnow().isoformat()
    for (fid,) in flights:
        try:
            c.execute(
                "INSERT OR REPLACE INTO demand_levels (flight_id, demand_level, last_updated) VALUES (?, ?, ?)",
                (fid, 1.0, now_iso)
            )
        except Exception as e:
            print(f"Error initializing demand for flight {fid}: {e}")

    print(f"Initialized demand levels for {len(flights)} flights")


if __name__ == '__main__':
    init_database()
