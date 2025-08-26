from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Article:
    """A simple dataclass to hold article information."""
    title: str
    url: str
    summary: Optional[str] = None
    source: Optional[str] = None
    content: Optional[str] = None # The full content fetched by the scraper
