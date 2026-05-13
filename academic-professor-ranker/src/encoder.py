from abc import ABC, abstractmethod


class BaseEncoder(ABC):
    @abstractmethod
    def encode(self, texts: list[str]) -> list[list[float]]:
        pass


class LocalEncoder(BaseEncoder):
    def encode(self, texts: list[str]) -> list[list[float]]:
        # TODO: replace this with a real local embedding model.
        return [[0.0] for _ in texts]
