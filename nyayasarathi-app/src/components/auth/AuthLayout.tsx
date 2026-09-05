'use client';

import React from 'react';
import { motion } from 'framer-motion';
import AuthBrandPanel from './AuthBrandPanel';
import Link from 'next/link';
import { Scale } from 'lucide-react';

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
      <header className="relative z-10 w-full shrink-0 border-b border-[#3B3A33]/60 bg-[#151716]/80 backdrop-blur-md px-6 sm:px-8 lg:px-12 py-3">
        <div className="w-full flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2.5 group focus:outline-none focus:ring-1 focus:ring-[#B59A68] rounded px-1"
          >
            <div className="w-6 h-6 rounded-full bg-[#1D211F] border border-[#B59A68]/40 flex items-center justify-center transition-colors group-hover:border-[#B59A68]">
              <Scale className="w-3.5 h-3.5 text-[#B59A68]" strokeWidth={1.5} />
            </div>
            <span className="font-display text-sm sm:text-base font-semibold tracking-wider text-[#F4EFE5]">
              NyayaSarathi
            </span>
          </Link>
          <div className="hidden sm:flex items-center gap-2 font-mono text-[10px] text-[#A9A49A]/60 uppercase tracking-widest">
            <span>SUPREME COURT &bull; HIGH COURTS</span>
          </div>
        </div>
      </header>

      {/* Main Expansive Split Screen Layout (Unrestricted by boxed frames, fit to screen) */}
      <main className="relative z-10 w-full flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 overflow-y-auto lg:overflow-hidden">
        {/* Left Side: Majestic Brand, Emblem & Sanskrit Shlokas (approx 58% on desktop) */}
        <div className="lg:col-span-7 flex flex-col h-full min-h-0 overflow-y-auto lg:overflow-hidden">
          <AuthBrandPanel />
        </div>

        {/* Right Side: Authentication Form Canvas (approx 42% on desktop) */}
        <div className="lg:col-span-5 flex flex-col justify-center items-center p-6 sm:p-8 lg:p-10 xl:p-12 bg-[#181C1A]/40 backdrop-blur-md relative h-full min-h-0 overflow-y-auto">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: activeTab === 'login' ? -12 : 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: activeTab === 'login' ? 12 : -12 }}
            transition={{ duration: 0.4, ease: EASE }}
            className="w-full max-w-md my-auto"
          >
            {children}
          </motion.div>
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
