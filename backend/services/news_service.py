"""
NyayaSarathi News Service — GNews API integration with in-memory TTL cache.

Features:
- Predefined category → GNews query mapping for Indian judiciary/legal news
- In-memory TTL cache (5-minute default) to avoid quota exhaustion
- Response normalisation and URL deduplication
- Official Indian court portal links (curated, stable)
- No raw API keys or stack traces exposed to callers
"""

from __future__ import annotations

import os
import logging
import hashlib
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
import urllib.request
import urllib.parse
import json
import re

from schemas.news import NewsArticle, NewsStoryGroup, OfficialSource, NewsResponse

log = logging.getLogger("nyayasarathi.news_service")

# ── Configuration ─────────────────────────────────────────────────────────────

GNEWS_API_KEY: str = os.environ.get("GNEWS_API_KEY", "")
GNEWS_BASE_URL: str = "https://gnews.io/api/v4/search"
CACHE_TTL_SECONDS: int = 300          # 5 minutes
MAX_ARTICLES_LIMIT: int = 20
DEFAULT_LIMIT: int = 10

# ── Category → GNews query mapping ───────────────────────────────────────────

CATEGORY_QUERY_MAP: Dict[str, str] = {
    "all":           "India Supreme Court OR High Court OR Indian judiciary OR Indian law",
    "supreme-court": "India Supreme Court judgment OR ruling OR verdict",
    "high-courts":   "India High Court judgment OR order OR ruling",
    "legal":         "India legal news OR Indian law amendment OR legal reform India",
    "government":    "India government legislation OR ordinance OR law ministry India",
}

VALID_CATEGORIES = set(CATEGORY_QUERY_MAP.keys())

# ── Official Indian Judiciary / Government Portals ────────────────────────────

OFFICIAL_SOURCES: List[OfficialSource] = [
    OfficialSource(
        name="Supreme Court of India",
        url="https://www.sci.gov.in/",
        description="Official portal of the Supreme Court of India — judgments, cause lists, and filings.",
    ),
    OfficialSource(
        name="eCourts — Judgments Search",
        url="https://judgments.ecourts.gov.in/",
        description="Search and download judgments from all District and High Courts via the eCourts platform.",
    ),
    OfficialSource(
        name="India Kanoon",
        url="https://indiankanoon.org/",
        description="Free full-text search of Indian court judgments and statutes.",
    ),
    OfficialSource(
        name="Ministry of Law & Justice",
        url="https://lawmin.gov.in/",
        description="Official portal for legislative drafting, legal affairs, and justice delivery.",
    ),
    OfficialSource(
        name="Legislative Department — Acts of Parliament",
        url="https://legislative.gov.in/acts-of-parliament-from-1836-to-2010",
        description="Official repository of Central Acts enacted by Parliament of India.",
    ),
    OfficialSource(
        name="National Legal Services Authority (NALSA)",
        url="https://nalsa.gov.in/",
        description="Legal aid services and schemes for marginalised citizens.",
    ),
]

# ── In-memory TTL cache ───────────────────────────────────────────────────────

_cache: Dict[str, Tuple[float, NewsResponse]] = {}


def _cache_key(category: str, limit: int) -> str:
    raw = f"{category}:{limit}"
    return hashlib.md5(raw.encode()).hexdigest()


def _get_cached(key: str) -> Optional[NewsResponse]:
    if key in _cache:
        stored_at, response = _cache[key]
        if time.monotonic() - stored_at < CACHE_TTL_SECONDS:
            return response
        del _cache[key]
    return None


def _set_cache(key: str, response: NewsResponse) -> None:
    _cache[key] = (time.monotonic(), response)


def _clear_expired_cache() -> None:
    now = time.monotonic()
    expired = [k for k, (t, _) in _cache.items() if now - t >= CACHE_TTL_SECONDS]
    for k in expired:
        del _cache[k]


# ── GNews fetcher ─────────────────────────────────────────────────────────────

def _fetch_gnews(query: str, limit: int) -> List[Dict[str, Any]]:
    """Call GNews /search and return raw article dicts. Raises on HTTP / network error."""
    if not GNEWS_API_KEY:
        log.warning("GNEWS_API_KEY is not set; returning empty article list.")
        return []

    params = urllib.parse.urlencode({
        "q": query,
        "lang": "en",
        "country": "in",
        "max": min(limit, MAX_ARTICLES_LIMIT),
        "apikey": GNEWS_API_KEY,
    })
    url = f"{GNEWS_BASE_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NyayaSarathi/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return data.get("articles", [])
    except urllib.error.HTTPError as exc:
        log.error("GNews HTTP error %s fetching '%s'", exc.code, query)
        return []
    except Exception as exc:
        log.error("GNews fetch failed for '%s': %s", query, exc)
        return []


