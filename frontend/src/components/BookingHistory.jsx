import React, { useEffect, useState } from 'react'

export default function BookingHistory({user, onClose, onOpenBooking}){
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [bookings, setBookings] = useState([])

  async function load(){
    setLoading(true); setError(null)
    try{
      const res = await fetch(`http://127.0.0.1:5000/bookings/history/${encodeURIComponent(user.email)}`, { credentials: 'include' })
      const data = await res.json()
      if(!res.ok) throw new Error(data.error || 'Failed to fetch bookings')
      setBookings(data.bookings || [])
    }catch(err){ setError(err.message) }
    finally{ setLoading(false) }
  }

  useEffect(()=>{ load() },[])

  async function downloadReceipt(pnr, format='json'){
    try{
      const url = `http://127.0.0.1:5000/bookings/${encodeURIComponent(pnr)}/receipt${format==='pdf'? '?format=pdf':''}`
      const res = await fetch(url, { credentials: 'include' })
      if(!res.ok) throw new Error('Failed to download')
      if(format==='pdf'){
        const blob = await res.blob()
        const a = document.createElement('a')
        const u = URL.createObjectURL(blob)
        a.href = u; a.download = `${pnr}_receipt.pdf`; a.click(); URL.revokeObjectURL(u)
      } else {
        const json = await res.json()
        const blob = new Blob([JSON.stringify(json, null, 2)], {type: 'application/json'})
        const a = document.createElement('a')
        const u = URL.createObjectURL(blob)
        a.href = u; a.download = `${pnr}_receipt.json`; a.click(); URL.revokeObjectURL(u)
      }
    }catch(err){ alert(err.message) }
  }

  async function cancelBooking(pnr){
    if(!confirm('Cancel booking ' + pnr + '?')) return
    try{
      const res = await fetch(`http://127.0.0.1:5000/bookings/${encodeURIComponent(pnr)}`, { method: 'DELETE', credentials: 'include' })
      const data = await res.json()
      if(!res.ok) throw new Error(data.error || 'Cancel failed')
      // refresh
      await load()
    }catch(err){ alert(err.message) }
  }

  return (
    <div className="booking-history">
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <h2>My Bookings</h2>
        <div>
          <button onClick={onClose}>Close</button>
          <button onClick={load} style={{marginLeft:8}}>Refresh</button>
        </div>
      </div>
      {loading && <div>Loading...</div>}
      {error && <div className="error">{error}</div>}
      {!loading && bookings.length===0 && <div>No bookings found</div>}
      <div className="history-list">
        {bookings.map(b => (
          <div key={b.pnr} className="history-item">
            <div className="h-left">
              <div><strong>{b.pnr}</strong> — {b.flight_number}</div>
              <div>{b.passenger_name} • {b.seat_number} • ₹{b.booked_price}</div>
              <div>{b.booking_date}</div>
            </div>
            <div className="h-right">
              <button onClick={()=>onOpenBooking(b)}>Open</button>
              <button onClick={()=>downloadReceipt(b.pnr,'json')}>JSON</button>
              <button onClick={()=>downloadReceipt(b.pnr,'pdf')}>PDF</button>
              {b.status !== 'cancelled' && <button onClick={()=>cancelBooking(b.pnr)}>Cancel</button>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
