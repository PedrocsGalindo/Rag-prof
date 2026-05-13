from pathlib import Path

import numpy as np

from .encoder import get_encoder
from .models import Professor, RankedProfessor
from .storage import load_json


DEFAULT_PROFILES_PATH = Path("data/processed/professor_profiles.json")
DEFAULT_EMBEDDINGS_PATH = Path("data/embeddings/professor_embeddings.npy")
DEFAULT_INDEX_PATH = Path("data/embeddings/professor_embedding_index.json")


def cosine_similarity(query_embedding, professor_embeddings) -> np.ndarray:
    query_vector = np.asarray(query_embedding, dtype=np.float32)
    embeddings = np.asarray(professor_embeddings, dtype=np.float32)

    if query_vector.ndim == 2:
        query_vector = query_vector[0]

    query_norm = np.linalg.norm(query_vector)
    embedding_norms = np.linalg.norm(embeddings, axis=1)
    denominator = query_norm * embedding_norms
    denominator = np.where(denominator == 0, 1e-12, denominator)

    return embeddings @ query_vector / denominator


def rank_professors(
    query: str,
    top_k: int = 3,
    profiles_path: str | Path = DEFAULT_PROFILES_PATH,
    embeddings_path: str | Path = DEFAULT_EMBEDDINGS_PATH,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    encoder_name: str = "local",
) -> list[RankedProfessor]:
    professors = load_professors(profiles_path)
    embeddings = np.load(embeddings_path)
    embedding_index = load_json(index_path, default=[])

    encoder = get_encoder(encoder_name)
    query_embedding = encoder.encode([query])
    scores = cosine_similarity(query_embedding, embeddings)

    professor_by_id = {professor.id: professor for professor in professors}
    index_by_position = {item["index"]: item for item in embedding_index}
    best_positions = np.argsort(scores)[::-1][:top_k]

    ranking = []
    for position in best_positions:
        index_item = index_by_position.get(int(position))
        if not index_item:
            continue

        professor = professor_by_id.get(index_item["professor_id"])
        if not professor:
            continue

        ranking.append(
            RankedProfessor(
                professor=professor,
                score=float(scores[position]),
                reason="Similaridade cosseno com a query.",
            )
        )

    return ranking


def load_professors(profiles_path: str | Path) -> list[Professor]:
    data = load_json(profiles_path, default=[])
    return [Professor(**item) for item in data]
