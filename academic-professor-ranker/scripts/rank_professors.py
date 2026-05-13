import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.ranker import rank_professors


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank professors for a text query.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--profiles", default=str(ROOT_DIR / "data" / "processed" / "professor_profiles.json"))
    parser.add_argument("--embeddings", default=str(ROOT_DIR / "data" / "embeddings" / "professor_embeddings.npy"))
    parser.add_argument("--index", default=str(ROOT_DIR / "data" / "embeddings" / "professor_embedding_index.json"))
    args = parser.parse_args()

    ranking = rank_professors(
        query=args.query,
        top_k=args.top_k,
        profiles_path=args.profiles,
        embeddings_path=args.embeddings,
        index_path=args.index,
    )

    print(f"Query: {args.query}")
    print(f"Top {len(ranking)} professores encontrados")

    for position, ranked_professor in enumerate(ranking, start=1):
        print_ranked_professor(position, ranked_professor)


def print_ranked_professor(position, ranked_professor) -> None:
    professor = ranked_professor.professor

    print()
    print(f"{position}. {professor.full_name}")
    print(f"Score: {ranked_professor.score:.4f}")
    print(f"E-mail: {professor.email}")
    print(f"Lattes: {professor.lattes_url}")
    print(f"Perfil no departamento: {professor.department_profile_url}")
    print(f"Áreas de atuação: {format_list(professor.research_areas)}")

    if professor.current_projects:
        print(f"Projetos atuais: {format_list(professor.current_projects)}")

    print(f"Trecho do perfil: {make_snippet(professor.profile_text_for_ranking)}")


def format_list(items: list[str]) -> str:
    if not items:
        return ""

    return "; ".join(items)


def make_snippet(text: str, max_length: int = 500) -> str:
    snippet = re.sub(r"\s+", " ", text or "").strip()

    if len(snippet) <= max_length:
        return snippet

    return snippet[:max_length].rstrip() + "..."


if __name__ == "__main__":
    main()
