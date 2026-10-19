import html as html_lib
import re
from urllib.parse import parse_qs, quote, urlparse

from bs4 import BeautifulSoup

from .fetch import FetchError, Fetcher
from .models import MakerWorldModel, PrintablesMatch
from .text import similarity


BASE = "https://www.printables.com"
SEARCH_FALLBACK_BASE = "https://html.duckduckgo.com/html/"

# Phrases seen on bot-challenge / interstitial pages. If a page contains one of
# these and no parseable results, it must never be read as "no results".
_BLOCK_MARKERS = (
    "unfortunately, bots use duckduckgo too",
    "please complete the following challenge",
    "verify you are human",
    "just a moment",
    "checking your browser",
    "access denied",
    "request rejected",
    "enable javascript and cookies",
)


def _looks_blocked(page: str) -> bool:
    lower = (page or "").lower()
    return any(marker in lower for marker in _BLOCK_MARKERS) or 'id="challenge-form"' in lower


def _fallback_says_no_results(page: str) -> bool:
    """True only when DuckDuckGo explicitly reports zero results."""
    soup = BeautifulSoup(page, "html.parser")
    return soup.select_one(".no-results") is not None


def _query_title(title: str) -> str:
    # A double quote inside the title would terminate the exact-phrase query.
    return " ".join(title.replace('"', " ").split())


def _results(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for link in soup.select('a[href*="/model/"]'):
        href = link.get("href", "")
        match = re.search(r"/model/(\d+)(?:-([^/?#]+))?", href)
        if not match:
            continue
        url = BASE + href.split("#", 1)[0] if href.startswith("/") else href.split("#", 1)[0]
        title = " ".join(link.get_text(" ", strip=True).split())
        key = (url, title)
        if key not in seen:
            seen.add(key)
            results.append(key)
    return results


def find_match(fetcher: Fetcher, model: MakerWorldModel) -> PrintablesMatch:
    query = quote(model.title)
    url = f"{BASE}/search/models?q={query}"
    try:
        html = fetcher.get(url)
    except FetchError as exc:
        fallback = find_search_fallback(fetcher, model)
        if fallback.status != "unknown":
            fallback.evidence = f"Direct Printables lookup failed ({exc}); {fallback.evidence}"
            return fallback
        return PrintablesMatch(status="unknown", evidence=f"Direct Printables lookup failed ({exc}); {fallback.evidence}")
    candidates = _results(html)
    if not candidates:
        # An empty page is not proof of absence: Printables search is rendered
        # client-side and may also serve a challenge page with HTTP 200.
        reason = "challenge page" if _looks_blocked(html) else "no parseable results"
        fallback = find_search_fallback(fetcher, model)
        fallback.evidence = f"Direct Printables lookup inconclusive ({reason}: {url}); {fallback.evidence}"
        return fallback
    scored = sorted(((similarity(model.title, title), title, result_url) for result_url, title in candidates), reverse=True)
    score, title, result_url = scored[0]
    if score >= 0.85:
        status, confidence = "matched", "high"
    elif score >= 0.55:
        status, confidence = "possible_match", "medium"
    else:
        status, confidence = "not_found", "low"
    return PrintablesMatch(status=status, confidence=confidence, title=title, url=result_url, evidence=url)


def _fallback_results(page: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(page, "html.parser")
    results = []
    seen = set()
    for link in soup.select("a.result__a"):
        href = html_lib.unescape(link.get("href", ""))
        parsed = urlparse(href)
        if parsed.netloc.endswith("duckduckgo.com"):
            href = parse_qs(parsed.query).get("uddg", [""])[0]
        if not re.search(r"https?://(?:www\.)?printables\.com/model/\d+", href):
            continue
        title = " ".join(link.get_text(" ", strip=True).split())
        key = (href.split("#", 1)[0], title)
        if key not in seen:
            seen.add(key)
            results.append(key)
    return results


def find_search_fallback(fetcher: Fetcher, model: MakerWorldModel) -> PrintablesMatch:
    query = quote(f'site:printables.com/model/ "{_query_title(model.title)}"')
    url = f"{SEARCH_FALLBACK_BASE}?q={query}"
    try:
        page = fetcher.get(url)
    except FetchError as exc:
        return PrintablesMatch(status="unknown", evidence=f"search fallback failed: {exc}")
    candidates = _fallback_results(page)
    if not candidates:
        if _looks_blocked(page) or not _fallback_says_no_results(page):
            # Without an explicit "no results" marker we cannot tell an empty
            # search from a blocked or changed page, so do not guess.
            reason = "challenge page" if _looks_blocked(page) else "unrecognized results page"
            return PrintablesMatch(
                status="unknown",
                evidence=f"Search fallback inconclusive ({reason}); manual review required: {url}",
            )
        return PrintablesMatch(
            status="likely_not_found",
            confidence="low",
            evidence=f"No indexed Printables model found; manual review recommended: {url}",
        )
    scored = sorted(
        ((similarity(model.title, title), title, result_url) for result_url, title in candidates),
        reverse=True,
    )
    score, title, result_url = scored[0]
    if score >= 0.85:
        status, confidence = "possible_match", "high"
    elif score >= 0.55:
        status, confidence = "possible_match", "medium"
    else:
        status, confidence = "likely_not_found", "low"
    return PrintablesMatch(
        status=status,
        confidence=confidence,
        title=title,
        url=result_url,
        evidence=f"Search fallback: {url}",
    )

