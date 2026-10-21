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

// ── Admin Dashboard & User Management APIs ────────────────────────────────────

export interface RoleAuditItem {
  id: string;
  target_user_id: string;
  actor_user_id: string;
  old_role: string;
  new_role: string;
  reason?: string | null;
  created_at: string;
  target_name?: string | null;
  target_email?: string | null;
  actor_name?: string | null;
  actor_email?: string | null;
}

export interface RoleAuditListResponse {
  total: number;
  items: RoleAuditItem[];
  limit: number;
  offset: number;
}

export interface AdminMetrics {
  total_users: number;
  role_counts: Record<string, number>;
  recent_users: Array<{
    id: string;
    email: string;
    full_name: string;
    role: string;
    avatar_url?: string | null;
    organization?: string | null;
    designation?: string | null;
    created_at: string;
  }>;
  recent_role_changes: RoleAuditItem[];
  total_activities: number;
  total_judgments: number;
}

export interface AdminUserItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  avatar_url?: string | null;
  organization?: string | null;
  designation?: string | null;
  profile_completed: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface AdminUserListResponse {
  total: number;
  items: AdminUserItem[];
  limit: number;
  offset: number;
}

export interface RoleUpdateResponse {
  success: boolean;
  audit_id: string;
  target_user_id: string;
  old_role: string;
  new_role: string;
  reason?: string | null;
  updated_at: string;
}

export async function fetchAdminMetrics(): Promise<AdminMetrics> {
  const res = await fetch(`${API_BASE_URL}/api/admin/dashboard`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load administrator metrics.');
  }
  return data;
}

export async function fetchAdminUsers(
  search?: string,
  role?: string,
  limit: number = 50,
  offset: number = 0
): Promise<AdminUserListResponse> {
  const params = new URLSearchParams();
  if (search && search.trim()) params.append('search', search.trim());
  if (role && role !== 'ALL') params.append('role', role);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const res = await fetch(`${API_BASE_URL}/api/admin/users?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load user list.');
  }
  return data;
}

export async function updateUserRole(
  userId: string,
  newRole: string,
  reason?: string
): Promise<RoleUpdateResponse> {
  const res = await fetch(`${API_BASE_URL}/api/admin/users/${userId}/role`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      new_role: newRole,
      reason: reason?.trim() || undefined,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to update user role.');
  }
  return data;
}

export async function fetchRoleAuditHistory(
  targetUserId?: string,
  limit: number = 50,
  offset: number = 0
): Promise<RoleAuditListResponse> {
  const params = new URLSearchParams();
  if (targetUserId) params.append('target_user_id', targetUserId);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const res = await fetch(`${API_BASE_URL}/api/admin/role-history?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load role audit logs.');
  }
  return data;
}

// ── Judge Dashboard, Case Docket & Precedents APIs ──────────────────────────

export interface JudgeMetrics {
  accessible_precedents: number;
  assigned_matters_count: number;
  active_matters_count?: number;
  recent_research_activities: number;
  court_jurisdiction: string;
  judge_name: string;
  bench_designation: string;
}

