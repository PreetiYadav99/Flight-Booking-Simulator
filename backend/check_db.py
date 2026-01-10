import sqlite3, os
p='D:/Flight-Booking-Simulator/flights.db'
print('path', p)
print('exists', os.path.exists(p))
try:
    conn=sqlite3.connect(p)
    cur=conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print('tables:', cur.fetchall())
    conn.close()
except Exception as e:
    print('err', e)
