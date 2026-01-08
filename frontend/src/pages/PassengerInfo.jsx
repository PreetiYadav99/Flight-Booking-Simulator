import React, { useState } from 'react'
import PassengerForm from '../components/PassengerForm'
import { useNavigate, useParams } from 'react-router-dom'

export default function PassengerInfo(){
  const [passengers, setPassengers] = useState([{name:'', email:''}])
  const [count, setCount] = useState(1)
  const [error, setError] = useState(null)
  const [fieldErrors, setFieldErrors] = useState([])
  const navigate = useNavigate()
  const { id } = useParams()

  function handleCountChange(e){
    let val = parseInt(e.target.value, 10) || 1
    if(val < 1) val = 1
    if(val > 9) val = 9
    setCount(val)
    setPassengers(prev => {
      const copy = prev.slice(0, val)
      while(copy.length < val) copy.push({name:'', email:''})
      return copy
    })
    setFieldErrors(prev => {
      const copy = (prev || []).slice(0, val)
      while(copy.length < val) copy.push({name:null, email:null})
      return copy
    })
  }

  function next(){
    setError(null)
    if(count < 1){ setError('Please select at least 1 passenger'); return }
    const errors = []
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    let hasError = false
    for(let i=0;i<count;i++){
      const p = passengers[i] || {name:'', email:''}
      const e = {name:null, email:null}
      if(!p.name || !p.name.trim()){ e.name = 'Name is required'; hasError = true }
      if(!p.email || !p.email.trim()){ e.email = 'Email is required'; hasError = true }
      else if(!emailRe.test(p.email)){ e.email = 'Invalid email address'; hasError = true }
      errors.push(e)
    }
    if(hasError){ setFieldErrors(errors); setError('Please fix highlighted fields'); return }
    sessionStorage.setItem('passengers', JSON.stringify(passengers.slice(0, count)))
    navigate(`/book/${id}`)
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">Passenger Information</h2>

      <div className="mt-3 mb-4 flex items-center gap-3">
        <label className="text-sm">Number of passengers</label>
        <input type="number" min="1" max="9" value={count} onChange={handleCountChange} className="w-20 p-2 border rounded" />
      </div>

      <PassengerForm passengers={passengers.slice(0, count)} onChange={setPassengers} fieldErrors={fieldErrors} setFieldErrors={setFieldErrors} />

      {error && <div className="mt-3 text-sm text-red-600">{error}</div>}

      <div className="mt-3">
        <button className="px-4 py-2 bg-indigo-600 text-white rounded" onClick={next}>Continue</button>
      </div>
    </div>
  )
}
