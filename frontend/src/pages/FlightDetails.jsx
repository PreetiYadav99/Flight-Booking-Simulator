import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import PriceTag from '../components/PriceTag'

export default function FlightDetails(){
  const { id } = useParams()
  const [flight, setFlight] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(()=>{
    async function load(){
      setLoading(true)
      try{
        const res = await fetch(`http://127.0.0.1:5000/flights/${id}`)
        const data = await res.json()
        if(!res.ok) throw new Error(data.error || 'Failed')
        setFlight(data.flight)
      }catch(err){ setError(err.message) }
      finally{ setLoading(false) }
    }
    load()
    // poll current price every 10s
    let t = setInterval(async ()=>{
      try{
        const r = await fetch(`http://127.0.0.1:5000/flights/${id}/price`)
        const d = await r.json()
        if(r.ok && d.current_price && flight) setFlight(prev=> ({...prev, current_price: d.current_price}))
      }catch(e){}
    }, 10000)
    return ()=> clearInterval(t)
  },[id])

  if(loading) return <div>Loading...</div>
  if(error) return <div className="text-red-600">{error}</div>
  if(!flight) return <div>No flight found</div>

  const totalSeats = flight.total_seats || 0
  const available = flight.available_seats || 0
  const occupied = totalSeats - available
  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-xl font-bold">{flight.flight_number} — {flight.origin_city} → {flight.destination_city}</h2>
      <div className="mt-2"><PriceTag price={flight.current_price ?? flight.base_price} /></div>
      <div className="mt-4">Departure: {new Date(flight.departure).toLocaleString()}</div>
      <div>Arrival: {new Date(flight.arrival).toLocaleString()}</div>
      <div className="mt-4">
        <div className="text-sm text-gray-600">Seat availability</div>
        <div className="w-full bg-gray-200 rounded h-4 mt-2">
          <div className="bg-green-500 h-4 rounded" style={{width: `${(available/Math.max(totalSeats,1))*100}%`}} />
        </div>
        <div className="text-sm mt-1">Available: {available} / {totalSeats} (Occupied: {occupied})</div>
      </div>
      <div className="mt-3">
        <button className="px-4 py-2 bg-indigo-600 text-white rounded" onClick={()=>navigate(`/passenger/${flight.id}`)}>Proceed to Book</button>
      </div>
    </div>
  )
}
