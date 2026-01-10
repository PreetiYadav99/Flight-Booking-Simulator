import React, { useEffect, useState } from 'react'

export default function AdminEmailQueue({ onClose }){
  const [emails, setEmails] = useState([])
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState({})
  const API = (import.meta.env?.VITE_API_URL) || 'http://127.0.0.1:5000'

  async function fetchEmails(){
    setLoading(true)
    try{
      const res = await fetch(`${API}/admin/email-queue`, { credentials: 'include' })
      const data = await res.json().catch(()=>({}))
      if (res.ok){ setEmails(data.emails || []) }
      else {
        console.error('Failed to fetch emails', data)
      }
    }catch(err){ console.error(err) }
    setLoading(false)
  }

  useEffect(()=>{ fetchEmails() }, [])

  async function retryEmail(id){
    setActionLoading(prev=>({ ...prev, [id]: true }))
    try{
      const res = await fetch(`${API}/admin/email-queue/${id}/retry`, { method: 'POST', credentials: 'include' })
      const data = await res.json().catch(()=>({}))
      if (!res.ok){ console.error('Retry failed', data) }
      await fetchEmails()
    }catch(err){ console.error(err) }
    setActionLoading(prev=>({ ...prev, [id]: false }))
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-start justify-center p-4 pt-16 z-50">
      <div className="w-full max-w-4xl bg-white/6 backdrop-blur rounded-lg overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-white/6">
          <h3 className="text-lg text-white">Email Queue ({emails.length})</h3>
          <div className="flex gap-2">
            <button onClick={fetchEmails} className="px-3 py-1 border rounded text-white">Refresh</button>
            <button onClick={onClose} className="px-3 py-1 border rounded text-white">Close</button>
          </div>
        </div>
        <div className="p-4">
          {loading && <div className="text-white">Loading...</div>}
          {!loading && emails.length===0 && <div className="text-white">No queued emails</div>}
          {!loading && emails.length>0 && (
            <div className="overflow-auto max-h-96">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-white/80 text-sm">
                    <th>ID</th><th>To</th><th>Subject</th><th>Created</th><th>Status</th><th>Attempts</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {emails.map(e=> (
                    <tr key={e.id} className="border-t border-white/6 text-white text-sm">
                      <td className="py-2 pr-3">{e.id}</td>
                      <td className="py-2 pr-3">{e.to_email}</td>
                      <td className="py-2 pr-3">{e.subject}</td>
                      <td className="py-2 pr-3">{e.created_at}</td>
                      <td className="py-2 pr-3">{e.status}{e.sent_at? ' @ '+e.sent_at:''}</td>
                      <td className="py-2 pr-3">{e.attempts}</td>
                      <td className="py-2 pr-3">
                        <button disabled={actionLoading[e.id]} onClick={()=>retryEmail(e.id)} className="px-2 py-1 bg-primary text-white rounded">{actionLoading[e.id]? '...' : 'Retry'}</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
