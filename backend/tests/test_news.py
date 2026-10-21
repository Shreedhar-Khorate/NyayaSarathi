"""
NyayaSarathi — Unit Tests: Legal News Service and Router

Tests cover:
- Category validation (valid and invalid slugs)
- GNews response normalisation
- URL deduplication
- TTL cache (hit / miss / expiry)
- Error handling when GNews key missing
- Category listing endpoint

Run: python -m pytest backend/tests/test_news.py -v
"""

from __future__ import annotations

import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Import modules under test ─────────────────────────────────────────────────
import services.news_service as news_service
from services.news_service import (
    fetch_legal_news,
    get_valid_categories,
    _normalise_articles,
    _cache_key,
    _cache,
    canonicalize_url,
    normalize_title,
    are_near_duplicate_titles,
    calculate_article_quality,
    deduplicate_articles,
    extract_matter_signature,
    belong_to_same_matter,
    group_articles_into_stories,
    VALID_CATEGORIES,
    CACHE_TTL_SECONDS,
)
from schemas.news import NewsArticle, NewsStoryGroup, NewsResponse


# ── Helper: build a fake GNews article dict ───────────────────────────────────

def _make_gnews_article(
    title: str = "Test Article",
    url: str = "https://example.com/article",
    source_name: str = "Test Source",
    published_at: str = "2024-10-21T10:00:00Z",
    description: str = "A test legal news snippet.",
    image: str | None = None,
) -> Dict[str, Any]:
    return {
        "title": title,
        "description": description,
        "url": url,
        "source": {"name": source_name, "url": "https://example.com"},
        "publishedAt": published_at,
        "image": image,
    }


# ── Test Suite ────────────────────────────────────────────────────────────────

class TestNewsSchemas(unittest.TestCase):
    """Test Pydantic schema construction."""

    def test_news_article_required_fields(self):
        art = NewsArticle(
            title="Judgment",
            url="https://sci.gov.in/judgment/1",
            source_name="Supreme Court of India",
            category="supreme-court",
        )
        self.assertEqual(art.title, "Judgment")
        self.assertIsNone(art.description)
        self.assertIsNone(art.image_url)

    def test_news_response_defaults(self):
        resp = NewsResponse(
            category="all",
            total=0,
            articles=[],
        )
        self.assertEqual(resp.total, 0)
        self.assertFalse(resp.cached)
        self.assertIn("GNews", resp.disclaimer)
        self.assertEqual(resp.articles, [])


class TestCategoryValidation(unittest.TestCase):
    """Tests that valid categories are accepted and invalid ones raise."""

    def test_all_valid_categories_accepted(self):
        for cat in VALID_CATEGORIES:
            with patch.object(news_service, "_fetch_gnews", return_value=[]):
                resp = fetch_legal_news(category=cat, limit=5)
                self.assertEqual(resp.category, cat)

    def test_invalid_category_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            fetch_legal_news(category="random-category")
        self.assertIn("random-category", str(ctx.exception))

    def test_get_valid_categories_returns_list(self):
        cats = get_valid_categories()
        self.assertIsInstance(cats, list)
        self.assertIn("all", cats)
        self.assertIn("supreme-court", cats)
        self.assertEqual(sorted(cats), cats)  # must be sorted


class TestNormalisation(unittest.TestCase):
    """Tests for _normalise_articles()."""

    def test_normalises_standard_article(self):
        raw = [_make_gnews_article()]
        articles = _normalise_articles(raw, "all")
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "Test Article")
        self.assertEqual(articles[0].source_name, "Test Source")
        self.assertEqual(articles[0].category, "all")

    def test_deduplicates_by_url(self):
        raw = [
            _make_gnews_article(title="A", url="https://example.com/1"),
            _make_gnews_article(title="B", url="https://example.com/1"),  # duplicate URL
            _make_gnews_article(title="C", url="https://example.com/2"),
        ]
        articles = _normalise_articles(raw, "legal")
        self.assertEqual(len(articles), 2)
        titles = [a.title for a in articles]
        self.assertIn("A", titles)
        self.assertIn("C", titles)
        self.assertNotIn("B", titles)

    def test_skips_articles_with_empty_url(self):
        raw = [
            _make_gnews_article(url=""),
            _make_gnews_article(url="   "),
            _make_gnews_article(url="https://example.com/valid"),
        ]
        articles = _normalise_articles(raw, "all")
        self.assertEqual(len(articles), 1)

    def test_missing_source_defaults_to_unknown(self):
        raw = [{"title": "X", "url": "https://x.com/a", "source": None, "publishedAt": None, "image": None, "description": None}]
        articles = _normalise_articles(raw, "all")
        self.assertEqual(articles[0].source_name, "Unknown Source")

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(_normalise_articles([], "all"), [])


