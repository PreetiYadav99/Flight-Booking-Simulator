import React from 'react'
import { Link } from 'react-router-dom'

export default function FlightCard({flight}){
  return (
    <div className="p-4 border rounded flex justify-between items-center">
      <div>
        <div className="font-semibold">{flight.airline_name} <span className="text-sm text-gray-500">{flight.airline_code}</span></div>
        <div className="text-sm">{flight.origin_city} → {flight.destination_city}</div>
        <div className="text-xs text-gray-500">{new Date(flight.departure).toLocaleString()}</div>
      </div>
      <div className="text-right">
        <div className="text-lg font-bold">₹ {flight.current_price ?? flight.base_price}</div>
        <div className="text-sm">Seats: {flight.available_seats}</div>
        <Link to={`/flight/${flight.id}`} className="mt-2 inline-block px-3 py-1 bg-indigo-600 text-white rounded">View</Link>
      </div>
    </div>
  )
}
