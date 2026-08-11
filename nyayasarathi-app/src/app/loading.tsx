'use client';

import { motion } from 'framer-motion';
import { Scale } from 'lucide-react';

export default function Loading() {
  return (
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-ink">
      <div className="grain-overlay" />

      {/* Very faint brass ambient glow */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="h-72 w-72 rounded-full bg-[#B59A68]/6 blur-[100px]" />
      </div>

      <div className="relative flex flex-col items-center gap-10">
        {/* Scales of Justice — slow, dignified tilt */}
        <motion.div
          animate={{
            rotate: [-5, 5, -5],
            y: [-2, 2, -2],
          }}
          transition={{
            rotate: { duration: 4.5, ease: 'easeInOut', repeat: Infinity },
            y: { duration: 2.25, ease: 'easeInOut', repeat: Infinity },
          }}
          className="text-[#B59A68] opacity-80"
        >
          <Scale size={56} strokeWidth={1.2} />
        </motion.div>

        <div className="flex flex-col items-center gap-4">
          {/* Wordmark */}
          <motion.h2
            className="font-display text-3xl font-semibold tracking-[0.15em] text-ivory/85"
            style={{ letterSpacing: '0.18em' }}
            animate={{ opacity: [0.5, 0.9, 0.5] }}
            transition={{ duration: 3, ease: 'easeInOut', repeat: Infinity }}
          >
            NYAYASARATHI
          </motion.h2>

          {/* Editorial subtitle */}
          <p className="font-sans text-[10px] tracking-[0.35em] uppercase text-stone/60">
            Judicial Intelligence Platform
          </p>

          {/* Restrained oxblood loading dots */}
          <div className="flex items-center gap-2 mt-2">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="h-1 w-1 rounded-full bg-[#6E2634]"
                animate={{ scale: [1, 1.8, 1], opacity: [0.25, 1, 0.25] }}
                transition={{
                  duration: 1.8,
                  repeat: Infinity,
                  delay: i * 0.25,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Bottom thin border line */}
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-[#3B3A33]" />
    </div>
  );
}
