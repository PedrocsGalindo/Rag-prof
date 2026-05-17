import argparse
import re
import sys
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


MIN_RECORD_CHARS = 30
MAX_ACADEMIC_BACKGROUND_RECORDS = 30

GENERIC_TEXTS = [
    "Formação não informada",
    "Perfil pessoal não cadastrado",
    "Formação acadêmica não cadastrada",
    "não informada",
    "Currículo Lattes: link não informado",
    "Ordenar por",
    "Ordem Cronológica",
    "Bancas",
    "Eventos",
    "Orientações",
    "Produção bibliográfica",
    "Textos em jornais de notícias/revistas",
    "Trabalhos completos publicados em anais de congressos",
    "Resumos expandidos publicados em anais de congressos",
    "Demais tipos de produção técnica",
    "Participação em bancas",
    "Participação em eventos",
    "Compreende Bem",
    "Fala Bem",
    "Lê Bem",
    "Escreve Bem",
    "Professor Homenageado",
    "Página gerada pelo Sistema Currículo Lattes",
    "Configuração de privacidade",
    "CNPq | Uma agência",
]


# Gera os records e embeddings locais.
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate local vector-store files.")
    parser.add_argument("--input", default=str(ROOT_DIR / "data" / "processed" / "professor_profiles.json"))
    parser.add_argument("--catalog-output", default=str(ROOT_DIR / "data" / "processed" / "professor_catalog.json"))
    parser.add_argument("--profile-records-output", default=str(ROOT_DIR / "data" / "processed" / "professor_profile_records.json"))
    parser.add_argument("--chunk-records-output", default=str(ROOT_DIR / "data" / "processed" / "professor_chunk_records.json"))
    parser.add_argument("--legacy-chunks-output", default=str(ROOT_DIR / "data" / "processed" / "professor_chunks.json"))
    parser.add_argument("--profile-embeddings-output", default=str(ROOT_DIR / "data" / "embeddings" / "professor_profile_embeddings.npy"))
    parser.add_argument("--profile-index-output", default=str(ROOT_DIR / "data" / "embeddings" / "professor_profile_embedding_index.json"))
    parser.add_argument("--chunk-embeddings-output", default=str(ROOT_DIR / "data" / "embeddings" / "professor_chunk_embeddings.npy"))
    parser.add_argument("--chunk-index-output", default=str(ROOT_DIR / "data" / "embeddings" / "professor_chunk_embedding_index.json"))
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

    catalog = build_professor_catalog(professors)
    profile_records, ignored_profile_records = build_profile_records(professors)
    chunk_records, ignored_chunk_records = build_chunk_records(professors)
    ignored_records = ignored_profile_records + ignored_chunk_records

    if not profile_records:
        print("Nenhum profile record útil foi gerado.")
        return

    if not chunk_records:
        print("Nenhum chunk record útil foi gerado.")
        return

    save_json(args.catalog_output, catalog)
    save_json(args.profile_records_output, profile_records)
    save_json(args.chunk_records_output, chunk_records)
    save_json(args.legacy_chunks_output, build_legacy_chunks(chunk_records, catalog))

    from src.encoder import get_encoder

    encoder = get_encoder(args.encoder)
    profile_embeddings = encode_records(encoder, profile_records)
    chunk_embeddings = encode_records(encoder, chunk_records)

    save_embeddings(profile_embeddings, args.profile_embeddings_output)
    save_embeddings(chunk_embeddings, args.chunk_embeddings_output)
    save_json(args.profile_index_output, build_embedding_index(profile_records))
    save_json(args.chunk_index_output, build_embedding_index(chunk_records))

    print(f"Arquivo carregado: {args.input}")
    print(f"Total de professores no catálogo: {len(catalog)}")
    print(f"Total de professor_profile_records gerados: {len(profile_records)}")
    print(f"Total de professor_chunk_records gerados: {len(chunk_records)}")
    print(f"Total de chunks ignorados por baixa qualidade: {ignored_records}")
    print(f"Shape de professor_profile_embeddings: {profile_embeddings.shape}")
    print(f"Shape de professor_chunk_embeddings: {chunk_embeddings.shape}")
    print(f"Catálogo salvo em: {args.catalog_output}")
    print(f"Profile records salvos em: {args.profile_records_output}")
    print(f"Chunk records salvos em: {args.chunk_records_output}")
    print(f"Embeddings gerais salvos em: {args.profile_embeddings_output}")
    print(f"Índice geral salvo em: {args.profile_index_output}")
    print(f"Embeddings dos chunks salvos em: {args.chunk_embeddings_output}")
    print(f"Índice dos chunks salvo em: {args.chunk_index_output}")


