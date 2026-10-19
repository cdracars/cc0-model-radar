import time
from typing import Optional

import requests


class FetchError(RuntimeError):
    pass


class Fetcher:
    def __init__(self, delay: float = 2.0, timeout: int = 25):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "cc0-model-radar/0.1 (read-only research tool)",
            "Accept-Language": "en-US,en;q=0.8",
        })
        self._last_request = 0.0

    def get(self, url: str) -> str:
        wait = self.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            response = self.session.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise FetchError(f"request failed for {url}: {exc}") from exc
        finally:
            self._last_request = time.monotonic()
        if response.status_code == 402:
            raise FetchError(
                "MakerWorld denied this automated public-page request (HTTP 402; no payment was made or requested): "
                + url
            )
        if response.status_code in (202, 401, 403, 429):
            raise FetchError(f"site denied or rate-limited request ({response.status_code}): {url}")
        response.raise_for_status()
        return response.text

