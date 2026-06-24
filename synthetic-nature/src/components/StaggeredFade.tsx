import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

interface StaggeredFadeProps {
  text: string
}

const containerVariants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.07,
    },
  },
}

const charVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1 },
}

export default function StaggeredFade({ text }: StaggeredFadeProps) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })

  return (
    <motion.div
      ref={ref}
      variants={containerVariants}
      initial="hidden"
      animate={isInView ? 'show' : 'hidden'}
      style={{ display: 'inline' }}
    >
      {text.split('').map((char, index) => (
        <motion.span
          key={index}
          variants={charVariants}
          transition={{ delay: index * 0.07, duration: 0.4 }}
          style={{ display: 'inline-block', whiteSpace: char === ' ' ? 'pre' : 'normal' }}
        >
          {char === ' ' ? ' ' : char}
        </motion.span>
      ))}
    </motion.div>
  )
}
