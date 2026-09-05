'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale, Sparkles, ShieldCheck, Database, FileText, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';

const EASE = [0.16, 1, 0.3, 1] as const;

export function AuthBrandPanel() {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="relative flex flex-col justify-between h-full p-4 sm:p-6 lg:p-7 xl:p-8 border-b lg:border-b-0 lg:border-r border-[#3B3A33]/70 overflow-hidden bg-[#151716] select-none">
      {/* Subtle fine architectural corner lines */}
      <div className="absolute top-5 left-5 w-4 h-4 border-t border-l border-[#B59A68]/30 pointer-events-none hidden sm:block" />
      <div className="absolute top-5 right-5 w-4 h-4 border-t border-r border-[#B59A68]/30 pointer-events-none hidden sm:block" />
      <div className="absolute bottom-5 left-5 w-4 h-4 border-b border-l border-[#B59A68]/30 pointer-events-none hidden sm:block" />
      <div className="absolute bottom-5 right-5 w-4 h-4 border-b border-r border-[#B59A68]/30 pointer-events-none hidden sm:block" />

      {/* Atmospheric ambient radiant glow that deepens dynamically on hover */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <motion.div
          animate={{
            scale: isHovered ? 1.25 : 1,
            opacity: isHovered ? 0.15 : 0.07,
          }}
          transition={{ duration: 0.8, ease: EASE }}
          className="w-[340px] h-[340px] sm:w-[460px] sm:h-[460px] rounded-full bg-[#B59A68] blur-[90px]"
        />
        <motion.div
          animate={{
            scale: isHovered ? 1.3 : 1,
            opacity: isHovered ? 0.3 : 0.15,
          }}
          transition={{ duration: 0.8, ease: EASE }}
          className="w-[200px] h-[200px] sm:w-[280px] sm:h-[280px] rounded-full bg-[#6E2634] blur-[70px]"
        />
      </div>

      {/* ── Center Section: Grand 2D Revolving Emblem & Headline ────────────── */}
      <div className="relative z-10 my-auto py-1 sm:py-2 flex flex-col items-center justify-center">
        {/* Responsive 2D Revolving Sacred Shloka Insignia */}
        <motion.div
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.035 }}
          transition={{ duration: 0.4, ease: EASE }}
          className="relative w-full max-w-[280px] sm:max-w-[340px] lg:max-w-[380px] xl:max-w-[420px] 2xl:max-w-[450px] aspect-square flex items-center justify-center cursor-pointer select-none"
        >
          <svg
            viewBox="0 0 500 500"
            className="w-full h-full drop-shadow-[0_16px_45px_rgba(0,0,0,0.85)] transition-all duration-500"
            aria-label="NyayaSarathi Sacred Judicial Insignia"
          >
            <defs>
              {/* Circular path for outer revolving Sanskrit shloka (radius: 185) */}
              <path
                id="shlokaCirclePath"
                d="M 250, 250 m -185, 0 a 185,185 0 1,1 370,0 a 185,185 0 1,1 -370,0"
              />

              {/* Central Badge Radial Gradient */}
              <radialGradient id="badgeGradient" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#28302C" />
                <stop offset="60%" stopColor="#181D1B" />
                <stop offset="100%" stopColor="#0F1211" />
              </radialGradient>

              {/* Metallic Brass Gradients */}
              <linearGradient id="brassMetallic" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#F7EEDC" />
                <stop offset="25%" stopColor="#B59A68" />
                <stop offset="70%" stopColor="#7E673B" />
                <stop offset="100%" stopColor="#E4D2AA" />
              </linearGradient>

              <linearGradient id="goldBeam" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#876F43" />
                <stop offset="50%" stopColor="#FFF2D6" />
                <stop offset="100%" stopColor="#876F43" />
              </linearGradient>

              {/* Glow filter for hover state */}
              <filter id="goldGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Outermost subtle guide ring */}
            <circle
              cx="250"
              cy="250"
              r="238"
              fill="none"
              stroke="#B59A68"
              strokeWidth="0.75"
              strokeDasharray="2 6"
              opacity={isHovered ? 0.5 : 0.25}
              className="transition-opacity duration-500"
            />

            {/* Counter-rotating celestial ticks ring */}
            <motion.g
              animate={{ rotate: -360 }}
              transition={{
                repeat: Infinity,
                duration: isHovered ? 22 : 50,
                ease: 'linear',
              }}
              style={{ transformOrigin: '250px 250px' }}
            >
              <circle
                cx="250"
                cy="250"
                r="226"
                fill="none"
                stroke="#B59A68"
                strokeWidth="1.2"
                strokeDasharray="3 9"
                opacity={isHovered ? 0.65 : 0.3}
                className="transition-opacity duration-500"
              />
            </motion.g>

            {/* Outer text track boundary ring */}
            <circle
              cx="250"
              cy="250"
              r="212"
              fill="none"
              stroke="url(#brassMetallic)"
              strokeWidth={isHovered ? 1.8 : 1.3}
              opacity={isHovered ? 0.85 : 0.5}
              className="transition-all duration-500"
            />

            {/* Revolving Sanskrit Shloka Ring with dynamic speed on hover */}
            <motion.g
              animate={{ rotate: 360 }}
              transition={{
                repeat: Infinity,
                duration: isHovered ? 16 : 32,
                ease: 'linear',
              }}
              style={{ transformOrigin: '250px 250px' }}
            >
              <text
                fill={isHovered ? '#FFF6DE' : '#DFCBA1'}
                filter={isHovered ? 'url(#goldGlow)' : undefined}
                className="transition-colors duration-300"
                style={{
                  fontFamily: 'var(--font-devanagari), "Noto Sans Devanagari", serif',
                  fontSize: '14.5px',
                  fontWeight: 600,
                  letterSpacing: '0.14em',
                }}
              >
                <textPath
                  href="#shlokaCirclePath"
                  startOffset="0%"
                  textLength="1160"
                  lengthAdjust="spacing"
                >
                  ॥ यतो धर्मस्ततो जयः ॥ धर्मो रक्षति रक्षितः ॥ सत्यमेव जयते नानृतम् ॥ न्यायमूलं स्वराज्यम् ॥
                </textPath>
              </text>
            </motion.g>

            {/* Inner text track boundary ring */}
            <circle
              cx="250"
              cy="250"
              r="160"
              fill="none"
              stroke="url(#brassMetallic)"
              strokeWidth={isHovered ? 1.8 : 1.3}
              opacity={isHovered ? 0.85 : 0.5}
              className="transition-all duration-500"
            />

            {/* Counter-rotating dashed orbital accent */}
            <motion.g
              animate={{ rotate: -360 }}
              transition={{
                repeat: Infinity,
                duration: isHovered ? 18 : 36,
                ease: 'linear',
              }}
              style={{ transformOrigin: '250px 250px' }}
            >
              <circle
                cx="250"
                cy="250"
                r="150"
                fill="none"
                stroke="#B59A68"
                strokeWidth="1"
                strokeDasharray="4 8"
                opacity={isHovered ? 0.6 : 0.35}
                className="transition-opacity duration-500"
              />
            </motion.g>

            {/* Central Emblem Main Disc */}
            <circle
              cx="250"
              cy="250"
              r="138"
              fill="url(#badgeGradient)"
              stroke="url(#brassMetallic)"
              strokeWidth={isHovered ? 3.2 : 2.6}
              className="transition-all duration-500"
            />

            {/* Inner fine concentric decorative circle */}
            <circle
              cx="250"
              cy="250"
              r="128"
              fill="none"
              stroke="#B59A68"
              strokeWidth="1"
              strokeDasharray="2 5"
              opacity={isHovered ? 0.65 : 0.35}
              className="transition-opacity duration-500"
            />

            {/* 4 Cardinal Diamond Accents */}
            <g opacity={isHovered ? 1 : 0.75} className="transition-opacity duration-300">
              <path d="M 250 120 L 253 124 L 250 128 L 247 124 Z" fill="#F4E8CF" />
              <path d="M 250 380 L 253 376 L 250 372 L 247 376 Z" fill="#F4E8CF" />
              <path d="M 120 250 L 124 253 L 128 250 L 124 247 Z" fill="#F4E8CF" />
              <path d="M 380 250 L 376 253 L 372 250 L 376 247 Z" fill="#F4E8CF" />
            </g>

            {/* Central Scales of Justice Emblem with interactive balance physics */}
            <g transform="translate(182, 182) scale(2.83)">
              {/* Central Pillar */}
              <path
                d="M24 6V42"
                stroke={isHovered ? '#EBD8B2' : '#B59A68'}
                strokeWidth="1.8"
                strokeLinecap="round"
                className="transition-colors duration-300"
              />
              {/* Top Finial */}
              <path
                d="M24 4L26 6L24 8L22 6L24 4Z"
                fill={isHovered ? '#FFFFFF' : '#DFCBA1'}
                className="transition-colors duration-300"
              />
              {/* Base Pedestal */}
              <path
                d="M16 42H32"
                stroke={isHovered ? '#EBD8B2' : '#B59A68'}
                strokeWidth="2.2"
                strokeLinecap="round"
                className="transition-colors duration-300"
              />
              <path
                d="M19 38H29"
                stroke="#B59A68"
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeOpacity={isHovered ? 1 : 0.8}
              />

              {/* Dynamic Oscillating Balance Beam */}
              <motion.g
                animate={
                  isHovered
                    ? {
                        rotate: [-2.5, 2.5, -2, 1.8, 0],
                        transition: { duration: 2.2, ease: 'easeInOut', repeat: Infinity },
                      }
                    : { rotate: 0 }
                }
                style={{ transformOrigin: '24px 14px' }}
              >
                {/* Horizontal Balance Beam */}
                <path
                  d="M10 14H38"
                  stroke="url(#goldBeam)"
                  strokeWidth="1.9"
                  strokeLinecap="round"
                />

                {/* Left Scale Strings & Pan */}
                <path
                  d="M10 14L6 26M10 14L14 26"
                  stroke={isHovered ? '#F7EEDC' : '#B59A68'}
                  strokeWidth="1.1"
                  strokeLinecap="round"
                  strokeOpacity="0.9"
                  className="transition-colors duration-300"
                />
                <path
                  d="M5 26C5 26 7 29 10 29C13 29 15 26 15 26H5Z"
                  fill="#B59A68"
                  fillOpacity={isHovered ? 0.38 : 0.22}
                  stroke={isHovered ? '#FFFFFF' : '#DFCBA1'}
                  strokeWidth="1.3"
                  strokeLinejoin="round"
                  className="transition-all duration-300"
                />

                {/* Right Scale Strings & Pan */}
                <path
                  d="M38 14L34 26M38 14L42 26"
                  stroke={isHovered ? '#F7EEDC' : '#B59A68'}
                  strokeWidth="1.1"
                  strokeLinecap="round"
                  strokeOpacity="0.9"
                  className="transition-colors duration-300"
                />
                <path
                  d="M33 26C33 26 35 29 38 29C41 29 43 26 43 26H33Z"
                  fill="#B59A68"
                  fillOpacity={isHovered ? 0.38 : 0.22}
                  stroke={isHovered ? '#FFFFFF' : '#DFCBA1'}
                  strokeWidth="1.3"
                  strokeLinejoin="round"
                  className="transition-all duration-300"
                />
              </motion.g>

              {/* Center Fulcrum Pivot */}
              <circle
                cx="24"
                cy="14"
                r="2.2"
                fill="#181C1A"
                stroke={isHovered ? '#FFFFFF' : '#DFCBA1'}
                strokeWidth="1.5"
                className="transition-colors duration-300"
              />

              {/* Antique Oxblood Ruby Axis Accent */}
              <circle
                cx="24"
                cy="26"
                r="1.2"
                fill={isHovered ? '#DC3854' : '#8A3545'}
                className="transition-colors duration-300"
              />
            </g>
          </svg>
        </motion.div>

        {/* Dynamic Sacred Shloka Meaning Reveal */}
        <div className="mt-2 min-h-[22px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {isHovered ? (
              <motion.div
                key="translation"
                initial={{ opacity: 0, y: 3, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -3, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-1.5"
              >
                <Sparkles className="w-3 h-3 text-[#B59A68]" />
                <span className="font-serif italic text-xs sm:text-[13px] text-[#F4EFE5] tracking-wide">
                  &ldquo;Where there is Dharma &amp; Truth, there is Victory&rdquo;
                </span>
              </motion.div>
            ) : (
              <motion.div
                key="tagline"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-2"
              >
                <div className="w-6 h-px bg-[#3B3A33]" />
                <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#A9A49A]/80">
                  ॥ यतो धर्मस्ततो जयः ॥
                </span>
                <div className="w-6 h-px bg-[#3B3A33]" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Informative Editorial Headline & Philosophy */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE, delay: 0.1 }}
          className="text-center max-w-lg mt-2 sm:mt-3 space-y-1"
        >
          <h1 className="font-display text-lg sm:text-xl lg:text-[1.35rem] font-medium leading-[1.2] text-[#F4EFE5] tracking-[-0.01em]">
            Find the Law. Understand the Precedent. Verify the Source.
          </h1>
          <p className="font-sans text-[11px] sm:text-xs text-[#A9A49A] leading-relaxed max-w-md mx-auto">
            AI-driven constitutional search, citation graphs, and verifiable judgment analysis indexing 75+ years of Indian jurisprudence.
          </p>
        </motion.div>
      </div>

      {/* ── Open Informative Feature Pillars (Unboxed, Full Canvas) ────────── */}
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE, delay: 0.2 }}
        className="relative z-10 pt-3 border-t border-[#3B3A33]/50 space-y-2 shrink-0"
      >
        {/* Floating 4-Column Intelligence Telemetry */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 py-0.5">
          <div className="flex flex-col space-y-0.5">
            <span className="font-display text-sm sm:text-base font-semibold text-[#B59A68]">2.4M+</span>
            <span className="font-mono text-[8.5px] uppercase tracking-wider text-[#F4EFE5]">Citations</span>
            <span className="font-sans text-[9.5px] text-[#A9A49A]/70">Supreme &amp; High Courts</span>
          </div>

          <div className="flex flex-col space-y-0.5 sm:border-l sm:border-[#3B3A33]/50 sm:pl-2.5">
            <span className="font-display text-sm sm:text-base font-semibold text-[#F4EFE5]">75+ Years</span>
            <span className="font-mono text-[8.5px] uppercase tracking-wider text-[#F4EFE5]">Archive</span>
            <span className="font-sans text-[9.5px] text-[#A9A49A]/70">1950 &ndash; Present</span>
          </div>

          <div className="flex flex-col space-y-0.5 sm:border-l sm:border-[#3B3A33]/50 sm:pl-2.5">
            <span className="font-display text-sm sm:text-base font-semibold text-[#71877A]">Zero Hallucination</span>
            <span className="font-mono text-[8.5px] uppercase tracking-wider text-[#F4EFE5]">Constitutional RAG</span>
            <span className="font-sans text-[9.5px] text-[#A9A49A]/70">Verifiable Paragraphs</span>
          </div>

          <div className="flex flex-col space-y-0.5 sm:border-l sm:border-[#3B3A33]/50 sm:pl-2.5">
            <span className="font-display text-sm sm:text-base font-semibold text-[#8A3545]">Dual Corpus</span>
            <span className="font-mono text-[8.5px] uppercase tracking-wider text-[#F4EFE5]">Bilingual</span>
            <span className="font-sans text-[9.5px] text-[#A9A49A]/70">English &amp; Hindi</span>
          </div>
        </div>

        {/* Bottom Sub-Line */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pt-1.5 border-t border-[#3B3A33]/30 text-[8.5px] sm:text-[9.5px] font-mono text-[#A9A49A]/50 uppercase tracking-widest">
          <span>INDIAN JUDICIAL ARCHIVE</span>
          <span>CANONICAL CITATION ENGINE &bull; 100% SOURCED</span>
        </div>
      </motion.div>
    </div>
  );
}

export default AuthBrandPanel;





