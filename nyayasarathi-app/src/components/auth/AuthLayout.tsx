'use client';

import React from 'react';
import { motion } from 'framer-motion';
import AuthBrandPanel from './AuthBrandPanel';
import Link from 'next/link';
import Image from 'next/image';

interface AuthLayoutProps {
  children: React.ReactNode;
  activeTab?: 'login' | 'signup';
}

const EASE = [0.16, 1, 0.3, 1] as const;

export function AuthLayout({ children, activeTab = 'login' }: AuthLayoutProps) {
  return (
    <div className="relative min-h-screen lg:h-screen w-full bg-[#151716] text-[#F4EFE5] flex flex-col justify-between overflow-x-hidden lg:overflow-hidden selection:bg-[#6E2634] selection:text-[#F4EFE5]">
      {/* Background Architectural Grid & Subtle Noise Grain */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-20 bg-[radial-gradient(#3B3A33_1px,transparent_1px)] [background-size:32px_32px]"
        aria-hidden="true"
      />
      <div className="grain-overlay" aria-hidden="true" />

      {/* Top Universal Access Bar */}
      <header className="relative z-10 w-full shrink-0 border-b border-[#3B3A33]/60 bg-[#151716]/80 backdrop-blur-md px-4 sm:px-8 lg:px-12 py-2.5 sm:py-3">
        <div className="w-full flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2.5 group focus:outline-none focus:ring-1 focus:ring-[#B59A68] rounded px-1"
          >
            <div className="w-7 h-7 rounded-full bg-[#1D211F] border border-[#B59A68]/40 flex items-center justify-center p-0.5 transition-colors group-hover:border-[#B59A68]">
              <Image
                src="/logo-transparent.png"
                alt="NyayaSarathi Logo"
                width={22}
                height={22}
                className="w-full h-full object-contain"
                priority
              />
            </div>
            <span className="font-display text-sm sm:text-base font-semibold tracking-wider text-[#F4EFE5]">
              NyayaSarathi
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 font-mono text-[10px] text-[#A9A49A]/60 uppercase tracking-widest">
              <span>SUPREME COURT &bull; HIGH COURTS</span>
            </div>
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs sm:text-[13px] text-[#A9A49A] hover:text-[#B59A68] transition-colors py-1 sm:py-1.5 px-2.5 sm:px-3 rounded-lg border border-[#3B3A33]/70 hover:border-[#B59A68]/40 bg-[#1D211F]/60"
            >
              <span>&larr;</span>
              <span className="hidden sm:inline">Back to Home</span>
              <span className="sm:hidden">Home</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Expansive Split Screen Layout */}
      <main className="relative z-10 w-full flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 overflow-y-auto lg:overflow-hidden">
        {/* Left Side: Majestic Brand, Emblem & Sanskrit Shlokas (Desktop split-screen) */}
        <div className="hidden lg:flex lg:col-span-6 flex-col h-full min-h-0 overflow-hidden">
          <AuthBrandPanel />
        </div>

        {/* Right Side: Authentication Form Canvas */}
        <div className="col-span-1 lg:col-span-6 flex flex-col items-center p-4 sm:p-6 lg:p-8 xl:p-10 bg-[#181C1A]/40 backdrop-blur-md relative h-full min-h-0 overflow-y-auto">
          <div className="w-full max-w-md xl:max-w-lg my-auto py-3 sm:py-6 flex flex-col justify-center min-h-min">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: activeTab === 'login' ? -10 : 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: activeTab === 'login' ? 10 : -10 }}
              transition={{ duration: 0.35, ease: EASE }}
              className="w-full"
            >
              {children}
            </motion.div>
          </div>
        </div>
      </main>

      {/* Bottom Legal Sub-Footer */}
      <footer className="relative z-10 w-full shrink-0 border-t border-[#3B3A33]/40 px-6 sm:px-8 lg:px-12 py-2.5 flex flex-col sm:flex-row items-center justify-between gap-1.5">
        <p className="font-mono text-[9px] sm:text-[10px] text-[#A9A49A]/60 uppercase tracking-widest">
          NyayaSarathi Legal Intelligence &copy; {new Date().getFullYear()} &bull; All Rights Reserved
        </p>
        <p className="font-mono text-[9px] sm:text-[10px] text-[#71877A]/70 uppercase tracking-widest">
          HIGH-PRECISION JUDICIAL RESEARCH
        </p>
      </footer>
    </div>
  );
}

export default AuthLayout;
