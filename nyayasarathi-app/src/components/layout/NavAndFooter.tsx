'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale, Menu, X, ArrowUpRight } from 'lucide-react';
import Link from 'next/link';

const NAV_LINKS = [
  { href: '#pipeline',     label: 'How It Works' },
  { href: '#capabilities', label: 'Capabilities' },
  { href: '#workspace',    label: 'Workspace'    },
];

const EASE = [0.16, 1, 0.3, 1] as const;

export function Navbar() {
  const [scrolled, setScrolled]     = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  return (
    <>
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.7, ease: EASE }}
        className={`fixed inset-x-0 top-0 z-50 py-5 bg-transparent transition-all duration-500 ${
          scrolled ? 'bg-[#151716]/40 backdrop-blur-sm' : 'bg-transparent'
        }`}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 shrink-0 group">
            <Scale
              className="h-[18px] w-[18px] text-[#B59A68] transition-opacity duration-200 group-hover:opacity-70"
              strokeWidth={1.5}
            />
            <span
              className="font-display text-[1.05rem] font-semibold text-ivory/90"
              style={{ letterSpacing: '0.04em' }}
            >
              NyayaSarathi
            </span>
          </Link>

          {/* Nav links with border pill */}
          <nav
            className="hidden items-center gap-1 md:flex rounded-full border border-[#3B3A33] px-2 py-1.5"
            aria-label="Main navigation"
          >
            {NAV_LINKS.map(({ href, label }) => (
              <a
                key={href}
                href={href}
                className="rounded-full px-4 py-1.5 font-sans text-sm font-medium text-stone/75 transition-colors duration-200 hover:text-ivory hover:bg-white/[0.04]"
              >
                {label}
              </a>
            ))}
          </nav>

          {/* Auth buttons */}
          <div className="hidden items-center gap-4 md:flex shrink-0">
            <button
              id="nav-signin-btn"
              className="font-sans text-sm font-medium text-stone/75 transition-colors duration-200 hover:text-ivory"
            >
              Sign In
            </button>
            <button
              id="nav-getstarted-btn"
              className="btn-oxblood group flex items-center gap-1.5 rounded px-4 py-2 font-sans text-sm font-semibold tracking-wide"
            >
              Get Started
              <ArrowUpRight
                className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                strokeWidth={2}
              />
            </button>
          </div>

          {/* Mobile hamburger */}
          <button
            id="nav-mobile-toggle"
            onClick={() => setMobileOpen(v => !v)}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
            className="flex h-8 w-8 items-center justify-center text-stone/75 hover:text-ivory transition-colors md:hidden"
          >
            <AnimatePresence mode="wait" initial={false}>
              {mobileOpen ? (
                <motion.span
                  key="x"
                  initial={{ rotate: -45, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: 45, opacity: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  <X className="h-5 w-5" strokeWidth={1.8} />
                </motion.span>
              ) : (
                <motion.span
                  key="m"
                  initial={{ rotate: 45, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: -45, opacity: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  <Menu className="h-5 w-5" strokeWidth={1.8} />
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>
      </motion.header>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            key="mob"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0, transition: { duration: 0.25, ease: EASE } }}
            exit={{ opacity: 0, y: -6, transition: { duration: 0.18 } }}
            className="fixed inset-x-0 top-[69px] z-40 bg-[#151716]/95 backdrop-blur-xl md:hidden"
          >
            <div className="h-px bg-[#3B3A33]" />
            <div className="mx-auto max-w-7xl px-6 pt-5 pb-7 space-y-0.5">

              {NAV_LINKS.map(({ href, label }, i) => (
                <motion.a
                  key={href}
                  href={href}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{
                    opacity: 1, x: 0,
                    transition: { delay: i * 0.05, duration: 0.22 },
                  }}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center rounded px-2 py-3 font-sans text-sm font-medium text-stone/80 transition-colors hover:text-ivory"
                >
                  {label}
                </motion.a>
              ))}

              <motion.div
                initial={{ opacity: 0, x: -8 }}
                animate={{
                  opacity: 1, x: 0,
                  transition: { delay: NAV_LINKS.length * 0.05, duration: 0.22 },
                }}
                className="flex flex-col gap-2.5 pt-5 mt-2 border-t border-[#3B3A33]"
              >
                <button
                  id="nav-mobile-signin"
                  className="w-full rounded border border-[#3B3A33] px-5 py-2.5 font-sans text-sm font-medium text-ivory/80 transition-colors hover:text-ivory hover:border-[#8A3545]/60"
                >
                  Sign In
                </button>
                <button
                  id="nav-mobile-getstarted"
                  className="btn-oxblood group flex w-full items-center justify-center gap-2 rounded px-5 py-2.5 font-sans text-sm font-semibold tracking-wide"
                >
                  Get Started
                  <ArrowUpRight
                    className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                    strokeWidth={2}
                  />
                </button>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export function Footer() {
  return (
    <footer className="relative border-t border-[#3B3A33] py-16 bg-[#151716]">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-10 px-6 md:flex-row md:items-center">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <Scale className="h-4 w-4 text-[#B59A68]" strokeWidth={1.4} />
            <span className="font-display text-lg font-semibold text-ivory">NyayaSarathi</span>
          </div>
          <p className="font-legal italic text-sm text-stone/70 mt-1">
            &ldquo;Fiat justitia ruat caelum.&rdquo;
          </p>
        </div>

        <p className="max-w-sm font-sans text-xs leading-relaxed text-stone">
          Built for legal researchers, judicial clerks, and chambers who need
          answers that hold up under cross-examination. Every citation is
          verifiable, every source is shown.
        </p>

        <p className="font-sans text-xs text-stone/50">
          &copy; {new Date().getFullYear()} NyayaSarathi
        </p>
      </div>
    </footer>
  );
}
