'use client';

import React from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { ArrowRight, Loader2 } from 'lucide-react';

export interface AuthButtonProps extends HTMLMotionProps<'button'> {
  children: React.ReactNode;
  isLoading?: boolean;
  showArrow?: boolean;
  variant?: 'primary' | 'secondary';
}

export function AuthButton({
  children,
  isLoading = false,
  showArrow = true,
  variant = 'primary',
  disabled,
  className = '',
  ...props
}: AuthButtonProps) {
  const isPrimary = variant === 'primary';

  return (
    <motion.button
      whileHover={
        !disabled && !isLoading
          ? {
              y: -2,
              filter: 'brightness(1.05)',
              transition: { duration: 0.2, ease: 'easeOut' },
            }
          : undefined
      }
      whileTap={
        !disabled && !isLoading
          ? {
              y: 0,
              scale: 0.99,
              transition: { duration: 0.1 },
            }
          : undefined
      }
      disabled={disabled || isLoading}
      className={`group relative w-full rounded-xl px-5 py-2.5 sm:py-3 font-sans text-sm sm:text-base font-semibold tracking-wide flex items-center justify-center gap-2.5 sm:gap-3 transition-all duration-200 outline-none select-none min-h-[46px] sm:min-h-[50px] ${
        isPrimary
          ? 'bg-[#6E2634] text-[#F4EFE5] hover:bg-[#8A3545] active:bg-[#5D1F2B] focus-visible:ring-2 focus-visible:ring-[#B59A68] focus-visible:ring-offset-2 focus-visible:ring-offset-[#151716] disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_4px_16px_rgba(110,38,52,0.35)]'
          : 'bg-[#1D211F] text-[#F4EFE5] border border-[#3B3A33] hover:bg-[#242925] hover:border-[#B59A68]/40 focus-visible:ring-2 focus-visible:ring-[#B59A68] disabled:opacity-50 disabled:cursor-not-allowed'
      } ${className}`}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin text-[#F4EFE5]" />
          <span>Processing...</span>
        </>
      ) : (
        <>
          <span>{children}</span>
          {showArrow && (
            <ArrowRight
              className="w-5 h-5 transition-transform duration-200 ease-out group-hover:translate-x-1"
              strokeWidth={2}
            />
          )}
        </>
      )}
    </motion.button>
  );
}

export default AuthButton;
