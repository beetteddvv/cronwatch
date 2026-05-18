"""Job ownership tracking — assign owners (teams/users) to jobs and query by owner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OwnerRecord:
    job_name: str
    owner: str
    team: Optional[str] = None
    contact: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "owner": self.owner,
            "team": self.team,
            "contact": self.contact,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OwnerRecord":
        return cls(
            job_name=data["job_name"],
            owner=data["owner"],
            team=data.get("team"),
            contact=data.get("contact"),
        )


class OwnershipRegistry:
    """Maps job names to their owner records."""

    def __init__(self) -> None:
        self._records: Dict[str, OwnerRecord] = {}

    def register(self, record: OwnerRecord) -> None:
        self._records[record.job_name] = record

    def get(self, job_name: str) -> Optional[OwnerRecord]:
        return self._records.get(job_name)

    def jobs_for_owner(self, owner: str) -> List[str]:
        return [name for name, rec in self._records.items() if rec.owner == owner]

    def jobs_for_team(self, team: str) -> List[str]:
        return [name for name, rec in self._records.items() if rec.team == team]

    def all_owners(self) -> List[str]:
        return list({rec.owner for rec in self._records.values()})

    def all_teams(self) -> List[str]:
        return list({rec.team for rec in self._records.values() if rec.team})

    def unowned_jobs(self, all_job_names: List[str]) -> List[str]:
        return [name for name in all_job_names if name not in self._records]
