type Props = {data?: number[], height?: number, color?: string}

export default function RiskSparkline({data=[0.2,0.35,0.41,0.38,0.55,0.63,0.71,0.72], height=80, color='#7be495'}:Props){
  const w = 280
  const h = height
  const minVal = Math.min(...data)
  const maxVal = Math.max(...data)
  const range = maxVal - minVal || 1

  const points = data.map((v,i)=>{
    const x = (i / (data.length - 1 || 1)) * w
    const y = h - ((v - minVal) / range) * (h - 10)
    return {x,y}
  })

  const pathD = points.length > 0 
    ? `M ${points.map(p=>`${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' L ')}`
    : ''

  return (
    <svg width={w} height={h} style={{display:'block', margin:'0 auto'}}>
      <defs>
        <linearGradient id="sparkGradient" x1="0%" x2="0%" y1="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity={0.4} />
          <stop offset="100%" stopColor={color} stopOpacity={0.05} />
        </linearGradient>
      </defs>
      {/* area fill */}
      <path d={pathD + ` L ${w} ${h} L 0 ${h}`} fill="url(#sparkGradient)" />
      {/* line */}
      <path d={pathD} fill="none" stroke={color} strokeWidth={2} />
      {/* dots */}
      {points.map((p,i)=>(
        <circle key={i} cx={p.x} cy={p.y} r={2.5} fill={color} />
      ))}
    </svg>
  )
}