# Carrega os perfis dos professores.
def load_professor_profiles(path: str | Path) -> list[Professor]:
    data = load_json(path, default=[])
    return [professor_from_dict(item) for item in data]


# Cria o catálogo com os dados repetidos de cada professor.
def build_professor_catalog(professors: list[Professor]) -> list[dict[str, str]]:
    return [
        {
            "professor_id": professor.id,
            "full_name": professor.full_name,
            "email": professor.email,
            "lattes_url": professor.lattes_url,
            "department_profile_url": professor.department_profile_url,
            "department_name": professor.department_name,
            "institution_name": professor.institution_name,
        }
        for professor in professors
    ]


# Cria um record geral por professor.
def build_profile_records(professors: list[Professor]) -> tuple[list[dict], int]:
    records = []
    ignored = 0

    for professor in professors:
        text, sections_used = build_general_professor_text(professor)
        if not is_useful_record_text(text, "professor_profile"):
            ignored += 1
            continue

        records.append(
            {
                "record_id": f"{professor.id}_profile",
                "professor_id": professor.id,
                "record_type": "professor_profile",
                "section": "professor_profile",
                "title": "Perfil geral do professor",
                "text": text,
                "metadata": {
                    "sections_used": sections_used,
                    "quality_score": 1.0,
                },
            }
        )

    return records, ignored


# Cria os records de chunks específicos.
def build_chunk_records(professors: list[Professor]) -> tuple[list[dict], int]:
    records = []
    ignored = 0

    for professor in professors:
        professor_records, professor_ignored = build_chunk_records_for_professor(professor)
        records.extend(professor_records)
        ignored += professor_ignored

    return records, ignored


# Cria os chunks de texto de um professor.
def build_chunk_records_for_professor(professor: Professor) -> tuple[list[dict], int]:
    records = []
    counts: dict[str, int] = {}
    ignored = 0

    ignored += add_record(records, counts, professor, "lattes_summary", "Resumo do Lattes", professor.lattes_summary)
    ignored += add_record(records, counts, professor, "department_text", "Texto do departamento", professor.department_text)

    for area in professor.research_areas:
        ignored += add_record(records, counts, professor, "research_areas", "Área de atuação", area)

    for line in professor.research_lines:
        ignored += add_record(records, counts, professor, "research_lines", "Linha de pesquisa", line)

    for item in professor.academic_background[:MAX_ACADEMIC_BACKGROUND_RECORDS]:
        background = academic_background_from_dict(item)
        ignored += add_record(
            records,
            counts,
            professor,
            "academic_background",
            academic_background_title(background),
            academic_background_text(background),
            metadata={
                "start_year": background.start_year,
                "end_year": background.end_year,
                "degree": background.degree,
            },
        )

    for item in professor.current_projects:
        project = research_project_from_dict(item)
        ignored += add_record(
            records,
            counts,
            professor,
            "current_projects",
            research_project_title(project),
            research_project_text(project),
            metadata={
                "start_year": project.start_year,
                "end_year": project.end_year,
                "status": project.status,
            },
        )

    for item in professor.publications:
        publication = publication_from_dict(item)
        ignored += add_record(
            records,
            counts,
            professor,
            "publications",
            publication_title(publication),
            publication_text(publication),
            metadata={
                "year": publication.year,
                "publication_type": publication.publication_type,
            },
        )

    return records, ignored


