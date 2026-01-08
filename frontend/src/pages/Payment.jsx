import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { confirmBooking } from '../services/bookingAPI'

function getPassenger(){
  try{ return JSON.parse(sessionStorage.getItem('passenger')||'null') }catch(e){return null}
}
function getHold(){
  try{ return JSON.parse(sessionStorage.getItem('current_hold')||'null') }catch(e){return null}
}

export default function Payment(){
  const navigate = useNavigate()
  const { id } = useParams()

  async function pay(){
    const hold = getHold()
    const passenger = getPassenger()
    if(!hold){ alert('No active hold found. Start booking again.'); return }
    if(!passenger){ alert('No passenger info found.'); return }
    // Call confirm booking endpoint with hold temp_reference and passenger details
    try{
      const payload = {
        flight_id: id,
        seat_number: hold.seat_number,
        passenger_name: passenger.name,
        passenger_email: passenger.email,
        temp_reference: hold.temp_reference
      }
      const res = await confirmBooking(payload)
      if(res && res.status === 'success' && res.pnr){
        // store booking result for confirmation page
        sessionStorage.setItem('last_booking', JSON.stringify(res))
        navigate(`/confirmation`)
      } else {
        alert('Payment/booking failed: ' + (res.error || res.message || JSON.stringify(res)))
      }
    }catch(err){ alert(err.message) }
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">Payment</h2>
      <p className="mt-2">Simulated payment for booking {id}.</p>
      <div className="mt-3">
        <button className="px-4 py-2 bg-indigo-600 text-white rounded" onClick={pay}>Pay Now</button>
      </div>
    </div>
  )
}