# ── Lightweight Deduplication Pipeline ───────────────────────────────────────

# Tracking query parameters to strip from URLs during canonicalization
TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "utm_name",
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref",
    "source",
    "cmpid",
    "_ga",
    "_gl",
    "ved",
    "usqp",
}

# Trailing publisher suffixes commonly attached to headlines by news syndicators
PUBLISHER_SUFFIX_RE = re.compile(
    r"\s*[-–—|]\s*(?:"
    r"ANI(?:\s+News)?|Devdiscourse|The\s+Hindu|NDTV|Times\s+of\s+India|TOI|"
    r"Hindustan\s+Times|HT|Live\s*Law|Bar\s*(?:and|&)\s*Bench|Indian\s+Express|"
    r"The\s+Print|The\s+Wire|Scroll(?:\.in)?|Firstpost|News18|Outlook\s+India|"
    r"India\s+Today|Zee\s+News|ABP\s+Live|Business\s+Standard|Economic\s+Times|"
    r"ET|Deccan\s+Herald|LatestLY|Republic\s+World|PTI|WION"
    r")[\w\s.]*$",
    re.IGNORECASE,
)

GENERIC_PUBLISHER_SUFFIX_RE = re.compile(r"\s+[-–—|]\s+[A-Za-z0-9\s.]{2,30}$")

LEGAL_ACRONYMS = {
    # Apex & High Courts
    r"\bsc\b": "supreme court",
    r"\bhc\b": "high court",
    r"\bcji\b": "chief justice of india",
    r"\bdhc\b": "delhi high court",
    r"\bbhc\b": "bombay high court",
    r"\bmhc\b": "madras high court",
    r"\bchc\b": "calcutta high court",
    r"\bahc\b": "allahabad high court",
    r"\bkhc\b": "karnataka high court",
    r"\bphhc\b": "punjab and haryana high court",
    # Legal Reforms & Criminal Codes
    r"\bbns\b": "bharatiya nyaya sanhita",
    r"\bbnss\b": "bharatiya nagarik suraksha sanhita",
    r"\bbsa\b": "bharatiya sakshya adhiniyam",
    r"\bipc\b": "indian penal code",
    r"\bcrpc\b": "code of criminal procedure",
    r"\bcpc\b": "code of civil procedure",
    r"\bbci\b": "bar council of india",
    # Tribunals & Commissions
    r"\bnclt\b": "national company law tribunal",
    r"\bnclat\b": "national company law appellate tribunal",
    r"\bcci\b": "competition commission of india",
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "as", "is", "was", "are", "were", "be", "been", "being", "it",
    "its", "this", "that", "into", "over", "after", "before", "about", "against",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
}

# Mutually exclusive judicial outcomes / stages that must NOT be merged
OPPOSING_VERB_PAIRS = [
    (
        {"grants", "granted", "granting", "allows", "allowed", "allowing"},
        {"denies", "denied", "denying", "rejects", "rejected", "rejecting", "dismisses", "dismissed", "dismissing", "refuses", "refused"},
    ),
    (
        {"acquits", "acquitted", "acquitting"},
        {"convicts", "convicted", "convicting"},
    ),
    (
        {"upholds", "upheld", "upholding"},
        {"strikes", "struck", "quashes", "quashed", "quashing"},
    ),
]


def canonicalize_url(url: str) -> str:
    """
    1. Canonical URL check:
       Normalizes URLs by removing tracking parameters (utm_*, fbclid, gclid, etc.),
       fragments (#...), and unnecessary trailing slashes.
       Preserves meaningful query parameters and sorts them deterministically.
    """
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urllib.parse.urlsplit(raw)
        scheme = (parsed.scheme or "https").lower()
        netloc = parsed.netloc.lower()

        # Remove trailing slash from path (unless it is root '/')
        path = parsed.path
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")

        # Filter out tracking query parameters
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        clean_pairs = [
            (k, v) for k, v in query_pairs
            if k.lower() not in TRACKING_QUERY_PARAMS
        ]
        clean_pairs.sort()
        clean_query = urllib.parse.urlencode(clean_pairs)

        return urllib.parse.urlunsplit((scheme, netloc, path, clean_query, ""))
    except Exception:
        return raw.rstrip("/")


