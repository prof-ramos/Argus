from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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
        return self.status == ResultStatus.FOUND
