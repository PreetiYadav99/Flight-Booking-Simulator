import React, { useState } from 'react'
import { jsPDF } from 'jspdf'

function SeatMap({ seats = 30, selected, onSelect }){
  return (
    <div className="grid grid-cols-6 gap-3">
      {Array.from({length: seats}).map((_,i)=>{
        const num = i+1
        // simple mock: make every 5th seat unavailable
        const available = (num % 5) !== 0
        const isSelected = selected == String(num)
        const base = available ? 'bg-emerald-600 text-white hover:bg-emerald-500' : 'bg-slate-600 text-slate-300 line-through'
        const cls = `p-3 rounded-md text-center font-medium ${isSelected ? 'ring-4 ring-amber-300' : base}`
        return (
          <button key={i} disabled={!available} onClick={()=>available && onSelect(''+num)} className={cls}>
            {num}
          </button>
        )
      })}
    </div>
  )
}

export default function BookingFlow({ flight, onClose, user }){
  const [step, setStep] = useState(1)
  const [seat, setSeat] = useState(null)
  const [passenger, setPassenger] = useState({ name:'', email: user?.email || '' })
  const [emailMe, setEmailMe] = useState(Boolean(user?.email))
  const [pnr, setPnr] = useState(null)

  function pay(){
    // simulate payment and produce PNR
    const token = 'PNR'+Math.random().toString(36).slice(2,8).toUpperCase()
    setPnr(token)
    setStep(4)
    // optionally enqueue an email with booking summary
    if (emailMe){
      const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
      const payload = {
        subject: `Your FlightSim booking ${token}`,
        body: JSON.stringify({ pnr: token, flight, seat, passenger }, null, 2)
      }
      fetch(`${BASE}/send-email`, { method:'POST', headers: { 'Content-Type':'application/json' }, credentials: 'include', body: JSON.stringify(payload) })
        .then(r=>r.json()).then(j=> console.log('enqueue email:', j)).catch(e=>console.warn('email enqueue failed', e))
    }
  }

  function downloadJSON(){
    const data = { pnr, flight, seat, passenger }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${pnr}.json`; a.click()
    URL.revokeObjectURL(url)
  }

  function downloadPDF(){
    const doc = new jsPDF({ unit: 'pt', format: 'a4' })
    // ticket background
    doc.setFillColor(3, 37, 65)
    doc.roundedRect(40, 40, 520, 220, 8, 8, 'F')
    // left accent
    doc.setFillColor(0, 173, 239)
    doc.rect(44, 44, 12, 212, 'F')

    // Header
    doc.setFontSize(20)
    doc.setTextColor(255,255,255)
    doc.text('FlightSim', 64, 70)
    doc.setFontSize(12)
    doc.text('E-Ticket', 64, 90)

    // Flight info block
    doc.setFontSize(11)
    doc.text(`PNR: ${pnr}`, 64, 120)
    doc.text(`Passenger: ${passenger.name || '-'}`, 64, 138)
    doc.text(`Email: ${passenger.email || '-'}`, 64, 156)
    doc.text(`Flight: ${flight.flight_number || flight.code || '-'}`, 64, 174)
    doc.text(`From: ${(flight.depart && flight.depart.airport) || flight.origin || flight.origin_city || '-'}  →  To: ${(flight.arrival && flight.arrival.airport) || flight.destination || flight.destination_city || '-'}`, 64, 192)
    doc.text(`Departure: ${(flight.depart && flight.depart.time) || flight.departure || '-'}`, 64, 210)

    // Right side box with seat and price
    doc.setFillColor(255,255,255)
    doc.roundedRect(360, 96, 180, 120, 6, 6, 'F')
    doc.setTextColor(0,0,0)
    doc.setFontSize(12)
    doc.text(`Seat: ${seat || '-'}`, 380, 128)
    doc.text(`Price: $${flight.price || flight.current_price || flight.base_price || '0.00'}`, 380, 148)
    doc.text(`Class: ${flight.travel_class || 'Economy'}`, 380, 168)

    // Barcode-like PNR (mock)
    doc.setDrawColor(255,255,255)
    let x = 64
    const y = 240
    for(let i=0;i<24;i++){
      const w = (i%2===0)?4:2
      doc.rect(x, y, w, 18, 'F')
      x += w + 2
    }
    doc.setFontSize(10)
    doc.text(pnr, 64, y + 36)

    doc.save(`${pnr || 'ticket'}.pdf`)
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-white rounded-lg p-6 shadow-lg text-slate-900">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Booking — {flight.code}</h3>
          <button onClick={onClose} className="text-slate-700">Close</button>
        </div>

        <div className="mt-4">
          {step===1 && (
            <div>
              <h4 className="font-semibold">Select seat</h4>
              <p className="text-sm text-slate-700">Available seats: {flight.seats}</p>
              <div className="mt-3">
                <SeatMap seats={flight.seats || 30} selected={seat} onSelect={s=>setSeat(s)} />
              </div>
              <div className="mt-4 flex justify-end">
                <button disabled={!seat} onClick={()=>setStep(2)} className="px-4 py-2 bg-accent text-white rounded">Next</button>
              </div>
            </div>
          )}

          {step===2 && (
            <div>
              <h4 className="font-semibold">Passenger details</h4>
                <div className="mt-3 grid grid-cols-1 gap-2">
                <input placeholder="Full name" className="p-2 border rounded text-slate-900 placeholder:text-slate-500" value={passenger.name} onChange={e=>setPassenger({...passenger, name:e.target.value})} />
                <input placeholder="Email" className="p-2 border rounded text-slate-900 placeholder:text-slate-500" value={passenger.email} onChange={e=>setPassenger({...passenger, email:e.target.value})} />
                <label className="inline-flex items-center gap-2 mt-2">
                  <input type="checkbox" checked={emailMe} onChange={e=>setEmailMe(e.target.checked)} />
                  <span className="text-sm">Email booking to my registered address</span>
                </label>
                <div className="flex justify-end gap-2 mt-2">
                  <button onClick={()=>setStep(1)} className="px-3 py-1 border rounded">Back</button>
                  <button onClick={()=>setStep(3)} className="px-4 py-2 bg-accent text-white rounded">Proceed to Payment</button>
                </div>
              </div>
            </div>
          )}

          {step===3 && (
            <div>
              <h4 className="font-semibold">Payment</h4>
              <p className="text-sm text-slate-700">This is a simulated payment. Enter any card number to continue.</p>
              <div className="mt-3 grid grid-cols-1 gap-2">
                <input placeholder="Card number" className="p-2 border rounded text-slate-900 placeholder:text-slate-500" />
                <div className="flex justify-end gap-2 mt-2">
                  <button onClick={()=>setStep(2)} className="px-3 py-1 border rounded">Back</button>
                  <button onClick={pay} className="px-4 py-2 bg-accent text-white rounded">Pay ${flight.price}</button>
                </div>
              </div>
            </div>
          )}

          {step===4 && (
            <div>
              <h4 className="font-semibold">Confirmation</h4>
              <p className="text-sm text-slate-700 mt-1">Your booking is confirmed.</p>
              <div className="mt-3 grid grid-cols-2 gap-3">
                <div className="card">
                  <div className="text-sm text-slate-700">PNR</div>
                  <div className="text-lg font-semibold">{pnr}</div>
                </div>
                <div className="card">
                  <div className="text-sm text-slate-700">Passenger</div>
                  <div className="text-lg font-semibold">{passenger.name}</div>
                  <div className="text-sm text-slate-700">Seat: {seat}</div>
                </div>
              </div>
              <div className="mt-4 flex gap-3 justify-end">
                <button onClick={downloadJSON} className="px-3 py-1 border rounded">Download JSON</button>
                <button onClick={downloadPDF} className="px-3 py-1 bg-primary text-white rounded">Download PDF</button>
                <button onClick={onClose} className="px-3 py-1 border rounded">Done</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
