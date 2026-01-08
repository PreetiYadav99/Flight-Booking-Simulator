import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

export default function FlightDetails({onBook}){
  const { id } = useParams()
  const [flight, setFlight] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(()=>{
    async function load(){
      setLoading(true); setError(null)
      try{
        const res = await fetch(`http://127.0.0.1:5000/flights/${encodeURIComponent(id)}`)
        const data = await res.json()
        if(!res.ok) throw new Error(data.error || 'Failed to load')
        setFlight(data.flight)
      }catch(err){ setError(err.message) }
      finally{ setLoading(false) }
    }
    load()
  },[id])

  if(loading) return <div>Loading flight...</div>
  if(error) return <div className="error">{error}</div>
  if(!flight) return <div>No flight found</div>

  return (
    <div className="flight-details">
      <h2>{flight.flight_number} — {flight.origin_city} → {flight.destination_city}</h2>
      <div>Airline: {flight.airline_name} ({flight.airline_code})</div>
      <div>Departure: {new Date(flight.departure).toLocaleString()}</div>
      <div>Arrival: {new Date(flight.arrival).toLocaleString()}</div>
      <div>Duration: {flight.duration_mins} mins</div>
      <div>Available Seats: {flight.available_seats}</div>
      <div>Price: ₹ {flight.current_price ?? flight.base_price}</div>
      <div style={{marginTop:12}}>
        <button onClick={()=>onBook(flight.id)}>Book this flight</button>
      </div>
    </div>
  )
}
