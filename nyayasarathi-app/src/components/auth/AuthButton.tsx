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
      className={`group relative w-full rounded-xl px-6 py-3.5 font-sans text-sm font-semibold tracking-wide flex items-center justify-center gap-2.5 transition-all duration-200 outline-none select-none min-h-[48px] ${
        isPrimary
          ? 'bg-[#6E2634] text-[#F4EFE5] hover:bg-[#8A3545] active:bg-[#5D1F2B] focus-visible:ring-2 focus-visible:ring-[#B59A68] focus-visible:ring-offset-2 focus-visible:ring-offset-[#151716] disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_1px_3px_rgba(0,0,0,0.3)]'
          : 'bg-[#1D211F] text-[#F4EFE5] border border-[#3B3A33] hover:bg-[#242925] hover:border-[#3B3A33]/90 focus-visible:ring-2 focus-visible:ring-[#6E2634] disabled:opacity-50 disabled:cursor-not-allowed'
      } ${className}`}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin text-[#F4EFE5]" />
          <span>Processing...</span>
        </>
      ) : (
        <>
          <span>{children}</span>
          {showArrow && (
            <ArrowRight
              className="w-4 h-4 transition-transform duration-200 ease-out group-hover:translate-x-1"
              strokeWidth={2}
            />
          )}
        </>
      )}
    </motion.button>
  );
}

export default AuthButton;
