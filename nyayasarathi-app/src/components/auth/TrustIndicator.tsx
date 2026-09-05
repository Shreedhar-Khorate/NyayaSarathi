'use client';

import React from 'react';

interface TrustIndicatorProps {
  text?: string;
  className?: string;
}

export function TrustIndicator({
  text = 'Secure research workspace',
  className = '',
}: TrustIndicatorProps) {
  return (
    <div
      className={`inline-flex items-center gap-2 font-mono text-[11px] tracking-wider text-[#A9A49A]/80 select-none ${className}`}
    >
      <span
        className="w-1.5 h-1.5 rounded-full bg-[#71877A] inline-block shadow-[0_0_6px_rgba(113,135,122,0.6)]"
        aria-hidden="true"
      />
      <span>{text}</span>
    </div>
  );
}

export default TrustIndicator;
