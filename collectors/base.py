from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ResultStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class AccountResult:
    site_name: str
    url: Optional[str] = None
    status: ResultStatus = ResultStatus.NOT_FOUND
    http_status: Optional[int] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def is_valid(self) -> bool:
        return self.status == ResultStatus.FOUND and self.http_status == 200
