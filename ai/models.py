from dataclasses import dataclass
from typing import List


@dataclass
class AIReport:
    summary: str
    profile_type: str
    insights: List[str]
    risk_flags: List[str]
    tags: List[str]
    digital_footprint_score: int
    confidence: str
    platforms_found: int
    high_value_platforms: List[str]
    categories: List[str]
