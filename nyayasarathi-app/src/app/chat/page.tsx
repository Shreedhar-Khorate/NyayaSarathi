'use client';

/**
 * NyayaSarathi — High-Performance Real-Time Chat Workspace
 * Private, verified, and end-to-end encrypted User–Advocate messaging.
 * Route: /chat and /messages (accessible by USER, ADVOCATE, and ADMIN).
 */

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  useMemo,
  Suspense,
} from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageCircle,
  Send,
  Paperclip,
  Download,
  AlertCircle,
  RefreshCw,
  X,
  CheckCheck,
  Check,
  Copy,
  Clock,
  Wifi,
  WifiOff,
  ChevronLeft,
  User,
  Users,
  Loader2,
  FileText,
  Image as ImageIcon,
  Search,
  ShieldCheck,
  Lock,
  ArrowDown,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { getUser } from '@/lib/auth';
import {
  fetchConversations,
  fetchMessages,
  sendMessage,
  markConversationRead,
  uploadAttachment,
  createOrGetConversation,
  fetchChatHealth,
  createChatPoller,
  getAttachmentDownloadUrl,
  type ChatConversation,
  type ChatMessage,
  type ChatAttachmentMeta,
} from '@/lib/chat';

// ── Constants ─────────────────────────────────────────────────────────────────
const CHAT_ALLOWED_ROLES = ['USER', 'ADVOCATE', 'ADMIN'];
const MAX_FILE_MB = 10;
const ALLOWED_EXTS = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.txt', '.doc', '.docx'];
const POLL_INTERVAL_MS = 2500;

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    if (d.toDateString() === today.toDateString()) return 'Today';
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
    return d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' });
  } catch {
    return 'Recent';
  }
}

