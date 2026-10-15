/**
 * NyayaSarathi Frontend Authentication & Profile Client Helper
 * Handles JWT token storage, login/signup API calls, profile fetching/editing,
 * profile completion onboarding, activity history, and request header generation.
 */

import { API_BASE_URL } from './config';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  avatar_url?: string | null;
  organization?: string | null;
  designation?: string | null;
  profile_completed?: boolean;
  created_at: string;
  updated_at?: string;
}

export interface ActivityHistoryItem {
  id: string;
  user_id: string;
  activity_type: string;
  title: string;
  query_text?: string | null;
  resource_id?: string | null;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

const TOKEN_KEY = 'nyayasarathi_jwt_token';
const USER_KEY = 'nyayasarathi_user_profile';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getUser(): UserProfile | null {
  if (typeof window === 'undefined') return null;
  const userJson = localStorage.getItem(USER_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson);
  } catch {
    return null;
  }
}

export function setUser(user: UserProfile): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Authentication failed.');
  }

  setToken(data.access_token);
  setUser(data.user);
  return data;
}

export async function signupUser(
  email: string,
  password: string,
  full_name: string,
  role: string = 'USER'
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, full_name, role }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Registration failed.');
  }

  setToken(data.access_token);
  setUser(data.user);
  return data;
}

export async function fetchMe(): Promise<UserProfile | null> {
  const token = getToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_BASE_URL}/api/profile/me`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      removeAuth();
      return null;
    }

    const user: UserProfile = await res.json();
    setUser(user);
    return user;
  } catch {
    return null;
  }
}

export async function updateProfile(fields: {
  full_name?: string;
  organization?: string;
  designation?: string;
  avatar_url?: string | null;
}): Promise<UserProfile> {
  const res = await fetch(`${API_BASE_URL}/api/profile/me`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(fields),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to update profile.');
  }

  setUser(data);
  return data;
}

export async function completeProfileOnboarding(fields: {
  full_name: string;
  organization: string;
  designation: string;
  avatar_url?: string | null;
}): Promise<UserProfile> {
  const res = await fetch(`${API_BASE_URL}/api/profile/complete`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(fields),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to complete profile onboarding.');
  }

  setUser(data);
  return data;
}

export async function fetchUserHistory(
  activityType?: string,
  limit: number = 50,
  offset: number = 0
): Promise<ActivityHistoryItem[]> {
  const params = new URLSearchParams();
  if (activityType) params.append('activity_type', activityType);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const res = await fetch(`${API_BASE_URL}/api/history?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    throw new Error('Failed to load user history.');
  }

  const data = await res.json();
  return data.items || [];
}

export async function deleteUserActivity(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE_URL}/api/history/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return res.ok;
}
