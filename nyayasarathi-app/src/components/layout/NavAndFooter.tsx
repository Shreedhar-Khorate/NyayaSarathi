'use client';

import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Gavel,
  FileText,
  Scale,
  FileCheck,
  ScanText,
  Search,
  Users,
  Newspaper,
  MessageSquare,
  ChevronDown,
  ChevronRight,
  ArrowUpRight,
  User,
  LogOut,
  Menu,
  X,
  Home,
} from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useLanguage } from '@/context/LanguageContext';
import { getUser, removeAuth, type UserProfile } from '@/lib/auth';
import { UserAvatar } from '@/components/ui/UserAvatar';

const EASE = [0.16, 1, 0.3, 1] as const;

// ── Page label map for breadcrumb / mobile header ────────────────────
const PAGE_LABELS: Record<string, string> = {
  '/': 'Home',
  '/legal-research': 'Research Hub',
  '/find-advocate': 'Find Advocate',
  '/news': 'Legal News',
  '/predictor': 'Judgment Predictor',
  '/war-room': 'War Room',
  '/legal-drafting': 'Legal Drafting',
  '/contracts': 'Contract Analyzer',
  '/ocr': 'Legal OCR',
  '/profile': 'My Profile',
  '/messages': 'Messages',
  '/chat': 'AI Chat',
  '/admin/dashboard': 'Admin Dashboard',
  '/admin/users': 'User Management',
  '/admin/audit-logs': 'Audit Logs',
  '/advocate/dashboard': 'Advocate Dashboard',
  '/advocate/activity': 'My Activity',
  '/login': 'Sign In',
  '/signup': 'Get Started',
};

function getPageLabel(pathname: string): string {
  if (PAGE_LABELS[pathname]) return PAGE_LABELS[pathname];
  // Prefix fallback for deep routes
  if (pathname.startsWith('/admin')) return 'Admin Portal';
  if (pathname.startsWith('/advocate')) return 'Advocate Portal';
  if (pathname.startsWith('/profile')) return 'Profile';
  return 'NyayaSarathi';
}

// ── AI Intelligence Suite Feature Modules ─────────────────────────────
const AI_SUITE_MODULES = [
  {
    href: '/war-room',
    title: 'War Room',
    desc: 'Simulated bench proceedings & argument audit',
    icon: Gavel,
  },
  {
    href: '/legal-drafting',
    title: 'Legal Drafting',
    desc: 'Statutory petitions, affidavits & legal notices',
    icon: FileText,
  },
  {
    href: '/predictor',
    title: 'Judgment Predictor',
    desc: 'Bench probability & judicial trend analysis',
    icon: Scale,
  },
  {
    href: '/contracts',
    title: 'Contract Analyzer',
    desc: 'Clause risk auditing & compliance verification',
    icon: FileCheck,
  },
  {
    href: '/ocr',
    title: 'Legal OCR',
    desc: 'Vernacular court order extraction & scanning',
    icon: ScanText,
  },
];

// ── Primary Direct Nav Links ──────────────────────────────────────────
const DIRECT_LINKS = [
  {
    href: '/legal-research',
    label: 'Research Hub',
    icon: Search,
  },
  {
    href: '/find-advocate',
    label: 'Find Advocate',
    icon: Users,
  },
  {
    href: '/news',
    label: 'Legal News',
    icon: Newspaper,
    hasLiveBadge: true,
  },
];

// ── Active underline indicator ────────────────────────────────────────
function ActiveDot() {
  return (
    <span className="absolute -bottom-[9px] left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-[#B59A68]" />
  );
}

