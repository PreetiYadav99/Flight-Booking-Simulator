import React, { useState, useEffect } from 'react'

export default function PassengerForm({passengers = [], onChange, fieldErrors = [], setFieldErrors}){
  const [localErrors, setLocalErrors] = useState([])

  useEffect(()=>{
    // initialize local errors length
    const init = passengers.map((_, i) => (fieldErrors[i] ? fieldErrors[i] : {name:null, email:null}))
    setLocalErrors(init)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [passengers.length])

  useEffect(()=>{
    // if parent updates fieldErrors, reflect them
    if(fieldErrors && fieldErrors.length === passengers.length){
      setLocalErrors(fieldErrors)
    }
  }, [fieldErrors, passengers.length])

  function validateEmail(email){
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if(!email || !email.trim()) return 'Email is required'
    if(!re.test(email)) return 'Invalid email address'
    return null
  }

  function validateName(name){
    if(!name || !name.trim()) return 'Name is required'
    return null
  }

  function updateAt(index, next){
    const copy = passengers.slice()
    copy[index] = { ...(copy[index] || {}), ...next }
    onChange(copy)

    // inline validate
    const ecopy = (localErrors.slice())
    const p = copy[index]
    ecopy[index] = { name: validateName(p.name), email: validateEmail(p.email) }
    setLocalErrors(ecopy)
    if(setFieldErrors) setFieldErrors(ecopy)
  }

  return (
    <div className="space-y-4">
      {passengers.map((p, i) => (
        <div key={i} className="p-3 border rounded">
          <div className="text-sm font-medium mb-2">Passenger {i+1}</div>
          <input className={`w-full p-2 border rounded mb-1 ${localErrors[i] && localErrors[i].name ? 'border-red-400' : ''}`} placeholder="Passenger name" value={p.name || ''} onChange={e=>updateAt(i, { name: e.target.value })} />
          {localErrors[i] && localErrors[i].name && <div className="text-xs text-red-600 mb-2">{localErrors[i].name}</div>}

          <input className={`w-full p-2 border rounded mb-1 ${localErrors[i] && localErrors[i].email ? 'border-red-400' : ''}`} placeholder="Passenger email" value={p.email || ''} onChange={e=>updateAt(i, { email: e.target.value })} />
          {localErrors[i] && localErrors[i].email && <div className="text-xs text-red-600">{localErrors[i].email}</div>}
        </div>
      ))}
    </div>
  )
}
