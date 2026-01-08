import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import '../tailwind.css'
import './styles.css'
import './styles/global.css'
import { BookingProvider } from './context/BookingContext'

const root = createRoot(document.getElementById('root'))
root.render(
  <React.StrictMode>
    <BookingProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </BookingProvider>
  </React.StrictMode>
)
