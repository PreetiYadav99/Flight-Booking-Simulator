import React from 'react'
import FlightCard from '../components/FlightCard'

export default function SearchResults({flights}){
  return (
    <div className="space-y-3 p-4">
      {flights && flights.length ? flights.map(f => <FlightCard key={f.id} flight={f} />) : <div>No flights</div>}
    </div>
  )
}
