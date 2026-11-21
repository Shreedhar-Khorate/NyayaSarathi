/**
 * Application Configuration & API Base URL
 *
 * Dynamically determines the appropriate API Base URL:
 * 1. NEXT_PUBLIC_API_URL environment variable if set (configured in .env.local or Vercel dashboard).
 * 2. In local development or fallback, defaults to 'http://127.0.0.1:8000'.
 */
export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (envUrl) {
    return envUrl.replace(/\/+$/, '');
  }

  // Fallback to local development API
  return 'http://127.0.0.1:8000';
}

export const API_BASE_URL = getApiBaseUrl();
