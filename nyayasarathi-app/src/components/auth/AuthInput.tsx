'use client';

import React, { forwardRef, InputHTMLAttributes } from 'react';

export interface AuthInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  id: string;
  error?: string;
  helperText?: string;
  rightElement?: React.ReactNode;
}

export const AuthInput = forwardRef<HTMLInputElement, AuthInputProps>(
  ({ label, id, error, helperText, rightElement, className = '', ...props }, ref) => {
    return (
      <div className="w-full space-y-2.5">
        <div className="flex items-center justify-between">
          <label
            htmlFor={id}
            className="block font-sans text-[13px] sm:text-sm font-semibold uppercase tracking-[0.14em] text-[#E4D2AA]/90"
          >
            {label}
          </label>
          {helperText && !error && (
            <span className="font-sans text-xs text-[#A9A49A]/80">{helperText}</span>
          )}
        </div>

        <div className="relative flex items-center">
          <input
            ref={ref}
            id={id}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${id}-error` : undefined}
            className={`w-full rounded-xl bg-[#1D211F] border px-4 sm:px-5 py-3.5 sm:py-4 font-sans text-base text-[#F4EFE5] placeholder:text-[#A9A49A]/75 placeholder:text-[15px] sm:placeholder:text-base transition-all duration-200 outline-none min-h-[52px] sm:min-h-[56px] ${
              error
                ? 'border-[#8A3545] focus:border-[#8A3545] focus:ring-1 focus:ring-[#8A3545]'
                : 'border-[#3B3A33] hover:border-[#3B3A33]/90 focus:border-[#6E2634] focus:ring-1 focus:ring-[#6E2634]'
            } ${rightElement ? 'pr-12 sm:pr-14' : ''} ${className}`}
            {...props}
          />

          {rightElement && (
            <div className="absolute right-3.5 sm:right-4 flex items-center justify-center">
              {rightElement}
            </div>
          )}
        </div>

        {error && (
          <p
            id={`${id}-error`}
            role="alert"
            className="font-sans text-xs sm:text-[13px] font-medium text-[#DC3854] mt-1.5 flex items-center gap-1.5"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#DC3854] inline-block shrink-0" />
            {error}
          </p>
        )}
      </div>
    );
  }
);

AuthInput.displayName = 'AuthInput';

export default AuthInput;
