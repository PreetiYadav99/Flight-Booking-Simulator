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
