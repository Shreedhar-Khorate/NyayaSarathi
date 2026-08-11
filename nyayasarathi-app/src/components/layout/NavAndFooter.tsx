'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Scale } from 'lucide-react';

const NAV_LINKS = [
  { href: '#pipeline',      label: 'How it works' },
  { href: '#capabilities',  label: 'Capabilities' },
  { href: '#workspace',     label: 'Workspace' },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'border-b border-[#3B3A33] bg-[#151716]/92 backdrop-blur-md'
          : 'bg-transparent'
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <Scale
            className="h-5 w-5 text-[#B59A68]"
            strokeWidth={1.4}
          />
          <span className="font-display text-xl font-semibold tracking-wide text-ivory"
            style={{ letterSpacing: '0.04em' }}>
            NyayaSarathi
          </span>
        </div>

        {/* Nav links */}
        <nav className="hidden items-center gap-9 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="font-sans text-sm font-medium text-stone transition-colors duration-200 hover:text-ivory"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* CTA */}
        <button className="btn-oxblood rounded px-5 py-2 font-sans text-sm font-semibold tracking-wide">
          Sign In
        </button>
      </div>
    </motion.header>
  );
}

export function Footer() {
  return (
    <footer className="relative border-t border-[#3B3A33] py-16 bg-[#151716]">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-10 px-6 md:flex-row md:items-center">
        {/* Brand */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <Scale className="h-4 w-4 text-[#B59A68]" strokeWidth={1.4} />
            <span className="font-display text-lg font-semibold text-ivory">NyayaSarathi</span>
          </div>
          <p className="font-legal italic text-sm text-stone/70 mt-1">
            &ldquo;Fiat justitia ruat caelum.&rdquo;
          </p>
        </div>

        {/* Descriptor */}
        <p className="max-w-sm font-sans text-xs leading-relaxed text-stone">
          Built for legal researchers, judicial clerks, and chambers who need
          answers that hold up under cross-examination. Every citation is
          verifiable, every source is shown.
        </p>

        {/* Copyright */}
        <p className="font-sans text-xs text-stone/50">
          &copy; {new Date().getFullYear()} NyayaSarathi
        </p>
      </div>
    </footer>
  );
}