# Adiciona um record se o texto for útil.
def add_record(
    records: list[dict],
    counts: dict[str, int],
    professor: Professor,
    section: str,
    title: str,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> int:
    clean_record_text = clean_text(text)
    if not is_useful_record_text(clean_record_text, section):
        return 1

    counts[section] = counts.get(section, 0) + 1
    record_id = f"{professor.id}_{section}_{counts[section]:03d}"
    records.append(
        {
            "record_id": record_id,
            "professor_id": professor.id,
            "record_type": "chunk",
            "section": section,
            "title": title,
            "text": clean_record_text,
            "metadata": build_record_metadata(section, metadata),
        }
    )
    return 0


# Monta metadados simples para os records.
def build_record_metadata(section: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = {
        "source_field": section,
        "start_year": "",
        "end_year": "",
        "year": "",
        "degree": "",
        "publication_type": "",
        "status": "",
        "quality_score": 1.0,
    }

    if extra:
        metadata.update({key: value for key, value in extra.items() if value is not None})

    return metadata


# Monta um texto geral curto e representativo.
def build_general_professor_text(professor: Professor) -> tuple[str, list[str]]:
    parts = [
        f"Nome: {professor.full_name}",
        f"Departamento: {professor.department_name}",
        f"Instituição: {professor.institution_name}",
    ]
    sections_used = []

    if professor.lattes_summary:
        parts.append(f"Resumo Lattes: {professor.lattes_summary}")
        sections_used.append("lattes_summary")

    if professor.research_areas:
        parts.append(f"Áreas de atuação: {'; '.join(professor.research_areas[:8])}")
        sections_used.append("research_areas")

    if professor.research_lines:
        parts.append(f"Linhas de pesquisa: {'; '.join(professor.research_lines[:5])}")
        sections_used.append("research_lines")

    project_texts = [
        short_text(research_project_text(item), 220)
        for item in professor.current_projects[:5]
        if research_project_text(item)
    ]
    if project_texts:
        parts.append(f"Projetos: {'; '.join(project_texts)}")
        sections_used.append("current_projects")

    publication_texts = [
        short_text(publication_text(item), 180)
        for item in professor.publications[:5]
        if publication_text(item)
    ]
    if publication_texts:
        parts.append(f"Publicações: {'; '.join(publication_texts)}")
        sections_used.append("publications")

    return clean_text("\n".join(parts)), sections_used


# Decide se um texto deve virar embedding.
def is_useful_record_text(text: str, section: str) -> bool:
    cleaned_text = clean_text(text)
    normalized_text = normalize_text(cleaned_text)

    if not cleaned_text:
        return False

    if len(cleaned_text) < MIN_RECORD_CHARS:
        return section == "research_areas" and ("grande area" in normalized_text or "area:" in normalized_text)

    for generic_text in GENERIC_TEXTS:
        normalized_generic = normalize_text(generic_text)
        if normalized_text == normalized_generic or normalized_text.startswith(normalized_generic):
            return False
        if normalized_generic in normalized_text and section in {"department_text", "research_areas"}:
            return False

    if section == "department_text":
        empty_profile_texts = [
            "formacao nao informada",
            "perfil pessoal nao cadastrado",
            "formacao academica nao cadastrada",
            "nao informada",
        ]
        if normalized_text in empty_profile_texts:
            return False

    return True


# Mantém um professor_chunks.json simples para compatibilidade.
def build_legacy_chunks(chunk_records: list[dict], catalog: list[dict]) -> list[dict]:
    catalog_by_id = {item["professor_id"]: item for item in catalog}
    chunks = []

    for record in chunk_records:
        professor = catalog_by_id.get(record["professor_id"], {})
        chunks.append(
            {
                "chunk_id": record["record_id"],
                "professor_id": record["professor_id"],
                "full_name": professor.get("full_name", ""),
                "email": professor.get("email", ""),
                "lattes_url": professor.get("lattes_url", ""),
                "department_profile_url": professor.get("department_profile_url", ""),
                "section": record["section"],
                "title": record["title"],
                "text": record["text"],
            }
        )

    return chunks


# Cria o índice dos embeddings.
def build_embedding_index(records: list[dict]) -> list[dict[str, str | int]]:
    return [
        {
            "index": index,
            "record_id": record["record_id"],
            "professor_id": record["professor_id"],
            "section": record["section"],
            "title": record["title"],
        }
        for index, record in enumerate(records)
    ]


# Gera embeddings para uma lista de records.
def encode_records(encoder, records: list[dict]) -> np.ndarray:
    texts = [record["text"] for record in records]
    embeddings = encoder.encode(texts)
    return np.asarray(embeddings, dtype=np.float32)


# Salva a matriz de embeddings.
def save_embeddings(embeddings: np.ndarray, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, embeddings)


# Limpa espaços repetidos.
def clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


# Normaliza texto para comparação simples.
def normalize_text(text: Any) -> str:
    text = clean_text(text)
    text = re.sub(r"[áàâã]", "a", text, flags=re.IGNORECASE)
    text = re.sub(r"[éèê]", "e", text, flags=re.IGNORECASE)
    text = re.sub(r"[íìî]", "i", text, flags=re.IGNORECASE)
    text = re.sub(r"[óòôõ]", "o", text, flags=re.IGNORECASE)
    text = re.sub(r"[úùû]", "u", text, flags=re.IGNORECASE)
    text = re.sub(r"ç", "c", text, flags=re.IGNORECASE)
    return text.lower()


# Monta texto curto para listas do perfil geral.
def short_text(text: str, max_length: int = 200) -> str:
    text = clean_text(text)
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


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
    return background.degree or background.course or short_text(background.description, 80) or "Formação acadêmica"


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
    return project.title or short_text(project.description, 80) or "Projeto de pesquisa"


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
    return publication.title or short_text(publication.description, 80) or "Publicação"


if __name__ == "__main__":
    main()
