from pathlib import Path

import numpy as np

from .encoder import get_encoder
from .models import Professor, RankedProfessor
from .ranking_config import get_ranking_profile
from .storage import load_json


DEFAULT_CHUNKS_PATH = Path("data/processed/professor_chunks.json")
DEFAULT_EMBEDDINGS_PATH = Path("data/embeddings/professor_chunk_embeddings.npy")
DEFAULT_INDEX_PATH = Path("data/embeddings/professor_chunk_embedding_index.json")
DEFAULT_CATALOG_PATH = Path("data/processed/professor_catalog.json")
DEFAULT_PROFILE_RECORDS_PATH = Path("data/processed/professor_profile_records.json")
DEFAULT_PROFILE_EMBEDDINGS_PATH = Path("data/embeddings/professor_profile_embeddings.npy")
DEFAULT_PROFILE_INDEX_PATH = Path("data/embeddings/professor_profile_embedding_index.json")
DEFAULT_CHUNK_RECORDS_PATH = Path("data/processed/professor_chunk_records.json")
DEFAULT_CHUNK_EMBEDDINGS_PATH = Path("data/embeddings/professor_chunk_embeddings.npy")
DEFAULT_CHUNK_INDEX_PATH = Path("data/embeddings/professor_chunk_embedding_index.json")

LAST_RANKING_INFO = {}


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


def load_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> list[dict]:
    return load_json(path, default=[])


def load_records(path: str | Path) -> list[dict]:
    return load_json(path, default=[])


