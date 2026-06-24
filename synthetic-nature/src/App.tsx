import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X } from 'lucide-react'
import StaggeredFade from './components/StaggeredFade'

const navLinks = ['Wander', 'Archive', 'Story', 'Connect']

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen overflow-hidden bg-[#010101] relative">

      {/* ── Video Background ── */}
      <div className="absolute inset-0 w-full h-full">
        <video
          autoPlay
          muted
          loop
          playsInline
          style={{
            objectFit: 'cover',
            objectPosition: 'center',
            width: '100%',
            height: '100%',
          }}
        >
          <source
            src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260619_191346_9d19d66e-86a4-47f7-8dc6-712c1788c3b2.mp4"
            type="video/mp4"
          />
        </video>
      </div>

      {/* ── Navigation ── */}
      <nav className="relative z-20 flex justify-between md:justify-center px-6 py-6 sm:px-10 sm:py-8">

        {/* Brand */}
        <span
          className="text-white uppercase font-light text-sm sm:text-base md:absolute md:left-10"
          style={{ letterSpacing: '0.25em' }}
        >
          <span className="hidden sm:inline" style={{ letterSpacing: '0.3em' }}>Organic Visions</span>
          <span className="sm:hidden">Organic Visions</span>
        </span>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-10">
          {navLinks.map(link => (
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

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-white bg-transparent"
          onClick={() => setMenuOpen(prev => !prev)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      {/* ── Mobile Menu ── */}
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
              {navLinks.map((link, index) => (
                <motion.div
                  key={link}
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 + index * 0.06, duration: 0.25 }}
                >
                  <a
                    href="#"
                    className="text-white/90 uppercase font-light hover:text-white transition-colors duration-200"
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

      {/* ── Hero Content ── */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center min-h-screen px-5 pt-12 sm:px-8 sm:pt-16 md:pt-24" style={{ marginTop: '-72px' }}>

        {/* Heading */}
        <h1
          className="font-garamond font-normal text-white text-4xl sm:text-6xl md:text-8xl lg:text-9xl tracking-tight mb-6 sm:mb-8"
          style={{ lineHeight: 1.08 }}
        >
          <div>
            <StaggeredFade text="WITNESS THE" />
          </div>
          <div>
            <StaggeredFade text="HIDDEN REALM" />
          </div>
        </h1>

        {/* Subtitle */}
        <motion.p
          className="text-white/70 font-light leading-relaxed text-sm sm:text-base lg:text-lg max-w-xs sm:max-w-md mb-8 sm:mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.6 }}
        >
          An odyssey through delicate living forms,
          <br className="hidden sm:block" />
          revealed by lens and curiosity.
        </motion.p>

        {/* CTA Button */}
        <motion.button
          className="liquid-glass rounded-full px-7 py-3.5 sm:px-10 sm:py-4 text-white/90 uppercase text-xs sm:text-sm"
          style={{ letterSpacing: '0.18em' }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 2.0 }}
        >
          Begin the Experience
        </motion.button>
      </div>

    </div>
  )
}
