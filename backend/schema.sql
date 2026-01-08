CREATE TABLE airlines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  code TEXT NOT NULL UNIQUE
);

CREATE TABLE airports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  country TEXT,
  iata_code TEXT NOT NULL UNIQUE
);

CREATE TABLE flights (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  flight_number TEXT NOT NULL,
  airline_id INTEGER NOT NULL,
  origin_id INTEGER NOT NULL,
  destination_id INTEGER NOT NULL,
  departure DATETIME NOT NULL,
  arrival DATETIME NOT NULL,
  base_price REAL NOT NULL,
  total_seats INTEGER NOT NULL,
  available_seats INTEGER NOT NULL,
  duration_mins INTEGER,
  FOREIGN KEY (airline_id) REFERENCES airlines(id),
  FOREIGN KEY (origin_id) REFERENCES airports(id),
  FOREIGN KEY (destination_id) REFERENCES airports(id)
);


-- Table to track simulated demand levels per flight (used by dynamic pricing)
CREATE TABLE IF NOT EXISTS demand_levels (
  flight_id INTEGER PRIMARY KEY,
  demand_level REAL NOT NULL DEFAULT 1.0,
  last_updated TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (flight_id) REFERENCES flights(id)
);


-- Table to store fare history for auditing price changes
CREATE TABLE IF NOT EXISTS fare_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  flight_id INTEGER NOT NULL,
  timestamp TEXT NOT NULL DEFAULT (datetime('now')),
  old_price REAL,
  new_price REAL,
  demand_level REAL,
  available_seats INTEGER,
  FOREIGN KEY (flight_id) REFERENCES flights(id)
);

-- Table to store bookings with transaction/concurrency safety
CREATE TABLE IF NOT EXISTS bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pnr TEXT NOT NULL UNIQUE,
  flight_id INTEGER NOT NULL,
  passenger_name TEXT NOT NULL,
  passenger_email TEXT NOT NULL,
  seat_number TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'confirmed',
  booked_price REAL NOT NULL,
  booking_date DATETIME NOT NULL DEFAULT (datetime('now')),
  payment_status TEXT NOT NULL DEFAULT 'success',
  FOREIGN KEY (flight_id) REFERENCES flights(id)
);

-- Index for quick lookups by PNR and email
CREATE INDEX IF NOT EXISTS idx_bookings_pnr ON bookings(pnr);
CREATE INDEX IF NOT EXISTS idx_bookings_email ON bookings(passenger_email);
CREATE INDEX IF NOT EXISTS idx_bookings_flight ON bookings(flight_id);

-- Users table for simple authentication
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  password_hash TEXT NOT NULL,
  is_admin INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Table to store short-lived seat holds (temp reservations)
CREATE TABLE IF NOT EXISTS seat_holds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  flight_id INTEGER NOT NULL,
  seat_number TEXT NOT NULL,
  temp_ref TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  FOREIGN KEY (flight_id) REFERENCES flights(id)
);

CREATE INDEX IF NOT EXISTS idx_seatholds_flight_seat ON seat_holds(flight_id, seat_number);
