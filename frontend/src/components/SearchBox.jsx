import React, { useState, useEffect, useRef } from 'react'

export default function SearchBox({ onSearch }){
  const [from, setFrom] = useState('LAX')
  const [to, setTo] = useState('SFO')
  const [date, setDate] = useState(new Date().toISOString().slice(0,10))
  const [passengers, setPassengers] = useState(1)
  const [cabin, setCabin] = useState('Economy')
  const [airports, setAirports] = useState([])
  const [fromSuggestions, setFromSuggestions] = useState([])
  const [toSuggestions, setToSuggestions] = useState([])
  const [showFrom, setShowFrom] = useState(false)
  const [showTo, setShowTo] = useState(false)
  const fromRef = useRef(null)
  const toRef = useRef(null)

  function submit(e){
    e?.preventDefault()
    onSearch({ from, to, date, passengers, cabin })
  }

  useEffect(()=>{
    // fetch airports for autocomplete (best-effort)
    const API = (import.meta.env?.VITE_API_URL) || 'http://127.0.0.1:5000'
    fetch(`${API}/airports`).then(r=>r.json()).then(j=>{
      if (j && Array.isArray(j.airports)) setAirports(j.airports)
    }).catch(()=>{})
  },[])

  function filterAirports(q){
    if (!q) return []
    const qq = q.trim().toLowerCase()
    return airports.filter(a => (a.city || '').toLowerCase().includes(qq) || (a.iata_code || '').toLowerCase().includes(qq) || (a.name || '').toLowerCase().includes(qq)).slice(0,8)
  }

  function handleSelectAirport(value, setter, hideSetter){
    setter(value)
    hideSetter(false)
  }

  return (
    <form onSubmit={submit} className="search-panel p-4 bg-primary-opaque md:p-6">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
        <div className="col-span-1 md:col-span-2 input-card p-3 bg-white/95 border-l-4 border-primary relative">
          <label className="text-xs text-slate-800">From</label>
          <input ref={fromRef} className="w-full mt-1 p-2 rounded text-slate-900" value={from} onChange={e=>{ setFrom(e.target.value); setFromSuggestions(filterAirports(e.target.value)); setShowFrom(true) }} onFocus={()=>{ setFromSuggestions(filterAirports(from)); setShowFrom(true) }} />
          {showFrom && fromSuggestions.length>0 && (
            <ul className="absolute left-3 right-3 top-full mt-1 bg-white shadow-lg rounded-md max-h-44 overflow-auto z-50 border">
              {fromSuggestions.map((a,idx)=> (
                <li key={idx} className="px-3 py-2 hover:bg-slate-100 cursor-pointer text-sm text-slate-800" onMouseDown={()=>handleSelectAirport(`${a.city} (${a.iata_code})`, setFrom, setShowFrom)}>{a.city} — {a.iata_code} <span className="text-xs text-slate-500">{a.name}</span></li>
              ))}
            </ul>
          )}
        </div>

        <div className="col-span-1 md:col-span-2 input-card p-3 bg-white/95 border-l-4 border-primary relative">
          <label className="text-xs text-slate-800">To</label>
          <input ref={toRef} className="w-full mt-1 p-2 rounded text-slate-900" value={to} onChange={e=>{ setTo(e.target.value); setToSuggestions(filterAirports(e.target.value)); setShowTo(true) }} onFocus={()=>{ setToSuggestions(filterAirports(to)); setShowTo(true) }} />
          {showTo && toSuggestions.length>0 && (
            <ul className="absolute left-3 right-3 top-full mt-1 bg-white shadow-lg rounded-md max-h-44 overflow-auto z-50 border">
              {toSuggestions.map((a,idx)=> (
                <li key={idx} className="px-3 py-2 hover:bg-slate-100 cursor-pointer text-sm text-slate-800" onMouseDown={()=>handleSelectAirport(`${a.city} (${a.iata_code})`, setTo, setShowTo)}>{a.city} — {a.iata_code} <span className="text-xs text-slate-500">{a.name}</span></li>
              ))}
            </ul>
          )}
        </div>

        <div className="input-card p-3 bg-white/95 border-l-4 border-accent">
          <label className="text-xs text-slate-800">Date</label>
          <input type="date" className="w-full mt-1 p-2 rounded text-slate-900" value={date} onChange={e=>setDate(e.target.value)} />
        </div>

        <div className="input-card p-3 bg-white/95 border-l-4 border-accent">
          <label className="text-xs text-slate-800">Passengers</label>
          <input type="number" min="1" className="w-full mt-1 p-2 rounded text-slate-900" value={passengers} onChange={e=>setPassengers(e.target.value)} />
        </div>

        <div className="md:col-span-5 flex gap-3 mt-1 items-center">
          <select className="p-3 rounded border bg-white/95 border-l-4 border-accent text-slate-900" value={cabin} onChange={e=>setCabin(e.target.value)}>
            <option>Economy</option>
            <option>Premium Economy</option>
            <option>Business</option>
            <option>First</option>
          </select>
          <button type="submit" className="ml-auto px-4 py-2 bg-accent text-white rounded">Search</button>
        </div>
      </div>
    </form>
  )
}
