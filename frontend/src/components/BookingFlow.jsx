import React, { useState, useEffect } from 'react'

import { useParams, useNavigate } from 'react-router-dom'

export default function BookingFlow({flight: flightProp, onComplete, onCancel}){
  const [seatMap, setSeatMap] = useState([])
  const [selectedSeat, setSelectedSeat] = useState('')
  const [initiated, setInitiated] = useState(null)
  const [error, setError] = useState(null)
  const [loadingInitiate, setLoadingInitiate] = useState(false)

  const { id: routeFlightId } = useParams()
  const navigate = useNavigate()

  async function loadSeats(flightId){
    try{
      const r = await fetch(`http://127.0.0.1:5000/flights/${flightId}/seats`)
      const d = await r.json()
      if(d.seats) setSeatMap(d.seats)
    }catch(e){ /* ignore */ }
  }

  useEffect(()=>{
    const fid = flightProp?.id ?? routeFlightId
    if(fid) loadSeats(fid)
  },[flightProp, routeFlightId])

  async function initiate(){
    setError(null); setLoadingInitiate(true)
    try{
      const flightId = flightProp?.id ?? routeFlightId
      const res = await fetch('http://127.0.0.1:5000/book/initiate', {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ flight_id: flightId, seat_number: selectedSeat })
      })
      const data = await res.json()
      if(!res.ok) throw new Error(data.error || 'Initiate failed')
      setInitiated(data)
      // store temporary hold so payment step can complete confirmation
      sessionStorage.setItem('current_hold', JSON.stringify(data))
      // navigate to payment step
      navigate(`/payment/${flightId}`)
    }catch(err){ setError(err.message) }
    finally{ setLoadingInitiate(false) }
  }


  return (
    <div className="booking">
      <button onClick={onCancel} className="link">Back to search</button>
      <h2>Booking: {flightProp?.flight_number ?? `Flight ${routeFlightId}`} — {flightProp?.origin_city ?? ''} → {flightProp?.destination_city ?? ''}</h2>
      <div>Price (current): ₹ {flightProp?.current_price ?? flightProp?.base_price ?? '—'}</div>

      <div className="seatgrid">
        {seatMap.map(s => (
          <button key={s.seat_number} disabled={s.status!=='available' && s.status!=='held'} className={selectedSeat===s.seat_number? 'selected':''} onClick={()=>setSelectedSeat(s.seat_number)}>
            {s.seat_number} {s.status!=='available' ? `(${s.status})` : ''}
          </button>
        ))}
      </div>

      <div className="passenger">
        <input placeholder="Passenger name" value={name} onChange={e=>setName(e.target.value)} />
        <input placeholder="Passenger email" value={email} onChange={e=>setEmail(e.target.value)} />
      </div>

      {!initiated && <button disabled={!selectedSeat || loadingInitiate} onClick={initiate}>{loadingInitiate? 'Holding...':'Hold seat & Initiate'}</button>}
      {initiated && <div>
        <div>Hold expires: {initiated.hold_expires_at}</div>
        <div>Price: ₹ {initiated.current_price}</div>
        <button onClick={confirm} disabled={!name || !email || loadingConfirm}>{loadingConfirm? 'Processing...':'Confirm & Pay'}</button>
      </div>}

      {error && <div className="error">{error}</div>}
    </div>
  )
}
