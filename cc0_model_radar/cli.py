import argparse

from .fetch import FetchError, Fetcher
from .makerworld import discover
from .models import Candidate
from .printables import find_match
from .report import write_csv, write_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Find MakerWorld CC0 models without an obvious Printables match.")
    parser.add_argument("--limit", type=int, default=25, help="maximum MakerWorld candidates to inspect")
    parser.add_argument("--delay", type=float, default=2.0, help="seconds between public-page requests")
    parser.add_argument("--makerworld-html", help="use a saved MakerWorld search page instead of fetching it")
    parser.add_argument("--output", default="reports/cc0-candidates.csv")
    parser.add_argument("--markdown", default=None)
    args = parser.parse_args()

    fetcher = Fetcher(delay=args.delay)
    try:
        models = discover(fetcher, limit=args.limit, html_path=args.makerworld_html)
    except FetchError as exc:
        parser.error(str(exc))
    candidates = []
    for model in models:
        candidates.append(Candidate(model=model, match=find_match(fetcher, model)))
    write_csv(candidates, args.output)
    markdown = args.markdown or args.output.rsplit(".", 1)[0] + ".md"
    write_markdown(candidates, markdown)
    print(f"Wrote {len(candidates)} candidates to {args.output}")
    print(f"Wrote review report to {markdown}")

