export default function Logo({ size = 36 }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      {/* SVG Logo: C + X combined into ascending chart path */}
      <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="logoGrad" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
            <stop stopColor="#A855F7" />
            <stop offset="1" stopColor="#22D3EE" />
          </linearGradient>
          <linearGradient id="logoGrad2" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
            <stop stopColor="#7C3AED" stopOpacity="0.3" />
            <stop offset="1" stopColor="#06B6D4" stopOpacity="0.3" />
          </linearGradient>
        </defs>
        {/* Background rounded rect */}
        <rect width="48" height="48" rx="12" fill="url(#logoGrad2)" />
        <rect width="48" height="48" rx="12" stroke="url(#logoGrad)" strokeWidth="1" fill="none" />

        {/* C shape - left arc */}
        <path
          d="M28 10 C18 10, 10 17, 10 24 C10 31, 18 38, 28 38"
          stroke="url(#logoGrad)"
          strokeWidth="3.5"
          strokeLinecap="round"
          fill="none"
        />

        {/* X shape - ascending diagonal (chart line) */}
        <path
          d="M30 14 L42 34"
          stroke="url(#logoGrad)"
          strokeWidth="3.5"
          strokeLinecap="round"
        />
        <path
          d="M30 34 L42 14"
          stroke="url(#logoGrad)"
          strokeWidth="3.5"
          strokeLinecap="round"
        />

        {/* Small chart dots */}
        <circle cx="30" cy="34" r="2" fill="#22D3EE" opacity="0.8" />
        <circle cx="36" cy="24" r="2" fill="#A855F7" opacity="0.8" />
        <circle cx="42" cy="14" r="2" fill="#22D3EE" opacity="0.8" />
      </svg>

      <div>
        <span style={{
          fontFamily: "'Space Grotesk', sans-serif",
          fontSize: size * 0.55,
          fontWeight: 700,
          background: 'linear-gradient(135deg, #A855F7, #22D3EE)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          letterSpacing: '-0.02em',
          lineHeight: 1,
        }}>
          Chartonex
        </span>
        <div style={{
          fontSize: size * 0.22,
          color: '#64748B',
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          fontWeight: 500,
          lineHeight: 1,
          marginTop: 2,
        }}>
          Beyond Charts
        </div>
      </div>
    </div>
  );
}
