from pathlib import Path

import numpy as np

from .encoder import get_encoder
from .models import Professor, RankedProfessor
from .storage import load_json


DEFAULT_CHUNKS_PATH = Path("data/processed/professor_chunks.json")
DEFAULT_EMBEDDINGS_PATH = Path("data/embeddings/professor_chunk_embeddings.npy")
DEFAULT_INDEX_PATH = Path("data/embeddings/professor_chunk_embedding_index.json")


def cosine_similarity(query_embedding, embeddings) -> np.ndarray:
    query_vector = np.asarray(query_embedding, dtype=np.float32)
    chunk_embeddings = np.asarray(embeddings, dtype=np.float32)

    if query_vector.ndim == 2:
        query_vector = query_vector[0]

    query_norm = np.linalg.norm(query_vector)
    embedding_norms = np.linalg.norm(chunk_embeddings, axis=1)
    denominator = np.where(query_norm * embedding_norms == 0, 1e-12, query_norm * embedding_norms)

    return chunk_embeddings @ query_vector / denominator


def load_chunks(path: str | Path) -> list[dict]:
    return load_json(path, default=[])


def load_embedding_index(path: str | Path) -> list[dict]:
    return load_json(path, default=[])


def group_chunk_results_by_professor(results: list[dict]) -> list[dict]:
    grouped = {}

    for result in results:
        professor_id = result["professor_id"]
        if professor_id not in grouped:
            grouped[professor_id] = {
                "professor": professor_from_chunk(result),
                "score": result["score"],
                "evidences": [],
            }

        grouped[professor_id]["score"] = max(grouped[professor_id]["score"], result["score"])
        if len(grouped[professor_id]["evidences"]) < 3:
            grouped[professor_id]["evidences"].append(
                {
                    "section": result["section"],
                    "title": result["title"],
                    "text": result["text"],
                    "score": result["score"],
                }
            )

    return sorted(grouped.values(), key=lambda item: item["score"], reverse=True)


def rank_professors(
    query: str,
    top_k: int = 3,
    chunks_path: str | Path = DEFAULT_CHUNKS_PATH,
    embeddings_path: str | Path = DEFAULT_EMBEDDINGS_PATH,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    encoder_name: str = "local",
) -> list[RankedProfessor]:
    chunks = load_chunks(chunks_path)
    embedding_index = load_embedding_index(index_path)
    embeddings = np.load(embeddings_path)

    encoder = get_encoder(encoder_name)
    query_embedding = encoder.encode([query])
    scores = cosine_similarity(query_embedding, embeddings)

    chunk_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    best_positions = np.argsort(scores)[::-1]
    chunk_results = []

    for position in best_positions:
        position = int(position)
        if position >= len(embedding_index):
            continue

        index_item = embedding_index[position]
        chunk = chunk_by_id.get(index_item["chunk_id"])
        if not chunk:
            continue

        chunk_results.append({**chunk, "score": float(scores[position])})

    grouped_results = group_chunk_results_by_professor(chunk_results)

    return [
        RankedProfessor(
            professor=item["professor"],
            score=float(item["score"]),
            reason="Maior similaridade cosseno entre os chunks do professor.",
            evidences=item["evidences"],
        )
        for item in grouped_results[:top_k]
    ]


def professor_from_chunk(chunk: dict) -> Professor:
    return Professor(
        id=chunk["professor_id"],
        full_name=chunk["full_name"],
        email=chunk.get("email", ""),
        lattes_url=chunk.get("lattes_url", ""),
        department_profile_url=chunk.get("department_profile_url", ""),
    )
