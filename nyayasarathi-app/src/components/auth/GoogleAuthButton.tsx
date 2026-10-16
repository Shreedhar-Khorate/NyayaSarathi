'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { API_BASE_URL } from '@/lib/config';

interface GoogleAuthButtonProps {
  label?: string;
}

/**
 * GoogleAuthButton — redirects to backend Google OAuth flow.
 * The backend handles token exchange, user upsert (Supabase + SQLite), JWT issuance
 * and redirects back to this page with credentials in the URL.
 */
export function GoogleAuthButton({ label = 'Continue with Google' }: GoogleAuthButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleAuth = () => {
    setIsLoading(true);
    // Redirect to backend Google OAuth initiation endpoint
    window.location.href = `${API_BASE_URL}/api/auth/google`;
  };

  return (
    <motion.button
      type="button"
      id="google-auth-btn"
      onClick={handleGoogleAuth}
      disabled={isLoading}
      whileHover={!isLoading ? { y: -1, filter: 'brightness(1.06)' } : undefined}
      whileTap={!isLoading ? { scale: 0.98 } : undefined}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      className="
        group relative w-full flex items-center justify-center gap-3
        rounded-xl border border-[#3B3A33] bg-[#1D211F]
        px-5 py-3 font-sans text-sm font-medium text-[#F4EFE5]
        hover:bg-[#242925] hover:border-[#B59A68]/40
        focus:outline-none focus-visible:ring-2 focus-visible:ring-[#B59A68]
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-all duration-200 min-h-[44px]
        shadow-[0_1px_3px_rgba(0,0,0,0.25)]
      "
      aria-label="Continue with Google"
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin text-[#A9A49A] shrink-0" />
          <span className="text-[#A9A49A]">Connecting to Google…</span>
        </>
      ) : (
        <>
          {/* Google G Logo SVG */}
          <svg
            className="w-4 h-4 shrink-0"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          <span>{label}</span>
        </>
      )}
    </motion.button>
  );
}

export default GoogleAuthButton;
