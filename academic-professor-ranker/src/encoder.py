import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_LOCAL_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


# Classe base para qualquer encoder do projeto.
class BaseEncoder:
    def encode(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError


# Encoder local usando sentence-transformers.
class LocalEncoder(BaseEncoder):
    def __init__(self, model_name: str = DEFAULT_LOCAL_MODEL):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        safe_texts = [text or " " for text in texts]
        return self.model.encode(safe_texts, convert_to_numpy=True)


# Retorna o encoder escolhido pelo nome.
def get_encoder(name: str = "local") -> BaseEncoder:
    if name == "local":
        return LocalEncoder()

    # Futuramente, podemos criar aqui um OpenAIEncoder usando API externa.
    raise ValueError(f"Encoder não suportado: {name}")


if __name__ == "__main__":
    encoder = get_encoder("local")
    embeddings = encoder.encode(["teste de inteligência artificial", "teste de sistemas distribuídos"])
    print(embeddings.shape)
