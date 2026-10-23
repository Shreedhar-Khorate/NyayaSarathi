'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles } from 'lucide-react';

const EASE = [0.16, 1, 0.3, 1] as const;

export function AuthBrandPanel() {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="relative flex flex-col justify-center items-center h-full p-4 sm:p-6 lg:p-8 xl:p-10 border-b lg:border-b-0 lg:border-r border-[#3B3A33]/70 overflow-hidden bg-[#151716] select-none">
      {/* Subtle fine architectural corner lines */}
      <div className="absolute top-4 left-4 w-3.5 h-3.5 border-t border-l border-[#B59A68]/30 pointer-events-none hidden sm:block" />
      <div className="absolute top-4 right-4 w-3.5 h-3.5 border-t border-r border-[#B59A68]/30 pointer-events-none hidden sm:block" />
      <div className="absolute bottom-4 left-4 w-3.5 h-3.5 border-b border-l border-[#B59A68]/30 pointer-events-none hidden sm:block" />
      <div className="absolute bottom-4 right-4 w-3.5 h-3.5 border-b border-r border-[#B59A68]/30 pointer-events-none hidden sm:block" />

      {/* Atmospheric ambient radiant glow that deepens dynamically on hover */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <motion.div
          animate={{
            scale: isHovered ? 1.2 : 1,
            opacity: isHovered ? 0.16 : 0.08,
          }}
          transition={{ duration: 0.8, ease: EASE }}
          className="w-[280px] h-[280px] sm:w-[380px] sm:h-[380px] lg:w-[460px] lg:h-[460px] rounded-full bg-[#B59A68] blur-[90px]"
        />
        <motion.div
          animate={{
            scale: isHovered ? 1.25 : 1,
            opacity: isHovered ? 0.3 : 0.15,
          }}
          transition={{ duration: 0.8, ease: EASE }}
          className="w-[180px] h-[180px] sm:w-[260px] sm:h-[260px] lg:w-[320px] lg:h-[320px] rounded-full bg-[#6E2634] blur-[70px]"
        />
      </div>

      {/* ── Center Section: Grand 2D Revolving Emblem & Headline ────────────── */}
      <div className="relative z-10 my-auto py-1 sm:py-2 flex flex-col items-center justify-center w-full max-w-lg">
        {/* Responsive 2D Revolving Sacred Shloka Insignia */}
        <motion.div
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.4, ease: EASE }}
          className="relative w-full max-w-[170px] sm:max-w-[220px] md:max-w-[260px] lg:max-w-[310px] xl:max-w-[360px] 2xl:max-w-[400px] max-h-[30vh] aspect-square flex items-center justify-center cursor-pointer select-none"
        >
          <svg
            viewBox="0 0 500 500"
            className="w-full h-full drop-shadow-[0_24px_64px_rgba(0,0,0,0.95)] transition-all duration-500"
            aria-label="NyayaSarathi Sacred Judicial Insignia"
          >
            <defs>
              {/* Circular path for outer revolving Sanskrit shloka (radius: 196) */}
              <path
                id="shlokaCirclePath"
                d="M 250, 250 m -196, 0 a 196,196 0 1,1 392,0 a 196,196 0 1,1 -392,0"
              />

              {/* Central Badge Radial Gradient */}
              <radialGradient id="badgeGradient" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#252D29" />
                <stop offset="65%" stopColor="#151A18" />
                <stop offset="100%" stopColor="#0B0E0D" />
              </radialGradient>

              {/* Metallic Brass Gradients */}
              <linearGradient id="brassMetallic" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#F9F2E3" />
                <stop offset="25%" stopColor="#D4BA82" />
                <stop offset="65%" stopColor="#8A7042" />
                <stop offset="100%" stopColor="#EAD8B2" />
              </linearGradient>

              <linearGradient id="goldBeam" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#B59A68" stopOpacity="0.6" />
                <stop offset="50%" stopColor="#FFF9EE" stopOpacity="1" />
                <stop offset="100%" stopColor="#B59A68" stopOpacity="0.6" />
              </linearGradient>

              {/* Medallion Depth Gradient */}
              <radialGradient id="medallionDepth" cx="50%" cy="45%" r="55%">
                <stop offset="0%" stopColor="#1E2522" />
                <stop offset="60%" stopColor="#141816" />
                <stop offset="100%" stopColor="#0D100F" />
              </radialGradient>

              {/* Subtle Gold Shadow Filter */}
              <filter id="goldGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3.5" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* 1. Deep Obsidian Outer Shield Ring with Precision Brass Bevel */}
            <circle
              cx="250"
              cy="250"
              r="240"
              fill="url(#badgeGradient)"
              stroke="#B59A68"
              strokeWidth="2.5"
              strokeOpacity="0.8"
            />
            <circle
              cx="250"
              cy="250"
              r="234"
              fill="none"
              stroke="#B59A68"
              strokeWidth="0.75"
              strokeDasharray="2 3"
              strokeOpacity="0.4"
            />

            {/* 2. Cardinal Precision Pointers (North, East, South, West) */}
            <g fill="#B59A68" stroke="#B59A68" strokeWidth="0.8">
              {/* North */}
              <polygon points="250,5 255,16 250,13 245,16" />
              {/* South */}
              <polygon points="250,495 255,484 250,487 245,484" />
              {/* East */}
              <polygon points="495,250 484,255 487,250 484,245" />
              {/* West */}
              <polygon points="5,250 16,255 13,250 16,245" />
            </g>

            {/* 3. Orbit Track for Compass Satellite */}
            <circle
              cx="250"
              cy="250"
              r="224"
              fill="none"
              stroke="#B59A68"
              strokeWidth="0.75"
              strokeDasharray="3 6"
              strokeOpacity="0.35"
            />

            {/* 4. Sanskrit Shloka Track Framing Borders */}
            <circle
              cx="250"
              cy="250"
              r="214"
              fill="none"
              stroke="#B59A68"
              strokeWidth="1.2"
              strokeOpacity="0.65"
            />
            <circle
              cx="250"
              cy="250"
              r="178"
              fill="none"
              stroke="#6E2634"
              strokeWidth="1.5"
              strokeOpacity="0.75"
            />

            {/* 5. Continuous Balanced Sanskrit Shloka Ring */}
            {/* 4 balanced sacred sutras connected by golden star gems filling the entire 360° circumference */}
            <g className="origin-center animate-[spin_52s_linear_infinite] hover:[animation-play-state:paused]">
              <text
                className="fill-[#EAD8B2] font-serif text-[11.5px] font-semibold tracking-[0.24em] select-none"
                style={{ textShadow: '0 2px 8px rgba(212,186,130,0.45)' }}
              >
                <textPath
                  href="#shlokaCirclePath"
                  startOffset="0%"
                  spacing="auto"
                >
                  ॥ यतो धर्मस्ततो जयः ॥ ❖ ॥ सत्यमेव जयते नानृतम् ॥ ❖ ॥ धर्मो रक्षति रक्षितः ॥ ❖ ॥ सर्वजनहिताय सर्वजनसुखाय ॥ ❖
                </textPath>
              </text>
            </g>

            {/* 6. 24 Radial Dharmachakra Ray Spokes */}
            <g transform="translate(250, 250)" stroke="#B59A68">
              {Array.from({ length: 24 }).map((_, i) => {
                const angle = (i * 360) / 24;
                const rad = (angle * Math.PI) / 180;
                const isCardinal = i % 6 === 0;
                const isMajor = i % 3 === 0;
                const r1 = 158;
                const r2 = isCardinal ? 174 : isMajor ? 171 : 167;
                const x1 = Math.cos(rad) * r1;
                const y1 = Math.sin(rad) * r1;
                const x2 = Math.cos(rad) * r2;
                const y2 = Math.sin(rad) * r2;
                return (
                  <line
                    key={i}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    strokeWidth={isCardinal ? '1.8' : isMajor ? '1.2' : '0.75'}
                    stroke={isCardinal ? '#F9F2E3' : isMajor ? '#D4BA82' : '#8A7042'}
                    strokeOpacity={isCardinal ? 0.9 : isMajor ? 0.65 : 0.35}
                  />
                );
              })}
            </g>

            {/* 7. Central Sovereign Medallion (Generous, spacious radius 154) */}
            <circle
              cx="250"
              cy="250"
              r="154"
              fill="url(#medallionDepth)"
              stroke="#B59A68"
              strokeWidth="2.2"
              filter="url(#goldGlow)"
            />
            <circle
              cx="250"
              cy="250"
              r="146"
              fill="none"
              stroke="#6E2634"
              strokeWidth="1.2"
              strokeOpacity="0.75"
            />
            <circle
              cx="250"
              cy="250"
              r="142"
              fill="none"
              stroke="#B59A68"
              strokeWidth="0.6"
              strokeDasharray="2 3"
              strokeOpacity="0.3"
            />

            {/* 8. Centerpiece: Classical Pillars & Grand Scales of Justice */}
            {/* The Central Dharma Pillar Assembly */}
            <g className="transition-transform duration-500">
              {/* Stepped Architectural Plinth Foundation (Well above the typography) */}
              <rect
                x="206"
                y="298"
                width="88"
                height="8"
                rx="2"
                fill="url(#brassMetallic)"
                stroke="#4A3B1E"
                strokeWidth="0.5"
              />
              <rect
                x="218"
                y="291"
                width="64"
                height="7"
                rx="1.5"
                fill="url(#brassMetallic)"
              />
              <rect
                x="230"
                y="285"
                width="40"
                height="6"
                rx="1"
                fill="#8A7042"
              />

              {/* Tri-Fluted Classical Column Shaft */}
              <line
                x1="244"
                y1="180"
                x2="244"
                y2="285"
                stroke="url(#brassMetallic)"
                strokeWidth="2.5"
              />
              <line
                x1="250"
                y1="172"
                x2="250"
                y2="285"
                stroke="#F9F2E3"
                strokeWidth="4"
              />
              <line
                x1="256"
                y1="180"
                x2="256"
                y2="285"
                stroke="url(#brassMetallic)"
                strokeWidth="2.5"
              />

              {/* Column Capital */}
              <path
                d="M 226 180 L 274 180 L 268 172 L 232 172 Z"
                fill="url(#brassMetallic)"
              />

              {/* Central Lion Capitol & Fulcrum Hub */}
              <circle
                cx="250"
                cy="168"
                r="13"
                fill="#1E2522"
                stroke="url(#brassMetallic)"
                strokeWidth="2.2"
              />
              <circle
                cx="250"
                cy="168"
                r="5.5"
                fill="#6E2634"
                stroke="#F9F2E3"
                strokeWidth="1.2"
              />

              {/* Fulcrum Top Finial Spire */}
              <polygon
                points="250,146 255,156 245,156"
                fill="url(#brassMetallic)"
              />
            </g>

            {/* 9. Grand Horizontal Balance Beam & Hanging Pans (Proportional width: 212) */}
            <motion.g
              animate={{
                rotate: isHovered ? [0, -3.5, 3.5, -1, 1, 0] : [0, -1.2, 1.2, -0.6, 0.6, 0],
              }}
              transition={{
                duration: isHovered ? 4.5 : 8.5,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              style={{ originX: '250px', originY: '168px' }}
            >
              {/* Arched Balance Beam Bar */}
              <path
                d="M 144 169 C 180 164 320 164 356 169 L 356 166 C 320 161 180 161 144 166 Z"
                fill="url(#goldBeam)"
              />
              {/* Beam End Knobs */}
              <circle cx="144" cy="168" r="4" fill="url(#brassMetallic)" stroke="#8A7042" strokeWidth="0.8" />
              <circle cx="356" cy="168" r="4" fill="url(#brassMetallic)" stroke="#8A7042" strokeWidth="0.8" />

              {/* Left Scale Pan Assembly */}
              <g>
                {/* Suspension Triple Cords */}
                <line
                  x1="144"
                  y1="168"
                  x2="118"
                  y2="236"
                  stroke="#D4BA82"
                  strokeWidth="1"
                  strokeOpacity="0.85"
                />
                <line
                  x1="144"
                  y1="168"
                  x2="170"
                  y2="236"
                  stroke="#D4BA82"
                  strokeWidth="1"
                  strokeOpacity="0.85"
                />
                <line
                  x1="144"
                  y1="168"
                  x2="144"
                  y2="236"
                  stroke="#FFF9EE"
                  strokeWidth="0.9"
                  strokeOpacity="0.95"
                />

                {/* Left Pan (Brass Crescent Dish) */}
                <path
                  d="M 114 236 C 122 256 166 256 174 236 Z"
                  fill="url(#brassMetallic)"
                  stroke="#FFF9EE"
                  strokeWidth="1.2"
                />
                <ellipse
                  cx="144"
                  cy="236"
                  rx="29"
                  ry="4.5"
                  fill="#181D1B"
                  stroke="#D4BA82"
                  strokeWidth="1"
                />

                {/* Internal Weight of Dharma / Emerald Crystal */}
                <polygon
                  points="144,228 149,233 144,238 139,233"
                  fill="#71877A"
                  stroke="#FFF9EE"
                  strokeWidth="0.9"
                />
              </g>

              {/* Right Scale Pan Assembly */}
              <g>
                {/* Suspension Triple Cords */}
                <line
                  x1="356"
                  y1="168"
                  x2="330"
                  y2="236"
                  stroke="#D4BA82"
                  strokeWidth="1"
                  strokeOpacity="0.85"
                />
                <line
                  x1="356"
                  y1="168"
                  x2="382"
                  y2="236"
                  stroke="#D4BA82"
                  strokeWidth="1"
                  strokeOpacity="0.85"
                />
                <line
                  x1="356"
                  y1="168"
                  x2="356"
                  y2="236"
                  stroke="#FFF9EE"
                  strokeWidth="0.9"
                  strokeOpacity="0.95"
                />

                {/* Right Pan (Brass Crescent Dish) */}
                <path
                  d="M 326 236 C 334 256 378 256 386 236 Z"
                  fill="url(#brassMetallic)"
                  stroke="#FFF9EE"
                  strokeWidth="1.2"
                />
                <ellipse
                  cx="356"
                  cy="236"
                  rx="29"
                  ry="4.5"
                  fill="#181D1B"
                  stroke="#D4BA82"
                  strokeWidth="1"
                />

                {/* Internal Weight of Dharma / Crimson Ruby */}
                <polygon
                  points="356,228 361,233 356,238 351,233"
                  fill="#8A3545"
                  stroke="#FFF9EE"
                  strokeWidth="0.9"
                />
              </g>
            </motion.g>

            {/* 10. Architectural Medallion Typography (Generously positioned inside the medallion, no overlap) */}
            <g className="select-none pointer-events-none">
              <text
                x="250"
                y="326"
                textAnchor="middle"
                className="fill-[#EAD8B2] font-mono text-[10.5px] uppercase tracking-[0.34em] font-semibold"
                style={{ textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}
              >
                NYAYASARATHI
              </text>
              <line
                x1="205"
                y1="333"
                x2="295"
                y2="333"
                stroke="#6E2634"
                strokeWidth="1.2"
                strokeOpacity="0.85"
              />
              <polygon
                points="250,331 252,333 250,335 248,333"
                fill="#D4BA82"
              />
              <text
                x="250"
                y="345"
                textAnchor="middle"
                className="fill-[#B59A68] font-mono text-[7.5px] uppercase tracking-[0.26em] font-medium"
              >
                CONSTITUTIONAL JURISPRUDENCE
              </text>
            </g>

            {/* 11. Orbiting Satellite Compass Indicator (Smoothly glides along dedicated radius 224 orbit) */}
            <g className="origin-center animate-[spin_40s_linear_infinite_reverse]">
              <circle
                cx="250"
                cy="26"
                r="4"
                fill="#151A18"
                stroke="#D4BA82"
                strokeWidth="1.2"
              />
              <circle
                cx="250"
                cy="26"
                r="1.6"
                fill={isHovered ? '#DC3854' : '#8A3545'}
                className="transition-colors duration-300"
              />
            </g>
          </svg>
        </motion.div>

        {/* Dynamic Sacred Shloka Meaning Reveal */}
        <div className="mt-2.5 sm:mt-3 min-h-[24px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {isHovered ? (
              <motion.div
                key="translation"
                initial={{ opacity: 0, y: 3, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -3, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-1.5 sm:gap-2 px-2"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#B59A68] shrink-0" />
                <span className="font-serif italic text-xs sm:text-sm text-[#F4EFE5] tracking-wide text-center">
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
                className="flex items-center gap-2 sm:gap-2.5"
              >
                <div className="w-5 sm:w-8 h-px bg-[#3B3A33]" />
                <span className="font-mono text-[11px] sm:text-xs uppercase tracking-[0.22em] text-[#A9A49A]">
                  ॥ यतो धर्मस्ततो जयः ॥
                </span>
                <div className="w-5 sm:w-8 h-px bg-[#3B3A33]" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Informative Editorial Headline & Philosophy */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE, delay: 0.1 }}
          className="text-center max-w-lg mt-2 sm:mt-3 space-y-1.5 px-3"
        >
          <h1 className="font-display text-base sm:text-xl lg:text-2xl font-medium leading-[1.28] text-[#F4EFE5] tracking-[-0.01em]">
            Find the Law. Understand the Precedent. Verify the Source.
          </h1>
          <p className="font-sans text-[11px] sm:text-xs lg:text-[13px] text-[#A9A49A] leading-relaxed max-w-md mx-auto">
            AI-driven constitutional search, citation graphs, and verifiable judgment analysis indexing 75+ years of Indian jurisprudence.
          </p>
        </motion.div>
      </div>
    </div>
  );
}

export default AuthBrandPanel;
