from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DatasetResult:
    dataset_id: str
    title: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class CatalogStatus:
    mode: str
    operational: bool
    dataset_count: int = 0
    graph_count: int = 0
    registry_reachable: bool | None = None
    detail: str | None = None


class DiscoveryService(ABC):
    @abstractmethod
    def list_datasets(self) -> list[DatasetResult]:
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> CatalogStatus:
        raise NotImplementedError

