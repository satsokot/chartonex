import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

interface StaggeredFadeProps {
  text: string
}

export default function StaggeredFade({ text }: StaggeredFadeProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const isInView = useInView(ref, { once: true })

  return (
    <span ref={ref}>
      {text.split('').map((char, i) => (
        <motion.span
          key={i}
          variants={{ hidden: { opacity: 0 }, show: { opacity: 1 } }}
          initial="hidden"
          animate={isInView ? 'show' : 'hidden'}
          transition={{ duration: 0.4, delay: i * 0.07 }}
          style={{ display: 'inline-block', whiteSpace: char === ' ' ? 'pre' : undefined }}
        >
          {char}
        </motion.span>
      ))}
    </span>
  )
}