def normalize_title(title: str) -> str:
    """
    2. Exact title check:
       Normalizes titles by lowercasing, trimming whitespace, expanding standard
       legal acronyms, removing known publisher/syndication suffixes, and removing
       insignificant punctuation.
    """
    text = (title or "").strip()
    if not text:
        return ""

    # Strip publisher suffixes (e.g. ' - ANI News', ' | Devdiscourse')
    text = PUBLISHER_SUFFIX_RE.sub("", text)
    if len(text) > 35:
        text = GENERIC_PUBLISHER_SUFFIX_RE.sub("", text)

    text = text.lower()

    # Standardize legal acronyms
    for pattern, replacement in LEGAL_ACRONYMS.items():
        text = re.sub(pattern, replacement, text)

    # Remove insignificant punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def _extract_content_tokens(norm_title: str) -> set[str]:
    words = norm_title.split()
    return {w for w in words if len(w) > 1 and w not in STOPWORDS}


def _extract_numbers(norm_title: str) -> set[str]:
    return set(re.findall(r"\b\d+\b", norm_title))


def are_near_duplicate_titles(title_a: str, title_b: str, threshold: float = 0.78) -> bool:
    """
    3. Near-duplicate titles check:
       Detects minor title variations using token similarity on content words.
       Safe guards:
       - Preserves distinct court cases by checking numeric tokens (e.g. distinct sections or dates).
       - Preserves distinct orders by checking opposing judicial outcome verbs.
       - Disallows short titles (< 4 content tokens) from fuzzy matching.
    """
    norm_a = normalize_title(title_a)
    norm_b = normalize_title(title_b)

    if not norm_a or not norm_b:
        return False
    if norm_a == norm_b:
        return True

    tokens_a = _extract_content_tokens(norm_a)
    tokens_b = _extract_content_tokens(norm_b)

    # Short headlines must match exactly to avoid merging distinct short updates
    if len(tokens_a) < 4 or len(tokens_b) < 4:
        return False

    # Check numeric mismatch (distinct case sections, dates, or benches)
    nums_a = _extract_numbers(norm_a)
    nums_b = _extract_numbers(norm_b)
    if nums_a and nums_b and nums_a != nums_b:
        return False

    # Check opposing judicial outcomes (e.g. grants bail vs denies bail)
    for set_pos, set_neg in OPPOSING_VERB_PAIRS:
        if (tokens_a & set_pos and tokens_b & set_neg) or (tokens_a & set_neg and tokens_b & set_pos):
            return False

    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    jaccard = intersection / union if union > 0 else 0.0

    if jaccard < threshold:
        return False

    # Additional safety against distinct named entities in asymmetric tokens
    diff_a = tokens_a - tokens_b
    diff_b = tokens_b - tokens_a
    if len(diff_a) >= 2 and len(diff_b) >= 2:
        return False

    return True


def calculate_article_quality(article: NewsArticle) -> float:
    """
    4. Cross-publisher duplicate quality scoring:
       Scores article quality to retain the single best representative article:
       - Prefer valid HTTP/HTTPS URLs.
       - Prefer articles with useful descriptions over empty stubs.
       - Prefer valid publication timestamps.
       - Prefer established, verifiable publishers.
       - Use publication recency as a tie-breaker, not the sole criterion.
    """
    score = 0.0

    # 1. URL validity & cleanliness
    url = (article.url or "").strip()
    if url.startswith("https://"):
        score += 20.0
    elif url.startswith("http://"):
        score += 10.0
    else:
        score -= 10.0

    # 2. Useful description
    desc = (article.description or "").strip()
    if desc:
        score += 15.0
        desc_len = len(desc)
        if desc_len >= 80:
            score += 15.0
        elif desc_len >= 40:
            score += 8.0

        if desc.lower() == (article.title or "").strip().lower():
            score -= 10.0
    else:
        score -= 10.0

    # 3. Known, reputable publisher name
    source = (article.source_name or "").strip()
    if source and source.lower() not in {"unknown source", "unknown", "untitled", "news"}:
        score += 15.0
        reputable = {
            "live law", "livelaw", "bar and bench", "bar & bench",
            "supreme court observer", "the hindu", "indian express",
            "hindustan times", "times of india", "ndtv", "ani",
            "pti", "devdiscourse", "the print", "the wire", "scroll.in"
        }
        if any(rep in source.lower() for rep in reputable):
            score += 5.0
    else:
        score -= 10.0

    # 4. Valid image
    if (article.image_url or "").strip().startswith("http"):
        score += 5.0

    # 5. Valid publication date + recency tie-breaker
    pub_at = (article.published_at or "").strip()
    recency_tiebreaker = 0.0
    if pub_at:
        score += 10.0
        try:
            clean_ts = pub_at.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            # Recency tiebreaker adds 0.01 - 2.5 points, deciding ties between
            # articles of comparable content quality
            recency_tiebreaker = (dt.timestamp() / 1e9) * 1.5
        except Exception:
            pass
    else:
        score -= 5.0

    return score + recency_tiebreaker


