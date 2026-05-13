from abc import ABC, abstractmethod

import numpy as np


DEFAULT_LOCAL_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class BaseEncoder(ABC):
    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        pass


class LocalEncoder(BaseEncoder):
    def __init__(self, model_name: str = DEFAULT_LOCAL_MODEL):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)


def get_encoder(name: str) -> BaseEncoder:
    if name == "local":
        return LocalEncoder()

    # Future option: add OpenAIEncoder here.
    raise ValueError(f"Unknown encoder: {name}")
