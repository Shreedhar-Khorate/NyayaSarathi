'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Scale } from 'lucide-react';

const NAV_LINKS = [
  { href: '#pipeline', label: 'How it works' },
  { href: '#capabilities', label: 'Capabilities' },
  { href: '#workspace', label: 'Workspace' },
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
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
        scrolled ? 'border-b hairline bg-obsidian/80 backdrop-blur-md' : 'bg-transparent'
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber/15">
            <Scale className="h-4 w-4 text-amber" strokeWidth={2} />
          </div>
          <span className="font-display text-lg font-semibold tracking-wide text-cream">
            NyayaSarathi
          </span>
        </div>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="font-sans text-sm text-ash transition-colors duration-200 hover:text-cream"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <button className="rounded-lg border border-white/15 bg-white/5 px-4 py-2 font-sans text-sm font-medium text-cream backdrop-blur-sm transition-colors hover:border-amber/30 hover:bg-amber/10">
          Sign In
        </button>
      </div>
    </motion.header>
  );
}

export function Footer() {
  return (
    <footer className="relative border-t hairline py-14">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 md:flex-row md:items-center">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber/15">
            <Scale className="h-3.5 w-3.5 text-amber" strokeWidth={2} />
          </div>
          <span className="font-display text-base font-semibold text-cream">NyayaSarathi</span>
        </div>
        <p className="max-w-md text-xs leading-relaxed text-ash">
          Built for legal researchers, judicial clerks, and chambers who need answers that hold up
          under cross-examination. Every citation is verifiable, every source is shown.
        </p>
        <p className="font-sans text-xs text-ash">&copy; {new Date().getFullYear()} NyayaSarathi</p>
      </div>
    </footer>
  );
}
