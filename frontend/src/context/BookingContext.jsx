import React, { createContext, useState } from 'react'

export const BookingContext = createContext(null)

export function BookingProvider({children}){
  const [booking, setBooking] = useState(null)
  return (
    <BookingContext.Provider value={{booking, setBooking}}>
      {children}
    </BookingContext.Provider>
  )
}
