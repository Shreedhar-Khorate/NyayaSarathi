'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  Newspaper,
  ExternalLink,
  RefreshCw,
  Clock,
  Building2,
  Landmark,
  ShieldAlert,
  AlertCircle,
  BookOpen,
  Filter,
  Search,
  CheckCircle2,
  Info,
  Calendar,
  Share2,
  Check,
  ChevronDown,
  ChevronUp,
  Layers,
  FileText,
  Tag,
} from 'lucide-react';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import {
  fetchLegalNews,
  type NewsArticle,
  type NewsStoryGroup,
  type OfficialSource,
  type NewsResponse,
} from '@/lib/auth';

// ── Category definitions with metadata ────────────────────────────────────────

interface CategoryMeta {
  id: string;
  label: string;
  description: string;
  icon: typeof Scale;
}

const CATEGORIES: CategoryMeta[] = [
  {
    id: 'all',
    label: 'All Indian Law',
    description: 'Supreme Court, High Courts, legislative updates, and judiciary affairs',
    icon: Newspaper,
  },
  {
    id: 'supreme-court',
    label: 'Supreme Court',
    description: 'Constitutional bench orders, landmark rulings, and registry circulars',
    icon: Landmark,
  },
  {
    id: 'high-courts',
    label: 'High Courts',
    description: 'State High Court judgments, interim orders, and division bench rulings',
    icon: Building2,
  },
  {
    id: 'legal',
    label: 'Legal Reforms',
    description: 'Statutory amendments, procedural reforms, and Bar Council updates',
    icon: BookOpen,
  },
  {
    id: 'government',
    label: 'Legislation & Govt',
    description: 'Parliamentary acts, notifications, gazettes, and Ministry circulars',
    icon: Scale,
  },
];

// Format ISO date into user-friendly string
function formatPublishDate(dateStr?: string | null): string {
  if (!dateStr) return 'Recently';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return 'Recently';

    const now = new Date();
    const diffHours = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60));

    if (diffHours < 1) return 'Just now';
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;

    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return 'Recently';
  }
}

