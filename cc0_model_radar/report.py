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


def write_markdown(candidates: list[Candidate], path: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = ["# CC0 Model Radar report", "", f"Candidates checked: {len(candidates)}", "", "| Status | Model | Creator | Printables | Source | Evidence |", "|---|---|---|---|---|---|"]
    for candidate in candidates:
        model = candidate.model
        match = candidate.match
        printables = f"[{match.status}]({match.url})" if match.url else match.status
        rows.append(f"| {match.status} | [{model.title}]({model.url}) | {model.creator or '—'} | {printables} | {model.license_name} | {model.verification_evidence or '—'} |")
    target.write_text("\n".join(rows) + "\n", encoding="utf-8")