export interface JudgeActivityItem {
  id: string;
  activity_type: string;
  title: string;
  query_text?: string | null;
  resource_id?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface JudgeActivityListResponse {
  total: number;
  items: JudgeActivityItem[];
  limit: number;
  offset: number;
}

export interface JudgeAssignedCaseItem {
  id: string;
  case_number: string;
  title: string;
  court_name: string;
  case_type: string;
  judge_id: string;
  assigned_by_id?: string | null;
  status: string;
  priority: string;
  filing_date?: string | null;
  hearing_date?: string | null;
  petitioner?: string | null;
  respondent?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JudgeCaseListResponse {
  total: number;
  items: JudgeAssignedCaseItem[];
  limit: number;
  offset: number;
  notice?: string | null;
}

export interface PrecedentItem {
  cnr: string;
  title: string;
  court?: string | null;
  year?: number | null;
  decision_date?: string | null;
  disposal_nature?: string | null;
  judge?: string | null;
  case_type?: string | null;
  petitioner?: string | null;
  respondent?: string | null;
}

export interface PrecedentListResponse {
  total: number;
  items: PrecedentItem[];
  limit: number;
  offset: number;
  notice?: string | null;
}

export async function fetchJudgeMetrics(): Promise<JudgeMetrics> {
  const res = await fetch(`${API_BASE_URL}/api/judge/dashboard`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load judicial dashboard metrics.');
  }
  return data;
}

export async function fetchJudgeActivities(
  activityType?: string,
  limit: number = 50,
  offset: number = 0
): Promise<JudgeActivityListResponse> {
  const params = new URLSearchParams();
  if (activityType && activityType !== 'ALL') params.append('activity_type', activityType);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const res = await fetch(`${API_BASE_URL}/api/judge/activity?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load judicial activities.');
  }
  return data;
}

export async function fetchJudgeCases(
  status?: string,
  priority?: string,
  limit: number = 50,
  offset: number = 0
): Promise<JudgeCaseListResponse> {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  if (priority && priority !== 'ALL') params.append('priority', priority);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const res = await fetch(`${API_BASE_URL}/api/judge/cases?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load assigned bench matters.');
  }
  return data;
}

export async function updateJudgeCaseStatus(
  caseId: string,
  status: string,
  notes?: string,
  hearingDate?: string
): Promise<JudgeAssignedCaseItem> {
  const res = await fetch(`${API_BASE_URL}/api/judge/cases/${caseId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      status,
      notes: notes?.trim() || undefined,
      hearing_date: hearingDate || undefined,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to update case assignment.');
  }
  return data;
}

export async function fetchJudgePrecedents(
  search?: string,
  year?: number,
  limit: number = 50,
  offset: number = 0
): Promise<PrecedentListResponse> {
  const params = new URLSearchParams();
  if (search && search.trim()) params.append('search', search.trim());
  if (year) params.append('year', year.toString());
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const res = await fetch(`${API_BASE_URL}/api/judge/precedents?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load legal precedents.');
  }
  return data;
}

export async function assignCase(data: {
  case_number: string;
  title: string;
  court_name: string;
  judge_id: string;
  case_type?: string;
  priority?: string;
  filing_date?: string;
  hearing_date?: string;
  petitioner?: string;
  respondent?: string;
  notes?: string;
}): Promise<JudgeAssignedCaseItem> {
  const res = await fetch(`${API_BASE_URL}/api/admin/cases/assign`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  const resData = await res.json();
  if (!res.ok) {
    throw new Error(resData.detail || resData.error || 'Failed to assign case.');
  }
  return resData;
}


// ── Advocate Portal Types & Helpers ──────────────────────────────────────────

export interface AdvocateMetrics {
  advocate_name: string;
  organization: string;
  designation: string;
  total_activities: number;
  legal_research_count: number;
  drafts_created: number;
  documents_analysed: number;
  predictions_run: number;
}

export interface AdvocateActivityItem {
  id: string;
  activity_type: string;
  title: string;
  query_text?: string | null;
  resource_id?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface AdvocateActivityList {
  total: number;
  items: AdvocateActivityItem[];
  limit: number;
  offset: number;
}

export interface EligibleUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization?: string | null;
  designation?: string | null;
  created_at: string;
}

export interface EligibleUserList {
  total: number;
  items: EligibleUser[];
  limit: number;
  offset: number;
}

/** Fetch advocate dashboard KPI metrics (ADVOCATE or ADMIN role required). */
export async function fetchAdvocateMetrics(): Promise<AdvocateMetrics> {
  const res = await fetch(`${API_BASE_URL}/api/advocate/dashboard`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load advocate metrics.');
  }
  return data;
}

/** Fetch paginated advocate activity log scoped to the current user. */
export async function fetchAdvocateActivity(
  activityType?: string,
  limit = 20,
  offset = 0,
): Promise<AdvocateActivityList> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (activityType) params.append('activity_type', activityType);
  const res = await fetch(`${API_BASE_URL}/api/advocate/activity?${params}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load advocate activity.');
  }
  return data;
}

/** Fetch USER/ADVOCATE accounts eligible for judicial promotion (JUDGE role required). */
export async function fetchEligibleForJudgeship(
  search?: string,
  limit = 20,
  offset = 0,
): Promise<EligibleUserList> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (search) params.append('search', search);
  const res = await fetch(`${API_BASE_URL}/api/advocate/eligible-for-judgeship?${params}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to load eligible candidates.');
  }
  return data;
}

/** Judge-only: Promote a USER or ADVOCATE to the JUDGE role with a nomination reason. */
export async function judgePromoteToJudge(
  targetUserId: string,
  reason?: string,
): Promise<{ success: boolean; audit_id: string; new_role: string; updated_at: string }> {
  const res = await fetch(`${API_BASE_URL}/api/advocate/promote-to-judge`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ target_user_id: targetUserId, reason }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Promotion failed.');
  }
  return data;
}

// ── Contract Red-Flag Analysis API Client ───────────────────────────────────

export interface ContractRedFlag {
  finding_id?: string;
  risk_level: 'high' | 'medium' | 'low';
  risk_category?: string;
  risk_classification?: 'potential_commercial_risk' | 'possible_legal_concern' | 'legal_conclusion_requiring_review' | string;
  title?: string;
  verbatim_clause?: string;
  clause_text: string;
  source_page?: number | null;
  page_ref?: number | null;
  clause_location?: string | null;
  applicable_law?: string | null;
  statutory_provision?: string | null;
  statutory_verification_status?: 'verified' | 'unverified' | 'not_applicable' | string;
  legal_explanation?: string | null;
  explanation: string;
  application_to_clause?: string | null;
  uncertainty_or_limitation?: string | null;
  recommended_action?: string | null;
  recommendation?: string | null;
  evidence_confidence?: number | null;
  confidence?: number | null;
}

export interface ScoreContributingFinding {
  finding_id?: string;
  title?: string;
  risk_level: string;
  points: number;
  risk_classification?: string;
  statutory_provision?: string;
}

export interface ScoreBreakdown {
  numerical_score: number;
  scoring_method: string;
  high_count: number;
  medium_count: number;
  low_count: number;
  contributing_findings: ScoreContributingFinding[];
  risk_rationale: string;
  scoring_limitations?: string | null;
}

export interface ContractRiskCounts {
  high: number;
  medium: number;
  low: number;
  total: number;
}

export interface ContractAnalysisResult {
  filename?: string;
  overall_risk_score: 'High' | 'Medium' | 'Low' | 'Not Assessed' | string;
  summary?: string;
  red_flags: ContractRedFlag[];
  risk_counts?: ContractRiskCounts;
  score_breakdown?: ScoreBreakdown;
  limitations?: string[];
  extraction_method?: string;
  total_pages?: number;
  document_type?: string;
  document_type_label?: string;
  audit_status?: 'COMPLETED' | 'DOCUMENT_TYPE_MISMATCH' | 'INSUFFICIENT_CONTENT' | 'PARTIAL_ANALYSIS' | 'FAILED' | string;
  classification_confidence?: number | null;
  classification_reason?: string | null;
  recommended_action?: string | null;
}

/** Upload a contract file (PDF, DOCX, TXT) and receive structured red-flag risk analysis. */
export async function analyzeContract(file: File): Promise<ContractAnalysisResult> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/api/contracts/analyze`, {
    method: 'POST',
    headers, // Browser automatically sets Content-Type with multipart boundary
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    if (res.status === 401) {
      removeAuth();
    }
    throw new Error(data.error || data.detail || 'Contract analysis failed.');
  }
  return data;
}

// ── Indian Legal News API Client ─────────────────────────────────────────────

export interface NewsArticle {
  title: string;
  description?: string | null;
  url: string;
  source_name: string;
  published_at?: string | null;
  image_url?: string | null;
  category: string;
  story_id?: string | null;
}

export interface NewsStoryGroup {
  story_id: string;
  title: string;
  category: string;
  primary_article: NewsArticle;
  related_articles: NewsArticle[];
  coverage_count: number;
  key_entities: string[];
  last_updated?: string | null;
}

export interface OfficialSource {
  name: string;
  url: string;
  description: string;
}

export interface NewsResponse {
  category: string;
  total: number;
  articles: NewsArticle[];
  stories?: NewsStoryGroup[];
  official_sources: OfficialSource[];
  disclaimer: string;
  cached: boolean;
  fetched_at?: string | null;
}

/**
 * Fetch Indian legal news and official court sources.
 * @param category - 'all' | 'supreme-court' | 'high-courts' | 'legal' | 'government'
 * @param limit - 1 to 20
 */
export async function fetchLegalNews(
  category: string = 'all',
  limit: number = 10
): Promise<NewsResponse> {
  const params = new URLSearchParams({
    category: category.toLowerCase().trim(),
    limit: String(limit),
  });

  const res = await fetch(`${API_BASE_URL}/api/news?${params.toString()}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to fetch legal news.');
  }
  return data;
}

/**
 * Fetch available news categories from backend.
 */
export async function fetchNewsCategories(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/news/categories`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) return ['all', 'supreme-court', 'high-courts', 'legal', 'government'];
    const data = await res.json();
    return data.categories || ['all', 'supreme-court', 'high-courts', 'legal', 'government'];
  } catch {
    return ['all', 'supreme-court', 'high-courts', 'legal', 'government'];
  }
}

