import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash

DB = os.path.join(os.path.dirname(__file__), 'flights.db')

if len(sys.argv) < 3:
    print('Usage: python set_password.py <email> <new_password>')
    sys.exit(1)

email = sys.argv[1].strip().lower()
newpw = sys.argv[2]

if not os.path.exists(DB):
    print('Database not found:', DB)
    sys.exit(1)

pw_hash = generate_password_hash(newpw)
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('SELECT id, email FROM users WHERE email = ?', (email,))
row = cur.fetchone()
if not row:
    # insert new user
    cur.execute('INSERT INTO users (email, name, password_hash, is_admin) VALUES (?, ?, ?, ?)', (email, '', pw_hash, 0))
    print(f'Inserted new user {email} with provided password')
else:
    cur.execute('UPDATE users SET password_hash = ? WHERE email = ?', (pw_hash, email))
    print(f'Updated password for {email}')
conn.commit()
conn.close()