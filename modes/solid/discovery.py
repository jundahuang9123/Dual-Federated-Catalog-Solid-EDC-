"""Solid-mode discovery implementation."""

from __future__ import annotations

from core.interfaces.discovery import CatalogStatus, DatasetResult, DiscoveryService
from core.interfaces.registry import RegistryCheck
from core.interfaces.store import CatalogStore
from modes.solid.store import participant_from_graph_uri


def _int_value(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


class SolidDiscovery(DiscoveryService):
    def __init__(self, store: CatalogStore, registry: RegistryCheck) -> None:
        self.store = store
        self.registry = registry

    def list_datasets(self) -> list[DatasetResult]:
        rows = self.store.query(
            """
            PREFIX dcat: <http://www.w3.org/ns/dcat#>
            PREFIX dct: <http://purl.org/dc/terms/>

            SELECT ?graph ?dataset ?title ?provider
            WHERE {
              GRAPH ?graph {
                ?dataset a dcat:Dataset .
                OPTIONAL { ?dataset dct:title ?title . }
                OPTIONAL { ?dataset dct:publisher ?provider . }
              }
            }
            ORDER BY LCASE(STR(?title)) STR(?dataset)
            """
        )
        results: list[DatasetResult] = []
        for row in rows:
            graph = str(row.get("graph") or "")
            provider = row.get("provider") or participant_from_graph_uri(graph)
            results.append(
                DatasetResult(
                    dataset_id=str(row.get("dataset") or ""),
                    title=str(row["title"]) if row.get("title") else None,
                    provider=str(provider) if provider else None,
                    metadata={"graph": graph, "mode": "solid"},
                )
            )
        return results

    def get_status(self) -> CatalogStatus:
        registry_reachable = None
        if hasattr(self.registry, "registry_reachable"):
            registry_reachable = bool(self.registry.registry_reachable())  # type: ignore[attr-defined]

        try:
            rows = self.store.query(
                """
                PREFIX dcat: <http://www.w3.org/ns/dcat#>

                SELECT
                  (COUNT(DISTINCT ?dataset) AS ?dataset_count)
                  (COUNT(DISTINCT ?graph) AS ?graph_count)
                WHERE {
                  GRAPH ?graph {
                    ?dataset a dcat:Dataset .
                  }
                }
                """
            )
            first = rows[0] if rows else {}
            return CatalogStatus(
                mode="solid",
                operational=True,
                dataset_count=_int_value(first.get("dataset_count")),
                graph_count=_int_value(first.get("graph_count")),
                registry_reachable=registry_reachable,
            )
        except Exception as exc:
            return CatalogStatus(
                mode="solid",
                operational=False,
                registry_reachable=registry_reachable,
                detail=f"Solid discovery unavailable: {exc}",
            )

