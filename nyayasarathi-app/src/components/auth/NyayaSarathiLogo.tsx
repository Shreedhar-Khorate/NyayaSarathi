'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface NyayaSarathiLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'hero';
  showWordmark?: boolean;
  className?: string;
  isInteractive?: boolean;
}

export function NyayaSarathiLogo({
  size = 'md',
  showWordmark = true,
  className = '',
  isInteractive = true,
}: NyayaSarathiLogoProps) {
  const sizeMap = {
    sm: { box: 'w-8 h-8', icon: 18, text: 'text-sm' },
    md: { box: 'w-11 h-11', icon: 24, text: 'text-base' },
    lg: { box: 'w-16 h-16', icon: 34, text: 'text-xl' },
    hero: { box: 'w-20 h-20 sm:w-24 sm:h-24', icon: 48, text: 'text-2xl sm:text-3xl' },
  };

  const currentSize = sizeMap[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      whileHover={
        isInteractive
          ? {
              scale: 1.025,
              transition: { duration: 0.25, ease: 'easeOut' },
            }
          : undefined
      }
      className={`group inline-flex items-center gap-3.5 select-none ${className}`}
    >
      {/* 2D Vector Emblem */}
      <div
        className={`relative ${currentSize.box} rounded-full bg-[#181C1A] border border-[#B59A68]/40 flex items-center justify-center p-2.5 transition-all duration-300 group-hover:border-[#B59A68] group-hover:bg-[#1E2320] shadow-[0_2px_12px_rgba(0,0,0,0.4)]`}
      >
        {/* Subtle decorative inner concentric ring */}
        <div className="absolute inset-1 rounded-full border border-[#B59A68]/15 pointer-events-none transition-colors duration-300 group-hover:border-[#B59A68]/30" />

        {/* 2D Scales of Justice Vector */}
        <svg
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full text-[#B59A68] transition-all duration-300 group-hover:text-[#DED5C4]"
        >
          {/* Central Pillar / Plinth */}
          <path
            d="M24 6V42"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
          {/* Top Finial / Diamond */}
          <path
            d="M24 4L26 6L24 8L22 6L24 4Z"
            fill="currentColor"
          />
          {/* Base Pedestal */}
          <path
            d="M16 42H32"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <path
            d="M19 38H29"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeOpacity="0.7"
          />

          {/* Central Balance Beam (Horizontal) */}
          <path
            d="M10 14H38"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
          {/* Center Fulcrum Pivot */}
          <circle
            cx="24"
            cy="14"
            r="2.2"
            fill="#181C1A"
            stroke="currentColor"
            strokeWidth="1.8"
          />

          {/* Left Scale Strings & Pan */}
          <path
            d="M10 14L6 26M10 14L14 26"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeOpacity="0.85"
          />
          <path
            d="M5 26C5 26 7 29 10 29C13 29 15 26 15 26H5Z"
            fill="currentColor"
            fillOpacity="0.2"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />

          {/* Right Scale Strings & Pan */}
          <path
            d="M38 14L34 26M38 14L42 26"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeOpacity="0.85"
          />
          <path
            d="M33 26C33 26 35 29 38 29C41 29 43 26 43 26H33Z"
            fill="currentColor"
            fillOpacity="0.2"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />

          {/* Small Antique Brass Axis Accent */}
          <circle
            cx="24"
            cy="26"
            r="1"
            fill="#6E2634"
          />
        </svg>
      </div>

      {/* Brand Wordmark */}
      {showWordmark && (
        <div className="flex flex-col">
          <span
            className={`font-display font-semibold tracking-[0.06em] text-[#F4EFE5] transition-colors duration-200 group-hover:text-white ${currentSize.text}`}
          >
            NyayaSarathi
          </span>
          <span className="font-mono text-[9px] uppercase tracking-[0.25em] text-[#A9A49A]/70">
            Legal Intelligence
          </span>
        </div>
      )}
    </motion.div>
  );
}

export default NyayaSarathiLogo;
