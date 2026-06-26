import { motion } from 'framer-motion';
import { ArrowRight, TrendingUp, Zap, Shield } from 'lucide-react';
import ChartAnimation from './ChartAnimation';

export default function Hero() {
  return (
    <section style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      padding: '120px 24px 80px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background glows */}
      <div style={{
        position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0,
      }}>
        <div style={{
          position: 'absolute', top: '10%', left: '15%', width: 500, height: 500,
          background: 'radial-gradient(circle, rgba(124, 58, 237, 0.18) 0%, transparent 70%)',
          borderRadius: '50%', filter: 'blur(40px)',
        }} />
        <div style={{
          position: 'absolute', top: '20%', right: '10%', width: 400, height: 400,
          background: 'radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, transparent 70%)',
          borderRadius: '50%', filter: 'blur(40px)',
        }} />
        <div style={{
          position: 'absolute', bottom: '10%', left: '40%', width: 300, height: 300,
          background: 'radial-gradient(circle, rgba(168, 85, 247, 0.1) 0%, transparent 70%)',
          borderRadius: '50%', filter: 'blur(60px)',
        }} />
      </div>

      {/* Grid pattern */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        backgroundImage: `
          linear-gradient(rgba(124, 58, 237, 0.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(124, 58, 237, 0.05) 1px, transparent 1px)
        `,
        backgroundSize: '60px 60px',
        maskImage: 'radial-gradient(ellipse at center, black 30%, transparent 80%)',
      }} />

      <div style={{ maxWidth: 1200, margin: '0 auto', width: '100%', position: 'relative', zIndex: 1 }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 60,
          alignItems: 'center',
        }} className="hero-grid">

          {/* Left: Text content */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(124, 58, 237, 0.12)',
                border: '1px solid rgba(124, 58, 237, 0.3)',
                borderRadius: 100,
                padding: '6px 16px',
                marginBottom: 28,
              }}
            >
              <Zap size={14} color="#A855F7" />
              <span style={{ fontSize: 13, color: '#A855F7', fontWeight: 600, letterSpacing: '0.05em' }}>
                Next-Gen Trading Intelligence
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontSize: 'clamp(36px, 5vw, 64px)',
                fontWeight: 700,
                lineHeight: 1.1,
                letterSpacing: '-0.03em',
                marginBottom: 24,
                color: '#F8FAFC',
              }}
            >
              Trade Smarter.{' '}
              <span style={{
                background: 'linear-gradient(135deg, #A855F7, #22D3EE)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>
                Go Beyond
              </span>{' '}
              the Charts.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              style={{
                fontSize: 18,
                color: '#94A3B8',
                lineHeight: 1.7,
                marginBottom: 40,
                maxWidth: 500,
              }}
            >
              Chartonex combines advanced market analysis, AI-driven signals, and real-time intelligence for crypto, gold, and forex — all in one unified platform.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}
            >
              <motion.button
                whileHover={{ scale: 1.04, boxShadow: '0 0 40px rgba(124, 58, 237, 0.5)' }}
                whileTap={{ scale: 0.97 }}
                style={{
                  background: 'linear-gradient(135deg, #7C3AED, #06B6D4)',
                  color: '#fff',
                  padding: '14px 32px',
                  borderRadius: 12,
                  fontSize: 15,
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  letterSpacing: '0.01em',
                  transition: 'box-shadow 0.3s',
                }}
              >
                Start Trading Now <ArrowRight size={16} />
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.04, borderColor: 'rgba(168,85,247,0.5)' }}
                whileTap={{ scale: 0.97 }}
                style={{
                  background: 'transparent',
                  color: '#94A3B8',
                  padding: '14px 32px',
                  borderRadius: 12,
                  fontSize: 15,
                  fontWeight: 600,
                  border: '1px solid rgba(255,255,255,0.12)',
                  transition: 'all 0.2s',
                }}
              >
                Watch Demo
              </motion.button>
            </motion.div>

            {/* Trust badges */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 24,
                marginTop: 40,
                flexWrap: 'wrap',
              }}
            >
              {[
                { icon: <TrendingUp size={14} />, text: '10+ Years Experience' },
                { icon: <Shield size={14} />, text: 'Secure & Transparent' },
                { icon: <Zap size={14} />, text: 'Real-time Signals' },
              ].map((item, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  color: '#64748B', fontSize: 13, fontWeight: 500,
                }}>
                  <span style={{ color: '#7C3AED' }}>{item.icon}</span>
                  {item.text}
                </div>
              ))}
            </motion.div>
          </div>

          {/* Right: Chart visualization */}
          <motion.div
            initial={{ opacity: 0, x: 60 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            style={{ position: 'relative' }}
            className="hero-chart"
          >
            <ChartAnimation />
          </motion.div>
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .hero-grid {
            grid-template-columns: 1fr !important;
            gap: 40px !important;
          }
          .hero-chart {
            order: -1;
          }
        }
      `}</style>
    </section>
  );
}
