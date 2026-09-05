'use client';

import React, { useState, forwardRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { AuthInput, AuthInputProps } from './AuthInput';

export interface PasswordInputProps extends Omit<AuthInputProps, 'type' | 'rightElement'> {
  showToggle?: boolean;
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ showToggle = true, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);

    return (
      <AuthInput
        ref={ref}
        type={showPassword ? 'text' : 'password'}
        rightElement={
          showToggle ? (
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="text-[#A9A49A] hover:text-[#F4EFE5] p-1.5 rounded-md transition-colors focus:outline-none focus:ring-1 focus:ring-[#6E2634]"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              tabIndex={0}
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" strokeWidth={1.75} />
              ) : (
                <Eye className="w-4 h-4" strokeWidth={1.75} />
              )}
            </button>
          ) : undefined
        }
        {...props}
      />
    );
  }
);

PasswordInput.displayName = 'PasswordInput';

export default PasswordInput;
