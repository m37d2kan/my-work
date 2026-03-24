from dataclasses import dataclass
from typing import Optional


@dataclass
class TokenInfo:
    token: str
    fetched_at: Optional[str] = None
