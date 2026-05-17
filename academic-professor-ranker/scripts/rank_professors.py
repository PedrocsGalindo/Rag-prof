import argparse
import re
import sys
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.ranker import (
    get_last_ranking_info,
    load_chunks,
    load_embedding_index,
    rank_professors,
    rank_professors_hybrid,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank professors for a text query.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--mode", choices=["hybrid", "chunks"], default="hybrid")
    parser.add_argument("--ranking-profile", default=None)
    parser.add_argument("--first-stage-k", type=int, default=10)
    parser.add_argument("--chunks", default=str(ROOT_DIR / "data" / "processed" / "professor_chunks.json"))
    parser.add_argument("--embeddings", default=str(ROOT_DIR / "data" / "embeddings" / "professor_chunk_embeddings.npy"))
    parser.add_argument("--index", default=str(ROOT_DIR / "data" / "embeddings" / "professor_chunk_embedding_index.json"))
    args = parser.parse_args()

    if args.mode == "hybrid":
        ranking = rank_professors_hybrid(
            query=args.query,
            top_k=args.top_k,
            first_stage_k=args.first_stage_k,
            ranking_profile=args.ranking_profile,
        )
        print_hybrid_summary(args.query, ranking)
    else:
        ranking = rank_professors(
            query=args.query,
            top_k=args.top_k,
            chunks_path=args.chunks,
            embeddings_path=args.embeddings,
            index_path=args.index,
        )
        print_chunks_summary(args.query, ranking, args.chunks, args.embeddings, args.index)

    for position, ranked_professor in enumerate(ranking, start=1):
        print_ranked_professor(position, ranked_professor)


def print_hybrid_summary(query: str, ranking) -> None:
    info = get_last_ranking_info()
    print(f"Modo usado: {info.get('mode', 'hybrid')}")
    print(f"Perfil de ponderação usado: {info.get('ranking_profile', '')}")
    print(f"Query recebida: {query}")
    print(f"Total de professores avaliados na primeira etapa: {info.get('first_stage_professors_evaluated', 0)}")
    print(f"Total de chunks avaliados na segunda etapa: {info.get('second_stage_chunks_evaluated', 0)}")
    print(f"Top_k retornado: {len(ranking)}")


def print_chunks_summary(query: str, ranking, chunks_path: str, embeddings_path: str, index_path: str) -> None:
    print("Modo usado: chunks")
    print("Perfil de ponderação usado: não aplicado")
    print(f"Query recebida: {query}")
    print(f"Total de professores avaliados na primeira etapa: 0")
    print(f"Total de chunks avaliados na segunda etapa: {count_chunks(chunks_path, embeddings_path, index_path)}")
    print(f"Top_k retornado: {len(ranking)}")


def count_chunks(chunks_path: str, embeddings_path: str, index_path: str) -> int:
    chunks = load_chunks(chunks_path)
    index = load_embedding_index(index_path)
    embeddings = np.load(embeddings_path)
    return min(len(chunks), len(index), len(embeddings))


def print_ranked_professor(position, ranked_professor) -> None:
    professor = ranked_professor.professor

    print()
    print(f"{position}. {professor.full_name}")
    print(f"Score: {ranked_professor.score:.4f}")
    print(f"E-mail: {professor.email}")
    print(f"Lattes: {professor.lattes_url}")
    print(f"Perfil: {professor.department_profile_url}")
    print()
    print("Evidências encontradas:")

    if not ranked_professor.evidences:
        print("- Nenhuma evidência específica encontrada.")
        return

    for evidence in ranked_professor.evidences[:3]:
        section = evidence.get("section", "")
        title = evidence.get("title", "")
        label = section if not title else f"{section} | {title}"
        print(f"- [{label}] {make_snippet(evidence.get('text', ''))}")


def make_snippet(text: str, max_length: int = 300) -> str:
    snippet = re.sub(r"\s+", " ", text or "").strip()

    if len(snippet) <= max_length:
        return snippet

    return snippet[:max_length].rstrip() + "..."


if __name__ == "__main__":
    main()
