import React, { useState } from 'react'

export default function RetrievePNR(){
  const [pnr, setPnr] = useState('')
  const [result, setResult] = useState(null)

  async function fetchPNR(){
    try{
      const res = await fetch(`http://127.0.0.1:5000/bookings/${encodeURIComponent(pnr)}`)
      const d = await res.json()
      if(!res.ok) throw new Error(d.error || 'Not found')
      setResult(d.booking)
    }catch(e){ setResult({error: e.message}) }
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">Retrieve Booking by PNR</h2>
      <input className="p-2 border rounded mt-2" placeholder="Enter PNR" value={pnr} onChange={e=>setPnr(e.target.value)} />
      <div className="mt-2">
        <button className="px-3 py-1 bg-indigo-600 text-white rounded" onClick={fetchPNR}>Fetch</button>
      </div>
      {result && <pre className="mt-3">{JSON.stringify(result, null, 2)}</pre>}
    </div>
  )
}
