import React, { useState } from 'react'
import AuthModal from './AuthModal'

export default function Navbar({ user, onLogin, onLogout, onShowAuth, onShowAdmin }){
  return (
    <header className="bg-white/5 backdrop-blur sticky top-0 z-20 border-b border-white/6">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-2xl font-semibold text-primary">FlightSim</div>
          <div className="text-sm text-white/80">Professional booking simulator</div>
        </div>
        <nav className="flex items-center gap-4">
          <button className="text-sm px-3 py-1 rounded-md hover:bg-white/6 text-white">Help</button>
          {!user && (
            <>
              <button onClick={() => onShowAuth && onShowAuth()} className="text-sm px-3 py-1 rounded-md border border-white/10 text-white">Register</button>
              <button onClick={() => onShowAuth && onShowAuth()} className="text-sm px-3 py-1 rounded-md bg-primary text-white">Login</button>
            </>
          )}
          {user && (
            <div className="flex items-center gap-3">
              <div className="text-sm text-white">Hello, {user.name || user.email}</div>
              {user.is_admin && <button onClick={() => onShowAdmin && onShowAdmin()} className="text-sm px-3 py-1 rounded-md border">Admin</button>}
              <button onClick={onLogout} className="text-sm px-3 py-1 rounded-md border border-white/10 text-white">Logout</button>
            </div>
          )}
        </nav>
      </div>
    </header>
  )
}
