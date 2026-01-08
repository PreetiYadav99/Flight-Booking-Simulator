const BASE = 'http://127.0.0.1:5000'

export async function searchFlights(params){
  const url = new URL(`${BASE}/search`)
  Object.entries(params || {}).forEach(([k,v])=>{ if(v !== '' && v !== undefined) url.searchParams.set(k, v) })
  const res = await fetch(url.toString())
  return res.json()
}

export async function getFlight(id){
  const res = await fetch(`${BASE}/flights/${id}`)
  return res.json()
}

export async function getAirlines(){
  const res = await fetch(`${BASE}/airlines`)
  return res.json()
}
