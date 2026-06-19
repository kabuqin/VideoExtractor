from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PlatformInfo:
    platform: str
    source_url: str
    normalized_url: str
    video_id: str | None = None


class PlatformAdapter(Protocol):
    platform: str

    def matches(self, url: str) -> bool:
        ...

    def resolve(self, url: str) -> PlatformInfo:
        ...