class TestTTLCache(unittest.TestCase):
    """Tests for the in-memory TTL cache."""

    def setUp(self):
        # Clear cache before every test
        _cache.clear()

    def test_cache_miss_fetches_gnews(self):
        raw = [_make_gnews_article()]
        with patch.object(news_service, "_fetch_gnews", return_value=raw) as mock_fetch:
            resp = fetch_legal_news(category="all", limit=5)
            self.assertEqual(mock_fetch.call_count, 1)
            self.assertFalse(resp.cached)

    def test_cache_hit_does_not_call_gnews(self):
        raw = [_make_gnews_article()]
        with patch.object(news_service, "_fetch_gnews", return_value=raw) as mock_fetch:
            fetch_legal_news(category="all", limit=5)   # populates cache
            resp = fetch_legal_news(category="all", limit=5)  # should hit cache
            self.assertEqual(mock_fetch.call_count, 1)
            self.assertTrue(resp.cached)

    def test_different_limits_use_different_cache_keys(self):
        with patch.object(news_service, "_fetch_gnews", return_value=[]) as mock_fetch:
            fetch_legal_news(category="all", limit=5)
            fetch_legal_news(category="all", limit=10)
            self.assertEqual(mock_fetch.call_count, 2)

    def test_expired_cache_refetches(self):
        raw = [_make_gnews_article()]
        with patch.object(news_service, "_fetch_gnews", return_value=raw) as mock_fetch:
            fetch_legal_news(category="legal", limit=5)

            # Manually expire the cache entry
            key = _cache_key("legal", 5)
            stored_at, entry = _cache[key]
            _cache[key] = (stored_at - CACHE_TTL_SECONDS - 1, entry)

            fetch_legal_news(category="legal", limit=5)
            self.assertEqual(mock_fetch.call_count, 2)


