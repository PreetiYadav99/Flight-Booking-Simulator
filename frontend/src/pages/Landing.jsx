import React from 'react'
import { Link } from 'react-router-dom'

export default function Landing(){
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Welcome to Flight Booking Simulator</h2>
      <p className="mb-4">Search flights, view dynamic fares, and complete bookings with concurrency-safe seat holds.</p>
      <Link to="/" className="px-4 py-2 bg-indigo-600 text-white rounded">Start searching</Link>
    </div>
  )
}
