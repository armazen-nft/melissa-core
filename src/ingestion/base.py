
"""Abstract base class for all format-specific extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.utils.models import IngestedDoc


class BaseExtractor(ABC):

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]: ...

    @abstractmethod
    def extract(self, path: Path, consent: dict | None = None) -> IngestedDoc: ...
