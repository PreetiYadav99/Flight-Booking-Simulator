import React from 'react'

export default function PriceTag({price}){
  return (
    <div className="text-2xl font-bold text-indigo-600">₹ {price}</div>
  )
}
