'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import AuthInput from './AuthInput';
import PasswordInput from './PasswordInput';
import AuthButton from './AuthButton';
import TrustIndicator from './TrustIndicator';
import { loginUser } from '@/lib/auth';

const EASE = [0.16, 1, 0.3, 1] as const;

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string; general?: string }>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    // Client-side form validation
    const newErrors: { email?: string; password?: string } = {};
    if (!email.trim()) {
      newErrors.email = 'Please enter your email address.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Please provide a valid email format.';
    }

    if (!password) {
      newErrors.password = 'Please enter your password.';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);

    try {
      await loginUser(email, password);
      router.push('/predictor');
    } catch (err: any) {
      setErrors({ general: err.message || 'Authentication failed. Please verify your credentials and try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Editorial Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE }}
        className="mb-6"
      >
        <div className="flex items-center gap-2 mb-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-[#B59A68]">
          <span>02</span>
          <span>&bull;</span>
          <span>AUTHENTICATION</span>
        </div>
        <h2 className="font-display text-2xl sm:text-3xl font-medium text-[#F4EFE5] tracking-[-0.01em]">
          Welcome back.
        </h2>
        <p className="font-sans text-xs sm:text-sm text-[#A9A49A] mt-1">
          Continue your legal research.
        </p>
      </motion.div>

      {/* General Error Banner if applicable */}
      {errors.general && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          role="alert"
          className="mb-5 rounded-lg border border-[#8A3545]/60 bg-[#6E2634]/15 px-4 py-2.5 text-xs text-[#F4EFE5]"
        >
          {errors.general}
        </motion.div>
      )}

      {/* Login Form */}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Email Address */}
        <AuthInput
          id="login-email"
          name="email"
          type="email"
          autoComplete="email"
          label="Email Address"
          placeholder="Enter your email"
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
          placeholder="Enter your password"
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
              className="w-3.5 h-3.5 rounded border-[#3B3A33] bg-[#1D211F] text-[#6E2634] focus:ring-[#6E2634] focus:ring-offset-0 transition-colors cursor-pointer accent-[#6E2634]"
            />
            <span className="font-sans text-xs text-[#A9A49A] group-hover:text-[#F4EFE5] transition-colors">
              Remember me
            </span>
          </label>

          <Link
            href="/forgot-password"
            className="editorial-link font-sans text-xs text-[#A9A49A] hover:text-[#F4EFE5]"
          >
            Forgot password?
          </Link>
        </div>

        {/* Primary CTA */}
        <div className="pt-1.5">
          <AuthButton type="submit" isLoading={isLoading}>
            Continue Research
          </AuthButton>
        </div>
      </form>

      {/* Switch to Sign Up */}
      <div className="mt-6 pt-4 border-t border-[#3B3A33]/50 text-center">
        <p className="font-sans text-xs text-[#A9A49A]">
          Don&apos;t have an account?{' '}
          <Link
            href="/signup"
            className="editorial-link font-medium text-[#F4EFE5] hover:text-[#B59A68] ml-1"
          >
            Begin research &rarr;
          </Link>
        </p>
      </div>

      {/* Trust Indicator */}
      <div className="mt-4 flex justify-center">
        <TrustIndicator />
      </div>
    </div>
  );
}

export default LoginForm;
