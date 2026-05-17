import argparse
import re
import sys
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.ranker import load_chunks, load_embedding_index, rank_professors


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank professors for a text query.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--chunks", default=str(ROOT_DIR / "data" / "processed" / "professor_chunks.json"))
    parser.add_argument("--embeddings", default=str(ROOT_DIR / "data" / "embeddings" / "professor_chunk_embeddings.npy"))
    parser.add_argument("--index", default=str(ROOT_DIR / "data" / "embeddings" / "professor_chunk_embedding_index.json"))
    args = parser.parse_args()

    ranking = rank_professors(
        query=args.query,
        top_k=args.top_k,
        chunks_path=args.chunks,
        embeddings_path=args.embeddings,
        index_path=args.index,
    )

    print(f"Query recebida: {args.query}")
    print(f"Total de chunks comparados: {count_chunks(args.chunks, args.embeddings, args.index)}")
    print(f"Total de professores encontrados no ranking: {len(ranking)}")

    for position, ranked_professor in enumerate(ranking, start=1):
        print_ranked_professor(position, ranked_professor)


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

    for evidence in ranked_professor.evidences[:3]:
        print(f"- [{evidence['section']}] {make_snippet(evidence['text'])}")


def make_snippet(text: str, max_length: int = 300) -> str:
    snippet = re.sub(r"\s+", " ", text or "").strip()

    if len(snippet) <= max_length:
        return snippet

    return snippet[:max_length].rstrip() + "..."


if __name__ == "__main__":
    main()
