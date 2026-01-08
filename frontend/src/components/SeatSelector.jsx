import React from 'react'

export default function SeatSelector({seats, onSelect, selected}){
  return (
    <div className="grid grid-cols-6 gap-2">
      {seats.map(s => (
        <button key={s.seat_number} disabled={s.status==='booked'} onClick={()=>onSelect(s.seat_number)} className={`p-2 border rounded ${selected===s.seat_number? 'bg-indigo-600 text-white':''} ${s.status==='booked'?'opacity-50 cursor-not-allowed':''}`}>
          {s.seat_number}
        </button>
      ))}
    </div>
  )
}