export function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [aiMenuOpen, setAiMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const { t } = useLanguage();

  const aiMenuRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Sync auth state on route transition
  useEffect(() => {
    setCurrentUser(getUser());
    setMobileOpen(false);
    setAiMenuOpen(false);
    setUserMenuOpen(false);
  }, [pathname]);

  // Handle subtle scroll styling
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Prevent background scroll when mobile drawer is open
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileOpen]);

  // Click outside to dismiss desktop menus
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (aiMenuRef.current && !aiMenuRef.current.contains(e.target as Node)) {
        setAiMenuOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isAiSuiteActive = AI_SUITE_MODULES.some(m => pathname.startsWith(m.href));
  const isAdminActive = pathname.startsWith('/admin');
  const isAdvocateActive = pathname.startsWith('/advocate');
  const isProfileActive = pathname === '/profile';
  const isMessagesActive = pathname === '/messages';
  const isHomeActive = pathname === '/';

  const pageLabel = getPageLabel(pathname);

  const handleSignOut = () => {
    removeAuth();
    setCurrentUser(null);
    setUserMenuOpen(false);
    window.location.href = '/';
  };

  return (
    <>
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: EASE }}
        className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
          scrolled
            ? 'bg-[#151716]/85 backdrop-blur-2xl shadow-xl shadow-black/50 border-b border-[#3B3A33]/70'
            : 'bg-[#151716]/40 backdrop-blur-md border-b border-[#3B3A33]/30'
        }`}
      >
        {/* ── Main header row ─────────────────────────────────────── */}
        <div className="mx-auto flex w-full max-w-[1520px] items-center justify-between px-4 sm:px-6 lg:px-8 py-2.5">

          {/* ── Brand Logo ────────────────────────────────────────── */}
          <Link
            href="/"
            className="flex items-center gap-3 shrink-0 group focus:outline-none"
            aria-label="NyayaSarathi Home"
          >
            <div className="relative flex items-center justify-center">
              <Image
                src="/logo-transparent.png"
                alt="NyayaSarathi Logo"
                width={30}
                height={30}
                className="h-7 w-7 sm:h-8 sm:w-8 object-contain drop-shadow-[0_2px_12px_rgba(181,154,104,0.35)] transition-transform duration-200 group-hover:scale-105"
                priority
              />
            </div>
            <div className="flex flex-col">
              <span className="font-display text-[1.12rem] font-semibold text-ivory tracking-wide leading-none group-hover:text-brass transition-colors">
                NyayaSarathi
              </span>
              <span className="font-sans text-[8.5px] uppercase tracking-[0.22em] text-[#B59A68]/70 leading-none mt-1">
                Judicial Intelligence
              </span>
            </div>
          </Link>

          {/* ── Desktop Primary Navigation ─────────────────────────── */}
          <nav
            className="hidden lg:flex items-center gap-1 xl:gap-2 rounded-full border border-[#B59A68]/20 bg-gradient-to-r from-[#151716]/60 via-[#1D211F]/40 to-[#151716]/60 backdrop-blur-xl px-2.5 py-1.5 shadow-lg shadow-black/30"
            aria-label="Main navigation"
          >
            {/* Home */}
            <Link
              href="/"
              aria-current={isHomeActive ? 'page' : undefined}
              className={`relative flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1 font-sans text-xs font-medium transition-all duration-200 ${
                isHomeActive
                  ? 'text-[#B59A68] bg-[#B59A68]/15 border border-[#B59A68]/30 font-semibold shadow-sm'
                  : 'text-stone/85 hover:text-ivory hover:bg-white/[0.04] border border-transparent'
              }`}
            >
              <Home className="w-3 h-3" />
              <span>Home</span>
              {isHomeActive && <ActiveDot />}
            </Link>

            {/* AI Intelligence Suite Dropdown Trigger */}
            <div
              ref={aiMenuRef}
              className="relative"
              onMouseEnter={() => setAiMenuOpen(true)}
              onMouseLeave={() => setAiMenuOpen(false)}
            >
              <button
                type="button"
                onClick={() => setAiMenuOpen(prev => !prev)}
                aria-expanded={aiMenuOpen}
                aria-current={isAiSuiteActive ? 'page' : undefined}
                className={`relative flex items-center gap-1.5 rounded-full px-3 py-1 font-sans text-xs font-medium transition-all duration-200 focus:outline-none border ${
                  isAiSuiteActive || aiMenuOpen
                    ? 'text-[#B59A68] bg-[#B59A68]/15 border-[#B59A68]/30 font-semibold shadow-sm'
                    : 'text-stone/85 hover:text-ivory hover:bg-white/[0.04] border-transparent'
                }`}
              >
                <Scale className="w-3.5 h-3.5 text-[#B59A68]" strokeWidth={1.5} />
                <span>Judicial Suite</span>
                <ChevronDown
                  className={`w-3 h-3 text-[#B59A68]/80 transition-transform duration-200 ${
                    aiMenuOpen ? 'rotate-180' : ''
                  }`}
                />
                {isAiSuiteActive && <ActiveDot />}
              </button>

              {/* Dropdown Menu Card */}
              <AnimatePresence>
                {aiMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 8, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 8, scale: 0.98 }}
                    transition={{ duration: 0.18, ease: EASE }}
                    className="absolute left-0 top-full pt-2 z-50 w-[350px]"
                  >
                    <div className="rounded-2xl border border-[#B59A68]/25 bg-[#181C1A]/95 backdrop-blur-2xl p-2 shadow-2xl shadow-black/80 ring-1 ring-white/5">
                      <div className="px-3 py-2 border-b border-[#3B3A33]/50 mb-1 flex items-center justify-between">
                        <span className="font-mono text-[9.5px] font-semibold tracking-[0.18em] uppercase text-[#B59A68]">
                          Chambers Intelligence
                        </span>
                        <span className="font-mono text-[9px] text-stone/50 tracking-wider uppercase">Active Suite</span>
                      </div>

                      <div className="flex flex-col gap-0.5">
                        {AI_SUITE_MODULES.map(module => {
                          const Icon = module.icon;
                          const isActive = pathname === module.href || pathname.startsWith(module.href + '/');
                          return (
                            <Link
                              key={module.href}
                              href={module.href}
                              onClick={() => setAiMenuOpen(false)}
                              aria-current={isActive ? 'page' : undefined}
                              className={`group flex items-center justify-between rounded-xl px-3 py-2 transition-all duration-150 border ${
                                isActive
                                  ? 'bg-[#B59A68]/15 border-[#B59A68]/30'
                                  : 'border-transparent hover:bg-white/[0.04] hover:border-[#3B3A33]/50'
                              }`}
                            >
                              <div className="flex items-center gap-3 min-w-0">
                                <div className={`w-7 h-7 rounded-lg border flex items-center justify-center shrink-0 transition-colors shadow-sm ${
                                  isActive
                                    ? 'bg-[#B59A68]/20 border-[#B59A68]/50 text-[#B59A68]'
                                    : 'bg-[#151716] border-[#3B3A33] text-[#B59A68] group-hover:border-[#B59A68]/50 group-hover:text-ivory'
                                }`}>
                                  <Icon className="w-3.5 h-3.5" strokeWidth={1.5} />
                                </div>
                                <div className="flex flex-col min-w-0">
                                  <span className={`font-sans text-xs font-semibold transition-colors leading-tight ${
                                    isActive ? 'text-[#B59A68]' : 'text-ivory group-hover:text-[#B59A68]'
                                  }`}>
                                    {module.title}
                                  </span>
                                  <span className="font-sans text-[11px] text-stone/60 truncate mt-0.5">
                                    {module.desc}
                                  </span>
                                </div>
                              </div>
                              {isActive ? (
                                <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-[#B59A68] bg-[#B59A68]/10 border border-[#B59A68]/30 rounded-full px-1.5 py-0.5 shrink-0 ml-2">
                                  Active
                                </span>
                              ) : (
                                <ChevronRight className="w-3.5 h-3.5 text-stone/40 opacity-0 -translate-x-1 transition-all duration-150 group-hover:opacity-100 group-hover:translate-x-0 group-hover:text-[#B59A68] shrink-0 ml-2" />
                              )}
                            </Link>
                          );
                        })}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Direct Primary Links */}
            {DIRECT_LINKS.map(link => {
              const isActive = pathname === link.href || pathname.startsWith(link.href + '/');
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={`relative flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1 font-sans text-xs font-medium transition-all duration-200 border ${
                    isActive
                      ? 'text-[#B59A68] bg-[#B59A68]/15 border-[#B59A68]/30 font-semibold shadow-sm'
                      : 'text-stone/85 hover:text-ivory hover:bg-white/[0.04] border-transparent'
                  }`}
                >
                  <span>{link.label}</span>
                  {link.hasLiveBadge && (
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                    </span>
                  )}
                  {isActive && <ActiveDot />}
                </Link>
              );
            })}
          </nav>

          {/* ── Desktop Right Controls ─────────────────────────────── */}
          <div className="hidden lg:flex items-center gap-2.5 shrink-0">
            {currentUser ? (
              <div className="flex items-center gap-2">
                {/* Role Specific Portal Badge */}
                {currentUser.role === 'ADMIN' && (
                  <Link
                    href="/admin/dashboard"
                    id="nav-admin-portal-btn"
                    aria-current={isAdminActive ? 'page' : undefined}
                    className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 font-sans text-xs font-semibold transition-all shadow-sm whitespace-nowrap ${
                      isAdminActive
                        ? 'border-[#B59A68] bg-[#6E2634]/60 text-[#B59A68]'
                        : 'border-[#B59A68]/45 bg-gradient-to-r from-[#6E2634]/35 to-[#8A3545]/20 text-[#B59A68] hover:border-[#B59A68] hover:bg-[#6E2634]/55'
                    }`}
                  >
                    <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
                    <span>Admin Portal</span>
                  </Link>
                )}

                {currentUser.role === 'ADVOCATE' && (
                  <Link
                    href="/advocate/dashboard"
                    id="nav-advocate-portal-btn"
                    aria-current={isAdvocateActive ? 'page' : undefined}
                    className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 font-sans text-xs font-semibold transition-all shadow-sm whitespace-nowrap ${
                      isAdvocateActive
                        ? 'border-[#B59A68] bg-[#2e3530] text-[#B59A68]'
                        : 'border-[#B59A68]/50 bg-[#242925] text-[#B59A68] hover:bg-[#2e3530] hover:border-[#B59A68]'
                    }`}
                  >
                    <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
                    <span>Advocate Portal</span>
                  </Link>
                )}

                {/* Messages icon */}
                <Link
                  href="/messages"
                  id="nav-user-messages-btn"
                  title="Messages & Consultations"
                  aria-current={isMessagesActive ? 'page' : undefined}
                  className={`relative p-2 rounded-full border transition-colors ${
                    isMessagesActive
                      ? 'border-[#B59A68]/60 bg-[#B59A68]/10 text-[#B59A68]'
                      : 'border-[#3B3A33]/70 bg-[#1D211F]/70 text-stone/80 hover:text-ivory hover:border-[#B59A68]/40 hover:bg-white/[0.06]'
                  }`}
                >
                  <MessageSquare className="w-4 h-4" />
                  <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#B59A68] ring-2 ring-[#151716]" />
                </Link>

                {/* Profile Pill with Dropdown */}
                <div ref={userMenuRef} className="relative">
                  <button
                    type="button"
                    id="nav-profile-menu-btn"
                    onClick={() => setUserMenuOpen(prev => !prev)}
                    aria-expanded={userMenuOpen}
                    className={`flex items-center gap-2 rounded-full border pl-1 pr-3 py-1 font-sans text-xs font-medium transition-colors whitespace-nowrap focus:outline-none ${
                      isProfileActive || userMenuOpen
                        ? 'border-[#B59A68]/60 bg-[#B59A68]/10 text-ivory'
                        : 'border-[#3B3A33] bg-gradient-to-b from-[#1D211F] to-[#151716] text-ivory hover:border-[#B59A68]/50'
                    }`}
                  >
                    <UserAvatar
                      avatarUrl={currentUser.avatar_url}
                      name={currentUser.full_name}
                      email={currentUser.email}
                      size="sm"
                    />
                    <span className="max-w-[100px] xl:max-w-[130px] truncate text-xs">
                      {currentUser.full_name || 'Profile'}
                    </span>
                    <ChevronDown
                      className={`w-3 h-3 text-stone/70 transition-transform duration-200 ${
                        userMenuOpen ? 'rotate-180' : ''
                      }`}
                    />
                  </button>

                  <AnimatePresence>
                    {userMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: 8, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 8, scale: 0.98 }}
                        transition={{ duration: 0.16, ease: EASE }}
                        className="absolute right-0 top-full pt-2 z-50 w-52"
                      >
                        <div className="rounded-xl border border-[#3B3A33] bg-[#181C1A]/95 backdrop-blur-2xl p-1.5 shadow-2xl shadow-black/80 ring-1 ring-white/5">
                          <div className="px-3 py-2 border-b border-[#3B3A33]/50 flex items-center gap-2.5">
                            <UserAvatar
                              avatarUrl={currentUser.avatar_url}
                              name={currentUser.full_name}
                              email={currentUser.email}
                              size="md"
                            />
                            <div className="flex flex-col min-w-0">
                              <p className="font-sans text-xs font-medium text-ivory truncate">
                                {currentUser.full_name || 'User'}
                              </p>
                              <p className="font-mono text-[10px] text-stone/60 truncate mt-0.5">
                                {currentUser.email || currentUser.role}
                              </p>
                            </div>
                          </div>

                          <div className="py-1">
                            <Link
                              href="/profile"
                              id="nav-profile-link"
                              onClick={() => setUserMenuOpen(false)}
                              aria-current={isProfileActive ? 'page' : undefined}
                              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 font-sans text-xs transition-colors ${
                                isProfileActive
                                  ? 'text-[#B59A68] bg-[#B59A68]/10'
                                  : 'text-stone/80 hover:text-ivory hover:bg-white/[0.05]'
                              }`}
                            >
                              <User className="w-3.5 h-3.5 text-[#B59A68]" />
                              <span>View Profile</span>
                              {isProfileActive && (
                                <span className="ml-auto text-[9px] font-mono font-bold text-[#B59A68] uppercase tracking-widest">now</span>
                              )}
                            </Link>

                            <Link
                              href="/messages"
                              id="nav-messages-link"
                              onClick={() => setUserMenuOpen(false)}
                              aria-current={isMessagesActive ? 'page' : undefined}
                              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 font-sans text-xs transition-colors ${
                                isMessagesActive
                                  ? 'text-[#B59A68] bg-[#B59A68]/10'
                                  : 'text-stone/80 hover:text-ivory hover:bg-white/[0.05]'
                              }`}
                            >
                              <MessageSquare className="w-3.5 h-3.5 text-[#B59A68]" />
                              <span>Messages</span>
                              {isMessagesActive && (
                                <span className="ml-auto text-[9px] font-mono font-bold text-[#B59A68] uppercase tracking-widest">now</span>
                              )}
                            </Link>

                            <button
                              type="button"
                              id="nav-signout-btn"
                              onClick={handleSignOut}
                              className="w-full flex items-center gap-2.5 rounded-lg px-3 py-2 font-sans text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors text-left"
                            >
                              <LogOut className="w-3.5 h-3.5" />
                              <span>Sign Out</span>
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  href="/login"
                  id="nav-signin-btn"
                  aria-current={pathname === '/login' ? 'page' : undefined}
                  className={`font-sans text-xs font-semibold px-3 py-1.5 transition-colors ${
                    pathname === '/login' ? 'text-[#B59A68]' : 'text-stone/80 hover:text-ivory'
                  }`}
                >
                  {t('nav.signIn')}
                </Link>
                <Link
                  href="/signup"
                  id="nav-getstarted-btn"
                  className="btn-oxblood group flex items-center gap-1.5 rounded-full px-4 py-1.5 font-sans text-xs font-semibold tracking-wide shadow-sm"
                >
                  <span>{t('nav.getStarted')}</span>
                  <ArrowUpRight
                    className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                    strokeWidth={2}
                  />
                </Link>
              </div>
            )}
          </div>

          {/* ── Mobile: page label + hamburger ─────────────────────── */}
          <div className="flex items-center gap-2 lg:hidden">
            {/* Current page label chip */}
            {pathname !== '/' && (
              <span className="hidden sm:flex items-center gap-1.5 rounded-full border border-[#B59A68]/30 bg-[#B59A68]/10 px-2.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-widest text-[#B59A68]">
                {pageLabel}
              </span>
            )}
            <button
              type="button"
              id="nav-mobile-toggle"
              onClick={() => setMobileOpen(prev => !prev)}
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#3B3A33]/70 bg-[#1D211F]/70 text-stone/80 hover:text-ivory transition-colors"
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

        {/* ── Mobile breadcrumb strip (xs only — shows current page label) ── */}
        <AnimatePresence>
          {!mobileOpen && pathname !== '/' && (
            <motion.div
              key="breadcrumb"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="lg:hidden border-t border-[#3B3A33]/40 bg-[#151716]/60 px-4 py-1.5 flex items-center gap-1.5"
            >
              <Link href="/" className="font-mono text-[9px] uppercase tracking-widest text-stone/50 hover:text-stone/80 transition-colors">
                Home
              </Link>
              <ChevronRight className="w-2.5 h-2.5 text-stone/30" />
              <span className="font-mono text-[9px] uppercase tracking-widest text-[#B59A68] font-semibold">
                {pageLabel}
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.header>

      {/* ── Mobile Drawer (< lg) ────────────────────────────────────── */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            key="mob"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0, transition: { duration: 0.24, ease: EASE } }}
            exit={{ opacity: 0, y: -8, transition: { duration: 0.18 } }}
            className="fixed inset-x-0 top-[60px] bottom-0 z-40 bg-[#151716]/98 backdrop-blur-2xl lg:hidden overflow-y-auto border-t border-[#3B3A33]"
          >
            <div className="mx-auto max-w-xl px-5 py-6 space-y-6">

              {/* Current page indicator banner */}
              <div className="flex items-center gap-2 rounded-xl border border-[#B59A68]/25 bg-[#B59A68]/08 px-4 py-2.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#B59A68] animate-pulse" />
                <span className="font-mono text-[10px] uppercase tracking-widest text-[#B59A68]/70">Currently viewing</span>
                <span className="font-mono text-[10px] uppercase tracking-widest text-[#B59A68] font-semibold ml-1">{pageLabel}</span>
              </div>

              {/* Section 1: AI Intelligence Suite */}
              <div>
                <p className="font-sans text-[11px] font-semibold uppercase tracking-wider text-[#B59A68] mb-2.5">
                  Judicial Intelligence Suite
                </p>
                <div className="grid grid-cols-1 gap-1.5">
                  {AI_SUITE_MODULES.map(module => {
                    const Icon = module.icon;
                    const isActive = pathname === module.href || pathname.startsWith(module.href + '/');
                    return (
                      <Link
                        key={module.href}
                        href={module.href}
                        onClick={() => setMobileOpen(false)}
                        aria-current={isActive ? 'page' : undefined}
                        className={`flex items-center justify-between rounded-xl p-3 border transition-colors ${
                          isActive
                            ? 'bg-[#B59A68]/15 border-[#B59A68]/40 text-ivory'
                            : 'bg-[#181C1A]/60 border-[#3B3A33]/50 text-stone/85 hover:border-[#B59A68]/30 hover:text-ivory'
                        }`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 ${
                            isActive ? 'bg-[#B59A68]/20 border-[#B59A68]/40 text-[#B59A68]' : 'bg-[#151716] border-[#3B3A33] text-[#B59A68]'
                          }`}>
                            <Icon className="w-4 h-4" strokeWidth={1.5} />
                          </div>
                          <div className="flex flex-col min-w-0">
                            <span className="font-sans text-sm font-medium leading-tight text-ivory">
                              {module.title}
                            </span>
                            <span className="font-sans text-[11px] text-stone/60 line-clamp-1 mt-0.5">
                              {module.desc}
                            </span>
                          </div>
                        </div>
                        {isActive ? (
                          <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-[#B59A68] bg-[#B59A68]/10 border border-[#B59A68]/30 rounded-full px-2 py-0.5 shrink-0 ml-2">
                            Active
                          </span>
                        ) : (
                          <ChevronRight className="w-4 h-4 text-stone/50 shrink-0 ml-2" />
                        )}
                      </Link>
                    );
                  })}
                </div>
              </div>

              {/* Section 2: Explore & Directory */}
              <div>
                <p className="font-sans text-[11px] font-semibold uppercase tracking-wider text-[#B59A68] mb-2.5">
                  Explore & Research
                </p>
                <div className="grid grid-cols-1 gap-1.5">
                  {/* Home link in mobile */}
                  <Link
                    href="/"
                    onClick={() => setMobileOpen(false)}
                    aria-current={isHomeActive ? 'page' : undefined}
                    className={`flex items-center justify-between rounded-xl p-3 border transition-colors ${
                      isHomeActive
                        ? 'bg-[#B59A68]/15 border-[#B59A68]/40 text-ivory'
                        : 'bg-[#181C1A]/60 border-[#3B3A33]/50 text-stone/85 hover:border-[#B59A68]/30 hover:text-ivory'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Home className="w-4 h-4 text-[#B59A68]" />
                      <span className="font-sans text-sm font-medium">Home</span>
                    </div>
                    {isHomeActive ? (
                      <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-[#B59A68] bg-[#B59A68]/10 border border-[#B59A68]/30 rounded-full px-2 py-0.5">
                        Active
                      </span>
                    ) : (
                      <ChevronRight className="w-4 h-4 text-stone/50" />
                    )}
                  </Link>

                  {DIRECT_LINKS.map(link => {
                    const Icon = link.icon;
                    const isActive = pathname === link.href || pathname.startsWith(link.href + '/');
                    return (
                      <Link
                        key={link.href}
                        href={link.href}
                        onClick={() => setMobileOpen(false)}
                        aria-current={isActive ? 'page' : undefined}
                        className={`flex items-center justify-between rounded-xl p-3 border transition-colors ${
                          isActive
                            ? 'bg-[#B59A68]/15 border-[#B59A68]/40 text-ivory'
                            : 'bg-[#181C1A]/60 border-[#3B3A33]/50 text-stone/85 hover:border-[#B59A68]/30 hover:text-ivory'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className="w-4 h-4 text-[#B59A68]" />
                          <span className="font-sans text-sm font-medium">{link.label}</span>
                        </div>
                        {isActive ? (
                          <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-[#B59A68] bg-[#B59A68]/10 border border-[#B59A68]/30 rounded-full px-2 py-0.5">
                            Active
                          </span>
                        ) : link.hasLiveBadge ? (
                          <span className="font-mono text-[10px] bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded-full font-semibold">
                            LIVE
                          </span>
                        ) : (
                          <ChevronRight className="w-4 h-4 text-stone/50" />
                        )}
                      </Link>
                    );
                  })}
                </div>
              </div>

              {/* Section 3: User Account & Portals */}
              <div className="pt-2 border-t border-[#3B3A33]/70">
                {currentUser ? (
                  <div className="flex flex-col gap-2.5">
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-[#1D211F] border border-[#3B3A33]">
                      <UserAvatar
                        avatarUrl={currentUser.avatar_url}
                        name={currentUser.full_name}
                        email={currentUser.email}
                        size="md"
                      />
                      <div className="flex flex-col min-w-0">
                        <span className="font-sans text-sm font-semibold text-ivory truncate">
                          {currentUser.full_name || 'User'}
                        </span>
                        <span className="font-mono text-[10px] text-stone/60 truncate">
                          {currentUser.email || currentUser.role}
                        </span>
                      </div>
                    </div>

                    {currentUser.role === 'ADMIN' && (
                      <Link
                        href="/admin/dashboard"
                        onClick={() => setMobileOpen(false)}
                        aria-current={isAdminActive ? 'page' : undefined}
                        className={`w-full flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 font-sans text-sm font-semibold ${
                          isAdminActive
                            ? 'border-[#B59A68] bg-[#6E2634]/60 text-[#B59A68]'
                            : 'border-[#B59A68] bg-[#6E2634]/40 text-[#B59A68]'
                        }`}
                      >
                        <Scale className="w-4 h-4 text-[#B59A68]" />
                        <span>Admin Operations Portal</span>
                        {isAdminActive && <span className="ml-auto text-[9px] font-mono font-bold text-[#B59A68] uppercase tracking-widest">Active</span>}
                      </Link>
                    )}

                    {currentUser.role === 'ADVOCATE' && (
                      <Link
                        href="/advocate/dashboard"
                        onClick={() => setMobileOpen(false)}
                        aria-current={isAdvocateActive ? 'page' : undefined}
                        className={`w-full flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 font-sans text-sm font-semibold ${
                          isAdvocateActive
                            ? 'border-[#B59A68] bg-[#2e3530] text-[#B59A68]'
                            : 'border-[#B59A68]/60 bg-[#242925] text-[#B59A68]'
                        }`}
                      >
                        <Scale className="w-4 h-4 text-[#B59A68]" />
                        <span>Advocate Portal</span>
                        {isAdvocateActive && <span className="ml-auto text-[9px] font-mono font-bold text-[#B59A68] uppercase tracking-widest">Active</span>}
                      </Link>
                    )}

                    <div className="grid grid-cols-2 gap-2">
                      <Link
                        href="/messages"
                        onClick={() => setMobileOpen(false)}
                        aria-current={isMessagesActive ? 'page' : undefined}
                        className={`flex items-center justify-center gap-2 rounded-xl border px-3 py-2 font-sans text-xs font-medium ${
                          isMessagesActive
                            ? 'border-[#B59A68]/60 bg-[#B59A68]/10 text-[#B59A68]'
                            : 'border-[#3B3A33] bg-[#181C1A] text-ivory hover:border-[#B59A68]/50'
                        }`}
                      >
                        <MessageSquare className="w-3.5 h-3.5 text-[#B59A68]" />
                        <span>Messages</span>
                      </Link>

                      <Link
                        href="/profile"
                        onClick={() => setMobileOpen(false)}
                        aria-current={isProfileActive ? 'page' : undefined}
                        className={`flex items-center justify-center gap-2 rounded-xl border px-3 py-2 font-sans text-xs font-medium ${
                          isProfileActive
                            ? 'border-[#B59A68]/60 bg-[#B59A68]/10 text-[#B59A68]'
                            : 'border-[#3B3A33] bg-[#181C1A] text-ivory hover:border-[#B59A68]/50'
                        }`}
                      >
                        <User className="w-3.5 h-3.5 text-[#B59A68]" />
                        <span>Profile</span>
                      </Link>
                    </div>

                    <button
                      type="button"
                      onClick={handleSignOut}
                      className="w-full flex items-center justify-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2 font-sans text-xs font-medium text-red-400 hover:bg-red-500/20 transition-colors"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2.5">
                    <Link
                      href="/login"
                      onClick={() => setMobileOpen(false)}
                      aria-current={pathname === '/login' ? 'page' : undefined}
                      className={`w-full text-center rounded-xl border px-5 py-2.5 font-sans text-sm font-medium transition-colors ${
                        pathname === '/login'
                          ? 'border-[#B59A68]/50 text-[#B59A68] bg-[#B59A68]/10'
                          : 'border-[#3B3A33] text-ivory/80 hover:text-ivory hover:border-[#8A3545]/60'
                      }`}
                    >
                      {t('nav.signIn')}
                    </Link>
                    <Link
                      href="/signup"
                      onClick={() => setMobileOpen(false)}
                      className="btn-oxblood group flex w-full items-center justify-center gap-2 rounded-xl px-5 py-2.5 font-sans text-sm font-semibold tracking-wide"
                    >
                      <span>{t('nav.getStarted')}</span>
                      <ArrowUpRight
                        className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                        strokeWidth={2}
                      />
                    </Link>
                  </div>
                )}
              </div>
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
            <Image
              src="/logo-transparent.png"
              alt="NyayaSarathi Logo"
              width={24}
              height={24}
              className="h-6 w-6 object-contain drop-shadow-[0_2px_8px_rgba(181,154,104,0.3)]"
            />
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