function formatConvTime(iso?: string | null): string {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / (60 * 1000));
    const diffHours = Math.floor(diffMs / (60 * 60 * 1000));
    const diffDays = Math.floor(diffMs / (24 * 60 * 60 * 1000));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24 && d.toDateString() === now.toDateString()) {
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return d.toLocaleDateString([], { weekday: 'short' });
    return d.toLocaleDateString([], { day: 'numeric', month: 'short' });
  } catch {
    return '';
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileIcon(mime: string | null): React.ReactNode {
  if (!mime) return <FileText className="w-4 h-4 text-[#B59A68]" />;
  if (mime.startsWith('image/')) return <ImageIcon className="w-4 h-4 text-[#4F8EF7]" />;
  return <FileText className="w-4 h-4 text-[#B59A68]" />;
}

// ── Attachment Chip ───────────────────────────────────────────────────────────
function AttachmentChip({ att, isOwn }: { att: ChatAttachmentMeta; isOwn: boolean }) {
  const downloadUrl = getAttachmentDownloadUrl(att.id);
  return (
    <a
      href={downloadUrl}
      target="_blank"
      rel="noopener noreferrer"
      id={`chat-att-${att.id}`}
      className={`group flex items-center gap-2.5 mt-2 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
        isOwn
          ? 'bg-white/15 hover:bg-white/25 text-white border border-white/20'
          : 'bg-[#222825] hover:bg-[#2A312E] text-[#F4EFE5] border border-white/10'
      }`}
    >
      <div className={`p-1.5 rounded-lg ${isOwn ? 'bg-white/20' : 'bg-[#151817]'}`}>
        {fileIcon(att.content_type)}
      </div>
      <div className="flex-1 min-w-0 text-left">
        <p className="truncate max-w-[190px] font-semibold">{att.original_filename}</p>
        <p className={`text-[10px] ${isOwn ? 'text-white/70' : 'text-[#A9A49A]'}`}>
          {formatFileSize(att.size_bytes)}
        </p>
      </div>
      <Download className={`w-4 h-4 flex-shrink-0 transition-transform group-hover:translate-y-0.5 ${
        isOwn ? 'text-white' : 'text-[#4F8EF7]'
      }`} />
    </a>
  );
}

// ── Message Bubble Component ──────────────────────────────────────────────────
function MessageBubble({
  msg,
  isOwn,
  senderName,
}: {
  msg: ChatMessage;
  isOwn: boolean;
  senderName?: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (msg.body) {
      navigator.clipboard.writeText(msg.body);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isPending = msg.status === 'sending';
  const initials = senderName
    ? senderName.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : 'C';

  return (
    <motion.div
      initial={{ opacity: 0, y: 6, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.15 }}
      className={`group flex items-end gap-2 mb-3 ${isOwn ? 'justify-end' : 'justify-start'}`}
    >
      {/* Incoming Avatar */}
      {!isOwn && (
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#1E2522] to-[#2B3430] border border-white/10 flex items-center justify-center flex-shrink-0 text-[10px] font-bold text-[#E5E0D8] mb-1 shadow-sm">
          {initials}
        </div>
      )}

      {/* Bubble Container */}
      <div className="relative max-w-[80%] sm:max-w-[70%]">
        <div
          className={`relative px-4 py-3 rounded-2xl text-sm leading-relaxed transition-all shadow-md ${
            isOwn
              ? 'bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] text-white rounded-br-xs border border-blue-400/25 shadow-blue-500/10'
              : 'bg-[#181D1B] text-[#F4EFE5] rounded-bl-xs border border-white/[0.08] shadow-black/30'
          }`}
        >
          {/* Sender label for incoming */}
          {!isOwn && senderName && (
            <p className="text-[11px] font-bold text-[#4F8EF7] mb-1 tracking-wide">
              {senderName}
            </p>
          )}

          {/* Text Body */}
          {msg.body && !msg.body.startsWith('[Attachment:') && (
            <p className="whitespace-pre-wrap break-words selection:bg-white/30">{msg.body}</p>
          )}

          {/* Attachments */}
          {msg.attachments && msg.attachments.length > 0 && (
            <div className="space-y-1.5 mt-1">
              {msg.attachments.map((att) => (
                <AttachmentChip key={att.id} att={att} isOwn={isOwn} />
              ))}
            </div>
          )}

          {/* Bottom metadata (Time & Delivery status) */}
          <div className={`flex items-center justify-end gap-1.5 mt-1 text-[10px] font-medium ${
            isOwn ? 'text-blue-100/75' : 'text-[#8E8B82]'
          }`}>
            <span>{formatTime(msg.created_at)}</span>
            {isOwn && (
              isPending ? (
                <span title="Sending...">
                  <Clock className="w-3 h-3 text-blue-200 animate-pulse" />
                </span>
              ) : (
                <span title="Delivered & Synced">
                  <CheckCheck className="w-3.5 h-3.5 text-blue-200" />
                </span>
              )
            )}
          </div>
        </div>

        {/* Hover Quick Action: Copy */}
        {msg.body && !msg.body.startsWith('[Attachment:') && (
          <button
            onClick={handleCopy}
            className={`absolute top-2 ${isOwn ? '-left-8' : '-right-8'} opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg bg-[#222724] border border-white/10 text-[#A9A49A] hover:text-[#F4EFE5] shadow-lg`}
            title={copied ? 'Copied!' : 'Copy text'}
            aria-label="Copy message text"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-[#6BD28E]" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
        )}
      </div>
    </motion.div>
  );
}

// ── Date Separator ────────────────────────────────────────────────────────────
function DateSeparator({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center my-5">
      <div className="bg-[#181C1A]/90 border border-white/[0.08] backdrop-blur-md px-3.5 py-1 rounded-full text-[10px] font-semibold text-[#A9A49A] tracking-wider uppercase shadow-sm">
        {label}
      </div>
    </div>
  );
}

// ── Conversation List Item ────────────────────────────────────────────────────
function ConvItem({
  conv,
  isActive,
  currentUserId,
  onClick,
}: {
  conv: ChatConversation;
  isActive: boolean;
  currentUserId: string;
  onClick: () => void;
}) {
  const isAdvocate = conv.other_party_role?.toUpperCase() === 'ADVOCATE' ||
                     (conv.user_id === currentUserId && Boolean(conv.advocate_id));
  const displayName = conv.other_party_name || (isAdvocate ? 'Verified Advocate' : 'Client');
  const designation = conv.other_party_designation || (isAdvocate ? 'Legal Counsel' : 'Case Party');
  const initials = conv.other_party_name
    ? conv.other_party_name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : (isAdvocate ? 'AD' : 'CL');
  const timeLabel = formatConvTime(conv.last_message_at || conv.updated_at);
  const isSentByMe = conv.last_message_sender_id === currentUserId;

  return (
    <button
      id={`chat-conv-${conv.id}`}
      onClick={onClick}
      className={`w-full text-left p-3 rounded-xl transition-all flex items-start gap-3 relative group border ${
        isActive
          ? 'bg-gradient-to-r from-[#4F8EF7]/15 to-transparent border-[#4F8EF7]/40 shadow-sm'
          : 'bg-transparent border-transparent hover:bg-white/[0.03] hover:border-white/[0.05]'
      }`}
    >
      {/* Active Bar indicator */}
      {isActive && (
        <span className="absolute left-0 top-3 bottom-3 w-1 bg-[#4F8EF7] rounded-r-full" />
      )}

      {/* Avatar with Online/Active Beacon */}
      <div className="relative flex-shrink-0">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center text-xs font-bold border transition-all ${
          isActive
            ? 'bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] text-white border-blue-400/30 shadow-md shadow-blue-500/20'
            : 'bg-[#1C211E] text-[#E5E0D8] border-white/10 group-hover:border-white/20'
        }`}>
          {initials}
        </div>
        <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-[#10B981] border-2 border-[#0F1211]" />
      </div>

      {/* Details */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-1.5 mb-0.5">
          <div className="flex items-center gap-1.5 truncate">
            <p className="text-sm font-semibold text-[#F4EFE5] truncate">{displayName}</p>
            {isAdvocate && (
              <span title="Verified Legal Counsel">
                <ShieldCheck className="w-3.5 h-3.5 text-[#F59E0B] flex-shrink-0" />
              </span>
            )}
          </div>
          <span className="text-[10px] font-medium text-[#8E8B82] flex-shrink-0">{timeLabel}</span>
        </div>

        <p className="text-[11px] font-medium text-[#A9A49A]/80 truncate mb-1">{designation}</p>

        <div className="flex items-center justify-between gap-2">
          <p className="text-xs text-[#8E8B82] truncate group-hover:text-[#B5B1A8] transition-colors">
            {isSentByMe && <span className="text-[#4F8EF7]/90 font-medium">You: </span>}
            {conv.last_message_body || 'No messages yet'}
          </p>

          {conv.unread_count && conv.unread_count > 0 ? (
            <span className="flex-shrink-0 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-[10px] font-extrabold rounded-full px-1.5 py-0.5 min-w-[18px] text-center shadow-md shadow-blue-500/30">
              {conv.unread_count > 9 ? '9+' : conv.unread_count}
            </span>
          ) : null}
        </div>
      </div>
    </button>
  );
}

// ── Main Chat Workspace ───────────────────────────────────────────────────────
function ChatContent() {
  const searchParams = useSearchParams();
  const paramConvId = searchParams?.get('conversationId');

  const currentUser = getUser();
  const currentUserId = currentUser?.id ?? '';
  const currentRole = currentUser?.role ?? 'USER';

  // State
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<{ before_created_at: string; before_id: string } | null>(null);

  const [convLoading, setConvLoading] = useState(true);
  const [msgLoading, setMsgLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);

  const [convError, setConvError] = useState<string | null>(null);
  const [msgError, setMsgError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);

  const [body, setBody] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isConnected, setIsConnected] = useState(true);
  const [realtimeMode, setRealtimeMode] = useState<'postgresql' | 'sqlite' | null>(null);
  const [showConvList, setShowConvList] = useState(true);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    setShowScrollBottom(scrollHeight - scrollTop - clientHeight > 160);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Pending attachment preview
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollerRef = useRef<ReturnType<typeof createChatPoller> | null>(null);
  const activeConvIdRef = useRef<string | null>(null);
  activeConvIdRef.current = activeConvId;
  const initialLoadedRef = useRef(false);

  // ── Load Conversation List ──────────────────────────────────────────────────
  const loadConversations = useCallback(async () => {
    setConvError(null);
    try {
      const data = await fetchConversations();
      setConversations(data.conversations);
      return data.conversations;
    } catch (e: unknown) {
      setConvError(e instanceof Error ? e.message : 'Failed to load conversations.');
      return [];
    } finally {
      setConvLoading(false);
    }
  }, []);

  // ── Load Message Thread ─────────────────────────────────────────────────────
  const loadMessages = useCallback(async (convId: string, append = false) => {
    if (append) setLoadingMore(true);
    else setMsgLoading(true);
    setMsgError(null);

    try {
      const cursor = append ? nextCursor ?? undefined : undefined;
      const page = await fetchMessages(convId, cursor ?? undefined);

      setMessages((prev) => {
        if (append) {
          const existingIds = new Set(prev.map((m) => m.id));
          const freshOlder = page.messages.filter((m) => !existingIds.has(m.id));
          return [...freshOlder, ...prev];
        }
        return page.messages.map((m) => ({ ...m, status: 'sent' as const }));
      });

      setHasMore(page.has_more);
      setNextCursor(page.next_cursor);
      setIsConnected(true);
    } catch (e: unknown) {
      setMsgError(e instanceof Error ? e.message : 'Failed to load messages.');
      setIsConnected(false);
    } finally {
      if (append) setLoadingMore(false);
      else setMsgLoading(false);
    }
  }, [nextCursor]);

  // ── Polling Synchronizer ───────────────────────────────────────────────────
  const startPolling = useCallback((convId: string) => {
    pollerRef.current?.stop();
    pollerRef.current = createChatPoller(
      convId,
      () => null,
      (incomingBatch) => {
        if (!incomingBatch || incomingBatch.length === 0) return;

        setMessages((prev) => {
          const map = new Map<string, ChatMessage>();
          for (const m of prev) {
            const key = m.idempotency_key || m.id;
            map.set(key, m);
          }

          let hasChange = false;
          for (const fresh of incomingBatch) {
            const key = fresh.idempotency_key || fresh.id;
            const existing = map.get(key);
            if (!existing || existing.id.startsWith('temp-')) {
              map.set(key, { ...fresh, status: 'sent' });
              hasChange = true;
            }
          }

          if (!hasChange && map.size === prev.length) return prev;

          const sorted = Array.from(map.values()).sort(
            (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          );

          // Update latest preview in conversations list
          const latest = sorted[sorted.length - 1];
          if (latest) {
            setConversations((convList) =>
              convList.map((c) =>
                c.id === convId
                  ? {
                      ...c,
                      last_message_body: latest.body,
                      last_message_at: latest.created_at,
                      last_message_sender_id: latest.sender_id,
                    }
                  : c
              )
            );
          }

          return sorted;
        });

        setIsConnected(true);
      },
      POLL_INTERVAL_MS
    );
    pollerRef.current.start();
  }, []);

  // ── Select Conversation ─────────────────────────────────────────────────────
  const selectConversation = useCallback(async (convId: string) => {
    if (activeConvIdRef.current === convId && messages.length > 0) {
      setShowConvList(false);
      return;
    }
    setActiveConvId(convId);
    setMessages([]);
    setNextCursor(null);
    setHasMore(false);
    setSendError(null);
    setShowConvList(false);

    await loadMessages(convId);
    startPolling(convId);

    // Clear unread badge locally for instant feedback
    setConversations((prev) =>
      prev.map((c) => (c.id === convId ? { ...c, unread_count: 0 } : c))
    );
  }, [loadMessages, startPolling, messages.length]);

  // ── Initial Mount & Route Sync ──────────────────────────────────────────────
  useEffect(() => {
    if (initialLoadedRef.current) return;
    initialLoadedRef.current = true;

    loadConversations().then((convs) => {
      const targetId = paramConvId || (convs.length > 0 ? convs[0].id : null);
      if (targetId) {
        selectConversation(targetId);
      }
    });

    fetchChatHealth()
      .then((h) => setRealtimeMode(h.chat_db_mode))
      .catch(() => setRealtimeMode('sqlite'));
  }, [loadConversations, paramConvId, selectConversation]);

  // ── Search Param Route Change ───────────────────────────────────────────────
  useEffect(() => {
    if (paramConvId && initialLoadedRef.current && paramConvId !== activeConvIdRef.current) {
      selectConversation(paramConvId);
    }
  }, [paramConvId, selectConversation]);

  // ── Background Conversations Refresh (every 8s) ─────────────────────────────
  useEffect(() => {
    const interval = setInterval(() => {
      fetchConversations()
        .then((data) => setConversations(data.conversations))
        .catch(() => { /* silent */ });
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  // ── Auto-scroll to Bottom on New Messages ──────────────────────────────────
  useEffect(() => {
    if (!loadingMore) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loadingMore]);

  // ── Mark Read Synchronizer ──────────────────────────────────────────────────
  useEffect(() => {
    if (!activeConvId || messages.length === 0) return;
    const last = messages[messages.length - 1];
    if (last.sender_id !== currentUserId && !last.id.startsWith('temp-')) {
      markConversationRead(activeConvId, last.id).catch(() => { /* non-critical */ });
    }
  }, [messages, activeConvId, currentUserId]);

  // ── Tab Visibility Recovery ─────────────────────────────────────────────────
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === 'visible' && activeConvIdRef.current) {
        loadMessages(activeConvIdRef.current);
        loadConversations();
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [loadMessages, loadConversations]);

  // ── Cleanup Poller on Unmount ───────────────────────────────────────────────
  useEffect(() => () => { pollerRef.current?.stop(); }, []);

  // ── Send Message with Optimistic 0ms UI Update ──────────────────────────────
  const handleSend = async () => {
    const trimmed = body.trim();
    if (!trimmed || !activeConvId || sending) return;

    const ikey = `${currentUserId}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    const tempId = `temp-${ikey}`;
    const nowIso = new Date().toISOString();

    // 1. Optimistic Message object
    const optimisticMsg: ChatMessage = {
      id: tempId,
      conversation_id: activeConvId,
      sender_id: currentUserId,
      body: trimmed,
      idempotency_key: ikey,
      created_at: nowIso,
      attachments: [],
      status: 'sending',
    };

    // 2. Immediate zero-latency UI append
    setMessages((prev) => [...prev, optimisticMsg]);
    setBody('');
    setSendError(null);

    // 3. Immediately update sidebar preview and float active conversation to top
    setConversations((prev) => {
      const updated = prev.map((c) =>
        c.id === activeConvId
          ? {
              ...c,
              last_message_body: trimmed,
              last_message_at: nowIso,
              last_message_sender_id: currentUserId,
            }
          : c
      );
      return updated.sort((a, b) => {
        const tA = new Date(a.last_message_at || a.created_at).getTime();
        const tB = new Date(b.last_message_at || b.created_at).getTime();
        return tB - tA;
      });
    });

    setSending(true);

    try {
      // 4. API dispatch (sub-second with connection pool + background event)
      const serverMsg = await sendMessage(activeConvId, trimmed, ikey);

      // 5. Reconcile optimistic message with verified server record
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempId || m.idempotency_key === ikey
            ? { ...serverMsg, attachments: [], status: 'sent' }
            : m
        )
      );
    } catch (e: unknown) {
      setSendError(e instanceof Error ? e.message : 'Failed to deliver message.');
      setMessages((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m, status: 'failed' } : m))
      );
    } finally {
      setSending(false);
    }
  };

  // ── Attachment Upload ───────────────────────────────────────────────────────
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activeConvId) return;

    if (file.size > MAX_FILE_MB * 1024 * 1024) {
      setSendError(`File exceeds maximum size limit of ${MAX_FILE_MB} MB.`);
      return;
    }
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setSendError(`File extension "${ext}" is not supported. Use PDF, DOCX, or Images.`);
      return;
    }

    setUploading(true);
    setSendError(null);

    try {
      const result = await uploadAttachment(activeConvId, file);
      setMessages((prev) => {
        if (prev.find((m) => m.id === result.id)) return prev;
        return [...prev, { ...result, attachments: [result.attachment], status: 'sent' }];
      });

      // Update sidebar
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConvId
            ? {
                ...c,
                last_message_body: `[Document: ${file.name}]`,
                last_message_at: new Date().toISOString(),
              }
            : c
        )
      );
    } catch (e: unknown) {
      setSendError(e instanceof Error ? e.message : 'File upload failed.');
    } finally {
      setUploading(false);
      setPendingFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // ── Filtered Conversations ──────────────────────────────────────────────────
  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const q = searchQuery.toLowerCase();
    return conversations.filter(
      (c) =>
        c.other_party_name?.toLowerCase().includes(q) ||
        c.other_party_designation?.toLowerCase().includes(q) ||
        c.last_message_body?.toLowerCase().includes(q)
    );
  }, [conversations, searchQuery]);

  // ── Group Messages by Date ──────────────────────────────────────────────────
  const groupedMessages = useMemo(() => {
    const groups: { date: string; msgs: ChatMessage[] }[] = [];
    for (const msg of messages) {
      const label = formatDate(msg.created_at);
      if (!groups.length || groups[groups.length - 1].date !== label) {
        groups.push({ date: label, msgs: [msg] });
      } else {
        groups[groups.length - 1].msgs.push(msg);
      }
    }
    return groups;
  }, [messages]);

  const activeConv = conversations.find((c) => c.id === activeConvId);
  const isAdvocatePartner = activeConv?.other_party_role?.toUpperCase() === 'ADVOCATE' ||
                            (activeConv?.user_id === currentUserId && Boolean(activeConv?.advocate_id));
  const partnerName = activeConv?.other_party_name || (isAdvocatePartner ? 'Advocate Counsel' : 'Case Client');

  return (
    <RoleGuard allowedRoles={CHAT_ALLOWED_ROLES} portalName="NyayaSarathi Chat">
      <div className="min-h-screen bg-[#0B0D0C] text-[#F4EFE5] pt-16 sm:pt-20 pb-4 px-2 sm:px-4 lg:px-6">
        {/* Ambient background glows */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
          <div className="absolute top-10 left-1/4 w-[600px] h-[600px] bg-[#4F8EF7]/5 rounded-full blur-[140px]" />
          <div className="absolute bottom-10 right-1/4 w-[600px] h-[600px] bg-[#B59A68]/5 rounded-full blur-[140px]" />
        </div>

        <div className="max-w-7xl mx-auto h-[calc(100vh-5.5rem)] flex flex-col relative z-10">
          {/* Main Chat Glass Container */}
          <div className="flex-1 flex min-h-0 rounded-2xl overflow-hidden border border-white/[0.08] bg-[#0F1211]/90 backdrop-blur-2xl shadow-2xl">
            
            {/* ── Left Sidebar (Conversations) ─────────────────────────────── */}
            <div className={`
              w-full sm:w-80 md:w-96 flex-shrink-0 flex flex-col border-r border-white/[0.08] bg-[#0E1110]
              ${activeConvId && !showConvList ? 'hidden sm:flex' : 'flex'}
            `}>
              {/* Sidebar Header */}
              <div className="p-4 border-b border-white/[0.08] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#2563EB]/20 to-[#1D4ED8]/20 border border-[#4F8EF7]/40 flex items-center justify-center">
                      <MessageCircle className="w-4 h-4 text-[#4F8EF7]" />
                    </div>
                    <div>
                      <h1 className="font-display text-base font-bold text-[#F4EFE5] tracking-tight">Messages</h1>
                      <p className="text-[11px] text-[#8E8B82]">Encrypted Consultations</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {currentRole === 'USER' && (
                      <Link
                        href="/find-advocate"
                        id="chat-find-advocate-sidebar-btn"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#4F8EF7]/15 border border-[#4F8EF7]/30 text-xs font-bold text-[#4F8EF7] hover:bg-[#4F8EF7]/25 transition-all shadow-sm"
                        title="Browse verified advocates"
                      >
                        <Users className="w-3.5 h-3.5" />
                        <span>Find Advocate</span>
                      </Link>
                    )}

                    <button
                      id="chat-refresh-convs"
                      onClick={() => loadConversations()}
                      className="p-1.5 rounded-xl hover:bg-white/[0.06] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                      aria-label="Refresh conversations"
                      title="Sync conversations"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${convLoading ? 'animate-spin text-[#4F8EF7]' : ''}`} />
                    </button>
                  </div>
                </div>

                {/* Instant Client-Side Search Bar */}
                <div className="relative">
                  <Search className="w-4 h-4 text-[#8E8B82] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    id="chat-conv-search-input"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search counsel, client, or message..."
                    className="w-full bg-[#161B18] border border-white/[0.07] focus:border-[#4F8EF7]/50 focus:ring-1 focus:ring-[#4F8EF7]/30 text-xs text-[#F4EFE5] placeholder-[#8E8B82] rounded-xl pl-9 pr-8 py-2 outline-none transition-all"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8E8B82] hover:text-white p-0.5"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Conversations Feed */}
              <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                {convLoading && conversations.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-40 space-y-2 text-[#8E8B82]">
                    <Loader2 className="w-6 h-6 text-[#4F8EF7] animate-spin" />
                    <p className="text-xs">Loading conversations...</p>
                  </div>
                )}

                {!convLoading && convError && (
                  <div className="p-3.5 rounded-xl bg-[#6E2634]/15 border border-[#E25C6F]/30 text-xs text-[#E25C6F] flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <p className="flex-1">{convError}</p>
                    <button onClick={loadConversations} className="text-xs font-bold underline">Retry</button>
                  </div>
                )}

                {!convLoading && conversations.length === 0 && !convError && (
                  <div className="text-center py-14 px-4 space-y-3">
                    <div className="w-12 h-12 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mx-auto text-[#8E8B82]">
                      <MessageCircle className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-[#F4EFE5]">No conversations yet</p>
                      <p className="text-xs text-[#8E8B82] mt-1 max-w-[200px] mx-auto">
                        {currentRole === 'USER'
                          ? 'Browse verified legal counsel and initiate your first confidential consult.'
                          : 'Incoming case consultations from clients will appear here.'}
                      </p>
                    </div>

                    {currentRole === 'USER' && (
                      <Link
                        href="/find-advocate"
                        id="chat-empty-find-advocate-btn"
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-[#2563EB] to-[#1D4ED8] text-white text-xs font-bold hover:brightness-110 transition-all shadow-lg shadow-blue-600/20"
                      >
                        <Users className="w-3.5 h-3.5" />
                        <span>Find an Advocate</span>
                      </Link>
                    )}
                  </div>
                )}

                {filteredConversations.map((conv) => (
                  <ConvItem
                    key={conv.id}
                    conv={conv}
                    isActive={conv.id === activeConvId}
                    currentUserId={currentUserId}
                    onClick={() => selectConversation(conv.id)}
                  />
                ))}

                {filteredConversations.length === 0 && searchQuery && (
                  <p className="text-center text-xs text-[#8E8B82] py-8">
                    No conversations matching &ldquo;{searchQuery}&rdquo;
                  </p>
                )}
              </div>
            </div>

            {/* ── Main Message Area ────────────────────────────────────────── */}
            <div className={`
              flex-1 flex flex-col min-w-0 bg-[#0B0D0C]/80
              ${activeConvId && !showConvList ? 'flex' : 'hidden sm:flex'}
            `}>
              {!activeConvId ? (
                /* Empty state when no conversation is selected */
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-4">
                  <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-[#2563EB]/15 to-[#B59A68]/10 border border-white/[0.08] flex items-center justify-center shadow-xl">
                    <MessageCircle className="w-10 h-10 text-[#4F8EF7]/70" />
                  </div>
                  <div className="max-w-md space-y-1">
                    <h3 className="text-lg font-bold text-[#F4EFE5]">NyayaSarathi Legal Workspace</h3>
                    <p className="text-xs text-[#8E8B82]">
                      Select an active consultation thread from the left or discover verified counsel to commence secure communications.
                    </p>
                  </div>
                  {currentRole === 'USER' && (
                    <Link
                      href="/find-advocate"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.05] border border-white/10 text-xs font-semibold hover:bg-white/10 transition-colors"
                    >
                      <Users className="w-4 h-4 text-[#4F8EF7]" />
                      <span>Discover Verified Advocates</span>
                    </Link>
                  )}
                </div>
              ) : (
                <>
                  {/* Chat Top Header */}
                  <div className="px-4 sm:px-6 py-3.5 border-b border-white/[0.08] bg-[#0E1110] flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      {/* Back button on mobile */}
                      <button
                        className="sm:hidden p-1.5 rounded-xl hover:bg-white/[0.06] text-[#A9A49A] transition-colors"
                        onClick={() => setShowConvList(true)}
                        aria-label="Back to conversations list"
                      >
                        <ChevronLeft className="w-5 h-5" />
                      </button>

                      {/* Other Party Avatar */}
                      <div className="relative">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] text-white border border-blue-400/30 flex items-center justify-center font-bold text-xs shadow-md shadow-blue-500/20">
                          {partnerName.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                        </div>
                        <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-[#10B981] border-2 border-[#0E1110]" />
                      </div>

                      {/* Other Party Info */}
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <h2 className="text-sm sm:text-base font-bold text-[#F4EFE5] truncate">
                            {partnerName}
                          </h2>
                          {isAdvocatePartner && (
                            <span title="Verified Advocate on Record">
                              <ShieldCheck className="w-4 h-4 text-[#F59E0B] flex-shrink-0" />
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[#8E8B82] truncate">
                          {activeConv?.other_party_designation || (isAdvocatePartner ? 'Advocate on Record' : 'Client Consultation')} • <span className="text-[#10B981]">Active Session</span>
                        </p>
                      </div>
                    </div>

                    {/* Status & Actions Header Bar */}
                    <div className="flex items-center gap-2">
                      {/* Live Sync Beacon */}
                      <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 text-[11px] font-semibold text-[#10B981]">
                        <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
                        <span>Live Sync</span>
                      </div>

                      {/* Encryption badge */}
                      <div className="hidden lg:flex items-center gap-1 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-[11px] text-[#8E8B82]">
                        <Lock className="w-3 h-3 text-[#B59A68]" />
                        <span>256-Bit</span>
                      </div>

                      {/* Manual Refresh */}
                      <button
                        id="chat-refresh-msgs"
                        onClick={() => activeConvId && loadMessages(activeConvId)}
                        className="p-2 rounded-xl hover:bg-white/[0.06] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                        aria-label="Refresh messages"
                        title="Sync current thread"
                      >
                        <RefreshCw className={`w-4 h-4 ${msgLoading ? 'animate-spin text-[#4F8EF7]' : ''}`} />
                      </button>
                    </div>
                  </div>

                  {/* Messages Feed Container */}
                  <div className="relative flex-1 min-h-0 flex flex-col">
                    <div
                      ref={messagesContainerRef}
                      onScroll={handleScroll}
                      className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-2 custom-scrollbar"
                      id="chat-messages-panel"
                    >
                      {/* Load More Older Messages */}
                      {hasMore && (
                        <div className="flex justify-center mb-4">
                          <button
                            id="chat-load-more"
                            onClick={() => activeConvId && loadMessages(activeConvId, true)}
                            disabled={loadingMore}
                            className="text-xs text-[#4F8EF7] hover:text-[#7FB3FF] font-semibold py-1.5 px-4 rounded-xl bg-[#4F8EF7]/10 hover:bg-[#4F8EF7]/20 border border-[#4F8EF7]/20 transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
                          >
                            {loadingMore ? (
                              <>
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                <span>Retrieving history...</span>
                              </>
                            ) : (
                              <span>Load previous messages</span>
                            )}
                          </button>
                        </div>
                      )}

                      {msgLoading && messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-48 space-y-2 text-[#8E8B82]">
                          <Loader2 className="w-7 h-7 text-[#4F8EF7] animate-spin" />
                          <p className="text-xs">Connecting to secure chamber...</p>
                        </div>
                      ) : msgError ? (
                        <div className="flex items-center gap-3 p-4 rounded-2xl bg-[#6E2634]/15 border border-[#E25C6F]/30 text-xs text-[#E25C6F]">
                          <AlertCircle className="w-5 h-5 flex-shrink-0" />
                          <p className="flex-1">{msgError}</p>
                          <button
                            onClick={() => activeConvId && loadMessages(activeConvId)}
                            className="font-bold underline"
                          >
                            Retry
                          </button>
                        </div>
                      ) : messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-48 text-center space-y-3">
                          <div className="w-12 h-12 rounded-2xl bg-[#4F8EF7]/10 border border-[#4F8EF7]/20 flex items-center justify-center text-[#4F8EF7]">
                            <MessageCircle className="w-6 h-6" />
                          </div>
                          <div>
                            <p className="text-sm font-bold text-[#F4EFE5]">Conversation opened</p>
                            <p className="text-xs text-[#8E8B82] mt-0.5">
                              This is the beginning of your confidential consultation.
                            </p>
                          </div>
                        </div>
                      ) : (
                        groupedMessages.map(({ date, msgs }) => (
                          <div key={date}>
                            <DateSeparator label={date} />
                            {msgs.map((msg) => (
                              <MessageBubble
                                key={msg.id}
                                msg={msg}
                                isOwn={msg.sender_id === currentUserId}
                                senderName={msg.sender_id === currentUserId ? 'You' : partnerName}
                              />
                            ))}
                          </div>
                        ))
                      )}
                      <div ref={messagesEndRef} />
                    </div>

                    {/* Floating Scroll To Bottom Button */}
                    <AnimatePresence>
                      {showScrollBottom && (
                        <motion.button
                          initial={{ opacity: 0, scale: 0.8, y: 10 }}
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.8, y: 10 }}
                          onClick={scrollToBottom}
                          className="absolute bottom-3 right-6 p-2 rounded-full bg-[#181D1B] border border-white/10 text-white shadow-2xl hover:bg-[#252D2A] transition-all flex items-center gap-1.5 text-xs font-semibold z-20 group"
                          aria-label="Scroll to newest messages"
                        >
                          <ArrowDown className="w-4 h-4 text-[#4F8EF7] group-hover:translate-y-0.5 transition-transform" />
                        </motion.button>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Send Error Notice */}
                  <AnimatePresence>
                    {sendError && (
                      <motion.div
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="mx-4 sm:mx-6 mb-2 px-4 py-2.5 rounded-xl bg-[#6E2634]/20 border border-[#E25C6F]/30 text-xs text-[#E25C6F] flex items-center justify-between gap-2 shadow-lg"
                      >
                        <span className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 flex-shrink-0" />
                          <span>{sendError}</span>
                        </span>
                        <button onClick={() => setSendError(null)} aria-label="Dismiss error">
                          <X className="w-4 h-4 text-[#E25C6F] hover:text-white" />
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Message Composer */}
                  <div className="p-3 sm:p-4 border-t border-white/[0.08] bg-[#0E1110]">
                    <div className="bg-[#141816] rounded-2xl border border-white/[0.08] focus-within:border-[#4F8EF7]/60 focus-within:ring-2 focus-within:ring-[#4F8EF7]/20 transition-all p-2 sm:p-2.5">
                      
                      {/* Hidden File Input */}
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept={ALLOWED_EXTS.join(',')}
                        className="hidden"
                        id="chat-file-input"
                        onChange={handleFileChange}
                      />

                      {/* Text Input Row */}
                      <div className="flex items-end gap-2">
                        {/* Attach button */}
                        <button
                          id="chat-attach-btn"
                          onClick={() => fileInputRef.current?.click()}
                          disabled={uploading || !activeConvId}
                          className="p-2 rounded-xl text-[#8E8B82] hover:text-[#F4EFE5] hover:bg-white/[0.06] transition-all disabled:opacity-40 flex-shrink-0"
                          title="Attach legal document or image (Max 10MB)"
                          aria-label="Attach file"
                        >
                          {uploading ? (
                            <Loader2 className="w-4 h-4 animate-spin text-[#4F8EF7]" />
                          ) : (
                            <Paperclip className="w-4 h-4" />
                          )}
                        </button>

                        {/* Textarea */}
                        <textarea
                          id="chat-message-input"
                          value={body}
                          onChange={(e) => setBody(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleSend();
                            }
                          }}
                          placeholder={`Message ${partnerName}… (Enter to send)`}
                          rows={1}
                          maxLength={4000}
                          className="flex-1 bg-transparent resize-none text-sm text-[#F4EFE5] placeholder-[#8E8B82]/70 outline-none py-1.5 max-h-36 overflow-y-auto leading-relaxed"
                          aria-label="Message input"
                        />

                        {/* Send Button */}
                        <button
                          id="chat-send-btn"
                          onClick={handleSend}
                          disabled={!body.trim() || sending || !activeConvId}
                          className={`p-2.5 rounded-xl transition-all flex-shrink-0 flex items-center justify-center ${
                            body.trim() && !sending
                              ? 'bg-gradient-to-r from-[#2563EB] to-[#1D4ED8] text-white hover:brightness-110 shadow-lg shadow-blue-500/25 scale-100 hover:scale-105 active:scale-95'
                              : 'bg-white/[0.05] text-[#8E8B82]/40 cursor-not-allowed'
                          }`}
                          aria-label="Send message"
                          title="Send message (Enter)"
                        >
                          {sending ? (
                            <Loader2 className="w-4 h-4 animate-spin text-white" />
                          ) : (
                            <Send className="w-4 h-4" />
                          )}
                        </button>
                      </div>

                      {/* Footer Hint Bar */}
                      <div className="flex items-center justify-between mt-1 px-1 text-[10px] text-[#8E8B82]/70 font-medium">
                        <span>Attach: PDF, DOCX, PNG, JPG (10MB max)</span>
                        <span>{body.length > 0 ? `${body.length}/4000` : 'Press Enter ↵ to send • Shift+Enter for new line'}</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#0B0D0C] flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-[#4F8EF7] animate-spin" />
          <p className="text-xs text-[#8E8B82] font-semibold">Loading Secure Chat Workspace...</p>
        </div>
      }
    >
      <ChatContent />
    </Suspense>
  );
}
