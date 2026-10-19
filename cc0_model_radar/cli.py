import argparse

from .fetch import FetchError, Fetcher
from .browser import BrowserFetcher
from .makerworld import discover
from .models import Candidate, PrintablesMatch
from .printables import find_match
from .report import write_csv, write_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Find MakerWorld CC0 models without an obvious Printables match.")
    parser.add_argument("--limit", type=int, default=25, help="maximum MakerWorld candidates to inspect")
    parser.add_argument("--delay", type=float, default=2.0, help="seconds between public-page requests")
    parser.add_argument("--makerworld-html", help="use a saved MakerWorld search page instead of fetching it")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="use a real Chromium browser for MakerWorld pages (does not log in or download files)",
    )
    parser.add_argument(
        "--browser-path",
        help="path to an installed Chromium-based browser such as Opera",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="show the browser window instead of running headless",
    )
    parser.add_argument(
        "--include-unverified",
        action="store_true",
        help="include models that could not be verified, with the reason in the report",
    )
    parser.add_argument("--output", default="reports/cc0-candidates.csv")
    parser.add_argument("--markdown", default=None)
    args = parser.parse_args()

    makerworld_fetcher = (
        BrowserFetcher(delay=args.delay, browser_path=args.browser_path, headless=not args.headed)
        if args.browser
        else Fetcher(delay=args.delay)
    )
    printables_fetcher = makerworld_fetcher if args.browser else Fetcher(delay=args.delay)
    try:
        try:
            models = discover(
                makerworld_fetcher,
                limit=args.limit,
                html_path=args.makerworld_html,
                include_unverified=args.include_unverified,
            )
        except FetchError as exc:
            parser.error(str(exc))
        candidates = []
        for model in models:
            match = (
                find_match(printables_fetcher, model)
                if model.license_name.lower().startswith("cc0")
                else PrintablesMatch(status="unknown", evidence=model.verification_evidence)
            )
            candidates.append(Candidate(model=model, match=match))
        write_csv(candidates, args.output)
        markdown = args.markdown or args.output.rsplit(".", 1)[0] + ".md"
        write_markdown(candidates, markdown)
        print(f"Wrote {len(candidates)} candidates to {args.output}")
        print(f"Wrote review report to {markdown}")
    finally:
        # Always shut the browser down, including after errors or Ctrl-C.
        close = getattr(makerworld_fetcher, "close", None)
        if close:
            close()

