import csv
from pathlib import Path

from .models import Candidate


FIELDS = [
    "model_id", "title", "creator", "url", "license_name", "license_url", "published_at", "source", "verification_evidence",
    "printables_status", "printables_confidence", "printables_title", "printables_creator",
    "printables_url", "printables_evidence",
]


def write_csv(candidates: list[Candidate], path: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(candidate.row() for candidate in candidates)


def _cell(value: str) -> str:
    """Make a value safe inside a Markdown table cell."""
    return " ".join((value or "").split()).replace("|", "\\|")


def _link(text: str, url: str) -> str:
    text = _cell(text).replace("[", "\\[").replace("]", "\\]")
    url = (url or "").replace(" ", "%20").replace(")", "%29")
    return f"[{text}]({url})" if url else text


def write_markdown(candidates: list[Candidate], path: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = ["# CC0 Model Radar report", "", f"Candidates checked: {len(candidates)}", "", "| Status | Model | Creator | Printables | Source | Evidence |", "|---|---|---|---|---|---|"]
    for candidate in candidates:
        model = candidate.model
        match = candidate.match
        printables = _link(match.status, match.url)
        evidence = _cell(" ".join(value for value in (model.verification_evidence, match.evidence) if value)) or "—"
        rows.append(
            f"| {_cell(match.status)} | {_link(model.title, model.url)} | {_cell(model.creator) or '—'} "
            f"| {printables} | {_cell(model.license_name)} | {evidence} |"
        )
    target.write_text("\n".join(rows) + "\n", encoding="utf-8")

