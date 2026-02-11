import React, { useEffect, useRef, useMemo } from 'react'
import * as THREE from 'three'

interface ConsciousnessOrbProps {
  systemMode: 'conscious' | 'predictive' | 'self_healing' | 'under_attack'
  threatLevel: 'critical' | 'high' | 'medium' | 'low' | 'none'
  activePolicies: number
  alertCount: number
  uptime: number // in seconds
  className?: string
}

/**
 * 3D Consciousness Orb Component
 * Displays AI state with real-time pulse animation
 * Uses Three.js for advanced 3D rendering
 */
export const ConsciousnessOrb: React.FC<ConsciousnessOrbProps> = ({
  systemMode,
  threatLevel,
  activePolicies,
  alertCount,
  uptime,
  className = '',
}) => {
  const mountRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const orbRef = useRef<THREE.Mesh | null>(null)
  const particlesRef = useRef<THREE.Points | null>(null)

  // Determine colors based on system mode
  const modeColors = useMemo(() => {
    switch (systemMode) {
      case 'conscious':
        return { primary: 0x3b82f6, secondary: 0x1e40af, glow: 0x60a5fa }
      case 'predictive':
        return { primary: 0x06b6d4, secondary: 0x0891b2, glow: 0x22d3ee }
      case 'self_healing':
        return { primary: 0x10b981, secondary: 0x047857, glow: 0x34d399 }
      case 'under_attack':
        return { primary: 0xf97316, secondary: 0xd97706, glow: 0xfbbf24 }
      default:
        return { primary: 0x3b82f6, secondary: 0x1e40af, glow: 0x60a5fa }
    }
  }, [systemMode])

  // Threat indicator intensity (0-1)
  const threatIntensity = useMemo(() => {
    switch (threatLevel) {
      case 'critical':
        return 1.0
      case 'high':
        return 0.8
      case 'medium':
        return 0.6
      case 'low':
        return 0.4
      case 'none':
        return 0.2
      default:
        return 0.2
    }
  }, [threatLevel])

  // Initialize Three.js scene
  useEffect(() => {
    if (!mountRef.current) return

    const currentMount = mountRef.current

    // Scene setup
    const scene = new THREE.Scene()
    sceneRef.current = scene

    const width = currentMount.clientWidth
    const height = currentMount.clientHeight

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
    camera.position.z = 3

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setClearColor(0x000000, 0.1)
    currentMount.appendChild(renderer.domElement)
    rendererRef.current = renderer

    // Main orb geometry
    const orbGeometry = new THREE.IcosahedronGeometry(1, 32)
    const orbMaterial = new THREE.MeshPhongMaterial({
      color: modeColors.primary,
      emissive: modeColors.secondary,
      emissiveIntensity: threatIntensity * 0.8,
      wireframe: false,
      shininess: 100,
    })
    const orb = new THREE.Mesh(orbGeometry, orbMaterial)
    orbRef.current = orb
    scene.add(orb)

    // Glow layer
    const glowGeometry = new THREE.IcosahedronGeometry(1.1, 32)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: modeColors.glow,
      transparent: true,
      opacity: 0.3,
    })
    const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial)
    scene.add(glowMesh)

    // Particle system
    const particleCount = 200
    const particleGeometry = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount * 3; i += 3) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.random() * Math.PI
      const r = 1.2 + Math.random() * 1.5

      positions[i] = r * Math.sin(phi) * Math.cos(theta)
      positions[i + 1] = r * Math.sin(phi) * Math.sin(theta)
      positions[i + 2] = r * Math.cos(phi)
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    const particleMaterial = new THREE.PointsMaterial({
      color: modeColors.glow,
      size: 0.05,
      transparent: true,
      opacity: 0.6,
    })
    const particles = new THREE.Points(particleGeometry, particleMaterial)
    particlesRef.current = particles
    scene.add(particles)

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5)
    scene.add(ambientLight)

    const pointLight = new THREE.PointLight(modeColors.primary, 1)
    pointLight.position.set(2, 2, 2)
    scene.add(pointLight)

    // Animation loop
    let animationFrame = 0
    const animate = () => {
      animationFrame = requestAnimationFrame(animate)

      // Rotate orb
      if (orbRef.current) {
        orbRef.current.rotation.x += 0.001
        orbRef.current.rotation.y += 0.002

        // Pulse based on threat level
        const pulseScale = 1 + Math.sin(Date.now() * 0.003) * threatIntensity * 0.1
        orbRef.current.scale.set(pulseScale, pulseScale, pulseScale)
      }

      // Rotate glow
      glowMesh.rotation.z -= 0.003

      // Rotate particles
      if (particlesRef.current) {
        particlesRef.current.rotation.x += 0.0005
        particlesRef.current.rotation.y += 0.001
      }

      renderer.render(scene, camera)
    }
    animate()

    // Handle window resize
    const handleResize = () => {
      if (!currentMount) return
      const newWidth = currentMount.clientWidth
      const newHeight = currentMount.clientHeight
      camera.aspect = newWidth / newHeight
      camera.updateProjectionMatrix()
      renderer.setSize(newWidth, newHeight)
    }

    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize)
      cancelAnimationFrame(animationFrame)
      if (renderer.domElement.parentNode === currentMount) {
        currentMount.removeChild(renderer.domElement)
      }
      orbGeometry.dispose()
      orbMaterial.dispose()
      glowGeometry.dispose()
      glowMaterial.dispose()
      particleGeometry.dispose()
      particleMaterial.dispose()
      renderer.dispose()
    }
  }, [modeColors, threatIntensity])

  return (
    <div className={`relative w-full h-full ${className}`}>
      <div
        ref={mountRef}
        className="w-full h-full rounded-xl bg-gradient-to-b from-slate-900 to-slate-950"
      />

      {/* Info overlay */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-slate-950 via-slate-950/50 to-transparent rounded-b-xl">
        <div className="grid grid-cols-3 gap-2 text-sm">
          <div className="text-center">
            <div className="text-xs text-slate-400">Active Policies</div>
            <div className="text-lg font-bold text-green-400">{activePolicies}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-400">Alerts</div>
            <div className="text-lg font-bold text-orange-400">{alertCount}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-400">Uptime</div>
            <div className="text-lg font-bold text-blue-400">{Math.floor(uptime / 3600)}h</div>
          </div>
        </div>
      </div>
    </div>
  )
}
