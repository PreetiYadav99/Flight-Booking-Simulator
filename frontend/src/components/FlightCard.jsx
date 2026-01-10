import React from 'react'

export default function FlightCard({ flight, onBook }){
  return (
    <div className="card flex items-center gap-4">
      <div className="w-20 flex-shrink-0">
        <div className="h-12 w-12 bg-slate-100 rounded flex items-center justify-center">{flight.logo}</div>
        <div className="text-xs text-slate-500 mt-1">{flight.code}</div>
      </div>
      <div className="flex-1 grid grid-cols-3">
        <div>
          <div className="text-lg font-semibold">{flight.depart.time}</div>
          <div className="text-sm text-slate-700">{flight.depart.airport}</div>
        </div>
        <div className="text-center">
          <div className="text-sm text-slate-700">{flight.duration}</div>
          <div className="text-xs mt-1 px-2 inline-block bg-slate-100 rounded text-slate-800">{flight.stops || 'Non-stop'}</div>
        </div>
        <div className="text-right">
          <div className="text-xl font-semibold">${flight.price}</div>
          <div className="text-sm text-slate-700">{flight.seats} seats left</div>
          <button onClick={()=>onBook(flight)} className="mt-2 px-3 py-1 bg-accent text-white rounded">Book</button>
        </div>
      </div>
    </div>
  )
}
