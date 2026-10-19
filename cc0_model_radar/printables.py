import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from .fetch import FetchError, Fetcher
from .models import MakerWorldModel, PrintablesMatch
from .text import similarity


BASE = "https://www.printables.com"


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
        return PrintablesMatch(status="unknown", evidence=str(exc))
    candidates = _results(html)
    if not candidates:
        return PrintablesMatch(status="not_found", confidence="medium", evidence=url)
    scored = sorted(((similarity(model.title, title), title, result_url) for result_url, title in candidates), reverse=True)
    score, title, result_url = scored[0]
    if score >= 0.85:
        status, confidence = "matched", "high"
    elif score >= 0.55:
        status, confidence = "possible_match", "medium"
    else:
        status, confidence = "not_found", "low"
    return PrintablesMatch(status=status, confidence=confidence, title=title, url=result_url, evidence=url)

