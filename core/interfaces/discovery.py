from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DatasetResult:
    dataset_id: str
    title: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] | None = None


class DiscoveryService(ABC):
    @abstractmethod
    def list_datasets(self) -> list[DatasetResult]:
        raise NotImplementedError

