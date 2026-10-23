'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';

export default function Loading() {
  return (
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-ink">
      <div className="grain-overlay" />

      {/* Very faint brass ambient glow */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="h-72 w-72 rounded-full bg-[#B59A68]/6 blur-[100px]" />
      </div>

      <div className="relative flex flex-col items-center gap-10">
        {/* Official NyayaSarathi Emblem — slow dignified pulse */}
        <motion.div
          animate={{
            scale: [0.96, 1.04, 0.96],
            opacity: [0.85, 1, 0.85],
          }}
          transition={{
            duration: 3,
            ease: 'easeInOut',
            repeat: Infinity,
          }}
          className="relative w-20 h-20"
        >
          <Image
            src="/logo-transparent.png"
            alt="NyayaSarathi Emblem"
            width={80}
            height={80}
            className="w-full h-full object-contain drop-shadow-[0_4px_24px_rgba(181,154,104,0.4)]"
            priority
          />
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
