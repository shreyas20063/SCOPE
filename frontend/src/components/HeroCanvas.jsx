import React, { useRef, useEffect } from 'react'

/*
 * Subtle discrete signal lollipop stems on left & right edges.
 * Matches the refined gradient palette. Sinusoidal, gently animated.
 */

const COLORS = [
  { r: 20, g: 184, b: 166 },   // teal
  { r: 124, g: 58, b: 237 },   // purple
  { r: 59, g: 130, b: 246 },   // blue
  { r: 20, g: 184, b: 166 },   // teal
  { r: 124, g: 58, b: 237 },   // purple
]

function HeroCanvas({ mousePos }) {
  const canvasRef = useRef(null)
  const animRef = useRef(null)
  const mouseRef = useRef({ x: -1, y: -1 })
  const smoothMouseRef = useRef({ x: -1, y: -1 })

  useEffect(() => {
    mouseRef.current = mousePos || { x: -1, y: -1 }
  }, [mousePos])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    let w = 0, h = 0

    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect()
      w = rect.width
      h = rect.height
      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    const observer = new ResizeObserver(resize)
    observer.observe(canvas.parentElement)
    resize()

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      observer.disconnect()
      return
    }

    const isMobile = window.innerWidth < 768
    const startTime = performance.now()

    const drawSide = (count, baseline, elapsed, isRight) => {
      const spacing = isMobile ? 16 : 13
      const maxH = h * 0.42
      const phase = elapsed * 0.35

      const smooth = smoothMouseRef.current
      const mouseActive = smooth.x >= 0
      const mx = smooth.x * w

      for (let i = 0; i < count; i++) {
        const x = isRight
          ? w - (count - i) * spacing
          : (i + 1) * spacing

        // Fade toward center
        const edgeDist = isRight ? (w - x) / w : x / w
        const fade = Math.min(1, edgeDist / (isMobile ? 0.25 : 0.22))
        if (fade < 0.02) continue

        // Sine value
        const val = Math.sin(2 * Math.PI * i * 0.13 + phase + (isRight ? Math.PI * 0.6 : 0))
        let stemH = val * maxH * 0.5

        // Mouse wobble
        if (mouseActive) {
          const dist = Math.abs(x - mx)
          if (dist < 120) {
            const prox = 1 - dist / 120
            stemH += prox * 12 * Math.sin(elapsed * 5 - dist * 0.06)
          }
        }

        const top = baseline - stemH
        const { r, g, b } = COLORS[i % COLORS.length]

        // Mouse glow boost
        let boost = 0
        if (mouseActive) {
          const dist = Math.abs(x - mx)
          if (dist < 80) boost = (1 - dist / 80) * 0.4
        }

        const alpha = (0.35 + 0.12 * Math.sin(elapsed * 0.6 + i * 0.4) + boost) * fade

        // Stem
        ctx.beginPath()
        ctx.moveTo(x, baseline)
        ctx.lineTo(x, top)
        ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.45})`
        ctx.lineWidth = isMobile ? 2 : 1.5
        ctx.stroke()

        // Dot — main
        const dotR = (isMobile ? 3.5 : 3) + boost * 2
        ctx.save()
        ctx.shadowColor = `rgba(${r}, ${g}, ${b}, ${alpha * 0.8})`
        ctx.shadowBlur = 10 + boost * 12
        ctx.beginPath()
        ctx.arc(x, top, dotR, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.85})`
        ctx.fill()
        ctx.restore()

        // Dot — bright core
        ctx.beginPath()
        ctx.arc(x, top, dotR * 0.4, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.5})`
        ctx.fill()
      }
    }

    const draw = (timestamp) => {
      animRef.current = requestAnimationFrame(draw)
      if (w === 0 || h === 0) return

      const elapsed = (timestamp - startTime) / 1000
      const mouse = mouseRef.current
      const smooth = smoothMouseRef.current

      // Smooth lerp
      if (mouse.x >= 0 && mouse.y >= 0) {
        if (smooth.x < 0) { smooth.x = mouse.x; smooth.y = mouse.y }
        else { smooth.x += (mouse.x - smooth.x) * 0.1; smooth.y += (mouse.y - smooth.y) * 0.1 }
      } else {
        smooth.x = -1; smooth.y = -1
      }

      ctx.clearRect(0, 0, w, h)

      const baseline = h * 0.68
      const count = isMobile
        ? Math.floor(w * 0.24 / 16)
        : Math.floor(w * 0.21 / 13)

      drawSide(count, baseline, elapsed, false)
      drawSide(count, baseline, elapsed, true)
    }

    animRef.current = requestAnimationFrame(draw)

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current)
      observer.disconnect()
    }
  }, [])

  return (
    <div className="hero-canvas-container">
      <canvas ref={canvasRef} />
    </div>
  )
}

export default React.memo(HeroCanvas)
