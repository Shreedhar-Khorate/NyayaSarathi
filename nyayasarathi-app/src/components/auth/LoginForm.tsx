'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import AuthInput from './AuthInput';
import PasswordInput from './PasswordInput';
import AuthButton from './AuthButton';
import TrustIndicator from './TrustIndicator';
import { GoogleAuthButton } from './GoogleAuthButton';
import { loginUser } from '@/lib/auth';
import { useGoogleAuth } from '@/lib/useGoogleAuth';

const EASE = [0.16, 1, 0.3, 1] as const;

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string; general?: string }>({});
  const [isLoading, setIsLoading] = useState(false);

  // Handle Google OAuth callback on mount
  const googleAuth = useGoogleAuth();
  useEffect(() => {
    if (googleAuth.handled && googleAuth.user) {
      if (!googleAuth.user.profile_completed) {
        router.push('/profile/complete');
      } else {
        const redirect = searchParams?.get('redirect');
        if (redirect && redirect.startsWith('/') && !redirect.startsWith('//')) {
          router.push(redirect);
        } else {
          router.push(googleAuth.user.role === 'ADVOCATE' ? '/advocate/dashboard' : '/predictor');
        }
      }
    }
    if (googleAuth.error) {
      setErrors({ general: googleAuth.error });
    }
  }, [googleAuth.handled, googleAuth.error, router, searchParams]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    // Client-side form validation
    const nextErrors: { email?: string; password?: string } = {};
    if (!email.trim()) {
      nextErrors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      nextErrors.email = 'Please provide a valid email format';
    }

    if (!password) {
      nextErrors.password = 'Password is required to authenticate';
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setIsLoading(true);

    try {
      const res = await loginUser(email, password);
      const redirect = searchParams?.get('redirect');
      if (redirect && redirect.startsWith('/') && !redirect.startsWith('//')) {
        router.push(redirect);
      } else {
        router.push(res.user?.role === 'ADVOCATE' ? '/advocate/dashboard' : '/predictor');
      }
    } catch (err: any) {
      setErrors({ general: err.message || 'Authentication failed. Please verify your credentials and try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-lg mx-auto">
      {/* Mode Switcher Tabs */}
      <div className="flex items-center p-1 rounded-xl bg-[#1D211F] border border-[#3B3A33]/80 mb-5 sm:mb-6">
        <Link
          href="/login"
          className="flex-1 text-center py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all bg-[#6E2634] text-[#F4EFE5] shadow-[0_2px_8px_rgba(110,38,52,0.4)]"
        >
          Sign In
        </Link>
        <Link
          href="/signup"
          className="flex-1 text-center py-2 rounded-lg text-xs sm:text-sm font-medium transition-all text-[#A9A49A] hover:text-[#F4EFE5]"
        >
          Create Account
        </Link>
      </div>

      {/* Editorial Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE }}
        className="mb-4 sm:mb-5"
      >
        <div className="flex items-center gap-2 mb-1.5 font-mono text-[11px] uppercase tracking-[0.22em] text-[#B59A68]">
          <span>02</span>
          <span>&bull;</span>
          <span>AUTHENTICATION</span>
        </div>
        <h2 className="font-display text-2xl sm:text-3xl font-medium text-[#F4EFE5] tracking-[-0.01em]">
          Welcome back.
        </h2>
        <p className="font-sans text-xs sm:text-sm text-[#A9A49A] mt-1">
          Continue your legal research and case analysis.
        </p>
      </motion.div>

      {/* Quick Demo Access Bar */}
      <div className="mb-4 sm:mb-5 p-2.5 sm:p-3 rounded-xl bg-[#1D211F]/90 border border-[#B59A68]/25 shadow-sm">
        <div className="flex items-center justify-between mb-2 px-0.5">
          <span className="font-mono text-[10px] sm:text-[11px] uppercase tracking-wider text-[#B59A68] font-semibold flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#B59A68] animate-pulse" />
            Quick Demo Profiles:
          </span>
          <span className="text-[10px] text-[#A9A49A]/70 font-mono">1-click fill</span>
        </div>
        <div className="grid grid-cols-3 gap-1.5 sm:gap-2">
          <button
            type="button"
            onClick={() => {
              setEmail('test_roles_advocate@nyayasarathi.in');
              setPassword('Advocate@12345');
              setErrors({});
            }}
            className="px-2 py-1.5 rounded-lg bg-[#151716] border border-[#3B3A33] hover:border-[#B59A68] text-left transition-all hover:bg-[#252A27] group cursor-pointer"
            title="Adv. Priya Sharma (Advocate Role)"
          >
            <div className="flex items-center gap-1">
              <span className="text-[#B59A68] font-bold text-[9px] sm:text-[10px] tracking-wide block uppercase">
                ADVOCATE
              </span>
            </div>
            <span className="truncate block text-[#F4EFE5] text-[11px] sm:text-xs font-medium group-hover:text-[#B59A68]">
              Adv. Priya
            </span>
          </button>

          <button
            type="button"
            onClick={() => {
              setEmail('test_roles_user@nyayasarathi.in');
              setPassword('User@12345');
              setErrors({});
            }}
            className="px-2 py-1.5 rounded-lg bg-[#151716] border border-[#3B3A33] hover:border-[#71877A] text-left transition-all hover:bg-[#252A27] group cursor-pointer"
            title="Rahul Verma (Citizen Litigant)"
          >
            <div className="flex items-center gap-1">
              <span className="text-[#71877A] font-bold text-[9px] sm:text-[10px] tracking-wide block uppercase">
                CITIZEN
              </span>
            </div>
            <span className="truncate block text-[#F4EFE5] text-[11px] sm:text-xs font-medium group-hover:text-[#71877A]">
              Rahul Verma
            </span>
          </button>

          <button
            type="button"
            onClick={() => {
              setEmail('test_roles_admin@nyayasarathi.in');
              setPassword('Admin@12345');
              setErrors({});
            }}
            className="px-2 py-1.5 rounded-lg bg-[#151716] border border-[#3B3A33] hover:border-[#8A3545] text-left transition-all hover:bg-[#252A27] group cursor-pointer"
            title="Registrar General (Administrator)"
          >
            <div className="flex items-center gap-1">
              <span className="text-[#DC3854] font-bold text-[9px] sm:text-[10px] tracking-wide block uppercase">
                ADMIN
              </span>
            </div>
            <span className="truncate block text-[#F4EFE5] text-[11px] sm:text-xs font-medium group-hover:text-[#DC3854]">
              Registrar
            </span>
          </button>
        </div>
      </div>

      {/* General Error Banner */}
      {errors.general && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          role="alert"
          className="mb-4 rounded-xl border border-[#8A3545]/60 bg-[#6E2634]/15 px-3.5 sm:px-4 py-2.5 text-xs sm:text-sm text-[#F4EFE5]"
        >
          {errors.general}
        </motion.div>
      )}

      {/* ── Google OAuth Button ─────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.08, ease: EASE }}
        className="mb-4 sm:mb-5"
      >
        <GoogleAuthButton label="Continue with Google" />
      </motion.div>

      {/* ── Divider ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 mb-4 sm:mb-5">
        <div className="flex-1 h-px bg-[#3B3A33]/60" />
        <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-[#A9A49A]/70">
          or sign in with email
        </span>
        <div className="flex-1 h-px bg-[#3B3A33]/60" />
      </div>

      {/* ── Email / Password Login Form ─────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="space-y-3.5 sm:space-y-4" noValidate>
        {/* Email Address */}
        <AuthInput
          id="login-email"
          name="email"
          type="email"
          autoComplete="email"
          label="Email Address"
          placeholder="e.g. advocate.sharma@delhibar.org"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          required
        />

        {/* Password */}
        <PasswordInput
          id="login-password"
          name="password"
          autoComplete="current-password"
          label="Password"
          placeholder="Enter your account password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          required
        />

        {/* Remember me & Forgot Password */}
        <div className="flex items-center justify-between pt-0.5">
          <label className="flex items-center gap-2 cursor-pointer select-none group">
            <input
              type="checkbox"
              id="remember-me"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-3.5 h-3.5 sm:w-4 sm:h-4 rounded border-[#3B3A33] bg-[#1D211F] text-[#6E2634] focus:ring-[#B59A68] focus:ring-offset-0 transition-colors cursor-pointer accent-[#6E2634]"
            />
            <span className="font-sans text-xs sm:text-sm text-[#A9A49A] group-hover:text-[#F4EFE5] transition-colors">
              Remember me
            </span>
          </label>

          <Link
            href="/forgot-password"
            className="editorial-link font-sans text-xs sm:text-sm text-[#A9A49A] hover:text-[#B59A68] transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        {/* Primary CTA */}
        <div className="pt-1.5 sm:pt-2">
          <AuthButton type="submit" isLoading={isLoading}>
            Continue Research
          </AuthButton>
        </div>
      </form>

      {/* Switch to Sign Up */}
      <div className="mt-5 sm:mt-6 pt-3.5 sm:pt-4 border-t border-[#3B3A33]/50 text-center">
        <p className="font-sans text-xs sm:text-sm text-[#A9A49A]">
          Don&apos;t have an account?{' '}
          <Link
            href="/signup"
            className="editorial-link font-semibold text-[#F4EFE5] hover:text-[#B59A68] ml-1 transition-colors"
          >
            Create an account &rarr;
          </Link>
        </p>
      </div>

      {/* Trust Indicator */}
      <div className="mt-3.5 sm:mt-4 flex justify-center">
        <TrustIndicator />
      </div>
    </div>
  );
}

export default LoginForm;
