import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), 'flights.db')

def list_users():
    if not os.path.exists(DB):
        print('Database not found:', DB)
        return
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT id, email, name, password_hash, is_admin FROM users ORDER BY id')
    rows = cur.fetchall()
    if not rows:
        print('No users found')
        return
    for r in rows:
        print(f"id={r['id']:>3} email={r['email']:<30} name={r['name'] or '' :<20} admin={r['is_admin']} hash_len={len(r['password_hash'] or '')}")
    conn.close()

if __name__ == '__main__':
    list_users()
