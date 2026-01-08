import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

function FlightCard({flight, onSelect}){
  return (
    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 border rounded-lg shadow-sm hover:shadow-md transition">
      <div className="sm:flex-1">
        <div className="font-semibold text-lg">{flight.airline_name} <span className="text-sm text-gray-500">({flight.airline_code})</span></div>
        <div className="text-gray-700">{flight.origin_city} → {flight.destination_city}</div>
        <div className="text-sm text-gray-500">{new Date(flight.departure).toLocaleString()} - {new Date(flight.arrival).toLocaleString()}</div>
      </div>
      <div className="mt-3 sm:mt-0 sm:text-right">
        <div className="text-xl font-bold text-indigo-600">₹ {flight.current_price ?? flight.base_price}</div>
        <div className="text-sm text-gray-600">Seats: {flight.available_seats}</div>
        <button className="mt-2 px-3 py-1 bg-indigo-600 text-white rounded" onClick={()=>onSelect(flight)}>View / Book</button>
      </div>
    </div>
  )
}

export default function Search({onSelectFlight}){
  // read query params from URL to pre-fill form and auto-search
  useEffect(()=>{
    const qp = new URLSearchParams(window.location.search)
    const o = qp.get('origin') || ''
    const d = qp.get('destination') || ''
    const dt = qp.get('date') || ''
    setOrigin(o); setDestination(d); setDate(dt)
    if(o && d) handleSearch()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [date, setDate] = useState('')
  const [flights, setFlights] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [airlines, setAirlines] = useState([])

  // advanced filters
  const [sort, setSort] = useState('departure')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [minSeats, setMinSeats] = useState('')
  const [selectedAirline, setSelectedAirline] = useState('')

  const navigate = useNavigate()

  useEffect(()=>{
    // load airlines for filter
    fetch('http://127.0.0.1:5000/airlines').then(r=>r.json()).then(d=>{
      if(d && d.airlines) setAirlines(d.airlines)
    }).catch(()=>{})
  },[])

  async function handleSearch(e){
    if(e) e.preventDefault()
    setLoading(true); setError(null);
    try{
      const params = new URLSearchParams({ origin, destination })
      if(date) params.set('date', date)
      if(sort) params.set('sort', sort)
      if(minPrice) params.set('min_price', minPrice)
      if(maxPrice) params.set('max_price', maxPrice)
      if(minSeats) params.set('min_seats', minSeats)
      if(selectedAirline) params.set('airline', selectedAirline)

      const res = await fetch(`http://127.0.0.1:5000/search?${params.toString()}`)
      const data = await res.json()
      if(!res.ok) throw new Error(data.error || 'Search failed')
      setFlights(data.flights || [])
    }catch(err){
      setError(err.message)
    }finally{ setLoading(false) }
  }

  function clearFilters(){
    setSort('departure'); setMinPrice(''); setMaxPrice(''); setMinSeats(''); setSelectedAirline('')
  }

  return (
    <section>
      <form className="space-y-3 p-4 bg-white rounded shadow" onSubmit={handleSearch}>
        <div className="flex flex-col sm:flex-row gap-3">
          <input className="flex-1 p-2 border rounded" placeholder="Origin (city or IATA)" value={origin} onChange={e=>setOrigin(e.target.value)} required />
          <input className="flex-1 p-2 border rounded" placeholder="Destination (city or IATA)" value={destination} onChange={e=>setDestination(e.target.value)} required />
          <input className="p-2 border rounded" type="date" value={date} onChange={e=>setDate(e.target.value)} />
        </div>

        <div className="flex flex-col sm:flex-row gap-3 items-center">
          <select className="p-2 border rounded" value={sort} onChange={e=>setSort(e.target.value)}>
            <option value="departure">Sort by: Departure</option>
            <option value="price">Sort by: Price</option>
            <option value="duration">Sort by: Duration</option>
            <option value="available_seats">Sort by: Available Seats</option>
          </select>

          <input className="p-2 border rounded" placeholder="Min price" type="number" value={minPrice} onChange={e=>setMinPrice(e.target.value)} />
          <input className="p-2 border rounded" placeholder="Max price" type="number" value={maxPrice} onChange={e=>setMaxPrice(e.target.value)} />
          <input className="p-2 border rounded" placeholder="Min seats" type="number" value={minSeats} onChange={e=>setMinSeats(e.target.value)} />

          <select className="p-2 border rounded" value={selectedAirline} onChange={e=>setSelectedAirline(e.target.value)}>
            <option value="">All Airlines</option>
            {airlines.map(a=> <option key={a.id} value={a.code}>{a.name} ({a.code})</option>)}
          </select>

          <div className="flex gap-2">
            <button className="px-4 py-2 bg-indigo-600 text-white rounded" type="submit">Search</button>
            <button type="button" className="px-3 py-2 border rounded" onClick={()=>{ clearFilters(); handleSearch() }}>Clear</button>
          </div>
        </div>
      </form>

      {loading && <div className="mt-4">Loading...</div>}
      {error && <div className="mt-4 text-red-600">{error}</div>}

      <div className="mt-4 space-y-3">
        {flights.map(f => <FlightCard key={f.id} flight={f} onSelect={(fl)=>navigate(`/flight/${fl.id}`)} />)}
      </div>
    </section>
  )
}
