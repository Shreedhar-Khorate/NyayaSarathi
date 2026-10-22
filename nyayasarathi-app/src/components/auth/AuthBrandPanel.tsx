'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles } from 'lucide-react';

const EASE = [0.16, 1, 0.3, 1] as const;

export function AuthBrandPanel() {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="relative flex flex-col justify-center items-center h-full p-6 sm:p-8 lg:p-10 xl:p-12 border-b lg:border-b-0 lg:border-r border-[#3B3A33]/70 overflow-hidden bg-[#151716] select-none">
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
            opacity: isHovered ? 0.16 : 0.08,
          }}
          transition={{ duration: 0.8, ease: EASE }}
          className="w-[420px] h-[420px] sm:w-[560px] sm:h-[560px] lg:w-[640px] lg:h-[640px] rounded-full bg-[#B59A68] blur-[110px]"
        />
        <motion.div
          animate={{
            scale: isHovered ? 1.3 : 1,
            opacity: isHovered ? 0.32 : 0.16,
          }}
          transition={{ duration: 0.8, ease: EASE }}
          className="w-[260px] h-[260px] sm:w-[360px] sm:h-[360px] lg:w-[420px] lg:h-[420px] rounded-full bg-[#6E2634] blur-[85px]"
        />
      </div>

      {/* ── Center Section: Grand 2D Revolving Emblem & Headline ────────────── */}
      <div className="relative z-10 my-auto py-2 sm:py-4 flex flex-col items-center justify-center w-full">
        {/* Responsive 2D Revolving Sacred Shloka Insignia */}
        <motion.div
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.035 }}
          transition={{ duration: 0.4, ease: EASE }}
          className="relative w-full max-w-[340px] sm:max-w-[420px] md:max-w-[480px] lg:max-w-[520px] xl:max-w-[580px] 2xl:max-w-[640px] aspect-square flex items-center justify-center cursor-pointer select-none"
        >
          <svg
            viewBox="0 0 500 500"
            className="w-full h-full drop-shadow-[0_20px_60px_rgba(0,0,0,0.9)] transition-all duration-500"
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
                <stop offset="0%" stopColor="#B59A68" stopOpacity="0.4" />
                <stop offset="50%" stopColor="#F4EFE5" stopOpacity="1" />
                <stop offset="100%" stopColor="#B59A68" stopOpacity="0.4" />
              </linearGradient>

              {/* Subtle Gold Shadow Filter */}
              <filter id="goldGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* 1. Deep Obsidian Outer Shield Ring with Brass Bevel */}
            <circle
              cx="250"
              cy="250"
              r="238"
              fill="url(#badgeGradient)"
              stroke="#B59A68"
              strokeWidth="2.5"
              strokeOpacity="0.7"
            />
            <circle
              cx="250"
              cy="250"
              r="228"
              fill="none"
              stroke="#B59A68"
              strokeWidth="0.8"
              strokeDasharray="3 3"
              strokeOpacity="0.4"
            />

            {/* 2. Concentric Orbit Lines with subtle rotation on hover */}
            <g className="transition-transform duration-1000 ease-out">
              <circle
                cx="250"
                cy="250"
                r="212"
                fill="none"
                stroke="#B59A68"
                strokeWidth="1.2"
                strokeOpacity="0.5"
              />
              <circle
                cx="250"
                cy="250"
                r="160"
                fill="none"
                stroke="#6E2634"
                strokeWidth="1.5"
                strokeOpacity="0.65"
              />
              <circle
                cx="250"
                cy="250"
                r="148"
                fill="none"
                stroke="#B59A68"
                strokeWidth="0.75"
                strokeDasharray="2 4"
                strokeOpacity="0.45"
              />
            </g>

            {/* 3. Outer Continuous Rotating Track: Sacred Sanskrit Shloka */}
            {/* "यतो धर्मस्ततो जयः" (Where there is Dharma, there is Victory) & "सत्यमेव जयते" (Truth alone triumphs) */}
            <g className="origin-center animate-[spin_48s_linear_infinite] hover:[animation-play-state:paused]">
              <text
                className="fill-[#E4D2AA] font-serif text-[11px] font-semibold tracking-[0.24em] select-none"
                style={{ textShadow: '0 2px 8px rgba(181,154,104,0.45)' }}
              >
                <textPath
                  href="#shlokaCirclePath"
                  startOffset="0%"
                  spacing="auto"
                >
                  ॥ यतो धर्मस्ततो जयः ॥ सत्यमेव जयते नानृतम् ॥ न्यायो रक्षति रक्षितः ॥ सर्वजन हिताय सर्वजन सुखाय ॥
                </textPath>
              </text>
            </g>

            {/* 4. Cardinal Decorative Geometric Pointers (North, East, South, West) */}
            <g stroke="#B59A68" strokeWidth="1" strokeOpacity="0.85" fill="#B59A68">
              {/* North */}
              <polygon points="250,22 254,32 250,30 246,32" />
              {/* South */}
              <polygon points="250,478 254,468 250,470 246,468" />
              {/* East */}
              <polygon points="478,250 468,254 470,250 468,246" />
              {/* West */}
              <polygon points="22,250 32,254 30,250 32,246" />
            </g>

            {/* 5. 24 Radial Precedent Nodes (Ashoka Chakra 24 Spokes Principle) */}
            <g transform="translate(250, 250)" stroke="#B59A68" strokeOpacity="0.35">
              {Array.from({ length: 24 }).map((_, i) => {
                const angle = (i * 360) / 24;
                const rad = (angle * Math.PI) / 180;
                const x1 = Math.cos(rad) * 140;
                const y1 = Math.sin(rad) * 140;
                const x2 = Math.cos(rad) * 154;
                const y2 = Math.sin(rad) * 154;
                return (
                  <line
                    key={i}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    strokeWidth={i % 3 === 0 ? '1.5' : '0.75'}
                    stroke={i % 3 === 0 ? '#B59A68' : '#7E673B'}
                    strokeOpacity={i % 3 === 0 ? 0.75 : 0.35}
                  />
                );
              })}
            </g>

            {/* 6. Central Inner Sovereign Medallion */}
            <circle
              cx="250"
              cy="250"
              r="132"
              fill="#181D1B"
              stroke="#B59A68"
              strokeWidth="2"
              filter="url(#goldGlow)"
            />
            <circle
              cx="250"
              cy="250"
              r="126"
              fill="none"
              stroke="#6E2634"
              strokeWidth="1.2"
              strokeOpacity="0.7"
            />

            {/* 7. Centerpiece: The Classical Pillars & Scales of Constitutional Justice */}
            {/* The Central Pillar / Dharma Pillar */}
            <g className="transition-transform duration-500">
              {/* Pillar Base Plinth */}
              <rect
                x="215"
                y="330"
                width="70"
                height="8"
                rx="2"
                fill="url(#brassMetallic)"
              />
              <rect
                x="222"
                y="324"
                width="56"
                height="6"
                rx="1"
                fill="url(#brassMetallic)"
              />
              <rect
                x="230"
                y="318"
                width="40"
                height="6"
                rx="1"
                fill="#7E673B"
              />

              {/* Central Fluted Column */}
              <line
                x1="246"
                y1="195"
                x2="246"
                y2="318"
                stroke="url(#brassMetallic)"
                strokeWidth="2.5"
              />
              <line
                x1="250"
                y1="188"
                x2="250"
                y2="318"
                stroke="#F7EEDC"
                strokeWidth="3.5"
              />
              <line
                x1="254"
                y1="195"
                x2="254"
                y2="318"
                stroke="url(#brassMetallic)"
                strokeWidth="2.5"
              />

              {/* Column Capital */}
              <path
                d="M 230 195 L 270 195 L 265 188 L 235 188 Z"
                fill="url(#brassMetallic)"
              />

              {/* Central Lion Capitol / Ashoka Chakra Core at Fulcrum */}
              <circle
                cx="250"
                cy="184"
                r="11"
                fill="#242925"
                stroke="url(#brassMetallic)"
                strokeWidth="2"
              />
              <circle
                cx="250"
                cy="184"
                r="4.5"
                fill="#6E2634"
                stroke="#E4D2AA"
                strokeWidth="1.2"
              />

              {/* Fulcrum Top Finial */}
              <polygon
                points="250,166 254,174 246,174"
                fill="url(#brassMetallic)"
              />
            </g>

            {/* 8. Horizontal Balance Beam (Tilt gently with dynamic equilibrium) */}
            <motion.g
              animate={{
                rotate: isHovered ? [0, -3.5, 3.5, -1, 1, 0] : [0, -1.2, 1.2, -0.6, 0.6, 0],
              }}
              transition={{
                duration: isHovered ? 4 : 8,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              style={{ originX: '250px', originY: '184px' }}
            >
              {/* The Balanced Beam Bar */}
              <path
                d="M 162 185 C 190 181 310 181 338 185 L 338 183 C 310 179 190 179 162 183 Z"
                fill="url(#goldBeam)"
              />
              {/* Beam End Knobs */}
              <circle cx="162" cy="184" r="3.5" fill="url(#brassMetallic)" />
              <circle cx="338" cy="184" r="3.5" fill="url(#brassMetallic)" />

              {/* Left Scale Assembly (Suspension cords + Pan) */}
              <g>
                {/* Suspension Triple Cords */}
                <line
                  x1="162"
                  y1="184"
                  x2="142"
                  y2="242"
                  stroke="#B59A68"
                  strokeWidth="0.9"
                  strokeOpacity="0.8"
                />
                <line
                  x1="162"
                  y1="184"
                  x2="182"
                  y2="242"
                  stroke="#B59A68"
                  strokeWidth="0.9"
                  strokeOpacity="0.8"
                />
                <line
                  x1="162"
                  y1="184"
                  x2="162"
                  y2="242"
                  stroke="#F7EEDC"
                  strokeWidth="0.8"
                  strokeOpacity="0.9"
                />

                {/* Left Pan (Brass Crescent Dish) */}
                <path
                  d="M 138 242 C 146 258 178 258 186 242 Z"
                  fill="url(#brassMetallic)"
                  stroke="#F7EEDC"
                  strokeWidth="1"
                />
                <ellipse
                  cx="162"
                  cy="242"
                  rx="24"
                  ry="3.5"
                  fill="#242925"
                  stroke="#B59A68"
                  strokeWidth="0.8"
                />

                {/* Internal Weight of Precedent / Glowing Sacred Diamond */}
                <polygon
                  points="162,236 166,240 162,244 158,240"
                  fill="#71877A"
                  stroke="#E4D2AA"
                  strokeWidth="0.8"
                />
              </g>

              {/* Right Scale Assembly (Suspension cords + Pan) */}
              <g>
                {/* Suspension Triple Cords */}
                <line
                  x1="338"
                  y1="184"
                  x2="318"
                  y2="242"
                  stroke="#B59A68"
                  strokeWidth="0.9"
                  strokeOpacity="0.8"
                />
                <line
                  x1="338"
                  y1="184"
                  x2="358"
                  y2="242"
                  stroke="#B59A68"
                  strokeWidth="0.9"
                  strokeOpacity="0.8"
                />
                <line
                  x1="338"
                  y1="184"
                  x2="338"
                  y2="242"
                  stroke="#F7EEDC"
                  strokeWidth="0.8"
                  strokeOpacity="0.9"
                />

                {/* Right Pan (Brass Crescent Dish) */}
                <path
                  d="M 314 242 C 322 258 354 258 362 242 Z"
                  fill="url(#brassMetallic)"
                  stroke="#F7EEDC"
                  strokeWidth="1"
                />
                <ellipse
                  cx="338"
                  cy="242"
                  rx="24"
                  ry="3.5"
                  fill="#242925"
                  stroke="#B59A68"
                  strokeWidth="0.8"
                />

                {/* Internal Weight of Precedent / Glowing Crimson Ruby */}
                <polygon
                  points="338,236 342,240 338,244 334,240"
                  fill="#8A3545"
                  stroke="#E4D2AA"
                  strokeWidth="0.8"
                />
              </g>
            </motion.g>

            {/* 9. Architectural Foundation Plinth Label */}
            <g transform="translate(250, 356)" className="select-none pointer-events-none">
              <text
                textAnchor="middle"
                className="fill-[#B59A68] font-mono text-[9.5px] uppercase tracking-[0.3em] font-medium"
              >
                NYAYASARATHI
              </text>
              <line
                x1="-35"
                y1="7"
                x2="35"
                y2="7"
                stroke="#6E2634"
                strokeWidth="1"
                strokeOpacity="0.75"
              />
              <text
                y="18"
                textAnchor="middle"
                className="fill-[#A9A49A]/80 font-mono text-[7px] uppercase tracking-[0.25em]"
              >
                CONSTITUTIONAL JURISPRUDENCE
              </text>
            </g>

            {/* 10. Outer Rotating Compass Diamond Indicator */}
            <g className="origin-center animate-[spin_60s_linear_infinite_reverse]">
              <circle
                cx="250"
                cy="26"
                r="3.5"
                fill="none"
                stroke="#B59A68"
                strokeWidth="1"
              />
              <circle
                cx="250"
                cy="26"
                r="1.2"
                fill={isHovered ? '#DC3854' : '#8A3545'}
                className="transition-colors duration-300"
              />
            </g>
          </svg>
        </motion.div>

        {/* Dynamic Sacred Shloka Meaning Reveal */}
        <div className="mt-4 min-h-[26px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {isHovered ? (
              <motion.div
                key="translation"
                initial={{ opacity: 0, y: 3, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -3, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-2"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#B59A68]" />
                <span className="font-serif italic text-sm sm:text-[15px] text-[#F4EFE5] tracking-wide">
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
                className="flex items-center gap-2.5"
              >
                <div className="w-8 h-px bg-[#3B3A33]" />
                <span className="font-mono text-xs sm:text-[13px] uppercase tracking-[0.25em] text-[#A9A49A]">
                  ॥ यतो धर्मस्ततो जयः ॥
                </span>
                <div className="w-8 h-px bg-[#3B3A33]" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Informative Editorial Headline & Philosophy */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE, delay: 0.1 }}
          className="text-center max-w-xl mt-3 sm:mt-4 space-y-2 px-2"
        >
          <h1 className="font-display text-xl sm:text-2xl lg:text-3xl font-medium leading-[1.25] text-[#F4EFE5] tracking-[-0.01em]">
            Find the Law. Understand the Precedent. Verify the Source.
          </h1>
          <p className="font-sans text-xs sm:text-sm text-[#A9A49A] leading-relaxed max-w-lg mx-auto">
            AI-driven constitutional search, citation graphs, and verifiable judgment analysis indexing 75+ years of Indian jurisprudence.
          </p>
        </motion.div>
      </div>
    </div>
  );
}

export default AuthBrandPanel;
