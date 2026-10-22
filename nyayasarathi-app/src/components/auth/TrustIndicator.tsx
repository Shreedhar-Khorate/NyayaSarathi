'use client';

import React from 'react';

interface TrustIndicatorProps {
  text?: string;
  className?: string;
}

export function TrustIndicator({
  text = 'Secure constitutional intelligence workspace',
  className = '',
}: TrustIndicatorProps) {
  return (
    <div
      className={`inline-flex items-center gap-2.5 font-mono text-xs tracking-wider text-[#A9A49A]/80 select-none ${className}`}
    >
      <span
        className="w-2 h-2 rounded-full bg-[#71877A] inline-block shadow-[0_0_8px_rgba(113,135,122,0.8)]"
        aria-hidden="true"
      />
      <span>{text}</span>
    </div>
  );
}

export default TrustIndicator;
