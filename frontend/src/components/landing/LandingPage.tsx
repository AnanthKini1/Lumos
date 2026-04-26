import { motion } from 'framer-motion'

interface Props {
  onBegin: () => void
}

const LUMOS_CHARS = ['L', 'u', 'm', 'o', 's']

const logoVariants = {
  hidden:  { opacity: 0, y: -24, scale: 0.92 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] },
  },
}

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07, delayChildren: 0.55 } },
}

const charVariants = {
  hidden:  { opacity: 0, y: 28, rotateX: 20 },
  visible: {
    opacity: 1,
    y: 0,
    rotateX: 0,
    transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
  },
}

const subtitleVariants = {
  hidden:  { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1], delay: 1.05 },
  },
}

const buttonVariants = {
  hidden:  { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1], delay: 1.35 },
  },
}

function LumosIcon({ size = 96 }: { size?: number }) {
  const r = size / 2
  const stroke = size * 0.085
  const inner = r - stroke / 2

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Lumos icon"
      data-testid="lumos-icon"
    >
      {/* Gold filled circle */}
      <circle cx={r} cy={r} r={inner} fill="#c9a96e" />

      {/* Black outer ring */}
      <circle cx={r} cy={r} r={inner} stroke="#0f0f0f" strokeWidth={stroke} />

      {/* Diagonal comet-tail swoosh — thick black line sweeping lower-left to upper-right */}
      <line
        x1={r * 0.22}
        y1={r * 1.72}
        x2={r * 1.6}
        y2={r * 0.3}
        stroke="#0f0f0f"
        strokeWidth={size * 0.09}
        strokeLinecap="round"
      />

      {/* 8-pointed star burst at upper-right */}
      {(() => {
        const cx = r * 1.38
        const cy = r * 0.46
        const outer = size * 0.19
        const innerR = size * 0.07
        const pts = Array.from({ length: 8 }, (_, i) => {
          const angle = (i * Math.PI) / 4 - Math.PI / 2
          const halfAngle = angle + Math.PI / 8
          const ox = cx + outer * Math.cos(angle)
          const oy = cy + outer * Math.sin(angle)
          const ix = cx + innerR * Math.cos(halfAngle)
          const iy = cy + innerR * Math.sin(halfAngle)
          return `${ox},${oy} ${ix},${iy}`
        })
        const d = `M ${pts.join(' L ')} Z`
        return <path d={d} fill="white" />
      })()}
    </svg>
  )
}

export default function LandingPage({ onBegin }: Props) {
  return (
    <div
      data-testid="landing-page"
      className="min-h-screen bg-[#fafafa] flex flex-col items-center justify-center"
    >
      <div className="flex flex-col items-start gap-0" style={{ minWidth: 320 }}>

        {/* Logo icon */}
        <motion.div
          variants={logoVariants}
          initial="hidden"
          animate="visible"
          className="mb-7 ml-1"
        >
          <LumosIcon size={88} />
        </motion.div>

        {/* "Lumos" — per-character staggered entrance */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          aria-label="Lumos"
          className="flex overflow-visible mb-2"
          style={{ perspective: 600 }}
        >
          {LUMOS_CHARS.map((char, i) => (
            <motion.span
              key={i}
              variants={charVariants}
              className="font-serif font-black text-[#0f0f0f] select-none leading-none"
              style={{ fontSize: 88, lineHeight: 1, display: 'inline-block' }}
            >
              {char}
            </motion.span>
          ))}
        </motion.div>

        {/* "Internal Mind Simulator" */}
        <motion.p
          variants={subtitleVariants}
          initial="hidden"
          animate="visible"
          data-testid="subtitle"
          className="font-mono text-base text-[#0f0f0f] opacity-55 tracking-widest uppercase ml-1 mb-12"
        >
          Internal Mind Simulator
        </motion.p>

        {/* Begin button */}
        <motion.div
          variants={buttonVariants}
          initial="hidden"
          animate="visible"
          className="ml-1"
        >
          <motion.button
            data-testid="begin-btn"
            onClick={onBegin}
            whileHover={{ scale: 1.03, backgroundColor: '#0f0f0f', color: '#fafafa' }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 400, damping: 22 }}
            className="font-serif font-bold text-xl text-[#0f0f0f] border-2 border-[#0f0f0f] px-10 py-3 bg-[#fafafa] cursor-pointer"
            style={{ letterSpacing: '0.04em' }}
          >
            Begin
          </motion.button>
        </motion.div>
      </div>
    </div>
  )
}
