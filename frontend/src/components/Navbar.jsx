import React from 'react'
import { Link } from 'react-router-dom'

export default function NavBar({user, onLogout}){
  const [from, setFrom] = React.useState('')
  const [to, setTo] = React.useState('')
  const [date, setDate] = React.useState('')
  const navigate = (window && window.location) ? null : null
  return (
    <nav className="bg-indigo-600 text-white p-4">
      <div className="max-w-5xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link to="/" className="font-bold text-white">Flight Booking Simulator</Link>
        </div>

        <form className="flex gap-2 items-center" onSubmit={(e)=>{e.preventDefault(); const q = new URLSearchParams(); if(from) q.set('origin', from); if(to) q.set('destination', to); if(date) q.set('date', date); window.location.href = '/search?'+q.toString(); }}>
          <input placeholder="From" value={from} onChange={e=>setFrom(e.target.value)} className="p-2 rounded text-black" />
          <input placeholder="To" value={to} onChange={e=>setTo(e.target.value)} className="p-2 rounded text-black" />
          <input type="date" value={date} onChange={e=>setDate(e.target.value)} className="p-2 rounded text-black" />
          <button className="px-3 py-1 bg-white text-indigo-600 rounded" type="submit">Search Flights</button>
        </form>

        <div className="flex items-center gap-3">
          <Link to="/history" className="hidden sm:inline">My Bookings</Link>
          {user ? (
            <>
              <span className="hidden sm:inline">Hi, {user.name || user.email}</span>
              <button className="bg-white text-indigo-600 px-3 py-1 rounded" onClick={onLogout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="bg-white text-indigo-600 px-3 py-1 rounded">Login</Link>
              <Link to="/register" className="hidden sm:inline ml-2 text-white hover:underline">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
