'use client';

import React from 'react';
import { User } from 'lucide-react';

interface UserAvatarProps {
  avatarUrl?: string | null;
  name?: string | null;
  email?: string | null;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  showOnlineBadge?: boolean;
}

const SIZE_MAP = {
  sm: {
    container: 'w-6 h-6 text-[10px]',
    icon: 'w-3 h-3',
    badge: 'w-2 h-2 -bottom-0.5 -right-0.5',
  },
  md: {
    container: 'w-8 h-8 text-xs',
    icon: 'w-4 h-4',
    badge: 'w-2.5 h-2.5 -bottom-0.5 -right-0.5',
  },
  lg: {
    container: 'w-12 h-12 text-sm',
    icon: 'w-6 h-6',
    badge: 'w-3 h-3 -bottom-0.5 -right-0.5',
  },
  xl: {
    container: 'w-20 h-20 text-2xl font-bold',
    icon: 'w-10 h-10',
    badge: 'w-4 h-4 -bottom-1 -right-1 border-2',
  },
};

// Distinct Google/Gmail-style background palette for initials
const AVATAR_PALETTE = [
  'bg-[#8A3545] text-[#F4EFE5]', // Oxblood
  'bg-[#1A73E8] text-white',     // Google Blue
  'bg-[#0D652D] text-white',     // Google Green
  'bg-[#C26401] text-white',     // Google Ochre / Gold
  'bg-[#681DA8] text-white',     // Google Purple
  'bg-[#8E24AA] text-white',     // Magenta
  'bg-[#007B83] text-white',     // Teal
  'bg-[#B59A68] text-[#151716]', // NyayaSarathi Gold
];

function getAvatarColor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % AVATAR_PALETTE.length;
  return AVATAR_PALETTE[index];
}

function getInitials(name?: string | null, email?: string | null): string {
  if (name && name.trim()) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  }
  if (email && email.trim()) {
    return email.trim().charAt(0).toUpperCase();
  }
  return 'U';
}

export function UserAvatar({
  avatarUrl,
  name,
  email,
  size = 'md',
  className = '',
  showOnlineBadge = false,
}: UserAvatarProps) {
  const { container, icon, badge } = SIZE_MAP[size];
  const initials = getInitials(name, email);
  const colorClass = getAvatarColor(name || email || 'user');
  const [imageError, setImageError] = React.useState(false);

  // Reset error when avatarUrl changes
  React.useEffect(() => {
    setImageError(false);
  }, [avatarUrl]);

  const hasValidImage = Boolean(avatarUrl && avatarUrl.trim() && !imageError);

  return (
    <div className={`relative inline-flex items-center justify-center shrink-0 ${className}`}>
      <div
        className={`rounded-2xl border border-[#3B3A33] overflow-hidden flex items-center justify-center select-none shadow-md ${container} ${
          hasValidImage ? 'bg-[#1D211F]' : colorClass
        }`}
      >
        {hasValidImage ? (
          <img
            src={avatarUrl!}
            alt={name || 'User Avatar'}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <span className="font-display font-medium tracking-wide">
            {initials}
          </span>
        )}
      </div>

      {showOnlineBadge && (
        <span
          className={`absolute rounded-full bg-[#34A853] border border-[#151716] ${badge}`}
          aria-hidden="true"
        />
      )}
    </div>
  );
}

export default UserAvatar;
