import urllib.request, urllib.error, json, sqlite3, sys
from urllib.parse import quote_plus

BASE = 'http://127.0.0.1:5000'

def get_json(path):
    url = BASE + path
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read().decode('utf-8')
            return resp.getcode(), json.loads(data)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'error': str(e)}
    except Exception as e:
        return None, {'error': str(e)}


def db_check(dbfile='flights.db'):
    out = {}
    try:
        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM demand_levels")
        out['demand_levels_count'] = cur.fetchone()[0]
        cur.execute("SELECT flight_id, demand_level, last_updated FROM demand_levels LIMIT 5")
        out['demand_sample'] = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fare_history")
        out['fare_history_count'] = cur.fetchone()[0]
        cur.execute("SELECT flight_id, timestamp, old_price, new_price, demand_level FROM fare_history ORDER BY timestamp DESC LIMIT 5")
        out['fare_history_recent'] = cur.fetchall()
        cur.execute("SELECT id, available_seats FROM flights ORDER BY id LIMIT 5")
        out['flight_seats_sample'] = cur.fetchall()
        conn.close()
    except Exception as e:
        out['db_error'] = str(e)
    return out


def print_json(title, code, data):
    print('\n' + '='*40)
    print(title)
    print('HTTP code:', code)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    print('Milestone 2 quick verification')

    code, data = get_json('/')
    print_json('Root /', code, data)

    code, data = get_json('/flights')
    print_json('/flights', code, {'count': data.get('count') if isinstance(data, dict) else None, 'sample_first': (data.get('flights')[0] if isinstance(data, dict) and data.get('flights') else None)})

    code2, data2 = get_json('/flights/1')
    print_json('/flights/1', code2, data2)

    # search example (replace names if needed)
    q = '/search?origin=Delhi&destination=Mumbai'
    code3, data3 = get_json(q)
    print_json('/search?origin=Delhi&destination=Mumbai', code3, {'count': data3.get('count') if isinstance(data3, dict) else None, 'sample_first': (data3.get('flights')[0] if isinstance(data3, dict) and data3.get('flights') else None)})

    # DB checks
    dbres = db_check('flights.db')
    print('\n' + '='*40)
    print('DB checks:')
    print(json.dumps(dbres, indent=2, ensure_ascii=False, default=str))

if __name__ == '__main__':
    main()
