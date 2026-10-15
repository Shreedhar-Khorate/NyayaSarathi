/**
 * useGoogleAuth — React hook that reads Google OAuth callback params from the URL
 * and stores the JWT token + user profile in localStorage.
 *
 * After Google OAuth completes, the backend redirects to:
 *   /login?google_token=<jwt>&google_user_email=...&google_user_name=...&google_user_role=...&google_user_id=...
 *
 * This hook:
 * 1. Reads those params on mount.
 * 2. Stores them via auth helpers (setToken, setUser).
 * 3. Returns { handled, error } so the form can redirect.
 */

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { setToken, setUser, type UserProfile } from '@/lib/auth';

export interface GoogleAuthResult {
  handled: boolean;
  error: string | null;
  user: UserProfile | null;
}

export function useGoogleAuth(): GoogleAuthResult {
  const searchParams = useSearchParams();
  const [result, setResult] = useState<GoogleAuthResult>({
    handled: false,
    error: null,
    user: null,
  });

  useEffect(() => {
    const googleToken = searchParams.get('google_token');
    const googleError = searchParams.get('error');

    if (googleError) {
      const errorMessages: Record<string, string> = {
        google_auth_cancelled: 'Google sign-in was cancelled.',
        missing_code: 'Google sign-in did not return a code.',
        token_exchange_failed: 'Failed to connect with Google. Please try again.',
        profile_fetch_failed: 'Could not retrieve your Google profile.',
        no_email: 'Your Google account did not provide an email address.',
      };
      setResult({
        handled: false,
        error: errorMessages[googleError] || 'Google sign-in failed.',
        user: null,
      });
      // Clean URL params
      window.history.replaceState({}, document.title, window.location.pathname);
      return;
    }

    if (!googleToken) return;

    // Parse user info from URL params
    const email = decodeURIComponent(searchParams.get('google_user_email') || '');
    const full_name = decodeURIComponent(searchParams.get('google_user_name') || '');
    const role = searchParams.get('google_user_role') || 'USER';
    const id = searchParams.get('google_user_id') || '';
    const completedParam = searchParams.get('google_profile_completed');
    const profile_completed = completedParam === 'true';

    const userProfile: UserProfile = {
      id,
      email,
      full_name,
      role,
      profile_completed,
      created_at: new Date().toISOString(),
    };

    // Store credentials in localStorage
    setToken(googleToken);
    setUser(userProfile);

    // Clean up URL so token isn't visible
    window.history.replaceState({}, document.title, window.location.pathname);

    setResult({ handled: true, error: null, user: userProfile });
  }, [searchParams]);

  return result;
}
