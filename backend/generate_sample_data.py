import csv
from datetime import datetime, timedelta
import random

OUT = 'sample_data.csv'
ROWS = 500
START = datetime(2024,1,1,5,0)
END = datetime(2025,1,31,23,0)

# sample airlines and airports
AIRLINES = [
    ('SkyWays','SW'),('AeroExpress','AE'),('FastAir','FA'),('CloudJet','CJ'),('TransIndia','TI')
]

AIRPORTS = [
    ('Indira Gandhi International','New Delhi','India','DEL'),
    ('Chhatrapati Shivaji International','Mumbai','India','BOM'),
    ('Kempegowda International','Bangalore','India','BLR'),
    ('Chennai International','Chennai','India','MAA'),
    ('Netaji Subhash Chandra Bose International','Kolkata','India','CCU'),
    ('Rajiv Gandhi International','Hyderabad','India','HYD'),
    ('Pune International','Pune','India','PUN'),
    ('Goa International','Goa','India','GOI'),
    ('Sardar Vallabhbhai Patel International','Ahmedabad','India','AMD'),
    ('Cochin International','Kochi','India','COK')
]

DURATIONS = [60,75,90,105,120,135,150,165,180]

fields = ['airline_name','airline_code','airport_name','city','country','iata_code','flight_number','origin_city','destination_city','departure','arrival','base_price','total_seats','available_seats','duration_mins']

rows = []
for i in range(ROWS):
    airline_name, airline_code = random.choice(AIRLINES)
    origin = random.choice(AIRPORTS)
    dest = random.choice(AIRPORTS)
    while dest[3] == origin[3]:
        dest = random.choice(AIRPORTS)
    origin_name, origin_city, origin_country, origin_iata = origin
    dest_name, dest_city, dest_country, dest_iata = dest

    # random departure between start and end
    total_seconds = int((END - START).total_seconds())
    rsec = random.randint(0, total_seconds)
    dep_dt = START + timedelta(seconds=rsec)
    # random time within day hours
    dep_dt = dep_dt.replace(hour=random.randint(5,20), minute=random.choice([0,15,30,45]), second=0, microsecond=0)
    duration = random.choice(DURATIONS)
    arr_dt = dep_dt + timedelta(minutes=duration)

    base_price = random.randint(2000,7000)
    total_seats = random.choice([150,160,170,180,190,200])
    available_seats = random.randint(max(0,total_seats-60), total_seats)
    duration_mins = duration

    flight_number = f"{airline_code}{100 + (i % 800)}"

    row = {
        'airline_name': airline_name,
        'airline_code': airline_code,
        'airport_name': origin_name,
        'city': origin_city,
        'country': origin_country,
        'iata_code': origin_iata,
        'flight_number': flight_number,
        'origin_city': origin_city,
        'destination_city': dest_city,
        'departure': dep_dt.strftime('%Y-%m-%d %H:%M:%S'),
        'arrival': arr_dt.strftime('%Y-%m-%d %H:%M:%S'),
        'base_price': base_price,
        'total_seats': total_seats,
        'available_seats': available_seats,
        'duration_mins': duration_mins
    }
    rows.append(row)

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"Wrote {len(rows)} rows to {OUT}")
