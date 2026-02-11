import { useEffect, useState } from 'react'
import GraphViz from './GraphViz'
import RiskSparkline from './RiskSparkline'

export default function PasmDashboard() {
  const [loading, setLoading] = useState(false)
  const [score, setScore] = useState<number | null>(null)
  const [uncertainty, setUncertainty] = useState<number | null>(null)
  const [paths, setPaths] = useState<string[]>([])
  const [riskHistory] = useState<number[]>([0.2, 0.35, 0.41, 0.38, 0.55, 0.63, 0.71, 0.72]); // Removed unused setRiskHistory to fix lint warning
  const [hoveredPath, setHoveredPath] = useState<number | null>(null)

  useEffect(() => {
    // initial health + fetch
    let mounted = true
      ; (async () => {
        setLoading(true)
        try {
          // check model health
          const h = await fetch('/pasm/health')
          if (h.ok) {
            const hj = await h.json()
            if (mounted && hj && hj.ok && hj.model_ready) {
              setLoading(true)
              // ask the backend a few times to build a tiny uncertainty estimate
              const calls = await Promise.allSettled([
                fetch('/pasm/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nodes: [], edges: [] }) }),
                fetch('/pasm/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nodes: [], edges: [] }) }),
                fetch('/pasm/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nodes: [], edges: [] }) }),
              ])
              const results: number[] = []
              const pathCandidates: string[] = []
              for (const c of calls) {
                if (c.status === 'fulfilled') {
                  try {
                    const j = await c.value.json()
                    const r = j.result || j
                    const sc = (typeof r === 'object' && 'score' in r) ? Number(r.score) : (Array.isArray(r) ? Number(r[0] || 0) : Number(r))
                    results.push(Number.isFinite(sc) ? sc : 0)
                    // collect any path suggestions
                    if (r && typeof r === 'object' && (r.top_paths || r.paths || (r.details && r.details.paths))) {
                      const candidate = r.top_paths || r.paths || (r.details && r.details.paths)
                      if (Array.isArray(candidate)) pathCandidates.push(...candidate.map(String))
                    }
                  } catch (e) { /* ignore per-call failures */ }
                }
              }

              if (results.length > 0) {
                const mean = results.reduce((a, b) => a + b, 0) / results.length
                const variance = results.reduce((a, b) => a + (b - mean) * (b - mean), 0) / results.length
                const std = Math.sqrt(variance)
                if (mounted) { setScore(Number(mean.toFixed(3))); setUncertainty(Number(std.toFixed(3))) }
              }

              if (pathCandidates.length > 0 && mounted) {
                setPaths(pathCandidates.slice(0, 5))
              }
            } else {
              // model not ready; fall back to mock view
              if (mounted) {
                setScore(0.48); setUncertainty(0.2)
                setPaths(['AuthServer → DB → AdminHost', 'WebApp → Cache → SensitiveAPI', 'VPN → JumpHost → Prod'])
              }
            }
          }
        } catch (e) {
          // network error -> keep mock values
          if (mounted) { setScore(0.72); setUncertainty(0.12); setPaths(['AuthServer → DB → AdminHost', 'WebApp → Cache → SensitiveAPI']) }
        }
        if (mounted) setLoading(false)
      })()
    return () => { mounted = false }
  }, [])

  const refresh = async () => {
    setLoading(true)
    try {
      // single predict call
      const res = await fetch('/pasm/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nodes: [], edges: [] }) })
      if (res.ok) {
        const j = await res.json()
        const r = j.result || j
        const sc = (typeof r === 'object' && 'score' in r) ? Number(r.score) : (Array.isArray(r) ? Number(r[0] || 0) : Number(r))
        setScore(Number.isFinite(sc) ? sc : 0)
        // update paths if provided
        const candidate = r.top_paths || r.paths || (r.details && r.details.paths)
        if (candidate && Array.isArray(candidate)) setPaths(candidate.map(String).slice(0, 5))
      }
    } catch (e) {
      // ignore, keep previous
    }
    setLoading(false)
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
      <section style={{ background: '#071226', padding: 20, borderRadius: 12, minHeight: 480 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ margin: 0 }}>Attack Surface Graph</h2>
          <div>
            <button onClick={refresh} style={{ marginRight: 8, padding: '8px 12px', background: '#2a5f6b', color: '#cfe9ff', border: '1px solid #3d7a8f', borderRadius: 6, cursor: 'pointer', transition: '0.2s', fontSize: 13 }} onMouseEnter={(e) => { e.currentTarget.style.background = '#3d7a8f'; e.currentTarget.style.boxShadow = '0 0 12px rgba(61,122,143,0.5)' }} onMouseLeave={(e) => { e.currentTarget.style.background = '#2a5f6b'; e.currentTarget.style.boxShadow = 'none' }}>Refresh</button>
            <button onClick={() => { alert('Simulate attack (demo)') }} style={{ padding: '8px 12px', background: '#5f4a3a', color: '#f4d8c9', border: '1px solid #7a6b59', borderRadius: 6, cursor: 'pointer', transition: '0.2s', fontSize: 13 }} onMouseEnter={(e) => { e.currentTarget.style.background = '#7a6b59'; e.currentTarget.style.boxShadow = '0 0 12px rgba(122,107,89,0.5)' }} onMouseLeave={(e) => { e.currentTarget.style.background = '#5f4a3a'; e.currentTarget.style.boxShadow = 'none' }}>Simulate</button>
          </div>
        </div>
        <div style={{ height: 380, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <GraphViz nodes={12} edges={16} highlightTopK={5} />
        </div>
      </section>

      <aside style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ background: '#071226', padding: 16, borderRadius: 12 }}>
          <h3 style={{ marginTop: 0 }}>Predicted Risk</h3>
          {loading ? <div style={{ color: '#9fb0c8' }}>Loading…</div> : (
            <div>
              <div style={{ fontSize: 40, fontWeight: 700, color: score && score > 0.75 ? '#ff7a7a' : '#7be495', transition: '0.3s', animation: score && score > 0.75 ? 'pulse-red 2s infinite' : 'none' }}>{score !== null ? (Math.round(score * 100)) + '%' : '—'}</div>
              <div style={{ color: '#9fb0c8', marginTop: 6 }}>Uncertainty: {uncertainty !== null ? (Math.round(uncertainty * 100)) + '%' : '—'}</div>
            </div>
          )}
          <style>{`@keyframes pulse-red { 0%, 100% { text-shadow: 0 0 8px rgba(255,122,122,0.5); } 50% { text-shadow: 0 0 16px rgba(255,122,122,0.8); } }`}</style>
        </div>

        <div style={{ background: '#071226', padding: 16, borderRadius: 12 }}>
          <h3 style={{ marginTop: 0 }}>Top Vulnerable Paths</h3>
          <ol style={{ paddingLeft: 18 }}>
            {paths.map((p, i) => (
              <li key={i} style={{ margin: '8px 0', cursor: 'pointer', transition: '0.2s', color: hoveredPath === i ? '#bdf4d6' : '#cfe9ff', textShadow: hoveredPath === i ? '0 0 8px rgba(189,244,214,0.4)' : 'none' }} onMouseEnter={() => setHoveredPath(i)} onMouseLeave={() => setHoveredPath(null)}>{p}</li>
            ))}
          </ol>
        </div>

        <div style={{ background: '#071226', padding: 16, borderRadius: 12, flex: 1 }}>
          <h3 style={{ marginTop: 0 }}>Risk Timeline</h3>
          <div style={{ opacity: 0, animation: 'fadeInUp 0.8s ease-out 0.3s forwards', transformOrigin: 'bottom' }}>
            <RiskSparkline data={riskHistory} height={80} color={score && score > 0.75 ? '#ff7a7a' : '#7be495'} />
          </div>
          <style>{`
            @keyframes fadeInUp { 
              from { opacity: 0; transform: translateY(12px); } 
              to { opacity: 1; transform: translateY(0); } 
            }
          `}</style>
        </div>
      </aside>
    </div>
  )
}