export default function LegalNewsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [data, setData] = useState<NewsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);
  const [expandedStories, setExpandedStories] = useState<Record<string, boolean>>({});

  // Load news
  const loadNews = useCallback(async (cat: string, isRefresh: boolean = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const resp = await fetchLegalNews(cat, 16);
      setData(resp);
    } catch (err: any) {
      setError(
        err?.message || 'Failed to fetch legal news. Please check connection and try again.'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadNews(selectedCategory, false);
  }, [selectedCategory, loadNews]);

  // Handle Share / Copy Link
  const handleCopyLink = (url: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(url);
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl(null), 2000);
  };

  // Toggle expanded related coverage inside a story group
  const toggleStoryExpand = (storyId: string) => {
    setExpandedStories((prev) => ({
      ...prev,
      [storyId]: !prev[storyId],
    }));
  };

  // Filter story groups by search query
  const filteredStories = useMemo(() => {
    if (!data?.stories || data.stories.length === 0) return [];

    // Deduplicate stories by story_id as safeguard
    const seenStoryIds = new Set<string>();
    const safeStories = data.stories.filter((story) => {
      const id = (story.story_id || story.primary_article?.url || story.title).trim();
      if (!id || seenStoryIds.has(id)) return false;
      seenStoryIds.add(id);
      return true;
    });

    if (!searchQuery.trim()) return safeStories;

    const q = searchQuery.toLowerCase().trim();
    return safeStories.filter((story) => {
      const titleMatch = story.title.toLowerCase().includes(q);
      const descMatch =
        story.primary_article?.description?.toLowerCase().includes(q) ?? false;
      const sourceMatch =
        story.primary_article?.source_name.toLowerCase().includes(q) ?? false;
      const entityMatch = story.key_entities.some((e) =>
        e.toLowerCase().includes(q)
      );
      const relatedMatch = story.related_articles.some(
        (r) =>
          r.title.toLowerCase().includes(q) ||
          r.source_name.toLowerCase().includes(q) ||
          (r.description?.toLowerCase().includes(q) ?? false)
      );
      return titleMatch || descMatch || sourceMatch || entityMatch || relatedMatch;
    });
  }, [data, searchQuery]);

  // Backward compatibility fallback for flat articles if stories are empty
  const filteredArticles = useMemo(() => {
    if (filteredStories.length > 0) return [];
    if (!data?.articles) return [];

    const seen = new Set<string>();
    const safeArticles = data.articles.filter((art) => {
      const key = (art.url || art.title || '').trim().toLowerCase();
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    if (!searchQuery.trim()) return safeArticles;

    const q = searchQuery.toLowerCase().trim();
    return safeArticles.filter((art) => {
      const titleMatch = art.title.toLowerCase().includes(q);
      const descMatch = art.description?.toLowerCase().includes(q) ?? false;
      const sourceMatch = art.source_name.toLowerCase().includes(q);
      return titleMatch || descMatch || sourceMatch;
    });
  }, [data, searchQuery, filteredStories.length]);

  const currentCategoryMeta = useMemo(() => {
    return (
      CATEGORIES.find((c) => c.id === selectedCategory) || {
        id: selectedCategory,
        label: 'Legal Updates',
        description: 'Latest judicial and statutory updates',
        icon: Newspaper,
      }
    );
  }, [selectedCategory]);

  const displayCount =
    filteredStories.length > 0 ? filteredStories.length : filteredArticles.length;

  return (
    <div className="min-h-screen bg-[#151716] text-[#F4EFE5] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-20">
        {/* Header Hero Section */}
        <section className="relative mb-10 overflow-hidden rounded-2xl border border-[#3B3A33] bg-[#1D211F]/80 p-8 sm:p-10 backdrop-blur-md shadow-2xl">
          <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-[#B59A68]/5 blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-80 h-80 rounded-full bg-[#6E2634]/10 blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="max-w-3xl">
              <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-[#F4EFE5] leading-[1.15]">
                Indian Legal & Judiciary News
              </h1>
              <p className="mt-3 font-sans text-sm sm:text-base text-[#A9A49A] leading-relaxed max-w-2xl">
                Real-time coverage of Supreme Court verdicts, High Court orders, legislative
                amendments, and official gazettes grouped into unified legal matter story cards.
              </p>
            </div>

            {/* Quick Actions & Freshness */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
              {data && (
                <div className="flex items-center gap-2 text-xs text-[#A9A49A] bg-[#242925] border border-[#3B3A33] px-3 py-1.5 rounded-lg">
                  <Clock className="w-3.5 h-3.5 text-[#B59A68]" />
                  <span>
                    {data.cached ? 'Cached (5m TTL)' : 'Live Feed'} • {data.total} legal matters
                  </span>
                </div>
              )}
              <button
                onClick={() => loadNews(selectedCategory, true)}
                disabled={loading || refreshing}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-[#B59A68]/40 bg-[#B59A68]/10 text-xs font-semibold text-[#B59A68] hover:bg-[#B59A68]/20 transition-all active:scale-95 disabled:opacity-50"
                title="Refresh news"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
              </button>
            </div>
          </div>

          {/* Search bar & Category filters */}
          <div className="mt-8 pt-6 border-t border-[#3B3A33]/60 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            {/* Category Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 lg:pb-0 scrollbar-none">
              {CATEGORIES.map((cat) => {
                const isSelected = selectedCategory === cat.id;
                const IconComponent = cat.icon;
                return (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all duration-200 ${
                      isSelected
                        ? 'bg-[#B59A68] text-[#151716] font-semibold shadow-md'
                        : 'bg-[#242925] text-[#A9A49A] hover:text-[#F4EFE5] hover:bg-[#3B3A33]/50 border border-[#3B3A33]'
                    }`}
                  >
                    <IconComponent className="w-3.5 h-3.5" />
                    <span>{cat.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Keyword Filter Input */}
            <div className="relative min-w-[240px] sm:min-w-[280px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A9A49A]" />
              <input
                type="text"
                placeholder="Filter legal matters or parties..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-1.5 bg-[#151716] border border-[#3B3A33] rounded-lg text-xs text-[#F4EFE5] placeholder-[#A9A49A]/60 focus:outline-none focus:border-[#B59A68] transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-[#A9A49A] hover:text-[#F4EFE5]"
                >
                  ✕
                </button>
              )}
            </div>
          </div>
        </section>

        {/* Content Layout: Stories Grid + Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Main Column: Stories Cards (8 cols) */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            {/* Active Category Heading */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-display text-xl sm:text-2xl font-semibold text-[#F4EFE5]">
                  {currentCategoryMeta.label}
                </h2>
                <p className="text-xs text-[#A9A49A] mt-0.5">
                  {currentCategoryMeta.description}
                </p>
              </div>
              <span className="text-xs text-[#A9A49A]">
                Showing {displayCount} {displayCount === 1 ? 'matter' : 'matters'}
              </span>
            </div>

            {/* Loading Skeleton State */}
            {loading && (
              <div className="flex flex-col gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="p-6 rounded-xl border border-[#3B3A33] bg-[#1D211F]/60 animate-pulse flex flex-col gap-3.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="h-4 w-28 bg-[#3B3A33] rounded" />
                      <div className="h-4 w-16 bg-[#3B3A33] rounded" />
                    </div>
                    <div className="h-6 w-full bg-[#3B3A33] rounded" />
                    <div className="h-4 w-4/5 bg-[#3B3A33]/70 rounded" />
                    <div className="h-10 w-full bg-[#3B3A33]/40 rounded mt-2" />
                    <div className="flex items-center justify-between pt-3 border-t border-[#3B3A33]/40">
                      <div className="h-3 w-32 bg-[#3B3A33] rounded" />
                      <div className="h-3 w-16 bg-[#3B3A33] rounded" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Error State */}
            {!loading && error && (
              <div className="p-8 rounded-xl border border-[#6E2634] bg-[#6E2634]/15 text-center flex flex-col items-center gap-3">
                <AlertCircle className="w-8 h-8 text-[#E25C6F]" />
                <h3 className="font-display text-lg font-semibold text-[#F4EFE5]">
                  Unable to load legal news
                </h3>
                <p className="text-xs text-[#A9A49A] max-w-md">{error}</p>
                <button
                  onClick={() => loadNews(selectedCategory, false)}
                  className="mt-2 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#6E2634] text-xs font-semibold text-[#F4EFE5] hover:bg-[#8A3545] transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry Request</span>
                </button>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && displayCount === 0 && (
              <div className="p-12 rounded-xl border border-[#3B3A33] bg-[#1D211F]/40 text-center flex flex-col items-center gap-3">
                <Newspaper className="w-10 h-10 text-[#B59A68]/60" />
                <h3 className="font-display text-lg font-semibold text-[#F4EFE5]">
                  No legal matters found
                </h3>
                <p className="text-xs text-[#A9A49A] max-w-md">
                  {searchQuery
                    ? `No legal matters match the keyword "${searchQuery}". Try a different search or clear the filter.`
                    : 'No articles are currently available in this category. Try selecting "All Indian Law".'}
                </p>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="mt-2 text-xs text-[#B59A68] hover:underline"
                  >
                    Clear search filter
                  </button>
                )}
              </div>
            )}

            {/* Story Groups List */}
            {!loading && !error && filteredStories.length > 0 && (
              <div className="flex flex-col gap-5">
                {filteredStories.map((story, idx) => {
                  const isExpanded = expandedStories[story.story_id] ?? false;
                  const hasRelated = story.related_articles && story.related_articles.length > 0;
                  const lead = story.primary_article;

                  return (
                    <motion.article
                      key={story.story_id || idx}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25, delay: Math.min(idx * 0.04, 0.4) }}
                      className="group relative flex flex-col rounded-xl border border-[#3B3A33] bg-[#1D211F]/80 hover:border-[#B59A68]/50 transition-all duration-300 p-6 shadow-xl overflow-hidden"
                    >
                      {/* Top Header: Source, Recency, Matter Chips & Coverage Count */}
                      <div className="flex flex-wrap items-center justify-between gap-2.5 pb-3 border-b border-[#3B3A33]/50 text-xs">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-[#242925] border border-[#3B3A33] text-[#B59A68] font-medium tracking-wide">
                            <Building2 className="w-3 h-3 text-[#B59A68]" />
                            <span>{lead.source_name}</span>
                          </span>

                          {story.key_entities && story.key_entities.length > 0 && (
                            <div className="flex items-center gap-1.5 flex-wrap">
                              {story.key_entities.map((ent) => (
                                <span
                                  key={ent}
                                  className="px-2 py-0.5 rounded bg-[#151716] text-[11px] text-[#A9A49A] border border-[#3B3A33]/70"
                                >
                                  {ent}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          {story.coverage_count > 1 && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#B59A68]/10 border border-[#B59A68]/30 text-[11px] font-semibold text-[#B59A68]">
                              <Layers className="w-3 h-3 text-[#B59A68]" />
                              <span>{story.coverage_count} Reports</span>
                            </span>
                          )}

                          <span className="flex items-center gap-1 text-[11px] text-[#A9A49A]">
                            <Clock className="w-3 h-3" />
                            <span>{formatPublishDate(story.last_updated || lead.published_at)}</span>
                          </span>
                        </div>
                      </div>

                      {/* Lead Story Title & Snippet */}
                      <div className="mt-3.5">
                        <a
                          href={lead.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block group/link"
                        >
                          <h3 className="font-display text-lg sm:text-xl font-semibold text-[#F4EFE5] group-hover/link:text-[#B59A68] transition-colors leading-snug">
                            {story.title}
                          </h3>
                        </a>

                        {lead.description && (
                          <p className="mt-2 text-xs sm:text-sm text-[#A9A49A] leading-relaxed font-sans">
                            {lead.description}
                          </p>
                        )}
                      </div>

                      {/* Related Legal Updates & Distinct Publisher Angles */}
                      {hasRelated && (
                        <div className="mt-4 pt-3.5 border-t border-[#3B3A33]/60">
                          <button
                            onClick={() => toggleStoryExpand(story.story_id)}
                            className="w-full flex items-center justify-between text-xs font-semibold text-[#B59A68] hover:text-[#DED5C4] transition-colors py-1"
                          >
                            <span className="flex items-center gap-1.5">
                              <Layers className="w-3.5 h-3.5" />
                              <span>
                                {story.related_articles.length}{' '}
                                {story.related_articles.length === 1
                                  ? 'Related Legal Update & Publisher'
                                  : 'Related Legal Updates & Coverage'}
                              </span>
                            </span>
                            {isExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5 text-[#B59A68]" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5 text-[#B59A68]" />
                            )}
                          </button>

                          <AnimatePresence>
                            {isExpanded && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.2 }}
                                className="mt-3 flex flex-col gap-2.5 overflow-hidden"
                              >
                                {story.related_articles.map((relArt, rIdx) => (
                                  <div
                                    key={relArt.url || rIdx}
                                    className="p-3 rounded-lg bg-[#151716]/80 border border-[#3B3A33]/80 hover:border-[#B59A68]/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-2.5"
                                  >
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2 text-[11px] text-[#A9A49A] mb-1">
                                        <span className="font-semibold text-[#B59A68]">
                                          {relArt.source_name}
                                        </span>
                                        <span>•</span>
                                        <span>{formatPublishDate(relArt.published_at)}</span>
                                      </div>
                                      <a
                                        href={relArt.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs font-medium text-[#F4EFE5] hover:text-[#B59A68] transition-colors line-clamp-2 block leading-snug"
                                      >
                                        {relArt.title}
                                      </a>
                                    </div>

                                    <a
                                      href={relArt.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 text-[11px] font-medium text-[#B59A68] hover:text-[#DED5C4] shrink-0 self-start sm:self-center"
                                    >
                                      <span>Read</span>
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  </div>
                                ))}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      )}

                      {/* Bottom Action Bar */}
                      <div className="mt-4 pt-3 border-t border-[#3B3A33]/50 flex items-center justify-between text-xs text-[#A9A49A]">
                        <a
                          href={lead.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-[#B59A68] hover:text-[#DED5C4] font-semibold transition-colors"
                        >
                          <span>Read primary coverage</span>
                          <ExternalLink className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                        </a>

                        <button
                          onClick={(e) => handleCopyLink(lead.url, e)}
                          className="inline-flex items-center gap-1 text-[#A9A49A] hover:text-[#F4EFE5] transition-colors p-1 rounded"
                          title="Copy article link"
                        >
                          {copiedUrl === lead.url ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-[11px] text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Share2 className="w-3.5 h-3.5" />
                              <span className="text-[11px]">Share</span>
                            </>
                          )}
                        </button>
                      </div>
                    </motion.article>
                  );
                })}
              </div>
            )}

            {/* Fallback to Flat Articles Grid (if stories are empty) */}
            {!loading && !error && filteredStories.length === 0 && filteredArticles.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredArticles.map((art, idx) => (
                  <motion.article
                    key={art.url || idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25, delay: Math.min(idx * 0.04, 0.4) }}
                    className="group relative flex flex-col justify-between rounded-xl border border-[#3B3A33] bg-[#1D211F]/70 hover:bg-[#1D211F] hover:border-[#B59A68]/50 transition-all duration-300 p-5 shadow-lg overflow-hidden"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 text-xs mb-2.5">
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-[#242925] border border-[#3B3A33] text-[#B59A68] font-medium tracking-wide">
                          <Building2 className="w-3 h-3 text-[#B59A68]" />
                          <span className="truncate max-w-[140px]">{art.source_name}</span>
                        </span>

                        <span className="flex items-center gap-1 text-[11px] text-[#A9A49A]">
                          <Clock className="w-3 h-3" />
                          <span>{formatPublishDate(art.published_at)}</span>
                        </span>
                      </div>

                      <a
                        href={art.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block group/link"
                      >
                        <h3 className="font-display text-base font-semibold text-[#F4EFE5] group-hover/link:text-[#B59A68] transition-colors leading-snug line-clamp-3">
                          {art.title}
                        </h3>
                      </a>

                      {art.description && (
                        <p className="mt-2 text-xs text-[#A9A49A] line-clamp-3 leading-relaxed font-sans">
                          {art.description}
                        </p>
                      )}
                    </div>

                    <div className="mt-4 pt-3 border-t border-[#3B3A33]/50 flex items-center justify-between text-xs text-[#A9A49A]">
                      <a
                        href={art.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[#B59A68] hover:text-[#DED5C4] font-medium transition-colors"
                      >
                        <span>Read full coverage</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>

                      <button
                        onClick={(e) => handleCopyLink(art.url, e)}
                        className="inline-flex items-center gap-1 text-[#A9A49A] hover:text-[#F4EFE5] transition-colors p-1 rounded"
                      >
                        {copiedUrl === art.url ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-[11px] text-emerald-400">Copied</span>
                          </>
                        ) : (
                          <>
                            <Share2 className="w-3.5 h-3.5" />
                            <span className="text-[11px]">Share</span>
                          </>
                        )}
                      </button>
                    </div>
                  </motion.article>
                ))}
              </div>
            )}
          </div>

          {/* Right Column: Official Sources & Legal Disclaimer (4 cols) */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            {/* Official Portals Widget */}
            <div className="rounded-xl border border-[#3B3A33] bg-[#1D211F]/80 p-6 backdrop-blur-md shadow-xl">
              <div className="flex items-center gap-2.5 pb-4 border-b border-[#3B3A33]">
                <div className="p-2 rounded-lg bg-[#B59A68]/10 text-[#B59A68] border border-[#B59A68]/30">
                  <Landmark className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-display text-base font-semibold text-[#F4EFE5]">
                    Official Court Portals
                  </h3>
                  <p className="text-[11px] text-[#A9A49A]">
                    Primary judicial databases & statutory gazettes
                  </p>
                </div>
              </div>

              <div className="mt-4 flex flex-col gap-3">
                {(data?.official_sources || []).map((source) => (
                  <a
                    key={source.url}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group block p-3 rounded-lg border border-[#3B3A33]/70 bg-[#242925]/60 hover:bg-[#242925] hover:border-[#B59A68]/40 transition-all duration-200"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-display text-sm font-semibold text-[#F4EFE5] group-hover:text-[#B59A68] transition-colors">
                        {source.name}
                      </span>
                      <ExternalLink className="w-3.5 h-3.5 text-[#A9A49A] group-hover:text-[#B59A68] transition-all shrink-0 mt-0.5" />
                    </div>
                    <p className="text-[11px] text-[#A9A49A] mt-1 leading-relaxed">
                      {source.description}
                    </p>
                  </a>
                ))}
              </div>
            </div>

            {/* Regulatory & Evidentiary Disclaimer */}
            <div className="rounded-xl border border-[#B59A68]/30 bg-[#242925]/50 p-5 text-xs text-[#A9A49A] flex flex-col gap-2.5">
              <div className="flex items-center gap-2 text-[#B59A68] font-semibold">
                <Info className="w-4 h-4 shrink-0" />
                <span className="uppercase tracking-wider text-[11px]">Legal Clarity Notice</span>
              </div>
              <p className="leading-relaxed">
                {data?.disclaimer ||
                  'The articles listed are sourced from GNews and represent media coverage only. NyayaSarathi does not guarantee accuracy, completeness, or legal validity. Always verify information through official court records.'}
              </p>
              <div className="pt-2 border-t border-[#3B3A33]/40 flex items-center justify-between text-[11px] text-[#A9A49A]">
                <span>Data Source: GNews API</span>
                <span className="text-[#B59A68]">Indian Jurisdiction</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
