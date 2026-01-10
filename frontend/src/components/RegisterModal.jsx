import React, { useState, useMemo } from 'react'

function validate(form){
  const errs = {}
  if (!form.name || form.name.trim().length < 2) errs.name = 'Full name must be at least 2 characters.'
  const email = (form.email||'').trim()
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email) errs.email = 'Email is required.'
  else if (!emailRe.test(email)) errs.email = 'Enter a valid email address.'
  const pw = form.password || ''
  if (pw.length < 8) errs.password = 'Password must be at least 8 characters.'
  return errs
}

export default function RegisterModal({ onClose }){
  const [form, setForm] = useState({ name:'', email:'', password:'' })
  const [touched, setTouched] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showPassword, setShowPassword] = useState(false)

  const errors = useMemo(()=> validate(form), [form])
  const isValid = Object.keys(errors).length === 0

  async function submit(e){
    e.preventDefault()
    setTouched({ name:true, email:true, password:true })
    if (!isValid) return
    setError(null)
    setLoading(true)
    try{
      const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
      const res = await fetch(`${BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: form.name, email: form.email, password: form.password })
      })
      const data = await res.json().catch(()=>({}))
      if (!res.ok){
        setError(data.error || `Registration failed (status ${res.status})`)
        setLoading(false)
        return
      }
      setLoading(false)
      onClose()
    }catch(err){
      setError(String(err))
      setLoading(false)
    }
  }

  function onChange(field, value){
    setForm(prev=>({ ...prev, [field]: value }))
  }

  function onBlur(field){ setTouched(prev=>({ ...prev, [field]: true })) }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg p-6 shadow-lg text-slate-900">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Create an account</h3>
          <button onClick={onClose} className="text-slate-700">Close</button>
        </div>
        <form onSubmit={submit} className="mt-4 grid gap-3">
          <div>
            <input
              required
              placeholder="Full name"
              className={`p-2 border rounded w-full text-slate-900 placeholder:text-slate-500 ${touched.name && errors.name ? 'border-red-500' : ''}`}
              value={form.name}
              onChange={e=>onChange('name', e.target.value)}
              onBlur={()=>onBlur('name')}
            />
            {touched.name && errors.name && <div className="text-sm text-red-600 mt-1">{errors.name}</div>}
          </div>

          <div>
            <input
              required
              type="email"
              placeholder="Email"
              className={`p-2 border rounded w-full text-slate-900 placeholder:text-slate-500 ${touched.email && errors.email ? 'border-red-500' : ''}`}
              value={form.email}
              onChange={e=>onChange('email', e.target.value)}
              onBlur={()=>onBlur('email')}
            />
            {touched.email && errors.email && <div className="text-sm text-red-600 mt-1">{errors.email}</div>}
          </div>

          <div className="relative">
            <input
              required
              type={showPassword ? 'text' : 'password'}
              placeholder="Password (min 8 chars)"
              className={`p-2 border rounded w-full text-slate-900 placeholder:text-slate-500 ${touched.password && errors.password ? 'border-red-500' : ''}`}
              value={form.password}
              onChange={e=>onChange('password', e.target.value)}
              onBlur={()=>onBlur('password')}
            />
            <button type="button" aria-label="Toggle password visibility" onClick={()=>setShowPassword(s=>!s)} className="absolute right-2 top-2 text-sm text-slate-700">
              {showPassword ? 'Hide' : 'Show'}
            </button>
            {touched.password && errors.password && <div className="text-sm text-red-600 mt-1">{errors.password}</div>}
          </div>

          {error && <div className="text-sm text-red-600">{error}</div>}

          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-3 py-1 border rounded">Cancel</button>
            <button type="submit" disabled={!isValid || loading} className="px-4 py-2 bg-primary text-white rounded">
              {loading? 'Creating...' : 'Create account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
