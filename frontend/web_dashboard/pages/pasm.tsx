import React from 'react'
import PasmDashboard from '../src/components/PasmDashboard'

export default function PASMPage() {
  return (
    <div style={{fontFamily: 'Inter, system-ui, Arial', padding: 24, background: '#0f1724', minHeight: '100vh', color: '#e6eef8'}}>
      <header style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24}}>
        <div>
          <h1 style={{margin: 0, fontSize: 28, fontWeight: 700}}>PASM — Predictive Attack Surface Modeling</h1>
          <p style={{margin: '6px 0 0 0', color: '#9fb0c8'}}>Temporal Graph Neural Networks (TGNN) — realtime predictions & risk paths</p>
        </div>
      </header>

      <main>
        <PasmDashboard />
      </main>
    </div>
  )
}
