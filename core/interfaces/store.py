from abc import ABC, abstractmethod


class CatalogStore(ABC):
    @abstractmethod
    def replace_graph(self, graph_id: str, rdf_payload: str) -> None:
        raise NotImplementedError

