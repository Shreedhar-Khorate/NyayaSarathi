'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ShieldAlert, ArrowLeft, LogOut, User, Loader2, Scale } from 'lucide-react';
import { getUser, fetchMe, removeAuth, type UserProfile } from '@/lib/auth';

interface RoleGuardProps {
  allowedRoles: string[];
  portalName?: string;
  children: React.ReactNode;
}

export function RoleGuard({ allowedRoles, portalName = 'Restricted Judicial Portal', children }: RoleGuardProps) {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isVerifying, setIsVerifying] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);

  const rolesKey = allowedRoles.slice().sort().join(',');

  useEffect(() => {
    let isMounted = true;

    async function checkAuth() {
      const cached = getUser();
      const currentPath = typeof window !== 'undefined' ? window.location.pathname + window.location.search : '';
      const loginUrl = currentPath ? `/login?redirect=${encodeURIComponent(currentPath)}` : '/login';

      if (!cached) {
        setIsVerifying(false);
        router.replace(loginUrl);
        return;
      }

      // Fast-path: check cached user role immediately
      const cachedRole = (cached.role || 'USER').toUpperCase();
      const hasInitialPermission = allowedRoles.map((r) => r.toUpperCase()).includes(cachedRole);
      if (hasInitialPermission) {
        setCurrentUser(cached);
        setIsAuthorized(true);
        setIsVerifying(false);
      }

      // Verify with server to defeat stale JWTs and demotion in background
      try {
        const freshUser = await fetchMe();
        if (!isMounted) return;

        if (!freshUser) {
          setIsVerifying(false);
          router.replace(loginUrl);
          return;
        }

        setCurrentUser(freshUser);
        const userRole = (freshUser.role || 'USER').toUpperCase();
        const hasPermission = allowedRoles.map((r) => r.toUpperCase()).includes(userRole);
        setIsAuthorized(hasPermission);
      } catch {
        if (!isMounted) return;
        if (!hasInitialPermission) {
          setIsVerifying(false);
          router.replace(loginUrl);
        }
      } finally {
        if (isMounted) {
          setIsVerifying(false);
        }
      }
    }

    checkAuth();

    return () => {
      isMounted = false;
    };
  }, [router, rolesKey]);

  if (isVerifying) {
    return (
      <div className="min-h-screen bg-[#151716] flex flex-col items-center justify-center p-6 text-center">
        <div className="w-16 h-16 rounded-2xl bg-[#6E2634]/20 border border-[#B59A68]/40 flex items-center justify-center mb-6 shadow-2xl relative">
          <div className="absolute inset-0 rounded-2xl bg-[#B59A68]/10 blur-xl animate-pulse" />
          <Loader2 className="w-8 h-8 text-[#B59A68] animate-spin relative z-10" />
        </div>
        <h2 className="font-display text-xl text-[#F4EFE5] font-semibold mb-2">
          Verifying Judicial Security Credentials...
        </h2>
        <p className="font-sans text-xs text-[#A9A49A] max-w-sm">
          Establishing role clearance with the NyayaSarathi authenticated gateway.
        </p>
      </div>
    );
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-[#151716] flex items-center justify-center p-6 relative overflow-hidden">
        {/* Ambient background glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-[#6E2634]/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-72 h-72 bg-[#B59A68]/10 rounded-full blur-3xl pointer-events-none" />

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="relative z-10 max-w-lg w-full rounded-2xl border border-[#6E2634]/40 bg-[#1D211F]/90 p-8 text-center backdrop-blur-xl shadow-2xl"
        >
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-[#6E2634] bg-[#6E2634]/20 shadow-inner">
            <ShieldAlert className="h-8 w-8 text-[#E25C6F]" />
          </div>

          <span className="inline-block px-3 py-1 rounded-full text-[11px] font-mono uppercase tracking-wider text-[#B59A68] bg-[#B59A68]/10 border border-[#B59A68]/30 mb-3">
            Security Boundary — 403 Forbidden
          </span>

          <h1 className="font-display text-2xl font-bold text-[#F4EFE5] mb-2">
            Restricted Access
          </h1>

          <p className="font-sans text-sm text-[#A9A49A] leading-relaxed mb-6">
            You do not possess the required clearance for <strong className="text-[#F4EFE5]">{portalName}</strong>. 
            This area requires one of the following judicial roles: <span className="font-mono text-[#B59A68] font-semibold">{allowedRoles.join(' or ')}</span>.
          </p>

          <div className="rounded-xl border border-[#3B3A33] bg-[#151716]/80 p-4 mb-6 text-left">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-[#A9A49A]">Current Account:</span>
              <span className="font-medium text-[#F4EFE5]">{currentUser?.email}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#A9A49A]">Your Assigned Role:</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]/50">
                {currentUser?.role || 'USER'}
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <Link
              href="/"
              className="w-full sm:w-1/2 flex items-center justify-center gap-2 rounded-xl border border-[#3B3A33] bg-[#242925] px-4 py-2.5 text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return Home</span>
            </Link>

            <button
              onClick={() => {
                removeAuth();
                router.push('/login');
              }}
              className="w-full sm:w-1/2 flex items-center justify-center gap-2 rounded-xl border border-[#6E2634]/60 bg-[#6E2634]/30 px-4 py-2.5 text-xs font-semibold text-[#F4EFE5] hover:bg-[#6E2634]/50 transition-colors"
            >
              <LogOut className="w-4 h-4 text-[#E25C6F]" />
              <span>Switch Account</span>
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return <>{children}</>;
}
