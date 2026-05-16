import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.models import Professor
from src.storage import load_json, save_json


# Gera embeddings para todos os chunks.
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate professor chunk embeddings.")
    parser.add_argument("--input", default=str(ROOT_DIR / "data" / "processed" / "professor_profiles.json"))
    parser.add_argument("--chunks-output", default=str(ROOT_DIR / "data" / "processed" / "professor_chunks.json"))
    parser.add_argument("--embeddings-output", default=str(ROOT_DIR / "data" / "embeddings" / "professor_chunk_embeddings.npy"))
    parser.add_argument("--index-output", default=str(ROOT_DIR / "data" / "embeddings" / "professor_chunk_embedding_index.json"))
    parser.add_argument("--encoder", default="local")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Arquivo não encontrado: {args.input}")
        print("Rode primeiro: python scripts/build_profiles.py")
        return

    professors = load_professor_profiles(input_path)
    if not professors:
        print("Nenhum professor encontrado no arquivo de perfis.")
        return

    chunks = build_all_chunks(professors)
    if not chunks:
        print("Nenhum chunk foi gerado.")
        return

    save_json(args.chunks_output, chunks)

    from src.encoder import get_encoder

    encoder = get_encoder(args.encoder)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = encoder.encode(texts)
    embeddings = np.asarray(embeddings, dtype=np.float32)
    save_embeddings(embeddings, args.embeddings_output)

    index = build_embedding_index(chunks)
    save_json(args.index_output, index)

    section_counts = Counter(chunk["section"] for chunk in chunks)

    print(f"Arquivo carregado: {args.input}")
    print(f"Total de professores carregados: {len(professors)}")
    print(f"Total de chunks gerados: {len(chunks)}")
    print("Total de chunks por seção:")
    for section, count in sorted(section_counts.items()):
        print(f"- {section}: {count}")
    print(f"Encoder usado: {args.encoder}")
    print(f"Shape dos embeddings: {embeddings.shape}")
    print(f"Caminho dos chunks salvo: {args.chunks_output}")
    print(f"Caminho dos embeddings salvo: {args.embeddings_output}")
    print(f"Caminho do índice salvo: {args.index_output}")


# Carrega os perfis dos professores.
def load_professor_profiles(path: str | Path) -> list[Professor]:
    data = load_json(path, default=[])
    return [Professor(**item) for item in data]


# Limpa espaços repetidos.
def clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


# Transforma strings, listas e dicionários em texto simples.
def text_from_value(value: Any) -> str:
    if isinstance(value, dict):
        parts = [
            value.get("title", ""),
            value.get("year", ""),
            value.get("type", ""),
            value.get("description", ""),
        ]
        return clean_text(" ".join(str(part) for part in parts if part))

    return clean_text(value)


# Cria um chunk com metadados do professor.
def create_chunk(professor: Professor, section: str, title: str, text: str, count: int) -> dict[str, str]:
    clean_chunk_text = clean_text(text)
    chunk_id = f"{professor.id}_{section}_{count:03d}"

    return {
        "chunk_id": chunk_id,
        "professor_id": professor.id,
        "full_name": professor.full_name,
        "email": professor.email,
        "lattes_url": professor.lattes_url,
        "department_profile_url": professor.department_profile_url,
        "section": section,
        "title": title,
        "text": clean_chunk_text,
    }


# Adiciona um chunk ignorando texto vazio.
def add_chunk(chunks: list[dict[str, str]], counts: dict[str, int], professor: Professor, section: str, title: str, text: str) -> None:
    clean_chunk_text = clean_text(text)
    if not clean_chunk_text:
        return

    counts[section] = counts.get(section, 0) + 1
    chunks.append(create_chunk(professor, section, title, clean_chunk_text, counts[section]))


# Adiciona chunks a partir de uma lista ou string.
def add_value_chunks(chunks: list[dict[str, str]], counts: dict[str, int], professor: Professor, section: str, title: str, value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            add_chunk(chunks, counts, professor, section, title, text_from_value(item))
        return

    add_chunk(chunks, counts, professor, section, title, text_from_value(value))


# Cria os chunks de texto de um professor.
def build_chunks_for_professor(professor: Professor) -> list[dict[str, str]]:
    chunks = []
    counts = {}

    profile_text = "\n".join(
        [
            professor.full_name,
            professor.department_name,
            professor.institution_name,
            professor.profile_text_for_ranking,
        ]
    )
    add_chunk(chunks, counts, professor, "professor_profile", "Perfil geral do professor", profile_text)
    add_chunk(chunks, counts, professor, "department_text", "Texto do departamento", professor.department_text)
    add_chunk(chunks, counts, professor, "lattes_summary", "Resumo do Lattes", professor.lattes_summary)
    add_value_chunks(chunks, counts, professor, "academic_background", "Formação acadêmica", professor.academic_background)
    add_value_chunks(chunks, counts, professor, "research_areas", "Áreas de atuação", professor.research_areas)
    add_value_chunks(chunks, counts, professor, "current_projects", "Projetos atuais", professor.current_projects)
    add_value_chunks(chunks, counts, professor, "publications", "Publicações", professor.publications)

    return chunks


# Cria todos os chunks dos professores.
def build_all_chunks(professors: list[Professor]) -> list[dict[str, str]]:
    chunks = []
    for professor in professors:
        chunks.extend(build_chunks_for_professor(professor))

    return chunks


# Cria o índice dos embeddings dos chunks.
def build_embedding_index(chunks: list[dict[str, str]]) -> list[dict[str, str | int]]:
    return [
        {
            "index": index,
            "chunk_id": chunk["chunk_id"],
            "professor_id": chunk["professor_id"],
            "full_name": chunk["full_name"],
            "section": chunk["section"],
            "title": chunk["title"],
            "email": chunk["email"],
            "lattes_url": chunk["lattes_url"],
            "department_profile_url": chunk["department_profile_url"],
        }
        for index, chunk in enumerate(chunks)
    ]


# Salva a matriz de embeddings.
def save_embeddings(embeddings: np.ndarray, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, embeddings)


if __name__ == "__main__":
    main()
