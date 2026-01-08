import React from 'react'

export default function Alert({children, type='info'}){
  const bg = type==='error'? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
  return <div className={`p-3 rounded ${bg}`}>{children}</div>
}