class TestErrorHandling(unittest.TestCase):
    """Tests that errors are swallowed gracefully and empty lists returned."""

    def setUp(self):
        _cache.clear()

    def test_gnews_key_missing_returns_empty(self):
        original_key = news_service.GNEWS_API_KEY
        try:
            news_service.GNEWS_API_KEY = ""
            resp = fetch_legal_news(category="all", limit=5)
            self.assertEqual(resp.total, 0)
            self.assertEqual(resp.articles, [])
        finally:
            news_service.GNEWS_API_KEY = original_key

    def test_gnews_network_error_returns_empty(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            resp = fetch_legal_news(category="supreme-court", limit=5)
            self.assertEqual(resp.total, 0)

    def test_official_sources_always_present(self):
        with patch.object(news_service, "_fetch_gnews", return_value=[]):
            resp = fetch_legal_news(category="all", limit=5)
            self.assertGreater(len(resp.official_sources), 0)
            self.assertTrue(any("Supreme Court" in s.name for s in resp.official_sources))

    def test_limit_capped_at_max(self):
        """Limit values above 20 are silently capped."""
        with patch.object(news_service, "_fetch_gnews", return_value=[]) as mock_fetch:
            fetch_legal_news(category="all", limit=100)
            call_args = mock_fetch.call_args
            # Second positional arg to _fetch_gnews is `limit`
            called_limit = call_args[0][1] if call_args[0] else call_args[1].get("limit")
            self.assertLessEqual(called_limit, 20)


class TestCacheKey(unittest.TestCase):
    def test_different_categories_produce_different_keys(self):
        k1 = _cache_key("all", 10)
        k2 = _cache_key("legal", 10)
        self.assertNotEqual(k1, k2)

    def test_same_inputs_produce_same_key(self):
        self.assertEqual(_cache_key("all", 10), _cache_key("all", 10))


class TestDeduplication(unittest.TestCase):
    """
    Tests for multi-stage deduplication:
    1. Canonical URL & tracking parameter normalization
    2. Identical headlines from ANI, Devdiscourse, and news syndicates
    3. Minor headline differences describing the same story
    4. Similar headlines about distinct court cases that must remain separate
    5. Missing descriptions, dates, or publisher names (quality scoring)
    6. Stable selection of the best representative article
    7. Deduplication before the result limit
    """

    def setUp(self):
        _cache.clear()

    def test_canonical_url_and_tracking_parameter_variations(self):
        """Articles with tracking parameters, fragments, or trailing slashes should be unified."""
        url_plain = "https://www.livelaw.in/top-stories/supreme-court-electoral-bonds-12345"
        url_with_utm = "https://www.livelaw.in/top-stories/supreme-court-electoral-bonds-12345/?utm_source=twitter&utm_medium=social#comments"
        url_with_fbclid = "https://www.livelaw.in/top-stories/supreme-court-electoral-bonds-12345?fbclid=IwAR123"

        # Canonical URLs must match
        c1 = canonicalize_url(url_plain)
        c2 = canonicalize_url(url_with_utm)
        c3 = canonicalize_url(url_with_fbclid)
        self.assertEqual(c1, c2)
        self.assertEqual(c2, c3)

        # In deduplication, only 1 should survive
        articles = [
            NewsArticle(title="SC Ruling A", url=url_with_utm, source_name="LiveLaw", category="all"),
            NewsArticle(title="SC Ruling B", url=url_with_fbclid, source_name="LiveLaw", category="all"),
            NewsArticle(title="SC Ruling C", url=url_plain, source_name="LiveLaw", category="all"),
        ]
        deduped = deduplicate_articles(articles)
        self.assertEqual(len(deduped), 1)

    def test_identical_headlines_from_ani_and_devdiscourse(self):
        """Cross-publisher identical headlines with syndicate suffixes must be merged."""
        art_ani = NewsArticle(
            title="Supreme Court dismisses plea on electoral bonds - ANI News",
            description="The Supreme Court on Monday dismissed a fresh plea regarding electoral bonds scheme.",
            url="https://www.aninews.in/news/national/general-news/sc-plea-bonds123",
            source_name="ANI",
            published_at="2024-10-21T09:00:00Z",
            category="all",
        )
        art_dev = NewsArticle(
            title="Supreme Court dismisses plea on electoral bonds | Devdiscourse",
            description="The Supreme Court on Monday dismissed a fresh plea regarding electoral bonds scheme.",
            url="https://www.devdiscourse.com/article/law-order/sc-plea-bonds123",
            source_name="Devdiscourse",
            published_at="2024-10-21T09:30:00Z",
            category="all",
        )

        deduped = deduplicate_articles([art_ani, art_dev])
        self.assertEqual(len(deduped), 1)
        # Original publisher name and URL must be preserved on the selected article
        self.assertIn(deduped[0].source_name, ["ANI", "Devdiscourse"])
        self.assertIn(deduped[0].url, [art_ani.url, art_dev.url])

    def test_minor_headline_differences_same_story(self):
        """Minor title variations for the same story must be merged."""
        art1 = NewsArticle(
            title="Delhi High Court rejects Kejriwal plea challenging arrest in excise policy case",
            description="The Delhi High Court on Tuesday dismissed the petition challenging his arrest.",
            url="https://thehindu.com/news/national/kejriwal-delhi-hc-plea",
            source_name="The Hindu",
            published_at="2024-10-21T10:00:00Z",
            category="all",
        )
        art2 = NewsArticle(
            title="Delhi High Court rejects plea of Arvind Kejriwal challenging arrest in excise policy case",
            description="Delhi HC on Tuesday dismissed Delhi Chief Minister plea against arrest.",
            url="https://ndtv.com/india-news/kejriwal-arrest-delhi-hc",
            source_name="NDTV",
            published_at="2024-10-21T10:05:00Z",
            category="all",
        )

        self.assertTrue(are_near_duplicate_titles(art1.title, art2.title))
        deduped = deduplicate_articles([art1, art2])
        self.assertEqual(len(deduped), 1)

    def test_similar_headlines_distinct_court_cases(self):
        """Articles regarding distinct court cases, orders, or hearings must remain separate."""
        # Case A vs Case B: Different people and opposing outcomes (grants bail vs denies bail)
        art_kejriwal = NewsArticle(
            title="Supreme Court grants bail to Arvind Kejriwal in excise policy case",
            description="SC bench granted bail to AAP leader Arvind Kejriwal.",
            url="https://livelaw.in/kejriwal-bail-grant",
            source_name="LiveLaw",
            category="all",
        )
        art_sisodia = NewsArticle(
            title="Supreme Court denies bail to Manish Sisodia in excise policy case",
            description="SC bench rejected bail plea of Manish Sisodia.",
            url="https://livelaw.in/sisodia-bail-reject",
            source_name="LiveLaw",
            category="all",
        )

        # Distinct hearing dates
        art_neet_jul8 = NewsArticle(
            title="Supreme Court to hear NEET UG paper leak petitions on July 8",
            description="CJI bench will hear petitions on July 8.",
            url="https://thehindu.com/neet-july-8",
            source_name="The Hindu",
            category="all",
        )
        art_neet_jul15 = NewsArticle(
            title="Supreme Court to hear NEET UG paper leak petitions on July 15",
            description="Hearing deferred to July 15 by apex court.",
            url="https://thehindu.com/neet-july-15",
            source_name="The Hindu",
            category="all",
        )

        # Distinct statutory sections
        art_sec377 = NewsArticle(
            title="Supreme Court issues notice on plea challenging Section 377",
            description="Notice issued on Section 377 constitutionality.",
            url="https://barandbench.com/sec-377",
            source_name="Bar and Bench",
            category="all",
        )
        art_sec124a = NewsArticle(
            title="Supreme Court issues notice on plea challenging Section 124A",
            description="Notice issued on sedition law Section 124A.",
            url="https://barandbench.com/sec-124a",
            source_name="Bar and Bench",
            category="all",
        )

        # Distinct judicial actions: upholds CAA vs strikes down electoral bonds
        art_caa = NewsArticle(
            title="Supreme Court upholds constitutional validity of citizenship amendment act",
            description="Supreme Court upholds CAA validity.",
            url="https://sci.gov.in/caa",
            source_name="Supreme Court Observer",
            category="all",
        )
        art_bonds = NewsArticle(
            title="Supreme Court strikes down electoral bonds scheme as unconstitutional",
            description="Constitution bench declares electoral bonds unconstitutional.",
            url="https://sci.gov.in/bonds",
            source_name="Supreme Court Observer",
            category="all",
        )

        distinct_articles = [
            art_kejriwal, art_sisodia,
            art_neet_jul8, art_neet_jul15,
            art_sec377, art_sec124a,
            art_caa, art_bonds,
        ]

        deduped = deduplicate_articles(distinct_articles)
        # All 8 distinct matters must be preserved!
        self.assertEqual(len(deduped), 8)

    def test_missing_descriptions_dates_or_publisher(self):
        """Prefer articles with valid URLs, useful descriptions, and valid dates over empty stubs."""
        stub_article = NewsArticle(
            title="Supreme Court reserves verdict on sub-classification of SC/ST quotas",
            description=None,  # missing description
            url="http://insecure-news.example.com/stub",
            source_name="Unknown Source",  # missing publisher
            published_at=None,  # missing date
            category="all",
        )

        rich_article = NewsArticle(
            title="Supreme Court reserves verdict on sub-classification of SC/ST quotas",
            description="A seven-judge Constitution bench headed by Chief Justice DY Chandrachud reserved its verdict on whether states have power to sub-classify Scheduled Castes and Scheduled Tribes.",
            url="https://www.livelaw.in/top-stories/supreme-court-sc-st-subclassification-249001",
            source_name="LiveLaw",
            published_at="2024-10-21T12:00:00Z",
            image_url="https://www.livelaw.in/images/sc_bench.jpg",
            category="all",
        )

        deduped = deduplicate_articles([stub_article, rich_article])
        self.assertEqual(len(deduped), 1)
        # Rich article should win
        self.assertEqual(deduped[0].url, rich_article.url)
        self.assertEqual(deduped[0].source_name, "LiveLaw")
        self.assertIsNotNone(deduped[0].description)

    def test_stable_selection_of_best_representative(self):
        """Representative selection must be deterministic regardless of input list ordering."""
        art_high_quality = NewsArticle(
            title="Supreme Court notice to Centre on PIL against digital arrest scams",
            description="The Supreme Court issued notice to the Union of India and CBI on a PIL seeking nationwide guidelines against cyber fraudsters extorting citizens through fake digital arrests.",
            url="https://www.thehindu.com/news/national/sc-pil-digital-arrest",
            source_name="The Hindu",
            published_at="2024-10-21T14:00:00Z",
            category="all",
        )
        art_low_quality = NewsArticle(
            title="Supreme Court notice to Centre on PIL against digital arrest scams",
            description="Notice issued on digital arrest.",
            url="https://wire-scraper.example.com/da",
            source_name="NewsBot",
            published_at="2024-10-21T13:00:00Z",
            category="all",
        )

        # Order 1
        deduped1 = deduplicate_articles([art_high_quality, art_low_quality])
        # Order 2 (reversed)
        deduped2 = deduplicate_articles([art_low_quality, art_high_quality])

        self.assertEqual(len(deduped1), 1)
        self.assertEqual(len(deduped2), 1)
        self.assertEqual(deduped1[0].url, art_high_quality.url)
        self.assertEqual(deduped2[0].url, art_high_quality.url)
        self.assertEqual(deduped1[0].source_name, "The Hindu")
        self.assertEqual(deduped2[0].source_name, "The Hindu")

    def test_deduplication_before_result_limit(self):
        """Duplicates must be removed before slicing by limit so unique items are not reduced."""
        # 6 raw articles representing 3 unique stories, each having 1 duplicate
        raw_mock = [
            # Story 1 (2 versions: ANI wire syndicated to two portals)
            _make_gnews_article(
                title="Supreme Court reserves verdict on nationwide water crisis - ANI",
                url="https://portal-a.com/water-crisis",
                description="The Supreme Court reserved its judgment on nationwide water crisis petitions.",
                published_at="2024-10-21T08:00:00Z",
            ),
            _make_gnews_article(
                title="Supreme Court reserves verdict on nationwide water crisis | Devdiscourse",
                url="https://portal-b.com/water-crisis",
                description="The Supreme Court reserved its judgment on nationwide water crisis petitions.",
                published_at="2024-10-21T08:10:00Z",
            ),
            # Story 2 (2 versions)
            _make_gnews_article(
                title="Delhi High Court questions municipal corporation over road safety - PTI",
                url="https://portal-a.com/delhi-hc-roads",
                description="Delhi High Court reprimanded civic authorities on unpaved roads and potholes.",
                published_at="2024-10-21T09:00:00Z",
            ),
            _make_gnews_article(
                title="Delhi High Court questions municipal corporation over road safety | LatestLY",
                url="https://portal-b.com/delhi-hc-roads",
                description="Delhi High Court reprimanded civic authorities on unpaved roads and potholes.",
                published_at="2024-10-21T09:15:00Z",
            ),
            # Story 3 (2 versions)
            _make_gnews_article(
                title="Supreme Court collegium recommends appointment of three High Court judges",
                url="https://portal-a.com/collegium-judges",
                description="The SC collegium led by CJI has recommended 3 advocates for HC judgeship.",
                published_at="2024-10-21T10:00:00Z",
            ),
            _make_gnews_article(
                title="Supreme Court collegium recommends appointment of three High Court judges - Bar and Bench",
                url="https://portal-b.com/collegium-judges",
                description="The SC collegium led by CJI has recommended 3 advocates for HC judgeship.",
                published_at="2024-10-21T10:05:00Z",
            ),
        ]

        with patch.object(news_service, "_fetch_gnews", return_value=raw_mock):
            # Request limit=3
            resp = fetch_legal_news(category="all", limit=3)

            # Must return exactly 3 unique stories
            self.assertEqual(len(resp.articles), 3)
            titles = [a.title for a in resp.articles]
            # Ensure Story 1, Story 2, and Story 3 are all present
            self.assertTrue(any("water crisis" in t.lower() for t in titles))
            self.assertTrue(any("road safety" in t.lower() for t in titles))
            self.assertTrue(any("collegium" in t.lower() for t in titles))

    def test_deduplication_applies_identically_across_all_sections(self):
        """
        Deduplication rules must apply consistently across each individual section:
        'supreme-court', 'high-courts', 'legal', 'government', and 'all'.
        """
        section_fixtures = {
            "supreme-court": [
                _make_gnews_article(
                    title="SC reserves verdict on sub-classification of SC/ST quotas - ANI",
                    url="https://sc-news.com/quotas-1?utm_source=twitter",
                    description="Constitution bench reserves verdict on sub-classification.",
                ),
                _make_gnews_article(
                    title="Supreme Court reserves verdict on sub-classification of SC/ST quotas | Devdiscourse",
                    url="https://sc-news.com/quotas-2?fbclid=xyz",
                    description="Constitution bench reserves verdict on sub-classification.",
                ),
            ],
            "high-courts": [
                _make_gnews_article(
                    title="DHC rejects plea challenging arrest in money laundering case - PTI",
                    url="https://hc-news.com/dhc-plea?ref=home",
                    description="Delhi High Court dismissed bail petition.",
                ),
                _make_gnews_article(
                    title="Delhi High Court rejects plea challenging arrest in money laundering case | LiveLaw",
                    url="https://hc-news.com/dhc-plea-2",
                    description="Delhi High Court dismissed bail petition.",
                ),
            ],
            "legal": [
                _make_gnews_article(
                    title="Supreme Court examines constitutional validity of BNS criminal code - ANI",
                    url="https://legal-reforms.com/bns-challenge?utm_medium=feed",
                    description="Plea challenges sections of the Bharatiya Nyaya Sanhita.",
                ),
                _make_gnews_article(
                    title="Supreme Court examines constitutional validity of Bharatiya Nyaya Sanhita criminal code",
                    url="https://legal-reforms.com/bns-challenge-2",
                    description="Plea challenges sections of the Bharatiya Nyaya Sanhita.",
                ),
            ],
            "government": [
                _make_gnews_article(
                    title="Law Ministry issues gazette notification for new court rules - PTI",
                    url="https://govt-orders.com/notification?utm_campaign=daily",
                    description="Ministry of Law and Justice notifies updated procedural rules.",
                ),
                _make_gnews_article(
                    title="Law Ministry issues gazette notification for new court rules | Devdiscourse",
                    url="https://govt-orders.com/notification-2",
                    description="Ministry of Law and Justice notifies updated procedural rules.",
                ),
            ],
            "all": [
                _make_gnews_article(
                    title="Bar Council of India issues advisory on foreign lawyers registration - ANI",
                    url="https://bar-news.com/foreign-lawyers?utm_source=telegram",
                    description="BCI issues notification on registration guidelines.",
                ),
                _make_gnews_article(
                    title="Bar Council of India issues advisory on foreign lawyers registration | LatestLY",
                    url="https://bar-news.com/foreign-lawyers-dup",
                    description="BCI issues notification on registration guidelines.",
                ),
            ],
        }

        for category, raw_items in section_fixtures.items():
            with self.subTest(category=category):
                _cache.clear()
                with patch.object(news_service, "_fetch_gnews", return_value=raw_items):
                    resp = fetch_legal_news(category=category, limit=10)
                    self.assertEqual(
                        len(resp.articles),
                        1,
                        f"Expected duplicates to be merged into 1 article in section '{category}', but got {len(resp.articles)}",
                    )
                    self.assertEqual(resp.category, category)


class TestStoryGrouping(unittest.TestCase):
    """
    Tests for legal matter / story grouping:
    Scenario A: Imran Khan and the Leave India order (grouping matter, deduplicating second notice, preserving October 26 hearing & OCI updates).
    Scenario B: Completely unrelated cases (Karnataka underage driver crash vs Yes Bank AT-1 bonds).
    Scenario C: Similar but distinct cases (electoral bonds vs telecom rules; Kejriwal defamation vs Kejriwal excise policy).
    """

    def setUp(self):
        _cache.clear()

    def test_scenario_a_imran_khan_leave_india_matter(self):
        """
        Scenario A: 6 reports covering the Imran Khan Leave India order.
        - Must produce exactly 1 main story group for the underlying legal matter.
        - Substantially duplicate reports about the 2nd FRRO notice (India Today + News18) must be deduplicated.
        - The October 26 Bombay HC hearing update must be retained.
        - Explanatory coverage of Leave India & OCI status must be preserved.
        - All original publisher articles and URLs must remain accessible.
        - Not all six articles are deleted down to 1 single article.
        """
        feed = [
            NewsArticle(
                title="Bombay High Court to hear Imran Khan petition on October 26",
                description="The Bombay High Court has scheduled a hearing on October 26 on the petition filed by actor Imran Khan challenging his Leave India order.",
                url="https://timesofindia.indiatimes.com/city/mumbai/bombay-hc-imran-khan-oct-26",
                source_name="Times of India",
                published_at="2024-10-21T08:00:00Z",
                category="high-courts",
            ),
            NewsArticle(
                title="Second FRRO notice while challenging Leave India order",
                description="Actor Imran Khan received a second FRRO notice from authorities even as his petition challenging the Leave India order is pending before the Bombay High Court.",
                url="https://indiatoday.in/national/imran-khan-second-frro-notice",
                source_name="India Today",
                published_at="2024-10-21T09:00:00Z",
                category="high-courts",
            ),
            NewsArticle(
                title="Second FRRO notice while challenging Leave India order - News18",
                description="Actor Imran Khan received a second FRRO notice from authorities even as his petition challenging the Leave India order is pending before the Bombay High Court.",
                url="https://news18.com/india/imran-khan-second-frro-notice-dup",
                source_name="News18",
                published_at="2024-10-21T09:10:00Z",
                category="high-courts",
            ),
            NewsArticle(
                title="Explanation of the Leave India order and OCI status",
                description="A legal explanation analyzing the provisions under the Foreigners Act regarding Leave India directives and the constitutional protections available to OCI cardholders.",
                url="https://newsx.com/national/explanation-leave-india-order-oci-status",
                source_name="NewsX",
                published_at="2024-10-21T10:00:00Z",
                category="high-courts",
            ),
            NewsArticle(
                title="Petition against the Leave India order and FRRO notice",
                description="Actor Imran Khan has approached the court challenging the deportation and Leave India order along with FRRO notices.",
                url="https://theprint.in/judiciary/petition-leave-india-order-frro-notice",
                source_name="ThePrint",
                published_at="2024-10-21T11:00:00Z",
                category="high-courts",
            ),
            NewsArticle(
                title="Challenge to the order and OCI status",
                description="Legal challenge filed by actor Imran Khan questions revocation of OCI status and deportation directive issued by authorities.",
                url="https://tribuneindia.com/news/nation/challenge-to-order-and-oci-status",
                source_name="The Tribune",
                published_at="2024-10-21T11:30:00Z",
                category="high-courts",
            ),
        ]

        stories = group_articles_into_stories(feed)

        # 1. Must form exactly ONE story group for this legal matter
        self.assertEqual(len(stories), 1, f"Expected 1 story group, got {len(stories)}")
        story = stories[0]

        # 2. Must retain stable identifier
        self.assertTrue(story.story_id.startswith("story_"))

        # 3. All articles in group must be accessible (not deleted down to 1 total article)
        all_articles_in_story = [story.primary_article] + story.related_articles
        self.assertGreater(len(all_articles_in_story), 1)

        # 4. Duplicate reports about the second FRRO notice (India Today and News18) must be deduplicated
        frro_duplicate_urls = [
            a.url for a in all_articles_in_story
            if "second-frro-notice" in a.url
        ]
        self.assertEqual(len(frro_duplicate_urls), 1, "Duplicate second FRRO notice articles should be merged into 1 representative")

        # 5. October 26 hearing update must be retained
        hearing_titles = [a.title for a in all_articles_in_story]
        self.assertTrue(any("October 26" in t for t in hearing_titles), "October 26 hearing update must be preserved in the group")

        # 6. Explanatory coverage of OCI status must be preserved
        self.assertTrue(any("OCI status" in t for t in hearing_titles), "OCI status explanatory coverage must be preserved")

        # 7. Original publisher articles & URLs must be preserved
        sources_present = {a.source_name for a in all_articles_in_story}
        self.assertTrue(len(sources_present) >= 3, f"Expected multiple distinct publisher sources, got {sources_present}")

    def test_scenario_b_completely_unrelated_cases_remain_separate(self):
        """
        Scenario B:
        - Karnataka HC case: father & underage driver's fatal crash.
        - Supreme Court ruling: Yes Bank AT-1 bonds.
        - Imran Khan Leave India order.
        Must remain 3 completely separate story groups.
        """
        feed = [
            NewsArticle(
                title="Karnataka High Court case involving a father and an underage driver fatal crash",
                description="The Karnataka High Court held that a father who permits an underage minor to drive leading to a fatal crash is criminally liable.",
                url="https://karnatakalaw.com/underage-driver-crash",
                source_name="The Hindu",
                published_at="2024-10-21T09:00:00Z",
                category="high-courts",
            ),
            NewsArticle(
                title="Supreme Court ruling involving Yes Bank AT-1 bonds write-off",
                description="The Supreme Court dismissed the appeal filed by retail investors against the write-off of Yes Bank Additional Tier-1 (AT-1) bonds.",
                url="https://sc-observer.com/yes-bank-at1-bonds",
                source_name="LiveLaw",
                published_at="2024-10-21T10:00:00Z",
                category="supreme-court",
            ),
            NewsArticle(
                title="Bombay High Court to hear Imran Khan petition challenging Leave India order",
                description="Bombay HC to hear petition on Leave India directive.",
                url="https://bombay-news.com/imran-khan-leave-india",
                source_name="NDTV",
                published_at="2024-10-21T11:00:00Z",
                category="high-courts",
            ),
        ]

        stories = group_articles_into_stories(feed)
        self.assertEqual(len(stories), 3, "Unrelated cases must produce 3 separate story groups")

        titles = [s.title for s in stories]
        self.assertTrue(any("underage driver" in t.lower() for t in titles))
        self.assertTrue(any("yes bank" in t.lower() for t in titles))
        self.assertTrue(any("imran khan" in t.lower() for t in titles))

    def test_scenario_c_similar_court_or_figure_distinct_cases_remain_separate(self):
        """
        Scenario C:
        - Similar court / generic terms: SC Electoral Bonds vs SC Telecom Interception Rules.
        - Same person, different cases: Arvind Kejriwal Defamation vs Arvind Kejriwal Liquor Excise Policy.
        Must remain distinct story groups.
        """
        # Test C1: Same court (Supreme Court), distinct cases
        art_electoral = NewsArticle(
            title="Supreme Court dismisses plea on electoral bonds transparency",
            description="SC rejected petition seeking disclosure of alphanumeric codes of electoral bonds.",
            url="https://livelaw.in/electoral-bonds-codes",
            source_name="LiveLaw",
            category="supreme-court",
        )
        art_telecom = NewsArticle(
            title="Supreme Court issues notice on plea challenging new telecom interception rules",
            description="SC bench headed by CJI issued notice on PIL challenging provisions of new Telecommunications Act.",
            url="https://barandbench.com/telecom-interception-pil",
            source_name="Bar and Bench",
            category="supreme-court",
        )

        stories_c1 = group_articles_into_stories([art_electoral, art_telecom])
        self.assertEqual(len(stories_c1), 2, "Distinct SC cases must not be merged merely because both mention Supreme Court and plea")

        # Test C2: Same public figure, distinct legal matters
        art_kejriwal_defamation = NewsArticle(
            title="Delhi High Court stays summons to Arvind Kejriwal in criminal defamation case",
            description="The High Court granted interim relief staying summons in defamation complaint.",
            url="https://thehindu.com/kejriwal-defamation-stay",
            source_name="The Hindu",
            category="high-courts",
        )
        art_kejriwal_excise = NewsArticle(
            title="Supreme Court grants bail to Arvind Kejriwal in excise policy case",
            description="The Supreme Court ordered release of Kejriwal on regular bail in liquor policy case.",
            url="https://ndtv.com/kejriwal-excise-bail-grant",
            source_name="NDTV",
            category="supreme-court",
        )

        stories_c2 = group_articles_into_stories([art_kejriwal_defamation, art_kejriwal_excise])
        self.assertEqual(len(stories_c2), 2, "Separate legal matters involving the same person must not be merged")

    def test_story_limit_applied_to_unique_story_groups(self):
        """When limit=2 is passed, the API returns at most 2 unique story groups."""
        raw_mock = [
            _make_gnews_article(title="Case 1: Imran Khan Leave India order hearing - TOI", url="https://pub1.com/1", description="Leave India order pending in Bombay High Court."),
            _make_gnews_article(title="Case 1: Imran Khan second FRRO notice - India Today", url="https://pub2.com/1", description="Second FRRO notice on Leave India order."),
            _make_gnews_article(title="Case 2: Yes Bank AT-1 bonds verdict - LiveLaw", url="https://pub1.com/2", description="Supreme Court ruling on Yes Bank Additional Tier-1 bonds."),
            _make_gnews_article(title="Case 3: Karnataka High Court underage driver crash - The Hindu", url="https://pub1.com/3", description="Father criminally liable in underage driver crash."),
        ]

        with patch.object(news_service, "_fetch_gnews", return_value=raw_mock):
            resp = fetch_legal_news(category="all", limit=2)
            # Response total and stories count should respect limit=2
            self.assertEqual(len(resp.stories), 2)
            self.assertEqual(resp.total, 2)
            # Backward-compatible articles field must also have 2 primary articles
            self.assertEqual(len(resp.articles), 2)


if __name__ == "__main__":
    unittest.main()

