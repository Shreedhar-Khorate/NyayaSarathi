/**
 * NyayaSarathi Chat API Client
 * All API calls go through FastAPI (never direct Supabase).
 * Bearer token is injected from localStorage (same as the rest of the app).
 */

import { API_BASE_URL } from './config';
import { getAuthHeaders } from './auth';

// ── Types ────────────────────────────────────────────────────────────────────

export interface ChatConversation {
  id: string;
  user_id: string;
  advocate_id: string;
  status: 'active' | 'closed' | 'archived';
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
  last_message_body?: string | null;
  last_message_sender_id?: string | null;
  unread_count?: number;
  other_party_name?: string | null;
  other_party_avatar?: string | null;
  other_party_designation?: string | null;
  other_party_role?: string | null;
}

export interface AdvocateProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  avatar_url?: string | null;
  organization?: string | null;
  designation?: string | null;
}

export interface AdvocateListResponse {
  advocates: AdvocateProfile[];
  total: number;
}

export interface ChatAttachmentMeta {
  id: string;
  message_id: string;
  conversation_id: string;
  uploaded_by: string;
  original_filename: string;
  content_type: string | null;
  size_bytes: number;
  created_at: string;
  // storage_key is intentionally omitted — server never sends it
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  body: string | null;
  idempotency_key?: string | null;
  created_at: string;
  attachments?: ChatAttachmentMeta[];
  status?: 'sending' | 'sent' | 'failed';
}

export interface MessagePage {
  messages: ChatMessage[];
  next_cursor: { before_created_at: string; before_id: string } | null;
  has_more: boolean;
}

export interface ConversationListResponse {
  conversations: ChatConversation[];
  total: number;
}

// ── Helper ────────────────────────────────────────────────────────────────────

async function chatFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}/api/chat${path}`, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? body?.error ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

// ── Conversation API ──────────────────────────────────────────────────────────

export async function fetchAdvocates(): Promise<AdvocateListResponse> {
  return chatFetch<AdvocateListResponse>('/advocates');
}

export async function fetchConversations(): Promise<ConversationListResponse> {
  return chatFetch<ConversationListResponse>('/conversations');
}

export async function createOrGetConversation(
  user_id: string,
  advocate_id: string
): Promise<ChatConversation> {
  return chatFetch<ChatConversation>('/conversations', {
    method: 'POST',
    body: JSON.stringify({ user_id, advocate_id }),
  });
}

export async function fetchConversation(conversationId: string): Promise<ChatConversation & { unread_count: number }> {
  return chatFetch(`/conversations/${conversationId}`);
}

// ── Message API ───────────────────────────────────────────────────────────────

export async function fetchMessages(
  conversationId: string,
  cursor?: { before_created_at: string; before_id: string }
): Promise<MessagePage> {
  const params = new URLSearchParams({ limit: '30' });
  if (cursor?.before_created_at) params.set('before_created_at', cursor.before_created_at);
  if (cursor?.before_id) params.set('before_id', cursor.before_id);
  return chatFetch<MessagePage>(`/conversations/${conversationId}/messages?${params}`);
}

export async function sendMessage(
  conversationId: string,
  body: string,
  idempotencyKey?: string
): Promise<ChatMessage> {
  return chatFetch<ChatMessage>(`/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({
      body,
      idempotency_key: idempotencyKey ?? null,
    }),
  });
}

// ── Read state API ────────────────────────────────────────────────────────────

export async function markConversationRead(
  conversationId: string,
  lastReadMessageId: string
): Promise<void> {
  await chatFetch(`/conversations/${conversationId}/read`, {
    method: 'POST',
    body: JSON.stringify({ last_read_message_id: lastReadMessageId }),
  });
}

// ── Attachment API ────────────────────────────────────────────────────────────

export async function uploadAttachment(
  conversationId: string,
  file: File
): Promise<ChatMessage & { attachment: ChatAttachmentMeta }> {
  const formData = new FormData();
  formData.append('file', file);

  // For file uploads, don't set Content-Type — let fetch set multipart boundary
  const headers = getAuthHeaders();
  delete (headers as Record<string, string>)['Content-Type'];

  const res = await fetch(
    `${API_BASE_URL}/api/chat/conversations/${conversationId}/attachments`,
    {
      method: 'POST',
      headers,
      body: formData,
    }
  );
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? body?.error ?? detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

export function getAttachmentDownloadUrl(attachmentId: string): string {
  // The server performs auth + redirect to signed URL
  return `${API_BASE_URL}/api/chat/attachments/${attachmentId}`;
}

// ── Chat health (mode info) ───────────────────────────────────────────────────

export interface ChatHealthResponse {
  chat_db_mode: 'postgresql' | 'sqlite';
  realtime_available: boolean;
  realtime_note: string;
}

export async function fetchChatHealth(): Promise<ChatHealthResponse> {
  return chatFetch<ChatHealthResponse>('/health');
}

// ── Realtime polling fallback (SQLite mode) ───────────────────────────────────
/**
 * In SQLite mode Supabase Realtime is not available.
 * Use this helper to poll for new messages at a conservative interval
 * when the chat view is active.
 */
export function createChatPoller(
  conversationId: string,
  getLatestMessageId: () => string | null,
  onNewMessages: (msgs: ChatMessage[]) => void,
  intervalMs = 2500
): { start: () => void; stop: () => void } {
  let timerId: ReturnType<typeof setInterval> | null = null;
  let running = false;

  const poll = async () => {
    if (!running) return;
    try {
      const page = await fetchMessages(conversationId);
      if (page.messages.length > 0) {
        onNewMessages(page.messages);
      }
    } catch {
      /* polling errors are non-fatal */
    }
  };

  return {
    start: () => {
      running = true;
      timerId = setInterval(poll, intervalMs);
    },
    stop: () => {
      running = false;
      if (timerId) clearInterval(timerId);
    },
  };
}
