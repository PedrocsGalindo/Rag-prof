import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.models import (
    AcademicBackground,
    Professor,
    Publication,
    ResearchProject,
    academic_background_from_dict,
    professor_from_dict,
    publication_from_dict,
    research_project_from_dict,
)
from src.storage import load_json, save_json


MIN_CHUNK_CHARS = 30
MAX_ACADEMIC_BACKGROUND_CHUNKS = 30

IGNORED_DEPARTMENT_TEXTS = [
    "Formação não informada",
    "Perfil pessoal não cadastrado",
    "Formação acadêmica não cadastrada",
]

INVALID_CHUNK_TEXTS = [
    "Ordenar por",
    "Ordem Cronológica",
    "Capítulos de livros publicados",
    "Bancas",
    "Eventos",
    "Orientações",
]


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
    return [professor_from_dict(item) for item in data]


# Limpa espaços repetidos.
def clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


# Transforma valores simples, listas e dicionários em texto.
def text_from_value(value: Any) -> str:
    if isinstance(value, dict):
        parts = [item for item in value.values() if item]
        return clean_text(" ".join(str(part) for part in parts if part))

    return clean_text(value)


# Monta um rótulo simples para anos de início e fim.
def years_text(start_year: str, end_year: str) -> str:
    if start_year and end_year:
        return f"{start_year} - {end_year}"

    return start_year or end_year


# Monta o texto de uma formação acadêmica.
def academic_background_text(item: AcademicBackground | dict | str) -> str:
    background = academic_background_from_dict(item)
    if background.degree and background.course:
        course_text = f"{background.degree} em {background.course}"
    else:
        course_text = background.degree or background.course

    parts = [
        years_text(background.start_year, background.end_year),
        course_text,
        background.institution,
        background.description,
    ]
    return clean_text(" ".join(part for part in parts if part))


# Define o título de uma formação acadêmica.
def academic_background_title(item: AcademicBackground | dict | str) -> str:
    background = academic_background_from_dict(item)

    if background.degree and background.course:
        return f"{background.degree} em {background.course}"

    return background.degree or background.course or short_title(background.description) or "Formação acadêmica"


# Monta o texto de um projeto de pesquisa.
def research_project_text(item: ResearchProject | dict | str) -> str:
    project = research_project_from_dict(item)
    parts = [
        years_text(project.start_year, project.end_year),
        project.title,
        project.status,
        project.description,
    ]
    return clean_text(" ".join(part for part in parts if part))


# Define o título de um projeto de pesquisa.
def research_project_title(item: ResearchProject | dict | str) -> str:
    project = research_project_from_dict(item)
    return project.title or short_title(project.description) or "Projeto de pesquisa"


# Monta o texto de uma publicação.
def publication_text(item: Publication | dict | str) -> str:
    publication = publication_from_dict(item)
    parts = [
        publication.year,
        publication.title,
        publication.authors,
        publication.publication_type,
        publication.description,
    ]
    return clean_text(" ".join(part for part in parts if part))


# Define o título de uma publicação.
def publication_title(item: Publication | dict | str) -> str:
    publication = publication_from_dict(item)
    return publication.title or short_title(publication.description) or "Publicação"


# Encurta títulos grandes usados nos metadados dos chunks.
def short_title(text: str, max_length: int = 80) -> str:
    title = clean_text(text)

    if len(title) <= max_length:
        return title

    return title[:max_length].rstrip() + "..."


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
    if len(clean_chunk_text) < MIN_CHUNK_CHARS or is_invalid_chunk_text(clean_chunk_text):
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


# Adiciona chunks de formação acadêmica.
def add_academic_background_chunks(chunks: list[dict[str, str]], counts: dict[str, int], professor: Professor) -> None:
    for item in professor.academic_background[:MAX_ACADEMIC_BACKGROUND_CHUNKS]:
        add_chunk(
            chunks,
            counts,
            professor,
            "academic_background",
            academic_background_title(item),
            academic_background_text(item),
        )


# Adiciona chunks de linhas de pesquisa.
def add_research_line_chunks(chunks: list[dict[str, str]], counts: dict[str, int], professor: Professor) -> None:
    for line in professor.research_lines:
        add_chunk(chunks, counts, professor, "research_lines", "Linha de pesquisa", line)


# Adiciona chunks de projetos.
def add_project_chunks(chunks: list[dict[str, str]], counts: dict[str, int], professor: Professor) -> None:
    for item in professor.current_projects:
        add_chunk(
            chunks,
            counts,
            professor,
            "current_projects",
            research_project_title(item),
            research_project_text(item),
        )


# Adiciona chunks de publicações.
def add_publication_chunks(chunks: list[dict[str, str]], counts: dict[str, int], professor: Professor) -> None:
    for item in professor.publications:
        add_chunk(
            chunks,
            counts,
            professor,
            "publications",
            publication_title(item),
            publication_text(item),
        )


# Monta um perfil geral curto, sem colocar o Lattes inteiro no chunk.
def build_general_profile_text(professor: Professor) -> str:
    parts = [
        f"Nome: {professor.full_name}",
        f"Departamento: {professor.department_name}",
        f"Instituição: {professor.institution_name}",
    ]

    if professor.lattes_summary:
        parts.append(f"Resumo Lattes: {professor.lattes_summary}")

    if professor.research_areas:
        parts.append(f"Principais áreas: {'; '.join(professor.research_areas[:5])}")

    if professor.research_lines:
        parts.append(f"Principais linhas de pesquisa: {'; '.join(professor.research_lines[:5])}")

    return "\n".join(part for part in parts if clean_text(part))


# Evita chunks com placeholders ou textos de navegação.
def is_invalid_chunk_text(text: str) -> bool:
    normalized_text = clean_text(text).lower()

    for invalid_text in INVALID_CHUNK_TEXTS:
        if normalized_text == invalid_text.lower():
            return True

    return False


# Ignora textos vazios ou placeholders do perfil do departamento.
def should_skip_department_text(text: str) -> bool:
    normalized_text = clean_text(text).lower()
    return any(normalized_text == value.lower() for value in IGNORED_DEPARTMENT_TEXTS)


# Cria os chunks de texto de um professor.
def build_chunks_for_professor(professor: Professor) -> list[dict[str, str]]:
    chunks = []
    counts = {}

    profile_text = build_general_profile_text(professor)
    add_chunk(chunks, counts, professor, "professor_profile", "Perfil geral do professor", profile_text)
    if not should_skip_department_text(professor.department_text):
        add_chunk(chunks, counts, professor, "department_text", "Texto do departamento", professor.department_text)
    add_chunk(chunks, counts, professor, "lattes_summary", "Resumo do Lattes", professor.lattes_summary)
    add_value_chunks(chunks, counts, professor, "research_areas", "Áreas de atuação", professor.research_areas)
    add_research_line_chunks(chunks, counts, professor)
    add_academic_background_chunks(chunks, counts, professor)
    add_project_chunks(chunks, counts, professor)
    add_publication_chunks(chunks, counts, professor)

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
