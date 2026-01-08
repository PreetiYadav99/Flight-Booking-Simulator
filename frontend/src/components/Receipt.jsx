import React from 'react'

export default function Receipt({booking}){
  return (
    <div className="p-4 border rounded bg-white">
      <h3 className="font-bold">Receipt - {booking?.pnr}</h3>
      <pre className="text-sm mt-2">{JSON.stringify(booking, null, 2)}</pre>
    </div>
  )
}
