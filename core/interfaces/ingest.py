from abc import ABC, abstractmethod


class IngestSource(ABC):
    @abstractmethod
    def routes(self) -> object:
        raise NotImplementedError

