import React, { useState } from 'react'

export default function AuthModal({ onClose, onLogin }){
  const [tab, setTab] = useState('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [loginForm, setLoginForm] = useState({ email:'', password:'' })
  const [regForm, setRegForm] = useState({ name:'', email:'', password:'' })
  const [showLoginPassword, setShowLoginPassword] = useState(false)
  const [showRegPassword, setShowRegPassword] = useState(false)

  const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

  async function doLogin(e){
    e.preventDefault()
    setError(null); setLoading(true)
    try{
      const res = await fetch(`${BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(loginForm)
      })
      const data = await res.json().catch(()=>({}))
      if (!res.ok){ setError(data.error || 'Login failed'); setLoading(false); return }
      onLogin && onLogin({ email: data.email, name: data.name })
      setLoading(false)
      onClose && onClose()
    }catch(err){ setError(String(err)); setLoading(false) }
  }

  async function doRegister(e){
    e.preventDefault()
    setError(null); setLoading(true)
    try{
      // register
      const r = await fetch(`${BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(regForm)
      })
      const rd = await r.json().catch(()=>({}))
      if (!r.ok){ setError(rd.error || 'Registration failed'); setLoading(false); return }
      // login after register
      const res = await fetch(`${BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: regForm.email, password: regForm.password })
      })
      const data = await res.json().catch(()=>({}))
      if (!res.ok){ setError(data.error || 'Auto-login failed'); setLoading(false); return }
      onLogin && onLogin({ email: data.email, name: data.name })
      setLoading(false)
      onClose && onClose()
    }catch(err){ setError(String(err)); setLoading(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-white/5 backdrop-blur-md rounded-lg overflow-hidden shadow-lg grid grid-cols-1 md:grid-cols-2">
        <div className="auth-info hidden md:block p-6">
          <h2 className="text-2xl font-semibold text-white">Flight Booking Simulator</h2>
          <p className="mt-2 text-white/80">A professional, minimal flight booking simulator built for testing dynamic pricing, seat reservation flows, and booking UX — useful for demos, interviews, and prototypes.</p>
          <ul className="mt-3 list-disc list-inside">
            <li>Simulated dynamic pricing and demand</li>
            <li>Seat selection and temporary holds</li>
            <li>Multi-step booking flow with PDF/JSON ticket download</li>
            <li>User authentication and admin tools</li>
          </ul>
          <p className="mt-4 text-sm">Sign up to try searches, bookings, and pricing simulations. This is a demo environment — no real payments are processed.</p>
        </div>

        <div className="p-6 bg-white/6">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <button onClick={()=>setTab('login')} className={`px-3 py-1 rounded ${tab==='login' ? 'bg-primary text-white' : 'border'}`}>Login</button>
              <button onClick={()=>setTab('register')} className={`px-3 py-1 rounded ${tab==='register' ? 'bg-primary text-white' : 'border'}`}>Register</button>
            </div>
            <button onClick={onClose} className="text-white/80">Close</button>
          </div>

          <div className="mt-4">
            {tab==='login' && (
              <form onSubmit={doLogin} className="grid gap-3">
                <input required type="email" placeholder="Email" className="p-2 border rounded bg-transparent text-white placeholder:text-white/60 border-white/10 caret-white outline-none" value={loginForm.email} onChange={e=>setLoginForm({...loginForm, email:e.target.value})} />
                <div className="relative">
                  <input required type={showLoginPassword ? 'text' : 'password'} placeholder="Password" className="p-2 border rounded w-full bg-transparent text-white placeholder:text-white/60 border-white/10 caret-white outline-none" value={loginForm.password} onChange={e=>setLoginForm({...loginForm, password:e.target.value})} />
                  <button type="button" aria-label="Toggle password visibility" onClick={()=>setShowLoginPassword(s=>!s)} className="absolute right-2 top-2 text-sm text-white/80">{showLoginPassword? 'Hide':'Show'}</button>
                </div>
                {error && <div className="text-sm text-red-500">{error}</div>}
                <div className="flex justify-end">
                  <button type="submit" disabled={loading} className="px-4 py-2 bg-primary text-white rounded">{loading? 'Logging in...' : 'Login'}</button>
                </div>
              </form>
            )}

            {tab==='register' && (
              <form onSubmit={doRegister} className="grid gap-3">
                <input required placeholder="Full name" className="p-2 border rounded bg-transparent text-white placeholder:text-white/60 border-white/10 caret-white outline-none" value={regForm.name} onChange={e=>setRegForm({...regForm, name:e.target.value})} />
                <input required type="email" placeholder="Email" className="p-2 border rounded bg-transparent text-white placeholder:text-white/60 border-white/10 caret-white outline-none" value={regForm.email} onChange={e=>setRegForm({...regForm, email:e.target.value})} />
                <div className="relative">
                  <input required type={showRegPassword ? 'text' : 'password'} placeholder="Password" className="p-2 border rounded w-full bg-transparent text-white placeholder:text-white/60 border-white/10 caret-white outline-none" value={regForm.password} onChange={e=>setRegForm({...regForm, password:e.target.value})} />
                  <button type="button" aria-label="Toggle password visibility" onClick={()=>setShowRegPassword(s=>!s)} className="absolute right-2 top-2 text-sm text-white/80">{showRegPassword? 'Hide':'Show'}</button>
                </div>
                {error && <div className="text-sm text-red-500">{error}</div>}
                <div className="flex justify-end">
                  <button type="submit" disabled={loading} className="px-4 py-2 bg-primary text-white rounded">{loading? 'Creating...' : 'Create account'}</button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
