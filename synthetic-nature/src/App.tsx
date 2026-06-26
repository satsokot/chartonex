import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X } from 'lucide-react'
import StaggeredFade from './components/StaggeredFade'

const NAV_LINKS = ['Wander', 'Archive', 'Story', 'Connect']

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div
      className="relative overflow-hidden bg-[#010101]"
      style={{ minHeight: '100vh' }}
    >

      {/* ════════════════════════════════
          VIDEO BACKGROUND
      ════════════════════════════════ */}
      <div className="absolute inset-0 w-full h-full">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="object-cover object-center w-full h-full"
        >
          <source
            src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260619_191346_9d19d66e-86a4-47f7-8dc6-712c1788c3b2.mp4"
            type="video/mp4"
          />
        </video>
      </div>

      {/* ════════════════════════════════
          NAVIGATION
      ════════════════════════════════ */}
      <nav className="relative z-20 flex justify-between md:justify-center items-center px-6 py-6 sm:px-10 sm:py-8">

        {/* Brand */}
        <span
          className="text-white uppercase font-light text-sm sm:text-base md:absolute md:left-10"
          style={{ letterSpacing: '0.25em' }}
        >
          <span className="hidden sm:inline" style={{ letterSpacing: '0.3em' }}>
            Organic Visions
          </span>
          <span className="sm:hidden" style={{ letterSpacing: '0.25em' }}>
            Organic Visions
          </span>
        </span>

        {/* Desktop links — centered */}
        <div className="hidden md:flex items-center gap-10">
          {NAV_LINKS.map(link => (
            <a
              key={link}
              href="#"
              className="text-white/80 uppercase text-xs transition-colors duration-300 hover:text-white"
              style={{ letterSpacing: '0.2em' }}
            >
              {link}
            </a>
          ))}
        </div>

        {/* Hamburger — mobile only */}
        <button
          className="md:hidden text-white bg-transparent border-none outline-none"
          onClick={() => setMenuOpen(v => !v)}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
        >
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      {/* ════════════════════════════════
          MOBILE MENU
      ════════════════════════════════ */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            className="fixed top-16 left-4 right-4 z-50 md:hidden mobile-menu-glass rounded-2xl py-8"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          >
            <div className="flex flex-col items-center gap-5">
              {NAV_LINKS.map((link, index) => (
                <motion.div
                  key={link}
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 + index * 0.06, duration: 0.25 }}
                >
                  <a
                    href="#"
                    className="text-white/90 uppercase font-light transition-colors duration-200 hover:text-white"
                    style={{ letterSpacing: '0.25em' }}
                    onClick={() => setMenuOpen(false)}
                  >
                    {link}
                  </a>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ════════════════════════════════
          HERO CONTENT
      ════════════════════════════════ */}
      <div
        className="relative z-10 flex flex-col items-center justify-center text-center min-h-screen px-5 sm:px-8 pt-12 sm:pt-16 md:pt-24"
      >
        {/* ── Heading ── */}
        <h1
          className="font-garamond font-normal text-white text-4xl sm:text-6xl md:text-8xl lg:text-9xl tracking-tight mb-6 sm:mb-8"
          style={{ lineHeight: 1.08 }}
        >
          <div><StaggeredFade text="WITNESS THE" /></div>
          <div><StaggeredFade text="HIDDEN REALM" /></div>
        </h1>

        {/* ── Subtitle ── */}
        <motion.p
          className="text-white/70 font-light leading-relaxed text-sm sm:text-base lg:text-lg max-w-xs sm:max-w-md mb-8 sm:mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.6 }}
        >
          An odyssey through delicate living forms,{' '}
          <br className="hidden sm:block" />
          revealed by lens and curiosity.
        </motion.p>

        {/* ── CTA Button ── */}
        <motion.button
          className="liquid-glass rounded-full px-7 py-3.5 sm:px-10 sm:py-4 text-white/90 uppercase text-xs sm:text-sm cursor-pointer"
          style={{ letterSpacing: '0.18em' }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 2.0 }}
        >
          <span className="hidden sm:inline" style={{ letterSpacing: '0.2em' }}>
            Begin the Experience
          </span>
          <span className="sm:hidden" style={{ letterSpacing: '0.18em' }}>
            Begin the Experience
          </span>
        </motion.button>
      </div>

    </div>
  )
}
