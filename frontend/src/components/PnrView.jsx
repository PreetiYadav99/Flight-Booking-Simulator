import React, { useState } from 'react'

export default function PnrView({booking, onDone}){
  const [downloading, setDownloading] = useState(false)
  const pnr = booking.pnr || booking.booking_details?.pnr || booking.booking?.pnr || booking.booking_details?.booking?.pnr
  const details = booking.booking_details || booking.booking || booking || {}

  function downloadJSON(){
    const payload = JSON.stringify(details, null, 2)
    const blob = new Blob([payload], {type: 'application/json'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${pnr || 'booking'}_receipt.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function downloadPDF(){
    if(!pnr) return alert('PNR missing')
    setDownloading(true)
    try{
      const res = await fetch(`http://127.0.0.1:5000/bookings/${encodeURIComponent(pnr)}/receipt?format=pdf`, {
        method: 'GET',
        credentials: 'include'
      })
      if(!res.ok){
        const txt = await res.text()
        throw new Error('Failed to download PDF: ' + txt)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${pnr}_receipt.pdf`
      a.click()
      URL.revokeObjectURL(url)
    }catch(err){
      alert(err.message)
    }finally{ setDownloading(false) }
  }

  return (
    <div className="pnr">
      <h2>Booking Confirmed</h2>
      <div><strong>PNR:</strong> {pnr}</div>
      <pre className="booking-json">{JSON.stringify(details, null, 2)}</pre>
      <div className="actions">
        <button onClick={downloadJSON}>Download Receipt (JSON)</button>
        <button onClick={downloadPDF} disabled={downloading}>{downloading? 'Downloading...':'Download Receipt (PDF)'}</button>
        <button onClick={onDone}>Done</button>
      </div>
    </div>
  )
}