def deduplicate_articles(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Lightweight, deterministic multi-stage deduplication.
    Applies Canonical URL, Exact Title, and Near-Duplicate Title checks.
    Selects the best quality representative and preserves original publisher and URL.
    """
    if not articles:
        return []

    # Precompute metadata and quality scores
    scored = []
    for art in articles:
        canon_url = canonicalize_url(art.url)
        norm_title = normalize_title(art.title)
        quality = calculate_article_quality(art)
        scored.append({
            "article": art,
            "canon_url": canon_url,
            "norm_title": norm_title,
            "quality": quality,
        })

    # Sort candidates by quality descending (highest quality considered first)
    scored.sort(key=lambda x: x["quality"], reverse=True)

    selected: List[Dict[str, Any]] = []

    for candidate in scored:
        c_art = candidate["article"]
        c_url = candidate["canon_url"]
        c_title = candidate["norm_title"]
        orig_title = c_art.title

        is_duplicate = False
        for rep in selected:
            # 1. Canonical URL match
            if c_url and rep["canon_url"] and c_url == rep["canon_url"]:
                is_duplicate = True
                break

            # 2. Exact normalized title match
            if c_title and rep["norm_title"] and c_title == rep["norm_title"]:
                is_duplicate = True
                break

            # 3. Near-duplicate title match
            if are_near_duplicate_titles(orig_title, rep["article"].title):
                is_duplicate = True
                break

        if not is_duplicate:
            selected.append(candidate)

    # Maintain recency ordering for the final curated list
    def _sort_key(item: Dict[str, Any]) -> float:
        pub_at = (item["article"].published_at or "").strip()
        if pub_at:
            try:
                return datetime.fromisoformat(pub_at.replace("Z", "+00:00")).timestamp()
            except Exception:
                pass
        return 0.0

    selected.sort(key=_sort_key, reverse=True)
    return [item["article"] for item in selected]


# ── Legal Matter / Story Grouping Pipeline ──────────────────────────────────

COMMON_COURT_NAMES = {
    "supreme court",
    "bombay high court",
    "delhi high court",
    "karnataka high court",
    "madras high court",
    "calcutta high court",
    "allahabad high court",
    "punjab and haryana high court",
    "kerala high court",
    "gujarat high court",
    "rajasthan high court",
    "patna high court",
    "high court",
}

GENERIC_LEGAL_TERMS = {
    "court", "supreme", "high", "bench", "judge", "justice", "chief",
    "order", "orders", "plea", "pleas", "petition", "petitions", "hearing", "hearings",
    "case", "cases", "matter", "matters", "notice", "notices", "ruling", "rulings",
    "verdict", "verdicts", "law", "laws", "legal", "judiciary", "judicial",
    "article", "section", "act", "india", "indian", "national", "state", "centre",
    "central", "government", "ministry", "union", "police", "authorities", "today",
    "filed", "challenge", "challenging", "report", "news", "trial",
}

DISTINCTIVE_MATTER_REGEXES = [
    ("leave_india_frro", re.compile(r"\b(?:leave\s+india(?:\s+order)?|frro(?:\s+notice)?|oci(?:\s+status|\s+card)?)\b", re.IGNORECASE)),
    ("underage_driver_crash", re.compile(r"\b(?:underage\s+driver|minor\s+driving|fatal\s+crash|father\s+criminally\s+liable)\b", re.IGNORECASE)),
    ("yes_bank_bonds", re.compile(r"\b(?:yes\s+bank|at-?1\s+bonds?|additional\s+tier-?1)\b", re.IGNORECASE)),
    ("electoral_bonds", re.compile(r"\b(?:electoral\s+bonds?)\b", re.IGNORECASE)),
    ("neet_ug_leak", re.compile(r"\b(?:neet(?:\s*-\s*ug)?(?:\s+paper\s+leak)?)\b", re.IGNORECASE)),
    ("excise_policy", re.compile(r"\b(?:excise\s+policy|liquor\s+(?:policy|scam|case))\b", re.IGNORECASE)),
    ("defamation_case", re.compile(r"\b(?:defamation(?:\s+case|\s+complaint|\s+suit)?)\b", re.IGNORECASE)),
    ("telecom_rules", re.compile(r"\b(?:telecom(?:munications)?\s+(?:act|rules|interception))\b", re.IGNORECASE)),
    ("bns_reform", re.compile(r"\b(?:bns|bharatiya\s+nyaya\s+sanhita)\b", re.IGNORECASE)),
    ("subclassification_quota", re.compile(r"\b(?:sub-?classification\s+of\s+sc/st|sc\s+st\s+quota)\b", re.IGNORECASE)),
    ("digital_arrest", re.compile(r"\b(?:digital\s+arrest(?:\s+scams?)?)\b", re.IGNORECASE)),
]


def extract_matter_signature(article: NewsArticle) -> Dict[str, Any]:
    """
    Extract deterministic legal matter anchors, court venue, and named entities
    from an article's title and description.
    """
    combined = f"{article.title} {article.description or ''}"
    norm = normalize_title(combined)
    tokens = set(norm.split())

    # 1. Court venue
    court = None
    for c in sorted(COMMON_COURT_NAMES, key=len, reverse=True):
        if c in norm:
            court = c
            break

    # 2. Named entities (2-word proper noun phrases from raw text)
    named_entities: set[str] = set()
    raw_text = f"{article.title} {article.description or ''}"
    cap_matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", raw_text)
    for m in cap_matches:
        m_lower = m.lower().strip()
        if not any(g in m for g in [
            "Court", "High", "Supreme", "Justice", "Chief", "Bench", "Government",
            "Union", "Ministry", "Bar Council", "India Today", "News", "Times", "Tribune"
        ]):
            if len(m_lower.split()) >= 2:
                named_entities.add(m_lower)

    # 3. Known distinctive legal matter anchors
    matter_anchors: set[str] = set()
    for anchor_key, pat in DISTINCTIVE_MATTER_REGEXES:
        if pat.search(combined):
            matter_anchors.add(anchor_key)

    # 4. Content tokens (excluding stopwords and generic legal terms)
    content_tokens = {
        w for w in tokens
        if len(w) > 2 and w not in STOPWORDS and w not in GENERIC_LEGAL_TERMS
    }

    return {
        "court": court,
        "named_entities": named_entities,
        "matter_anchors": matter_anchors,
        "content_tokens": content_tokens,
    }


def belong_to_same_matter(
    sig_a: Dict[str, Any],
    sig_b: Dict[str, Any],
    art_a: NewsArticle,
    art_b: NewsArticle,
) -> bool:
    """
    Deterministic rule to decide if two articles cover the SAME underlying legal matter.
    Safe guards:
    - Never group merely because they mention the same court or generic legal words.
    - Never group if they have mutually exclusive matter anchors (e.g. defamation vs excise).
    - Never group if numbers differ (e.g. section 377 vs 124A, or different case numbers).
    """
    # 1. Exact or near duplicate check -> same matter
    if canonicalize_url(art_a.url) == canonicalize_url(art_b.url):
        return True
    if normalize_title(art_a.title) == normalize_title(art_b.title):
        return True
    if are_near_duplicate_titles(art_a.title, art_b.title):
        return True

    # 2. Check for conflicting matter anchors
    anchors_a = sig_a["matter_anchors"]
    anchors_b = sig_b["matter_anchors"]
    if anchors_a and anchors_b:
        shared_anchors = anchors_a & anchors_b
        if not shared_anchors:
            return False

    # 3. Check for conflicting numbers in titles
    nums_a = _extract_numbers(normalize_title(art_a.title))
    nums_b = _extract_numbers(normalize_title(art_b.title))
    if nums_a and nums_b and nums_a != nums_b:
        return False

    # 4. Positive association criteria:
    # 4A. Shared distinctive matter anchor
    if anchors_a and anchors_b and (anchors_a & anchors_b):
        entities_a = sig_a["named_entities"]
        entities_b = sig_b["named_entities"]
        if entities_a and entities_b:
            if entities_a & entities_b:
                return True
            return False
        return True

    # 4B. Shared named entity AND high content token overlap
    entities_a = sig_a["named_entities"]
    entities_b = sig_b["named_entities"]
    if entities_a and entities_b and (entities_a & entities_b):
        tokens_a = sig_a["content_tokens"]
        tokens_b = sig_b["content_tokens"]
        if len(tokens_a & tokens_b) >= 2:
            return True

    return False


def generate_story_id(matter_key: str, fallback_title: str) -> str:
    """
    Generate a stable, deterministic story ID derived from normalized case matter.
    Avoids timestamps or array positions.
    """
    anchor = matter_key if matter_key else normalize_title(fallback_title)
    digest = hashlib.md5(anchor.encode("utf-8")).hexdigest()[:10]
    prefix = re.sub(r"[^a-z0-9]+", "_", anchor.lower())[:24].strip("_")
    return f"story_{prefix}_{digest}"


def group_articles_into_stories(articles: List[NewsArticle]) -> List[NewsStoryGroup]:
    """
    Group articles into unified story cards covering the same legal matter:
    1. Cluster articles by legal matter signature.
    2. Within each cluster:
       - Substantially duplicate reports about the exact same development are deduplicated.
       - Meaningful updates, hearing dates, or explanatory coverage are retained as related articles.
    3. Retain original article objects and source URLs.
    4. Generate a stable, deterministic story_id.
    """
    if not articles:
        return []

    # Compute matter signatures for each article
    signatures = [extract_matter_signature(art) for art in articles]

    # Cluster articles into matter groups
    clusters: List[List[int]] = []
    visited: set[int] = set()

    for i in range(len(articles)):
        if i in visited:
            continue
        cluster = [i]
        visited.add(i)

        for j in range(i + 1, len(articles)):
            if j in visited:
                continue
            if belong_to_same_matter(signatures[i], signatures[j], articles[i], articles[j]):
                cluster.append(j)
                visited.add(j)

        clusters.append(cluster)

    stories: List[NewsStoryGroup] = []

    for cluster_indices in clusters:
        cluster_articles = [articles[idx] for idx in cluster_indices]

        # Sub-development duplicate merging:
        # Group reports that describe substantially the same event,
        # but preserve distinct procedural updates, hearings, or explanations.
        distinct_in_cluster = deduplicate_articles(cluster_articles)

        # Sort distinct articles by quality score descending
        scored_distinct = [
            (calculate_article_quality(a), a) for a in distinct_in_cluster
        ]
        scored_distinct.sort(key=lambda x: x[0], reverse=True)

        primary_article = scored_distinct[0][1]
        related_articles = [item[1] for item in scored_distinct[1:]]

        # Determine matter anchor key for stable ID
        primary_sig = extract_matter_signature(primary_article)
        matter_anchors = primary_sig["matter_anchors"]
        named_entities = primary_sig["named_entities"]

        if matter_anchors:
            anchor_name = sorted(matter_anchors)[0]
            entity_name = sorted(named_entities)[0] if named_entities else ""
            matter_key = f"{entity_name}_{anchor_name}".strip("_")
        elif named_entities:
            matter_key = sorted(named_entities)[0]
        else:
            matter_key = normalize_title(primary_article.title)

        story_id = generate_story_id(matter_key, primary_article.title)

        # Assign story_id to all articles in the group
        primary_article.story_id = story_id
        for r_art in related_articles:
            r_art.story_id = story_id

        # Aggregate key entities for UI matter badges
        all_entities: set[str] = set()
        for idx in cluster_indices:
            sig = signatures[idx]
            if sig["court"]:
                all_entities.add(sig["court"].title())
            for ent in sig["named_entities"]:
                all_entities.add(ent.title())
            for anc in sig["matter_anchors"]:
                all_entities.add(anc.replace("_", " ").title())

        # Determine latest timestamp
        timestamps = [
            a.published_at for a in cluster_articles if a.published_at
        ]
        last_updated = max(timestamps) if timestamps else primary_article.published_at

        # Total coverage count tracks all reports received on this matter
        coverage_count = len(cluster_articles)

        story_group = NewsStoryGroup(
            story_id=story_id,
            title=primary_article.title,
            category=primary_article.category,
            primary_article=primary_article,
            related_articles=related_articles,
            coverage_count=coverage_count,
            key_entities=sorted(all_entities)[:4],
            last_updated=last_updated,
        )
        stories.append(story_group)

    # Order story groups by recency
    def _story_sort_key(s: NewsStoryGroup) -> float:
        pub_at = (s.last_updated or s.primary_article.published_at or "").strip()
        if pub_at:
            try:
                return datetime.fromisoformat(pub_at.replace("Z", "+00:00")).timestamp()
            except Exception:
                pass
        return 0.0

    stories.sort(key=_story_sort_key, reverse=True)
    return stories


# ── Normaliser ────────────────────────────────────────────────────────────────

def _normalise_articles(raw_articles: List[Dict[str, Any]], category: str) -> List[NewsArticle]:
    """Convert raw GNews article dicts into NewsArticle models and apply deduplication."""
    articles: List[NewsArticle] = []

    for art in raw_articles:
        url = (art.get("url") or "").strip()
        if not url:
            continue

        source = art.get("source") or {}
        source_name = source.get("name") or "Unknown Source"

        articles.append(NewsArticle(
            title=str(art.get("title") or "Untitled"),
            description=art.get("description") or None,
            url=url,
            source_name=source_name,
            published_at=art.get("publishedAt") or None,
            image_url=art.get("image") or None,
            category=category,
        ))

    return deduplicate_articles(articles)


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_legal_news(category: str = "all", limit: int = DEFAULT_LIMIT) -> NewsResponse:
    """
    Fetch Indian legal news for the given category with story grouping.

    Args:
        category: One of the VALID_CATEGORIES slugs.
        limit:    Max stories to return (capped at MAX_ARTICLES_LIMIT).

    Returns:
        NewsResponse with grouped stories, articles (for backward-compatibility),
        official sources, disclaimer, and cache flag.
    """
    category = category.lower().strip()
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Unknown category '{category}'. Valid options: {sorted(VALID_CATEGORIES)}"
        )

    limit = max(1, min(limit, MAX_ARTICLES_LIMIT))
    _clear_expired_cache()

    key = _cache_key(category, limit)
    cached = _get_cached(key)
    if cached:
        log.debug("Cache hit for news category='%s' limit=%d", category, limit)
        cached.cached = True
        return cached

    query = CATEGORY_QUERY_MAP[category]
    log.info("Fetching GNews: category='%s' limit=%d query='%s'", category, limit, query)

    # Candidate pool expansion: fetch extra raw candidates so grouping and deduplication
    # have enough depth before applying the final story limit
    fetch_pool = min(max(limit + 5, limit), MAX_ARTICLES_LIMIT)
    raw = _fetch_gnews(query, fetch_pool)

    # Convert to candidate articles
    raw_articles: List[NewsArticle] = []
    for art in raw:
        url = (art.get("url") or "").strip()
        if not url:
            continue
        source = art.get("source") or {}
        raw_articles.append(NewsArticle(
            title=str(art.get("title") or "Untitled"),
            description=art.get("description") or None,
            url=url,
            source_name=source.get("name") or "Unknown Source",
            published_at=art.get("publishedAt") or None,
            image_url=art.get("image") or None,
            category=category,
        ))

    # 1. Exact deduplication on raw candidates
    all_deduped = deduplicate_articles(raw_articles)

    # 2. Story-level grouping
    all_stories = group_articles_into_stories(all_deduped)

    # Apply limit to unique stories
    final_stories = all_stories[:limit]

    # For 100% backward compatibility with consumers expecting resp.articles:
    final_articles = [s.primary_article for s in final_stories]

    fetched_at = datetime.now(timezone.utc).isoformat()

    response = NewsResponse(
        category=category,
        total=len(final_stories),
        articles=final_articles,
        stories=final_stories,
        official_sources=OFFICIAL_SOURCES,
        cached=False,
        fetched_at=fetched_at,
    )

    _set_cache(key, response)
    return response


def get_valid_categories() -> List[str]:
    """Return the list of valid category slugs."""
    return sorted(VALID_CATEGORIES)
