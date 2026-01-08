import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

export default function Login({onSuccess}){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function submit(e){
    e.preventDefault(); setError(null); setLoading(true)
    try{
      const res = await fetch('http://127.0.0.1:5000/login', {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ email, password })
      })
      const data = await res.json()
      setLoading(false)
      if(!res.ok) throw new Error(data.error || 'Login failed')
      onSuccess && onSuccess({ email: data.email, name: data.name })
      navigate('/')
    }catch(err){ setLoading(false); setError(err.message) }
  }

  return (
    <div className="max-w-md mx-auto bg-white shadow-md rounded p-6">
      <h3 className="text-2xl font-semibold mb-4">Sign in to your account</h3>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input className="mt-1 block w-full px-3 py-2 border rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" placeholder="you@example.com" value={email} onChange={e=>setEmail(e.target.value)} type="email" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <input className="mt-1 block w-full px-3 py-2 border rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
        </div>

        <div className="flex items-center justify-between">
          <button disabled={loading} className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-60">{loading ? 'Signing in...' : 'Sign in'}</button>
          <Link to="/register" className="text-sm text-indigo-600 hover:underline">Create account</Link>
        </div>

        {error && <div className="text-sm text-red-600">{error}</div>}
      </form>
    </div>
  )
}
