/**
 * Application Configuration & API Base URL
 *
 * Dynamically determines the appropriate API Base URL:
 * 1. Explicit NEXT_PUBLIC_API_URL environment variable if set.
 *    - In browser runtime: If the current host is a production domain (e.g. nyayasarathi.vercel.app)
 *      and the configured URL erroneously points to localhost/127.0.0.1, it automatically upgrades
 *      to the deployed Render backend (https://nyayasarathi.onrender.com).
 * 2. In browser runtime on non-localhost domains (e.g. Vercel), default directly to
 *    'https://nyayasarathi.onrender.com'.
 * 3. In production builds (VERCEL or NODE_ENV=production), default to
 *    'https://nyayasarathi.onrender.com'.
 * 4. In local development, fallback to 'http://127.0.0.1:8000'.
 */
export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  // 1. Browser runtime check
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const isLocal =
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '0.0.0.0' ||
      hostname.endsWith('.local');

    if (!isLocal) {
      // In production browser: override missing or accidental localhost settings
      if (!envUrl || envUrl.includes('localhost') || envUrl.includes('127.0.0.1')) {
        return 'https://nyayasarathi.onrender.com';
      }
      return envUrl.replace(/\/+$/, '');
    }
  }

  // 2. Build-time / Server-side check
  if (process.env.VERCEL || process.env.NODE_ENV === 'production') {
    if (!envUrl || envUrl.includes('localhost') || envUrl.includes('127.0.0.1')) {
      return 'https://nyayasarathi.onrender.com';
    }
    return envUrl.replace(/\/+$/, '');
  }

  // 3. Local development fallback
  return envUrl || 'http://127.0.0.1:8000';
}

export const API_BASE_URL = getApiBaseUrl();
