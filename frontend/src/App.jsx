import React, { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import SearchBox from './components/SearchBox'
import SearchResults from './components/SearchResults'
import AuthModal from './components/AuthModal'
import AdminEmailQueue from './components/AdminEmailQueue'

export default function App(){
  const [query, setQuery] = useState(null)
  const [user, setUser] = useState(null)
  const [showAuth, setShowAuth] = useState(true)
  const [showAdmin, setShowAdmin] = useState(false)

  useEffect(()=>{
    // check session
    const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
    fetch(`${BASE}/me`, { credentials: 'include' })
      .then(r=>r.json())
      .then(data=>{
        if (data && data.status === 'success' && data.user){
          setUser(data.user)
          setShowAuth(false)
        } else {
          setShowAuth(true)
        }
      }).catch(()=> setShowAuth(true))
  }, [])

  async function handleLogout(){
    const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
    try{
      await fetch(`${BASE}/logout`, { method: 'POST', credentials: 'include' })
    }catch(e){}
    setUser(null)
    setShowAuth(true)
  }

  return (
    <div className="min-h-screen app-bg relative">
      {/* subtle colored accent blobs in background */}
      <div className="bg-animated">
          <div className="gradient-anim" />
          {/* simple plane SVG moving across the screen */}
          <svg className="plane" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style={{top: '20%'}}>
            <path fill="rgba(230,249,255,0.95)" d="M2 13.5L22 3l-6 11 6 3-20-3z" />
          </svg>
          <svg className="plane" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style={{top: '60%', animationDelay: '4s', width: '110px'}}>
            <path fill="rgba(200,230,255,0.85)" d="M2 13.5L22 3l-6 11 6 3-20-3z" />
          </svg>
      </div>
      <Navbar user={user} onLogin={(u)=>{ setUser(u); setShowAuth(false) }} onLogout={handleLogout} onShowAuth={()=>setShowAuth(true)} onShowAdmin={()=>setShowAdmin(true)} />
      <div className="container mx-auto px-4 py-8">
        {!user && showAuth && <AuthModal onClose={()=>setShowAuth(false)} onLogin={(u)=>{ setUser(u); setShowAuth(false) }} />}
        {user && showAdmin && <AdminEmailQueue onClose={()=>setShowAdmin(false)} />}

        {user && (
          <>
            <div className="max-w-4xl mx-auto card">
              <SearchBox onSearch={setQuery} />
            </div>
            {query && (
              <div className="mt-6 max-w-6xl mx-auto">
                <SearchResults query={query} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
