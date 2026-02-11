type Props = { nodes?: number, edges?: number, highlightTopK?: number }

export default function GraphViz({ nodes = 8, edges = 10, highlightTopK = 3 }: Props) {
  // simple circular layout
  const radius = 140
  const cx = 260
  const cy = 180
  const pts = Array.from({ length: nodes }).map((_, i) => {
    const angle = (i / nodes) * Math.PI * 2
    return {
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius
    }
  })

  // create some random edges deterministically
  const edgesList: Array<[number, number]> = []
  for (let i = 0; i < Math.min(edges, nodes * 2); i++) {
    edgesList.push([i % nodes, (i * 3 + 1) % nodes])
  }

  return (
    <svg width={520} height={360} style={{ borderRadius: 12, background: '#071226' }}>
      <defs>
        <linearGradient id="g1" x1="0%" x2="100%" y1="0%" y2="0%">
          <stop offset="0%" stopColor="#7be495" />
          <stop offset="100%" stopColor="#4cc9f0" />
        </linearGradient>
      </defs>
      {/* edges */}
      {edgesList.map((e, i) => {
        const a = pts[e[0]]
        const b = pts[e[1]]
        return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#18324a" strokeWidth={2} />
      })}

      {/* nodes */}
      {pts.map((p, i) => {
        const isTop = i < highlightTopK
        return (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r={isTop ? 12 : 8} fill={isTop ? 'url(#g1)' : '#18324a'} stroke={isTop ? '#bdf4d6' : '#5b7184'} strokeWidth={isTop ? 3 : 1} />
            <text x={p.x} y={p.y + 4} textAnchor="middle" fontSize={10} fill="#cfe9ff">{i}</text>
          </g>
        )
      })}
    </svg>
  )
}
