'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import AuthInput from './AuthInput';
import PasswordInput from './PasswordInput';
import AuthButton from './AuthButton';
import TrustIndicator from './TrustIndicator';
import { GoogleAuthButton } from './GoogleAuthButton';
import { signupUser } from '@/lib/auth';
import { useGoogleAuth } from '@/lib/useGoogleAuth';

const EASE = [0.16, 1, 0.3, 1] as const;

export function SignupForm() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    general?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);

  // Handle Google OAuth callback on mount
  const googleAuth = useGoogleAuth();
  useEffect(() => {
    if (googleAuth.handled && googleAuth.user) {
      if (!googleAuth.user.profile_completed) {
        router.push('/profile/complete');
      } else {
        router.push('/predictor');
      }
    }
    if (googleAuth.error) {
      setErrors({ general: googleAuth.error });
    }
  }, [googleAuth.handled, googleAuth.error, router]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    const newErrors: {
      fullName?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    if (!fullName.trim()) {
      newErrors.fullName = 'Please enter your full name.';
    }

    if (!email.trim()) {
      newErrors.email = 'Please enter your email address.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Please provide a valid email format.';
    }

    if (!password) {
      newErrors.password = 'Please create a password.';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters.';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password.';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match.';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);

    try {
      await signupUser(email, password, fullName);
      router.push('/predictor');
    } catch (err: any) {
      setErrors({ general: err.message || 'Unable to complete registration. Please try again.' });
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
        className="mb-6"
      >
        <div className="flex items-center gap-2 mb-2 font-mono text-xs uppercase tracking-[0.25em] text-[#B59A68]">
          <span>02</span>
          <span>&bull;</span>
          <span>REGISTRATION</span>
        </div>
        <h2 className="font-display text-3xl sm:text-4xl font-medium text-[#F4EFE5] tracking-[-0.01em]">
          Begin your research.
        </h2>
        <p className="font-sans text-sm sm:text-base text-[#A9A49A] mt-1.5 leading-relaxed">
          Create your NyayaSarathi workspace for verifiable judicial intelligence.
        </p>
      </motion.div>

      {/* General Error Banner */}
      {errors.general && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          role="alert"
          className="mb-5 rounded-xl border border-[#8A3545]/60 bg-[#6E2634]/15 px-4 sm:px-5 py-3 text-sm text-[#F4EFE5]"
        >
          {errors.general}
        </motion.div>
      )}

      {/* ── Google OAuth Button ─────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.08, ease: EASE }}
        className="mb-5"
      >
        <GoogleAuthButton label="Sign up with Google" />
      </motion.div>

      {/* ── Divider ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex-1 h-px bg-[#3B3A33]/60" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-[#A9A49A]/70">
          or register with email
        </span>
        <div className="flex-1 h-px bg-[#3B3A33]/60" />
      </div>

      {/* ── Email / Password Signup Form ─────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Full Name */}
        <AuthInput
          id="signup-fullname"
          name="fullName"
          type="text"
          autoComplete="name"
          label="Full Name"
          placeholder="e.g. Adv. Rajesh Sharma"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          error={errors.fullName}
          required
        />

        {/* Email Address */}
        <AuthInput
          id="signup-email"
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
          id="signup-password"
          name="password"
          autoComplete="new-password"
          label="Password"
          placeholder="Create a secure password (min. 8 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          required
        />

        {/* Confirm Password */}
        <PasswordInput
          id="signup-confirm-password"
          name="confirmPassword"
          autoComplete="new-password"
          label="Confirm Password"
          placeholder="Re-enter your password to confirm"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={errors.confirmPassword}
          required
        />

        {/* Primary CTA */}
        <div className="pt-2">
          <AuthButton type="submit" isLoading={isLoading}>
            Create Research Account
          </AuthButton>
        </div>
      </form>

      {/* Switch to Sign In */}
      <div className="mt-6 pt-4 border-t border-[#3B3A33]/50 text-center">
        <p className="font-sans text-sm text-[#A9A49A]">
          Already have an account?{' '}
          <Link
            href="/login"
            className="editorial-link font-semibold text-[#F4EFE5] hover:text-[#B59A68] ml-1 transition-colors"
          >
            Sign in &rarr;
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

export default SignupForm;
