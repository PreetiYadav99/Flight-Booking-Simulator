import React, { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'

export default function Register({onSuccess}){
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const strength = useMemo(()=>{
    let score = 0
    if(password.length >= 8) score += 1
    if(/[0-9]/.test(password)) score += 1
    if(/[A-Z]/.test(password)) score += 1
    if(/[^A-Za-z0-9]/.test(password)) score += 1
    return score
  }, [password])

  async function submit(e){
    e.preventDefault(); setError(null); setLoading(true)
    try{
      const res = await fetch('http://127.0.0.1:5000/register', {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ email, name, password })
      })
      const data = await res.json()
      setLoading(false)
      if(!res.ok) throw new Error(data.error || 'Register failed')
      onSuccess && onSuccess({ email: data.email, name: data.name })
    }catch(err){ setLoading(false); setError(err.message) }
  }

  const strengthLabel = ['Very Weak','Weak','Okay','Strong','Very Strong'][strength]
  const strengthColor = ['bg-red-400','bg-orange-400','bg-yellow-400','bg-green-400','bg-green-600'][strength]

  return (
    <div className="max-w-md mx-auto bg-white shadow-md rounded p-6">
      <h3 className="text-2xl font-semibold mb-4">Create an account</h3>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Full name</label>
          <input className="mt-1 block w-full px-3 py-2 border rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" placeholder="Jane Doe" value={name} onChange={e=>setName(e.target.value)} required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input className="mt-1 block w-full px-3 py-2 border rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" placeholder="you@example.com" value={email} onChange={e=>setEmail(e.target.value)} type="email" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <input className="mt-1 block w-full px-3 py-2 border rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" placeholder="Choose a strong password" value={password} onChange={e=>setPassword(e.target.value)} type="password" required />
          <div className="flex items-center gap-3 mt-2">
            <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
              <div className={`${strengthColor} h-2`} style={{width: `${(strength/4)*100}%`}} />
            </div>
            <div className="text-xs text-gray-600">{strengthLabel}</div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <button disabled={loading} className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-60">{loading ? 'Creating...' : 'Create account'}</button>
          <Link to="/login" className="text-sm text-indigo-600 hover:underline">Already have an account?</Link>
        </div>

        {error && <div className="text-sm text-red-600">{error}</div>}
      </form>
    </div>
  )
}