def group_chunk_results_by_professor(results: list[dict]) -> list[dict]:
    grouped = {}

    for result in results:
        professor_id = result.get("professor_id")
        if not professor_id:
            continue

        if professor_id not in grouped:
            grouped[professor_id] = {
                "professor": professor_from_chunk(result),
                "score": result["score"],
                "evidences": [],
            }

        grouped[professor_id]["score"] = max(grouped[professor_id]["score"], result["score"])
        evidence_text = result.get("text", "")
        if evidence_text and len(grouped[professor_id]["evidences"]) < 3:
            grouped[professor_id]["evidences"].append(
                {
                    "section": result.get("section", ""),
                    "title": result.get("title", ""),
                    "text": evidence_text,
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

    chunk_by_id = {
        chunk.get("record_id") or chunk.get("chunk_id"): chunk
        for chunk in chunks
        if chunk.get("record_id") or chunk.get("chunk_id")
    }
    best_positions = np.argsort(scores)[::-1]
    chunk_results = []

    for position in best_positions:
        position = int(position)
        if position >= len(embedding_index):
            continue

        index_item = embedding_index[position]
        record_id = index_item.get("record_id") or index_item.get("chunk_id")
        chunk = chunk_by_id.get(record_id)
        if not chunk or not chunk.get("text", ""):
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


def rank_professors_hybrid(
    query: str,
    top_k: int = 3,
    first_stage_k: int = 10,
    ranking_profile: str | None = None,
    encoder_name: str = "local",
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
    profile_records_path: str | Path = DEFAULT_PROFILE_RECORDS_PATH,
    profile_embeddings_path: str | Path = DEFAULT_PROFILE_EMBEDDINGS_PATH,
    profile_index_path: str | Path = DEFAULT_PROFILE_INDEX_PATH,
    chunk_records_path: str | Path = DEFAULT_CHUNK_RECORDS_PATH,
    chunk_embeddings_path: str | Path = DEFAULT_CHUNK_EMBEDDINGS_PATH,
    chunk_index_path: str | Path = DEFAULT_CHUNK_INDEX_PATH,
) -> list[RankedProfessor]:
    profile_name, profile_config = get_ranking_profile(ranking_profile)
    catalog = load_catalog(catalog_path)
    profile_records = load_records(profile_records_path)
    profile_index = load_embedding_index(profile_index_path)
    profile_embeddings = np.load(profile_embeddings_path)

    encoder = get_encoder(encoder_name)
    query_embedding = encoder.encode([query])
    profile_scores = cosine_similarity(query_embedding, profile_embeddings)

    catalog_by_id = {item["professor_id"]: item for item in catalog}
    profile_record_by_id = {record["record_id"]: record for record in profile_records}
    first_stage_results = build_first_stage_results(profile_index, profile_record_by_id, profile_scores)
    selected_results = first_stage_results[:first_stage_k]
    selected_professor_ids = {item["professor_id"] for item in selected_results}

    chunk_records = load_records(chunk_records_path)
    chunk_index = load_embedding_index(chunk_index_path)
    chunk_embeddings = np.load(chunk_embeddings_path)
    chunk_scores = cosine_similarity(query_embedding, chunk_embeddings)
    chunk_record_by_id = {record["record_id"]: record for record in chunk_records}
    chunk_results = build_chunk_results(
        chunk_index,
        chunk_record_by_id,
        chunk_scores,
        selected_professor_ids,
        profile_config.get("section_weights", {}),
    )

    ranking = build_hybrid_ranking(
        selected_results,
        chunk_results,
        catalog_by_id,
        profile_config.get("final_score_weights", {}),
        top_k,
    )

    global LAST_RANKING_INFO
    LAST_RANKING_INFO = {
        "mode": "hybrid",
        "ranking_profile": profile_name,
        "first_stage_professors_evaluated": len(first_stage_results),
        "second_stage_chunks_evaluated": len(chunk_results),
        "top_k": top_k,
    }

    return ranking


def build_first_stage_results(profile_index: list[dict], records_by_id: dict, scores: np.ndarray) -> list[dict]:
    results = []

    for item in profile_index:
        position = int(item["index"])
        if position >= len(scores):
            continue

        record = records_by_id.get(item.get("record_id"))
        if not record:
            continue

        results.append(
            {
                "professor_id": record["professor_id"],
                "record_id": record["record_id"],
                "profile_score": float(scores[position]),
            }
        )

    return sorted(results, key=lambda item: item["profile_score"], reverse=True)


def build_chunk_results(
    chunk_index: list[dict],
    records_by_id: dict,
    scores: np.ndarray,
    selected_professor_ids: set[str],
    section_weights: dict,
) -> list[dict]:
    results = []

    for item in chunk_index:
        position = int(item["index"])
        if position >= len(scores):
            continue

        record = records_by_id.get(item.get("record_id"))
        if not record or record.get("professor_id") not in selected_professor_ids:
            continue

        raw_score = float(scores[position])
        section = record.get("section", "")
        section_weight = float(section_weights.get(section, 1.0))
        results.append(
            {
                **record,
                "score": raw_score * section_weight,
                "raw_score": raw_score,
                "section_weight": section_weight,
            }
        )

    return sorted(results, key=lambda item: item["score"], reverse=True)


def build_hybrid_ranking(
    profile_results: list[dict],
    chunk_results: list[dict],
    catalog_by_id: dict,
    final_score_weights: dict,
    top_k: int,
) -> list[RankedProfessor]:
    chunks_by_professor = group_records_by_professor(chunk_results)
    profile_weight = float(final_score_weights.get("profile_score", 0.30))
    best_chunk_weight = float(final_score_weights.get("best_chunk_score", 0.45))
    avg_top_3_weight = float(final_score_weights.get("avg_top_3_chunk_score", 0.25))
    ranked = []

    for profile_result in profile_results:
        professor_id = profile_result["professor_id"]
        professor_chunks = chunks_by_professor.get(professor_id, [])
        best_chunk_score = professor_chunks[0]["score"] if professor_chunks else 0.0
        avg_top_3_chunk_score = average_score(professor_chunks[:3])
        final_score = (
            profile_weight * profile_result["profile_score"]
            + best_chunk_weight * best_chunk_score
            + avg_top_3_weight * avg_top_3_chunk_score
        )

        ranked.append(
            RankedProfessor(
                professor=professor_from_catalog(catalog_by_id.get(professor_id, {"professor_id": professor_id})),
                score=float(final_score),
                reason=(
                    f"profile_score={profile_result['profile_score']:.4f}; "
                    f"best_chunk_score={best_chunk_score:.4f}; "
                    f"avg_top_3_chunk_score={avg_top_3_chunk_score:.4f}"
                ),
                evidences=build_evidences(professor_chunks[:3]),
            )
        )

    return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]


def group_records_by_professor(records: list[dict]) -> dict[str, list[dict]]:
    grouped = {}

    for record in records:
        grouped.setdefault(record["professor_id"], []).append(record)

    for professor_records in grouped.values():
        professor_records.sort(key=lambda item: item["score"], reverse=True)

    return grouped


def average_score(records: list[dict]) -> float:
    if not records:
        return 0.0

    return float(sum(record["score"] for record in records) / len(records))


def build_evidences(records: list[dict]) -> list[dict[str, str | float]]:
    return [
        {
            "section": record.get("section", ""),
            "title": record.get("title", ""),
            "text": record.get("text", ""),
            "score": float(record.get("score", 0.0)),
        }
        for record in records
        if record.get("text")
    ]


def professor_from_catalog(item: dict) -> Professor:
    return Professor(
        id=item.get("professor_id", ""),
        full_name=item.get("full_name", ""),
        email=item.get("email", ""),
        lattes_url=item.get("lattes_url", ""),
        department_profile_url=item.get("department_profile_url", ""),
        department_name=item.get("department_name", ""),
        institution_name=item.get("institution_name", ""),
    )


def professor_from_chunk(chunk: dict) -> Professor:
    return Professor(
        id=chunk.get("professor_id", ""),
        full_name=chunk.get("full_name", ""),
        email=chunk.get("email", ""),
        lattes_url=chunk.get("lattes_url", ""),
        department_profile_url=chunk.get("department_profile_url", ""),
    )


def get_last_ranking_info() -> dict:
    return LAST_RANKING_INFO.copy()
