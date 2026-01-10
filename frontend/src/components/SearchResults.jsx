import React, { useEffect, useState } from 'react'
import FlightCard from './FlightCard'
import BookingFlow from './BookingFlow'

function makeSample(query){
  const base = 120
  const flights = [
    { id:1, logo:'A', code:'AA123', depart:{time:'08:00', airport:query.from}, arrival:{time:'09:30', airport:query.to}, duration:'1h30m', price: base + Math.floor(Math.random()*80), seats: 5 },
    { id:2, logo:'B', code:'BB456', depart:{time:'11:15', airport:query.from}, arrival:{time:'12:45', airport:query.to}, duration:'1h30m', price: base + 60 + Math.floor(Math.random()*100), seats: 3 },
    { id:3, logo:'C', code:'CC789', depart:{time:'16:40', airport:query.from}, arrival:{time:'18:10', airport:query.to}, duration:'1h30m', price: base + 120 + Math.floor(Math.random()*150), seats: 7 }
  ]
  return flights
}

export default function SearchResults({ query }){
  const [flights, setFlights] = useState(makeSample(query))
  const [bookingFlight, setBookingFlight] = useState(null)

  // simulate dynamic price updates
  useEffect(()=>{
    const t = setInterval(()=>{
      setFlights(prev=>prev.map(f=>({ ...f, price: Math.max(49, f.price + (Math.floor(Math.random()*21)-10)) })))
    }, 2500)
    return ()=>clearInterval(t)
  },[])

  return (
    <div>
      <div className="grid gap-4">
        {flights.map(f=> (
          <FlightCard key={f.id} flight={f} onBook={f=>setBookingFlight(f)} />
        ))}
      </div>
      {bookingFlight && <BookingFlow flight={bookingFlight} onClose={()=>setBookingFlight(null)} />}
    </div>
  )
}
