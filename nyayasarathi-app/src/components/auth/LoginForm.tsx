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
      {/* Editorial Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE }}
        className="mb-7"
      >
        <div className="flex items-center gap-2 mb-2 font-mono text-xs uppercase tracking-[0.25em] text-[#B59A68]">
          <span>02</span>
          <span>&bull;</span>
          <span>AUTHENTICATION</span>
        </div>
        <h2 className="font-display text-3xl sm:text-4xl font-medium text-[#F4EFE5] tracking-[-0.01em]">
          Welcome back.
        </h2>
        <p className="font-sans text-sm sm:text-base text-[#A9A49A] mt-1.5">
          Continue your legal research and case analysis.
        </p>
      </motion.div>

      {/* General Error Banner */}
      {errors.general && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          role="alert"
          className="mb-6 rounded-xl border border-[#8A3545]/60 bg-[#6E2634]/15 px-4 sm:px-5 py-3 text-sm text-[#F4EFE5]"
        >
          {errors.general}
        </motion.div>
      )}

      {/* ── Google OAuth Button ─────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.08, ease: EASE }}
        className="mb-6"
      >
        <GoogleAuthButton label="Continue with Google" />
      </motion.div>

      {/* ── Divider ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 h-px bg-[#3B3A33]/60" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-[#A9A49A]/70">
          or sign in with email
        </span>
        <div className="flex-1 h-px bg-[#3B3A33]/60" />
      </div>

      {/* ── Email / Password Login Form ─────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
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
        <div className="flex items-center justify-between pt-1">
          <label className="flex items-center gap-2.5 cursor-pointer select-none group">
            <input
              type="checkbox"
              id="remember-me"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 rounded border-[#3B3A33] bg-[#1D211F] text-[#6E2634] focus:ring-[#6E2634] focus:ring-offset-0 transition-colors cursor-pointer accent-[#6E2634]"
            />
            <span className="font-sans text-sm text-[#A9A49A] group-hover:text-[#F4EFE5] transition-colors">
              Remember me
            </span>
          </label>

          <Link
            href="/forgot-password"
            className="editorial-link font-sans text-sm text-[#A9A49A] hover:text-[#B59A68] transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        {/* Primary CTA */}
        <div className="pt-2">
          <AuthButton type="submit" isLoading={isLoading}>
            Continue Research
          </AuthButton>
        </div>
      </form>

      {/* Switch to Sign Up */}
      <div className="mt-8 pt-5 border-t border-[#3B3A33]/50 text-center">
        <p className="font-sans text-sm text-[#A9A49A]">
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
      <div className="mt-5 flex justify-center">
        <TrustIndicator />
      </div>
    </div>
  );
}

export default LoginForm;
