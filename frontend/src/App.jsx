import React, { useState, useEffect } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import NavBar from './components/NavBar'
import Landing from './pages/Landing'
import Search from './components/Search'
import FlightDetailsPage from './pages/FlightDetails'
import BookingFlow from './components/BookingFlow'
import PnrView from './components/PnrView'
import Login from './components/Login'
import Register from './components/Register'
import BookingHistory from './components/BookingHistory'
import PassengerInfo from './pages/PassengerInfo'
import Payment from './pages/Payment'
import Confirmation from './pages/Confirmation'
import RetrievePNR from './pages/RetrievePNR'

export default function App(){
  const [selectedFlight, setSelectedFlight] = useState(null)
  const [bookingResult, setBookingResult] = useState(null)
  const [user, setUser] = useState(null)
  const [showRegister, setShowRegister] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  const navigate = useNavigate()

  useEffect(()=>{
    async function restoreSession(){
      try{
        const res = await fetch('http://127.0.0.1:5000/me', { credentials: 'include' })
        const data = await res.json()
        if(res.ok && data.status === 'success' && data.user){
          setUser({ email: data.user.email, name: data.user.name, id: data.user.id, is_admin: data.user.is_admin })
        }
      }catch(e){
        // ignore
      }
    }
    restoreSession()
  }, [])

  async function handleLogout(){
    try{ await fetch('http://127.0.0.1:5000/logout', { method: 'POST', credentials: 'include' }) }catch(e){}
    setUser(null)
    navigate('/')
  }

  return (
    <div className="app min-h-screen bg-gray-50">
      <NavBar user={user} onLogout={handleLogout} />
      <main className="main py-6">
        <div className="max-w-5xl mx-auto">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/search" element={<Search />} />
            <Route path="/flight/:id" element={<FlightDetailsPage />} />
            <Route path="/passenger/:id" element={<PassengerInfo />} />
            <Route path="/book/:id" element={<BookingFlow />} />
            <Route path="/payment/:id" element={<Payment />} />
            <Route path="/confirmation" element={<Confirmation />} />
            <Route path="/pnr/:pnr" element={<PnrView booking={bookingResult} />} />
            <Route path="/history" element={<BookingHistory user={user} onOpenBooking={(b)=>{ setBookingResult(b); navigate(`/pnr/${b.pnr}`) }} />} />
            <Route path="/retrieve" element={<RetrievePNR />} />
            <Route path="/login" element={<Login onSuccess={(u)=>setUser(u)} />} />
            <Route path="/register" element={<Register onSuccess={(u)=>setUser(u)} />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

