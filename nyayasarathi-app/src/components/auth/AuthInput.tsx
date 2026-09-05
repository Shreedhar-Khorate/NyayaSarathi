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
      <div className="w-full space-y-2">
        <div className="flex items-center justify-between">
          <label
            htmlFor={id}
            className="block font-sans text-xs font-semibold uppercase tracking-[0.14em] text-[#A9A49A]"
          >
            {label}
          </label>
          {helperText && !error && (
            <span className="font-sans text-xs text-[#A9A49A]/60">{helperText}</span>
          )}
        </div>

        <div className="relative flex items-center">
          <input
            ref={ref}
            id={id}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${id}-error` : undefined}
            className={`w-full rounded-xl bg-[#1D211F] border px-4 py-3 font-sans text-[15px] sm:text-sm text-[#F4EFE5] placeholder:text-[#A9A49A]/60 transition-all duration-200 outline-none min-h-[46px] ${
              error
                ? 'border-[#8A3545] focus:border-[#8A3545] focus:ring-1 focus:ring-[#8A3545]'
                : 'border-[#3B3A33] hover:border-[#3B3A33]/80 focus:border-[#6E2634] focus:ring-1 focus:ring-[#6E2634]'
            } ${rightElement ? 'pr-11' : ''} ${className}`}
            {...props}
          />

          {rightElement && (
            <div className="absolute right-3.5 flex items-center justify-center">
              {rightElement}
            </div>
          )}
        </div>

        {error && (
          <p
            id={`${id}-error`}
            role="alert"
            className="font-sans text-xs font-medium text-[#8A3545] mt-1 flex items-center gap-1.5"
          >
            <span className="w-1 h-1 rounded-full bg-[#8A3545] inline-block" />
            {error}
          </p>
        )}
      </div>
    );
  }
);

AuthInput.displayName = 'AuthInput';

export default AuthInput;
