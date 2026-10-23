'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Scale, Building2, Briefcase, User, AlertCircle, ArrowRight, Loader2, Upload, Camera } from 'lucide-react';
import { UserAvatar } from '@/components/ui/UserAvatar';
import { getUser, completeProfileOnboarding, type UserProfile } from '@/lib/auth';

const EASE = [0.16, 1, 0.3, 1] as const;

export default function ProfileCompletePage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [fullName, setFullName] = useState('');
  const [organization, setOrganization] = useState('');
  const [designation, setDesignation] = useState('');
  const [avatarUrl, setAvatarUrl] = useState<string | null>('');
  const [isCompressingImage, setIsCompressingImage] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const user = getUser();
    if (!user) {
      router.push('/login');
      return;
    }
    // If profile is already completed, redirect to workspace
    if (user.profile_completed) {
      router.push('/predictor');
      return;
    }
    setCurrentUser(user);
    setFullName(user.full_name || '');
    setAvatarUrl(user.avatar_url || '');
    setIsLoading(false);
  }, [router]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setError('Please select an image file (PNG, JPG, WebP).');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('Selected image is too large. Please select an image under 10MB.');
      return;
    }

    setIsCompressingImage(true);
    setError(null);
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new window.Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const maxDim = 256;
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > maxDim) {
            height = Math.round((height * maxDim) / width);
            width = maxDim;
          }
        } else {
          if (height > maxDim) {
            width = Math.round((width * maxDim) / height);
            height = maxDim;
          }
        }

        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(img, 0, 0, width, height);
          const compressed = canvas.toDataURL('image/jpeg', 0.85);
          setAvatarUrl(compressed);
        }
        setIsCompressingImage(false);
      };
      img.onerror = () => {
        setError('Failed to process image file.');
        setIsCompressingImage(false);
      };
      img.src = event.target?.result as string;
    };
    reader.onerror = () => {
      setError('Could not read image file.');
      setIsCompressingImage(false);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!fullName.trim()) {
      setError('Please provide your full legal or professional name.');
      return;
    }
    if (!organization.trim()) {
      setError('Please specify your Chambers, Court, Law Firm, or University.');
      return;
    }
    if (!designation.trim()) {
      setError('Please specify your designation (e.g. Advocate, Senior Counsel, Researcher).');
      return;
    }

    setIsSubmitting(true);
    try {
      const cleanAvatar = avatarUrl && avatarUrl.trim() ? avatarUrl.trim() : null;
      await completeProfileOnboarding({
        full_name: fullName.trim(),
        organization: organization.trim(),
        designation: designation.trim(),
        avatar_url: cleanAvatar,
      });
      router.push('/predictor');
    } catch (err: any) {
      setError(err.message || 'Failed to complete profile onboarding. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#151716] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#B59A68]" />
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-[#151716] text-[#F4EFE5] flex flex-col justify-between items-center px-4 py-8 selection:bg-[#6E2634] selection:text-[#F4EFE5]">
      {/* Top Universal Access Bar */}
      <header className="relative z-10 w-full max-w-5xl flex items-center justify-between pb-6 border-b border-[#3B3A33]/40">
        <Link href="/" className="flex items-center gap-2.5 group">
          <Image
            src="/logo-transparent.png"
            alt="NyayaSarathi Logo"
            width={28}
            height={28}
            className="w-7 h-7 object-contain drop-shadow-[0_2px_8px_rgba(181,154,104,0.3)]"
          />
          <span className="font-display text-base font-semibold text-ivory tracking-wide">NyayaSarathi</span>
        </Link>
        <Link
          href="/"
          className="font-sans text-xs text-stone/70 hover:text-ivory transition-colors flex items-center gap-1"
        >
          <span>Return to Portal</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </header>

      {/* Background Architectural Grid */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-20 bg-[radial-gradient(#3B3A33_1px,transparent_1px)] [background-size:32px_32px]"
        aria-hidden="true"
      />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE }}
        className="relative z-10 w-full max-w-lg bg-[#181C1A]/90 backdrop-blur-xl border border-[#3B3A33] rounded-2xl p-6 sm:p-10 shadow-2xl"
      >
        {/* Emblem & Editorial Kicker */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-full bg-[#1D211F] border border-[#B59A68]/40 flex items-center justify-center">
            <Scale className="w-5 h-5 text-[#B59A68]" strokeWidth={1.5} />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#B59A68]">
              MEMBER ONBOARDING &bull; STEP 02
            </div>
            <h1 className="font-display text-xl sm:text-2xl font-medium text-[#F4EFE5]">
              Complete Your Research Profile
            </h1>
          </div>
        </div>

        <p className="font-sans text-xs sm:text-sm text-[#A9A49A] mb-6 leading-relaxed">
          Welcome to NyayaSarathi. To personalize your judicial precedent queries and citation verification, please complete your professional profile.
        </p>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-5 flex items-center gap-2.5 rounded-lg border border-[#8A3545]/60 bg-[#6E2634]/15 px-4 py-3 text-xs text-[#F4EFE5]"
          >
            <AlertCircle className="w-4 h-4 text-[#8A3545] shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          {/* Avatar Photo / Gmail monogram */}
          <div className="flex items-center gap-4 p-3.5 rounded-xl border border-[#3B3A33] bg-[#1D211F]/60">
            <UserAvatar
              avatarUrl={avatarUrl}
              name={fullName || currentUser?.full_name}
              email={currentUser?.email}
              size="lg"
            />
            <div className="flex-1 min-w-0">
              <input
                type="file"
                ref={fileInputRef}
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isCompressingImage}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#6E2634] hover:bg-[#8A3545] text-xs font-semibold text-[#F4EFE5] transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {isCompressingImage ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>Processing…</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-3 h-3" />
                      <span>Take / Upload Photo</span>
                    </>
                  )}
                </button>
                {avatarUrl && (
                  <button
                    type="button"
                    onClick={() => setAvatarUrl('')}
                    className="px-2.5 py-1.5 rounded-lg border border-[#3B3A33] bg-[#151716] text-[11px] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                  >
                    Use Google Monogram
                  </button>
                )}
              </div>
              <p className="font-sans text-[11px] text-[#A9A49A]/70 mt-1">
                Optional: Upload a photo or keep your initial monogram logo.
              </p>
            </div>
          </div>

          {/* Email (Readonly) */}
          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A9A49A] mb-1.5">
              Email Address (Verified)
            </label>
            <input
              type="email"
              disabled
              value={currentUser?.email || ''}
              className="w-full rounded-xl border border-[#3B3A33]/50 bg-[#1D211F]/50 px-4 py-2.5 font-sans text-xs text-[#A9A49A] cursor-not-allowed"
            />
          </div>

          {/* Full Name */}
          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-[#F4EFE5] mb-1.5">
              Full Legal Name <span className="text-[#8A3545]">*</span>
            </label>
            <div className="relative">
              <User className="absolute left-3.5 top-3 w-4 h-4 text-[#A9A49A]" />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Adv. Rajesh Sharma"
                className="w-full rounded-xl border border-[#3B3A33] bg-[#1D211F] pl-10 pr-4 py-2.5 font-sans text-sm text-[#F4EFE5] placeholder-[#A9A49A]/40 focus:border-[#B59A68] focus:outline-none transition-colors"
              />
            </div>
          </div>

          {/* Organization / Chambers */}
          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-[#F4EFE5] mb-1.5">
              Organization / Chambers / Court <span className="text-[#8A3545]">*</span>
            </label>
            <div className="relative">
              <Building2 className="absolute left-3.5 top-3 w-4 h-4 text-[#A9A49A]" />
              <input
                type="text"
                required
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                placeholder="e.g. Chambers of Senior Advocate, Delhi High Court"
                className="w-full rounded-xl border border-[#3B3A33] bg-[#1D211F] pl-10 pr-4 py-2.5 font-sans text-sm text-[#F4EFE5] placeholder-[#A9A49A]/40 focus:border-[#B59A68] focus:outline-none transition-colors"
              />
            </div>
          </div>

          {/* Designation */}
          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-[#F4EFE5] mb-1.5">
              Professional Designation <span className="text-[#8A3545]">*</span>
            </label>
            <div className="relative">
              <Briefcase className="absolute left-3.5 top-3 w-4 h-4 text-[#A9A49A]" />
              <input
                type="text"
                required
                value={designation}
                onChange={(e) => setDesignation(e.target.value)}
                placeholder="e.g. Advocate, Judicial Clerk, Legal Researcher"
                className="w-full rounded-xl border border-[#3B3A33] bg-[#1D211F] pl-10 pr-4 py-2.5 font-sans text-sm text-[#F4EFE5] placeholder-[#A9A49A]/40 focus:border-[#B59A68] focus:outline-none transition-colors"
              />
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-[#6E2634] hover:bg-[#8A3545] text-[#F4EFE5] px-6 py-3 font-sans text-sm font-semibold tracking-wide transition-all duration-200 shadow-lg disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#F4EFE5]" />
                  <span>Saving Profile…</span>
                </>
              ) : (
                <>
                  <span>Enter Legal Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </motion.div>

      {/* Footer copyright */}
      <div className="relative z-10 text-center font-sans text-xs text-stone/50 pt-8 pb-2">
        &copy; {new Date().getFullYear()} NyayaSarathi &bull; Judicial Intelligence
      </div>
    </div>
  );
}
