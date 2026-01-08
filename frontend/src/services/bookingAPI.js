const BASE = 'http://127.0.0.1:5000'

export async function initiateBooking(payload){
  const res = await fetch(`${BASE}/book/initiate`, { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) })
  return res.json()
}

export async function confirmBooking(payload){
  const res = await fetch(`${BASE}/book/confirm`, { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) })
  return res.json()
}

export async function getBooking(pnr){
  const res = await fetch(`${BASE}/bookings/${encodeURIComponent(pnr)}`)
  return res.json()
}
