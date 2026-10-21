'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale, Menu, X, ArrowUpRight, User } from 'lucide-react';
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

  const NAV_LINKS = [
    { href: '/war-room',       label: t('nav.warRoom')   },
    { href: '/legal-drafting', label: t('nav.drafting') || 'Legal Drafting' },
    { href: '/predictor',      label: t('nav.predictor') },
    { href: '/legal-research', label: t('nav.research')  },
    { href: '/ocr',            label: t('nav.ocr')       },
    { href: '/#pipeline',       label: t('nav.howItWorks') },
    { href: '/#capabilities',   label: t('nav.capabilities') },
    { href: '/#workspace',      label: t('nav.workspace')    },
  ];

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
            className="hidden items-center gap-0.5 lg:flex rounded-full border border-[#3B3A33] px-1.5 py-1 bg-[#151716]/60 backdrop-blur-md"
            aria-label="Main navigation"
          >
            {NAV_LINKS.map(({ href, label }) => {
              const isActive = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`rounded-full px-3.5 py-1.5 font-sans text-xs xl:text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'text-[#B59A68] bg-[#B59A68]/15 border border-[#B59A68]/30 font-semibold shadow-sm'
                      : 'text-stone/80 hover:text-ivory hover:bg-white/[0.04]'
                  }`}
                >
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* Auth buttons */}
          <div className="hidden items-center gap-2.5 md:flex shrink-0">

            {currentUser ? (
              <div className="flex items-center gap-2">
                {currentUser.role === 'ADMIN' && (
                  <Link
                    href="/admin/dashboard"
                    id="nav-admin-portal-btn"
                    className="flex items-center gap-1.5 rounded-xl border border-[#B59A68]/50 bg-[#6E2634]/30 px-3 py-1.5 font-sans text-xs font-bold text-[#B59A68] hover:bg-[#6E2634]/60 hover:border-[#B59A68] transition-all shadow-sm"
                  >
                    <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
                    <span>Admin Portal</span>
                  </Link>
                )}

                {currentUser.role === 'JUDGE' && (
                  <Link
                    href="/judge/dashboard"
                    id="nav-judge-portal-btn"
                    className="flex items-center gap-1.5 rounded-xl border border-[#6E2634] bg-[#6E2634]/30 px-3 py-1.5 font-sans text-xs font-bold text-[#E25C6F] hover:bg-[#6E2634]/60 hover:border-[#E25C6F] transition-all shadow-sm"
                  >
                    <Scale className="w-3.5 h-3.5 text-[#E25C6F]" />
                    <span>Judicial Bench</span>
                  </Link>
                )}

                <Link
                  href="/profile"
                  id="nav-profile-btn"
                  className="flex items-center gap-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] px-3.5 py-1.5 font-sans text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors"
                >
                  <div className="w-5 h-5 rounded-full bg-[#B59A68]/20 flex items-center justify-center">
                    <User className="w-3 h-3 text-[#B59A68]" />
                  </div>
                  <span className="max-w-[120px] truncate">{currentUser.full_name || 'Profile'}</span>
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
                  className="btn-oxblood group flex items-center gap-1.5 rounded px-4 py-2 font-sans text-sm font-semibold tracking-wide"
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
                    transition: { delay: i * 0.05, duration: 0.22 },
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
                  transition: { delay: NAV_LINKS.length * 0.05, duration: 0.22 },
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

                    {currentUser.role === 'JUDGE' && (
                      <Link
                        href="/judge/dashboard"
                        id="nav-mobile-judge"
                        onClick={() => setMobileOpen(false)}
                        className="w-full flex items-center justify-center gap-2 rounded border border-[#6E2634] bg-[#6E2634]/40 px-5 py-2.5 font-sans text-sm font-bold text-[#E25C6F]"
                      >
                        <Scale className="w-4 h-4 text-[#E25C6F]" />
                        <span>Judicial Bench Dashboard</span>
                      </Link>
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
