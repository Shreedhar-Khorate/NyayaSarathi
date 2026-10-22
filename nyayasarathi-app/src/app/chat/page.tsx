'use client';

/**
 * NyayaSarathi — Chat Page
 * Real-time User–Advocate secure messaging.
 * Route: /chat  (accessible by USER and ADVOCATE)
 *
 * Architecture:
 * - All API calls go through FastAPI (/api/chat/*)
 * - In PostgreSQL mode: backend publishes Realtime events → frontend polls
 *   on reconnect / visibility change since Supabase SDK not in browser.
 * - In SQLite mode: conservative 5s polling fallback.
 */

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
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
  Wifi,
  WifiOff,
  ChevronLeft,
  User,
  Loader2,
  FileText,
  Image as ImageIcon,
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
const MAX_FILE_MB = 10;
const ALLOWED_EXTS = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.txt', '.doc', '.docx'];
const POLL_INTERVAL_MS = 5000;

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' });
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

// ── Conversation list item ────────────────────────────────────────────────────
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
  const isUser = conv.user_id === currentUserId;
  const otherId = isUser ? conv.advocate_id : conv.user_id;
  const label = isUser ? 'Advocate' : 'Client';

  return (
    <button
      id={`chat-conv-${conv.id}`}
      onClick={onClick}
      className={`w-full text-left px-4 py-3 rounded-xl transition-all flex items-start gap-3 group ${
        isActive
          ? 'bg-[#4F8EF7]/15 border border-[#4F8EF7]/40'
          : 'hover:bg-[#1D211F]/80 border border-transparent hover:border-[#2A2E2B]'
      }`}
    >
      {/* Avatar */}
      <div className="w-10 h-10 rounded-full bg-[#2A2E2B] border border-[#3B3A33] flex items-center justify-center flex-shrink-0">
        <User className="w-5 h-5 text-[#A9A49A]" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold text-[#F4EFE5] truncate">{label}</p>
          {conv.unread_count ? (
            <span className="flex-shrink-0 bg-[#4F8EF7] text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center">
              {conv.unread_count > 9 ? '9+' : conv.unread_count}
            </span>
          ) : null}
        </div>
        <p className="text-xs text-[#A9A49A] truncate mt-0.5">
          {conv.last_message_body ?? 'No messages yet'}
        </p>
      </div>
    </button>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────
function MessageBubble({
  msg,
  isOwn,
}: {
  msg: ChatMessage;
  isOwn: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-2`}
    >
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
          isOwn
            ? 'bg-[#4F8EF7] text-white rounded-br-sm'
            : 'bg-[#1D211F] border border-[#2A2E2B] text-[#F4EFE5] rounded-bl-sm'
        }`}
      >
        {msg.body && !msg.body.startsWith('[Attachment:') && (
          <p className="whitespace-pre-wrap break-words">{msg.body}</p>
        )}

        {/* Attachments */}
        {msg.attachments?.map((att) => (
          <AttachmentChip key={att.id} att={att} isOwn={isOwn} />
        ))}

        <p className={`text-[10px] mt-1 ${isOwn ? 'text-white/60 text-right' : 'text-[#A9A49A]'}`}>
          {formatTime(msg.created_at)}
          {isOwn && <CheckCheck className="inline w-3 h-3 ml-1 opacity-70" />}
        </p>
      </div>
    </motion.div>
  );
}

function AttachmentChip({ att, isOwn }: { att: ChatAttachmentMeta; isOwn: boolean }) {
  const downloadUrl = getAttachmentDownloadUrl(att.id);
  return (
    <a
      href={downloadUrl}
      target="_blank"
      rel="noopener noreferrer"
      id={`chat-att-${att.id}`}
      className={`flex items-center gap-2 mt-1 px-3 py-2 rounded-xl text-xs font-medium ${
        isOwn
          ? 'bg-white/15 hover:bg-white/25 text-white'
          : 'bg-[#2A2E2B] hover:bg-[#3B3A33] text-[#F4EFE5] border border-[#3B3A33]'
      } transition-colors`}
    >
      {fileIcon(att.content_type)}
      <span className="truncate max-w-[160px]">{att.original_filename}</span>
      <span className="text-[10px] opacity-60">{formatFileSize(att.size_bytes)}</span>
      <Download className="w-3 h-3 flex-shrink-0" />
    </a>
  );
}

// ── Date separator ────────────────────────────────────────────────────────────
function DateSeparator({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 my-4">
      <div className="flex-1 h-px bg-[#2A2E2B]" />
      <span className="text-[10px] text-[#A9A49A] font-medium tracking-wide uppercase">{label}</span>
      <div className="flex-1 h-px bg-[#2A2E2B]" />
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ChatPage() {
  const currentUser = getUser();
  const currentUserId = currentUser?.id ?? '';
  const currentRole = currentUser?.role ?? 'USER';

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
  const [isConnected, setIsConnected] = useState(true);
  const [realtimeMode, setRealtimeMode] = useState<'postgresql' | 'sqlite' | null>(null);

  const [showConvList, setShowConvList] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollerRef = useRef<ReturnType<typeof createChatPoller> | null>(null);
  const activeConvIdRef = useRef<string | null>(null);

  // ── Load conversation list ──────────────────────────────────────────────────
  const loadConversations = useCallback(async () => {
    setConvLoading(true);
    setConvError(null);
    try {
      const data = await fetchConversations();
      setConversations(data.conversations);
    } catch (e: unknown) {
      setConvError(e instanceof Error ? e.message : 'Failed to load conversations.');
    } finally {
      setConvLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
    fetchChatHealth()
      .then((h) => setRealtimeMode(h.chat_db_mode))
      .catch(() => setRealtimeMode('sqlite'));
  }, [loadConversations]);

  // ── Load messages for active conversation ───────────────────────────────────
  const loadMessages = useCallback(async (convId: string, append = false) => {
    if (append) setLoadingMore(true);
    else setMsgLoading(true);
    setMsgError(null);
    try {
      const cursor = append ? nextCursor ?? undefined : undefined;
      const page = await fetchMessages(convId, cursor ?? undefined);
      setMessages((prev) => append ? [...page.messages, ...prev] : page.messages);
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

  // ── Start polling (SQLite mode or reconnect fallback) ───────────────────────
  const startPolling = useCallback((convId: string) => {
    pollerRef.current?.stop();
    pollerRef.current = createChatPoller(
      convId,
      () => messages[messages.length - 1]?.id ?? null,
      (newMsgs) => {
        setMessages((prev) => {
          const existingIds = new Set(prev.map((m) => m.id));
          const fresh = newMsgs.filter((m) => !existingIds.has(m.id));
          return fresh.length ? [...prev, ...fresh] : prev;
        });
        setIsConnected(true);
        loadConversations();
      },
      POLL_INTERVAL_MS
    );
    pollerRef.current.start();
  }, [messages, loadConversations]);

  // ── Select conversation ─────────────────────────────────────────────────────
  const selectConversation = useCallback(async (convId: string) => {
    activeConvIdRef.current = convId;
    setActiveConvId(convId);
    setMessages([]);
    setNextCursor(null);
    setHasMore(false);
    setSendError(null);
    setShowConvList(false);
    await loadMessages(convId);
    startPolling(convId);
  }, [loadMessages, startPolling]);

  // ── Auto-scroll ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!loadingMore) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loadingMore]);

  // ── Mark read ───────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!activeConvId || messages.length === 0) return;
    const last = messages[messages.length - 1];
    if (last.sender_id !== currentUserId) {
      markConversationRead(activeConvId, last.id).catch(() => { /* non-critical */ });
      setConversations((prev) =>
        prev.map((c) => c.id === activeConvId ? { ...c, unread_count: 0 } : c)
      );
    }
  }, [messages, activeConvId, currentUserId]);

  // ── Visibility / reconnect recovery ────────────────────────────────────────
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === 'visible' && activeConvId) {
        loadMessages(activeConvId).then(() => loadConversations());
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [activeConvId, loadMessages, loadConversations]);

  // ── Cleanup poller on unmount ───────────────────────────────────────────────
  useEffect(() => () => { pollerRef.current?.stop(); }, []);

  // ── Send message ────────────────────────────────────────────────────────────
  const handleSend = async () => {
    if (!body.trim() || !activeConvId || sending) return;
    setSending(true);
    setSendError(null);
    const ikey = `${currentUserId}-${Date.now()}`;
    try {
      const msg = await sendMessage(activeConvId, body.trim(), ikey);
      // Deduplicate by id
      setMessages((prev) => {
        if (prev.find((m) => m.id === msg.id)) return prev;
        return [...prev, { ...msg, attachments: [] }];
      });
      setBody('');
      loadConversations();
    } catch (e: unknown) {
      setSendError(e instanceof Error ? e.message : 'Failed to send message.');
    } finally {
      setSending(false);
    }
  };

  // ── File upload ─────────────────────────────────────────────────────────────
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activeConvId) return;
    if (file.size > MAX_FILE_MB * 1024 * 1024) {
      setSendError(`File exceeds maximum size of ${MAX_FILE_MB} MB.`);
      return;
    }
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setSendError(`File type "${ext}" is not allowed.`);
      return;
    }
    setUploading(true);
    setSendError(null);
    try {
      const result = await uploadAttachment(activeConvId, file);
      setMessages((prev) => {
        if (prev.find((m) => m.id === result.id)) return prev;
        return [...prev, { ...result, attachments: [result.attachment] }];
      });
      loadConversations();
    } catch (e: unknown) {
      setSendError(e instanceof Error ? e.message : 'File upload failed.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // ── Start new conversation (USER initiates with advocate) ───────────────────
  const handleNewConversation = async (advocateId: string) => {
    if (!currentUserId) return;
    try {
      const conv = await createOrGetConversation(currentUserId, advocateId);
      await loadConversations();
      selectConversation(conv.id);
    } catch (e: unknown) {
      setConvError(e instanceof Error ? e.message : 'Failed to open conversation.');
    }
  };

  // ── Group messages by date ──────────────────────────────────────────────────
  const groupedMessages = (() => {
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
  })();

  const activeConv = conversations.find((c) => c.id === activeConvId);

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <RoleGuard allowedRoles={['USER', 'ADVOCATE', 'ADMIN']} portalName="NyayaSarathi Chat">
      <div className="min-h-screen bg-[#151716] pt-20 pb-4 px-2 sm:px-4 lg:px-6">
        {/* Background glows */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-[#4F8EF7]/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-[#B59A68]/5 rounded-full blur-3xl" />
        </div>

        <div className="max-w-6xl mx-auto h-[calc(100vh-6rem)] flex flex-col relative z-10">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 mb-4"
          >
            <div className="w-9 h-9 rounded-xl bg-[#4F8EF7]/20 border border-[#4F8EF7]/40 flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-[#4F8EF7]" />
            </div>
            <div>
              <h1 className="font-display text-xl font-bold text-[#F4EFE5]">Secure Chat</h1>
              <p className="text-xs text-[#A9A49A]">Private User–Advocate messaging</p>
            </div>
            {/* DB mode badge */}
            <div className="ml-auto flex items-center gap-2">
              {realtimeMode && (
                <span className={`text-[10px] px-2 py-1 rounded-full font-mono border ${
                  realtimeMode === 'postgresql'
                    ? 'text-[#6BD28E] bg-[#6BD28E]/10 border-[#6BD28E]/30'
                    : 'text-[#F97316] bg-[#F97316]/10 border-[#F97316]/30'
                }`}>
                  {realtimeMode === 'postgresql' ? '⚡ PostgreSQL' : '💾 SQLite (polling)'}
                </span>
              )}
              {isConnected
                ? <Wifi className="w-4 h-4 text-[#6BD28E]" />
                : <WifiOff className="w-4 h-4 text-[#E25C6F]" />
              }
            </div>
          </motion.div>

          {/* Chat body */}
          <div className="flex-1 flex gap-3 min-h-0 rounded-2xl overflow-hidden border border-[#2A2E2B] bg-[#151716]">
            {/* ── Conversation list ────────────────────────────────────────── */}
            <div className={`
              w-full sm:w-72 flex-shrink-0 flex flex-col border-r border-[#2A2E2B] bg-[#0F1211]
              ${activeConvId && !showConvList ? 'hidden sm:flex' : 'flex'}
            `}>
              <div className="px-4 py-3 border-b border-[#2A2E2B] flex items-center justify-between">
                <span className="text-xs font-semibold text-[#A9A49A] uppercase tracking-widest">Conversations</span>
                <button
                  id="chat-refresh-convs"
                  onClick={loadConversations}
                  className="p-1 rounded-lg hover:bg-[#1D211F] transition-colors"
                  aria-label="Refresh conversations"
                >
                  <RefreshCw className={`w-3.5 h-3.5 text-[#A9A49A] ${convLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {convLoading && (
                  <div className="flex items-center justify-center h-20">
                    <Loader2 className="w-5 h-5 text-[#4F8EF7] animate-spin" />
                  </div>
                )}
                {!convLoading && convError && (
                  <div className="p-3 rounded-xl bg-[#6E2634]/10 border border-[#6E2634]/30 text-xs text-[#E25C6F] flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" /> {convError}
                  </div>
                )}
                {!convLoading && conversations.length === 0 && !convError && (
                  <div className="text-center py-10 px-4">
                    <MessageCircle className="w-8 h-8 text-[#3B3A33] mx-auto mb-2" />
                    <p className="text-xs text-[#A9A49A]">No conversations yet.</p>
                    {currentRole === 'USER' && (
                      <p className="text-xs text-[#A9A49A] mt-1">
                        Contact support to be assigned an advocate.
                      </p>
                    )}
                  </div>
                )}
                {conversations.map((conv) => (
                  <ConvItem
                    key={conv.id}
                    conv={conv}
                    isActive={conv.id === activeConvId}
                    currentUserId={currentUserId}
                    onClick={() => selectConversation(conv.id)}
                  />
                ))}
              </div>
            </div>

            {/* ── Message area ─────────────────────────────────────────────── */}
            <div className={`
              flex-1 flex flex-col min-w-0
              ${activeConvId && !showConvList ? 'flex' : 'hidden sm:flex'}
            `}>
              {!activeConvId ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center px-8">
                  <div className="w-16 h-16 rounded-2xl bg-[#4F8EF7]/10 border border-[#4F8EF7]/20 flex items-center justify-center mb-4">
                    <MessageCircle className="w-8 h-8 text-[#4F8EF7]/50" />
                  </div>
                  <p className="text-[#F4EFE5] font-semibold mb-1">Select a conversation</p>
                  <p className="text-sm text-[#A9A49A]">Choose a conversation from the left panel to start messaging.</p>
                </div>
              ) : (
                <>
                  {/* Conversation header */}
                  <div className="px-4 py-3 border-b border-[#2A2E2B] flex items-center gap-3">
                    <button
                      className="sm:hidden p-1.5 rounded-lg hover:bg-[#1D211F] transition-colors"
                      onClick={() => setShowConvList(true)}
                      aria-label="Back to conversations"
                    >
                      <ChevronLeft className="w-4 h-4 text-[#A9A49A]" />
                    </button>
                    <div className="w-8 h-8 rounded-full bg-[#2A2E2B] border border-[#3B3A33] flex items-center justify-center">
                      <User className="w-4 h-4 text-[#A9A49A]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-[#F4EFE5]">
                        {activeConv?.user_id === currentUserId ? 'Your Advocate' : 'Client'}
                      </p>
                      <p className="text-[10px] text-[#A9A49A] truncate">
                        Conversation · {activeConvId.slice(0, 8)}…
                      </p>
                    </div>
                    <button
                      id="chat-refresh-msgs"
                      onClick={() => activeConvId && loadMessages(activeConvId)}
                      className="p-1.5 rounded-lg hover:bg-[#1D211F] transition-colors"
                      aria-label="Refresh messages"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 text-[#A9A49A] ${msgLoading ? 'animate-spin' : ''}`} />
                    </button>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto px-4 py-4" id="chat-messages-panel">
                    {/* Load more */}
                    {hasMore && (
                      <div className="flex justify-center mb-3">
                        <button
                          id="chat-load-more"
                          onClick={() => activeConvId && loadMessages(activeConvId, true)}
                          disabled={loadingMore}
                          className="text-xs text-[#4F8EF7] hover:text-[#7FB3FF] font-medium py-1 px-3 rounded-lg hover:bg-[#4F8EF7]/10 transition-colors disabled:opacity-50"
                        >
                          {loadingMore ? <Loader2 className="w-4 h-4 animate-spin inline" /> : 'Load older messages'}
                        </button>
                      </div>
                    )}

                    {msgLoading ? (
                      <div className="flex items-center justify-center h-32">
                        <Loader2 className="w-6 h-6 text-[#4F8EF7] animate-spin" />
                      </div>
                    ) : msgError ? (
                      <div className="flex items-center gap-2 p-3 rounded-xl bg-[#6E2634]/10 border border-[#6E2634]/30 text-xs text-[#E25C6F]">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" /> {msgError}
                      </div>
                    ) : messages.length === 0 ? (
                      <div className="flex flex-col items-center justify-center h-32 text-center">
                        <p className="text-sm text-[#A9A49A]">No messages yet. Send the first one!</p>
                      </div>
                    ) : (
                      <>
                        {groupedMessages.map(({ date, msgs }) => (
                          <div key={date}>
                            <DateSeparator label={date} />
                            {msgs.map((msg) => (
                              <MessageBubble
                                key={msg.id}
                                msg={msg}
                                isOwn={msg.sender_id === currentUserId}
                              />
                            ))}
                          </div>
                        ))}
                      </>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Send error */}
                  <AnimatePresence>
                    {sendError && (
                      <motion.div
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="mx-4 mb-2 px-3 py-2 rounded-xl bg-[#6E2634]/10 border border-[#6E2634]/30 text-xs text-[#E25C6F] flex items-center justify-between gap-2"
                      >
                        <span className="flex items-center gap-1.5">
                          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                          {sendError}
                        </span>
                        <button onClick={() => setSendError(null)} aria-label="Dismiss">
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Composer */}
                  <div className="px-4 pb-4 pt-2 border-t border-[#2A2E2B]">
                    <div className="flex items-end gap-2 bg-[#0F1211] rounded-2xl border border-[#2A2E2B] focus-within:border-[#4F8EF7]/50 transition-colors px-3 py-2">
                      {/* File upload button */}
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept={ALLOWED_EXTS.join(',')}
                        className="hidden"
                        id="chat-file-input"
                        onChange={handleFileChange}
                      />
                      <button
                        id="chat-attach-btn"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploading || !activeConvId}
                        className="p-1.5 rounded-lg hover:bg-[#1D211F] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors disabled:opacity-40 flex-shrink-0"
                        aria-label="Attach file"
                      >
                        {uploading
                          ? <Loader2 className="w-4 h-4 animate-spin" />
                          : <Paperclip className="w-4 h-4" />
                        }
                      </button>

                      {/* Text area */}
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
                        placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
                        rows={1}
                        maxLength={4000}
                        className="flex-1 bg-transparent resize-none text-sm text-[#F4EFE5] placeholder-[#A9A49A]/50 outline-none py-1 max-h-32 overflow-y-auto"
                        aria-label="Message input"
                      />

                      {/* Send button */}
                      <button
                        id="chat-send-btn"
                        onClick={handleSend}
                        disabled={!body.trim() || sending || !activeConvId}
                        className="p-1.5 rounded-xl bg-[#4F8EF7] hover:bg-[#6FA4FF] text-white disabled:opacity-40 transition-all flex-shrink-0"
                        aria-label="Send message"
                      >
                        {sending
                          ? <Loader2 className="w-4 h-4 animate-spin" />
                          : <Send className="w-4 h-4" />
                        }
                      </button>
                    </div>
                    <p className="text-[10px] text-[#A9A49A]/50 mt-1.5 text-right">
                      {body.length}/4000 · Shift+Enter for new line
                    </p>
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
