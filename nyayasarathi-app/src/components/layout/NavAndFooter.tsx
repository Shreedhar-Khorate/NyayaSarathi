'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale, Menu, X, ArrowUpRight, User, Users, MessageCircle } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLanguage } from '@/context/LanguageContext';
import { getUser, type UserProfile } from '@/lib/auth';

const EASE = [0.16, 1, 0.3, 1] as const;

export function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled]     = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const { t } = useLanguage();

  useEffect(() => {
    setCurrentUser(getUser());
  }, [pathname]);

  // All 10 navigation modules directly displayed without hiding any section
  const NAV_LINKS = [
    { href: '/war-room',       label: 'War Room' },
    { href: '/legal-drafting', label: 'Legal Drafting' },
    { href: '/predictor',      label: 'Judgment Predictor' },
    { href: '/contracts',      label: 'Contract Analyzer' },
    { href: '/legal-research', label: 'Legal Research' },
    { href: '/ocr',            label: 'Legal OCR' },
    { href: '/find-advocate',  label: 'Find Advocate' },
    { href: '/messages',       label: 'Messages' },
    { href: '/news',           label: 'Legal News' },
    { href: '/#pipeline',      label: t('nav.howItWorks') || 'How It Works' },
  ];

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
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
        className={`fixed inset-x-0 top-0 z-50 py-3 bg-[#151716]/30 backdrop-blur-xl border-b border-[#3B3A33]/30 transition-all duration-300 ${
          scrolled ? 'bg-[#151716]/65 backdrop-blur-2xl shadow-xl shadow-black/40 border-[#3B3A33]/60' : ''
        }`}
      >
        <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between px-4 sm:px-6 xl:px-8">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 shrink-0 group mr-2 xl:mr-4">
            <Scale
              className="h-[18px] w-[18px] text-[#B59A68] transition-opacity duration-200 group-hover:opacity-70"
              strokeWidth={1.5}
            />
            <span
              className="font-display text-[1.05rem] font-semibold text-ivory/95"
              style={{ letterSpacing: '0.04em' }}
            >
              NyayaSarathi
            </span>
          </Link>

          {/* Nav links with transparent blurry glass pill — all 10 sections visible & proper fit */}
          <nav
            className="hidden items-center gap-0.5 xl:gap-1 lg:flex rounded-full border border-[#B59A68]/20 bg-gradient-to-r from-[#151716]/40 via-[#1D211F]/30 to-[#151716]/40 backdrop-blur-2xl px-2 py-1 shadow-2xl shadow-black/50"
            aria-label="Main navigation"
          >
            {NAV_LINKS.map(({ href, label }) => {
              const isActive = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`whitespace-nowrap rounded-full px-2 xl:px-2.5 2xl:px-3 py-1 font-sans text-[11px] xl:text-[12px] 2xl:text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? 'text-[#B59A68] bg-gradient-to-r from-[#B59A68]/20 via-[#6E2634]/15 to-[#B59A68]/20 border border-[#B59A68]/40 font-semibold shadow-sm'
                      : 'text-stone/85 hover:text-ivory hover:bg-white/[0.04]'
                  }`}
                >
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* Auth buttons */}
          <div className="hidden items-center gap-2.5 md:flex shrink-0 ml-2 xl:ml-4">

            {currentUser ? (
              <div className="flex items-center gap-2">
                {currentUser.role === 'ADMIN' && (
                  <Link
                    href="/admin/dashboard"
                    id="nav-admin-portal-btn"
                    className="flex items-center gap-1.5 rounded-full border border-[#B59A68]/45 bg-gradient-to-r from-[#6E2634]/35 to-[#8A3545]/20 px-3.5 py-1.5 font-sans text-xs font-semibold text-[#B59A68] hover:border-[#B59A68] hover:bg-[#6E2634]/55 transition-all shadow-sm whitespace-nowrap"
                  >
                    <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
                    <span>Admin Portal</span>
                  </Link>
                )}

                {currentUser.role === 'ADVOCATE' && (
                  <Link
                    href="/advocate/dashboard"
                    id="nav-advocate-portal-btn"
                    className="flex items-center gap-1.5 rounded-full border border-[#B59A68]/50 bg-[#242925] px-3.5 py-1.5 font-sans text-xs font-semibold text-[#B59A68] hover:bg-[#2e3530] hover:border-[#B59A68] transition-all shadow-sm whitespace-nowrap"
                  >
                    <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
                    <span>Advocate Portal</span>
                  </Link>
                )}

                {currentUser.role === 'USER' && (
                  <>
                    <Link
                      href="/find-advocate"
                      id="nav-user-find-advocate-btn"
                      className="hidden sm:flex items-center gap-1.5 rounded-full border border-[#4F8EF7]/40 bg-[#4F8EF7]/10 px-3 py-1.5 font-sans text-xs font-semibold text-[#4F8EF7] hover:bg-[#4F8EF7]/20 transition-all shadow-sm whitespace-nowrap"
                    >
                      <Users className="w-3.5 h-3.5 text-[#4F8EF7]" />
                      <span>Find Advocate</span>
                    </Link>
                    <Link
                      href="/messages"
                      id="nav-user-messages-btn"
                      className="flex items-center gap-1.5 rounded-full border border-[#B59A68]/40 bg-[#B59A68]/10 px-3 py-1.5 font-sans text-xs font-semibold text-[#B59A68] hover:bg-[#B59A68]/20 transition-all shadow-sm whitespace-nowrap"
                    >
                      <MessageCircle className="w-3.5 h-3.5 text-[#B59A68]" />
                      <span>Messages</span>
                    </Link>
                  </>
                )}

                <Link
                  href="/profile"
                  id="nav-profile-btn"
                  className="flex items-center gap-2 rounded-full border border-[#3B3A33] bg-gradient-to-b from-[#1D211F] to-[#151716] px-3.5 py-1.5 font-sans text-xs font-medium text-ivory hover:border-[#B59A68]/50 transition-colors whitespace-nowrap"
                >
                  <div className="w-5 h-5 rounded-full bg-[#B59A68]/20 flex items-center justify-center">
                    <User className="w-3 h-3 text-[#B59A68]" />
                  </div>
                  <span className="max-w-[110px] xl:max-w-[140px] truncate">{currentUser.full_name || 'Profile'}</span>
                </Link>
              </div>
            ) : (
              <>
                <Link
                  href="/login"
                  id="nav-signin-btn"
                  className="font-sans text-sm font-medium text-stone/75 transition-colors duration-200 hover:text-ivory px-2"
                >
                  {t('nav.signIn')}
                </Link>
                <Link
                  href="/signup"
                  id="nav-getstarted-btn"
                  className="btn-oxblood group flex items-center gap-1.5 rounded-full px-4 py-2 font-sans text-sm font-semibold tracking-wide"
                >
                  {t('nav.getStarted')}
                  <ArrowUpRight
                    className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                    strokeWidth={2}
                  />
                </Link>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <div className="flex items-center gap-2 md:hidden">

            <button
              type="button"
              suppressHydrationWarning
              id="nav-mobile-toggle"
              onClick={() => setMobileOpen(v => !v)}
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              className="flex h-8 w-8 items-center justify-center text-stone/75 hover:text-ivory transition-colors"
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
                <motion.div
                  key={href}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{
                    opacity: 1, x: 0,
                    transition: { delay: i * 0.04, duration: 0.22 },
                  }}
                >
                  <Link
                    href={href}
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center rounded px-2 py-3 font-sans text-sm font-medium text-stone/80 transition-colors hover:text-ivory"
                  >
                    {label}
                  </Link>
                </motion.div>
              ))}

              <motion.div
                initial={{ opacity: 0, x: -8 }}
                animate={{
                  opacity: 1, x: 0,
                  transition: { delay: NAV_LINKS.length * 0.04, duration: 0.22 },
                }}
                className="flex flex-col gap-2.5 pt-5 mt-2 border-t border-[#3B3A33]"
              >
                {currentUser ? (
                  <>
                    {currentUser.role === 'ADMIN' && (
                      <Link
                        href="/admin/dashboard"
                        id="nav-mobile-admin"
                        onClick={() => setMobileOpen(false)}
                        className="w-full flex items-center justify-center gap-2 rounded border border-[#B59A68] bg-[#6E2634]/40 px-5 py-2.5 font-sans text-sm font-bold text-[#B59A68]"
                      >
                        <Scale className="w-4 h-4 text-[#B59A68]" />
                        <span>Admin Operations Portal</span>
                      </Link>
                    )}

                    {currentUser.role === 'ADVOCATE' && (
                      <Link
                        href="/advocate/dashboard"
                        id="nav-mobile-advocate"
                        onClick={() => setMobileOpen(false)}
                        className="w-full flex items-center justify-center gap-2 rounded border border-[#B59A68]/60 bg-[#242925] px-5 py-2.5 font-sans text-sm font-bold text-[#B59A68]"
                      >
                        <Scale className="w-4 h-4 text-[#B59A68]" />
                        <span>Advocate Portal</span>
                      </Link>
                    )}

                    {currentUser.role === 'USER' && (
                      <>
                        <Link
                          href="/find-advocate"
                          id="nav-mobile-user-find-advocate"
                          onClick={() => setMobileOpen(false)}
                          className="w-full flex items-center justify-center gap-2 rounded border border-[#4F8EF7]/60 bg-[#4F8EF7]/20 px-5 py-2.5 font-sans text-sm font-bold text-[#4F8EF7]"
                        >
                          <Users className="w-4 h-4 text-[#4F8EF7]" />
                          <span>Find an Advocate</span>
                        </Link>
                        <Link
                          href="/messages"
                          id="nav-mobile-user-messages"
                          onClick={() => setMobileOpen(false)}
                          className="w-full flex items-center justify-center gap-2 rounded border border-[#B59A68]/60 bg-[#B59A68]/20 px-5 py-2.5 font-sans text-sm font-bold text-[#B59A68]"
                        >
                          <MessageCircle className="w-4 h-4 text-[#B59A68]" />
                          <span>Messages</span>
                        </Link>
                      </>
                    )}

                    <Link
                      href="/profile"
                      id="nav-mobile-profile"
                      onClick={() => setMobileOpen(false)}
                      className="w-full flex items-center justify-center gap-2 rounded border border-[#B59A68]/60 bg-[#1D211F] px-5 py-2.5 font-sans text-sm font-semibold text-[#F4EFE5]"
                    >
                      <User className="w-4 h-4 text-[#B59A68]" />
                      <span>My Profile ({currentUser.full_name || 'Member'})</span>
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      href="/login"
                      id="nav-mobile-signin"
                      onClick={() => setMobileOpen(false)}
                      className="w-full text-center rounded border border-[#3B3A33] px-5 py-2.5 font-sans text-sm font-medium text-ivory/80 transition-colors hover:text-ivory hover:border-[#8A3545]/60"
                    >
                      {t('nav.signIn')}
                    </Link>
                    <Link
                      href="/signup"
                      id="nav-mobile-getstarted"
                      onClick={() => setMobileOpen(false)}
                      className="btn-oxblood group flex w-full items-center justify-center gap-2 rounded px-5 py-2.5 font-sans text-sm font-semibold tracking-wide"
                    >
                      {t('nav.getStarted')}
                      <ArrowUpRight
                        className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                        strokeWidth={2}
                      />
                    </Link>
                  </>
                )}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="relative border-t border-[#3B3A33] py-16 bg-[#151716]">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-10 px-6 md:flex-row md:items-center">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <Scale className="h-4 w-4 text-[#B59A68]" strokeWidth={1.4} />
            <span className="font-display text-lg font-semibold text-ivory">NyayaSarathi</span>
          </div>
          <p className="font-legal italic text-sm text-stone/70 mt-1">
            &ldquo;{t('footer.motto')}&rdquo;
          </p>
        </div>

        <p className="max-w-sm font-sans text-xs leading-relaxed text-stone">
          {t('footer.description')}
        </p>

        <p className="font-sans text-xs text-stone/50">
          &copy; {new Date().getFullYear()} NyayaSarathi
        </p>
      </div>
    </footer>
  );
}
