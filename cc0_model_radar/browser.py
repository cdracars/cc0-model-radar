"""Browser-backed public-page fetcher for sites that block plain HTTP clients."""

import time

from .fetch import FetchError


class BrowserFetcher:
    """Fetch rendered public pages through Playwright.

    This intentionally does not log in, solve CAPTCHAs, or download files. It
    only loads pages and returns their rendered HTML to the existing parsers.
    """

    def __init__(
        self,
        delay: float = 2.0,
        headless: bool = True,
        timeout: int = 30,
        browser_path: str | None = None,
    ):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise FetchError(
                "browser mode requires Playwright. Install it with "
                "'pip install -r requirements.txt' and then "
                "'playwright install chromium'."
            ) from exc

        self.delay = delay
        self.timeout = timeout * 1000
        self._last_request = 0.0
        self._playwright = sync_playwright().start()
        launch_options = {"headless": headless}
        if browser_path:
            launch_options["executable_path"] = browser_path
        self.browser = self._playwright.chromium.launch(**launch_options)
        self.context = self.browser.new_context(
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)

    def get(self, url: str) -> str:
        wait = self.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            response = self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            self.page.wait_for_timeout(750)
            if response is not None and response.status in (401, 402, 403, 429):
                raise FetchError(f"browser request denied or rate-limited ({response.status}): {url}")
            return self.page.content()
        except FetchError:
            raise
        except Exception as exc:
            raise FetchError(f"browser request failed for {url}: {exc}") from exc
        finally:
            self._last_request = time.monotonic()

    def close(self) -> None:
        self.context.close()
        self.browser.close()
        self._playwright.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
