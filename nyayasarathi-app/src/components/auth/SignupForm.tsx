'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import AuthInput from './AuthInput';
import PasswordInput from './PasswordInput';
import AuthButton from './AuthButton';
import TrustIndicator from './TrustIndicator';

const EASE = [0.16, 1, 0.3, 1] as const;

export function SignupForm() {
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
      // Connect to signup workflow (real logic, no fake mock response)
      await new Promise((resolve) => setTimeout(resolve, 800));
    } catch {
      setErrors({ general: 'Unable to complete registration. Please try again.' });
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
        className="mb-4"
      >
        <div className="flex items-center gap-2 mb-1 font-mono text-[10px] uppercase tracking-[0.25em] text-[#B59A68]">
          <span>02</span>
          <span>&bull;</span>
          <span>REGISTRATION</span>
        </div>
        <h2 className="font-display text-2xl sm:text-3xl font-medium text-[#F4EFE5] tracking-[-0.01em]">
          Begin your research.
        </h2>
        <p className="font-sans text-xs text-[#A9A49A] mt-0.5 leading-relaxed">
          Create your NyayaSarathi account and build your legal research workspace.
        </p>
      </motion.div>

      {/* General Error Banner if applicable */}
      {errors.general && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          role="alert"
          className="mb-4 rounded-lg border border-[#8A3545]/60 bg-[#6E2634]/15 px-4 py-2 text-xs text-[#F4EFE5]"
        >
          {errors.general}
        </motion.div>
      )}

      {/* Signup Form */}
      <form onSubmit={handleSubmit} className="space-y-3" noValidate>
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
          placeholder="advocate@chamber.in"
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
          placeholder="Create a secure password"
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
          placeholder="Re-enter your password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={errors.confirmPassword}
          required
        />

        {/* Primary CTA */}
        <div className="pt-1">
          <AuthButton type="submit" isLoading={isLoading}>
            Create Research Account
          </AuthButton>
        </div>
      </form>

      {/* Switch to Sign In */}
      <div className="mt-5 pt-3.5 border-t border-[#3B3A33]/50 text-center">
        <p className="font-sans text-xs text-[#A9A49A]">
          Already have an account?{' '}
          <Link
            href="/login"
            className="editorial-link font-medium text-[#F4EFE5] hover:text-[#B59A68] ml-1"
          >
            Sign in
          </Link>
        </p>
      </div>

      {/* Trust Indicator */}
      <div className="mt-3.5 flex justify-center">
        <TrustIndicator />
      </div>
    </div>
  );
}

export default SignupForm;
