import json
import urllib.request

URL = 'http://127.0.0.1:5000'

def post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(URL+path, data=data, headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode('utf-8')
            print(f"POST {path} -> {resp.status}\n{body}\n")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"POST {path} -> {e.code}\n{body}\n")
    except Exception as e:
        print(f"POST {path} -> ERROR: {e}\n")

if __name__ == '__main__':
    # Test register with a new-looking email
    post('/register', {'email':'new_unique_user@example.com', 'name':'New Unique', 'password':'Password123'})
    # Test register with an existing email (admin)
    post('/register', {'email':'admin@example.com', 'name':'Admin', 'password':'password'})
    # Test login with admin
    post('/login', {'email':'admin@example.com', 'password':'password'})
    # Test login with the new user
    post('/login', {'email':'new_unique_user@example.com', 'password':'Password123'})
