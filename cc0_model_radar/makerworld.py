import re
from pathlib import Path
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .fetch import Fetcher
from .models import MakerWorldModel


BASE = "https://makerworld.com"
SEARCH = BASE + "/en/search/models?keyword=tag%3A+cc0"


def _clean(value: str) -> str:
    return " ".join((value or "").split())


def parse_models(html: str, source: str = "html") -> list[MakerWorldModel]:
    soup = BeautifulSoup(html, "html.parser")
    found: dict[str, MakerWorldModel] = {}
    for link in soup.select('a[href*="/models/"]'):
        href = link.get("href", "")
        match = re.search(r"/models/(\d+)(?:-[^/?#]+)?", href)
        if not match:
            continue
        model_id = match.group(1)
        url = urljoin(BASE, href.split("#", 1)[0])
        text = _clean(link.get_text(" ", strip=True))
        if not text or text.lower() in {"models", "view model", "download"}:
            continue
        found.setdefault(model_id, MakerWorldModel(
            model_id=model_id,
            title=text,
            creator="",
            url=url,
            license_name="CC0 (search candidate)",
            source=source,
        ))
    return list(found.values())


def parse_model_page(html: str, model: MakerWorldModel) -> MakerWorldModel:
    text = _clean(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
    lower = text.lower()
    if "creative commons zero" in lower or "cc0" in lower or "public domain" in lower:
        model.license_name = "CC0"
    else:
        model.license_name = "unverified"
    if not model.title or model.title.startswith("Model "):
        title = BeautifulSoup(html, "html.parser").title
        if title:
            model.title = _clean(title.get_text()).replace(" - Free 3D Print Model - MakerWorld", "")
    creator_match = re.search(r"(?:designed by|by)\s+([A-Z][^|.]{2,80})", text)
    if creator_match:
        model.creator = _clean(creator_match.group(1))
    license_match = re.search(r"https?://[^\"'\s>]*creativecommons[^\"'\s>]*", html, re.I)
    if license_match:
        model.license_url = license_match.group(0)
    return model


def discover(fetcher: Fetcher, limit: int = 100, html_path: str | None = None) -> list[MakerWorldModel]:
    if html_path:
        html = Path(html_path).read_text(encoding="utf-8")
        models = parse_models(html, source=html_path)
    else:
        html = fetcher.get(SEARCH)
        models = parse_models(html, source=SEARCH)
    verified = []
    for model in models[:limit]:
        if model.source != html_path and model.url:
            try:
                parse_model_page(fetcher.get(model.url), model)
            except Exception:
                model.license_name = "unverified"
        if model.license_name.lower().startswith("cc0"):
            verified.append(model)
    return verified

