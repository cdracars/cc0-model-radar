from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class MakerWorldModel:
    model_id: str
    title: str
    creator: str
    url: str
    license_name: str = ""
    license_url: str = ""
    published_at: str = ""
    source: str = ""

    def row(self) -> dict:
        return asdict(self)


@dataclass
class PrintablesMatch:
    status: str
    confidence: str = ""
    title: str = ""
    creator: str = ""
    url: str = ""
    evidence: str = ""


@dataclass
class Candidate:
    model: MakerWorldModel
    match: PrintablesMatch

    def row(self) -> dict:
        row = self.model.row()
        row.update({
            "printables_status": self.match.status,
            "printables_confidence": self.match.confidence,
            "printables_title": self.match.title,
            "printables_creator": self.match.creator,
            "printables_url": self.match.url,
            "printables_evidence": self.match.evidence,
        })
        return row

