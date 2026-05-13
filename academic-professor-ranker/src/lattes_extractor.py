import re
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .models import Professor


DEFAULT_HEADERS = {
    "User-Agent": "academic-professor-ranker/0.1",
}

SECTION_KEYWORDS = [
    "Resumo",
    "Formação acadêmica",
    "Formação acadêmica/titulação",
    "Áreas de atuação",
    "Projetos de pesquisa",
    "Projetos",
    "Produções bibliográficas",
    "Artigos completos publicados em periódicos",
]


def enrich_professor_with_lattes(
    professor: Professor,
    cache_dir: str | Path = "data/raw/lattes_cache",
    verbose: bool = False,
) -> Professor:
    if not professor.lattes_url:
        return professor

    try:
        html = get_lattes_html(professor, cache_dir=cache_dir, verbose=verbose)
    except requests.RequestException as error:
        if verbose:
            print(f"  Falha ao acessar Lattes: {error}")
        return professor

    extracted = extract_lattes_data(html)

    professor.lattes_summary = extracted["lattes_summary"] or professor.lattes_summary
    professor.academic_background = extracted["academic_background"] or professor.academic_background
    professor.research_areas = extracted["research_areas"] or professor.research_areas
    professor.current_projects = extracted["current_projects"] or professor.current_projects
    professor.publications = extracted["publications"] or professor.publications
    professor.lattes_raw_text = extracted["lattes_raw_text"]
    professor.lattes_clean_text = extracted["lattes_clean_text"]
    add_source(professor, source_type="lattes", url=professor.lattes_url)

    return professor


def enrich_professors_with_lattes(
    professors: list[Professor],
    cache_dir: str | Path = "data/raw/lattes_cache",
    verbose: bool = False,
) -> list[Professor]:
    for index, professor in enumerate(professors, start=1):
        if verbose:
            print(f"Processando Lattes {index}/{len(professors)}: {professor.full_name}")

        if not professor.lattes_url:
            if verbose:
                print("  Sem lattes_url, pulando.")
            continue

        try:
            enrich_professor_with_lattes(
                professor=professor,
                cache_dir=cache_dir,
                verbose=verbose,
            )
        except Exception as error:
            if verbose:
                print(f"  Falha ao processar Lattes: {error}")
            continue

        if verbose:
            print(f"  Resumo encontrado: {'sim' if professor.lattes_summary else 'nao'}")
            print(f"  Formação encontrada: {len(professor.academic_background)} item(ns)")
            print(f"  Áreas encontradas: {len(professor.research_areas)} item(ns)")
            print(f"  Projetos encontrados: {len(professor.current_projects)} item(ns)")
            print(f"  Publicações encontradas: {len(professor.publications)} item(ns)")

    return professors


def get_lattes_html(
    professor: Professor,
    cache_dir: str | Path,
    verbose: bool = False,
) -> str:
    cache_path = get_cache_path(professor, cache_dir)

    if cache_path.exists():
        if verbose:
            print(f"  Usando cache: {cache_path}")
        return cache_path.read_text(encoding="utf-8", errors="ignore")

    if verbose:
        print(f"  Baixando: {professor.lattes_url}")

    response = requests.get(professor.lattes_url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    html = response.text

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html, encoding="utf-8")

    return html


def get_cache_path(professor: Professor, cache_dir: str | Path) -> Path:
    safe_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", professor.id)
    return Path(cache_dir) / f"{safe_id}.html"


def extract_lattes_data(html: str) -> dict[str, str | list[str]]:
    raw_text = html_to_text(html)
    clean_text_value = clean_text(raw_text)
    lines = clean_lines(raw_text)

    return {
        "lattes_summary": extract_section_text(lines, ["Resumo"]),
        "academic_background": extract_section_lines(
            lines,
            ["Formação acadêmica", "Formação acadêmica/titulação"],
        ),
        "research_areas": extract_section_lines(lines, ["Áreas de atuação"]),
        "current_projects": extract_section_lines(lines, ["Projetos de pesquisa", "Projetos"]),
        "publications": extract_section_lines(
            lines,
            [
                "Produções bibliográficas",
                "Artigos completos publicados em periódicos",
            ],
        ),
        "lattes_raw_text": raw_text,
        "lattes_clean_text": clean_text_value,
    }


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.select("script, style"):
        tag.decompose()

    return soup.get_text("\n")


def extract_section_text(lines: list[str], keywords: list[str]) -> str:
    section_lines = extract_section_lines(lines, keywords)
    return clean_text(" ".join(section_lines))


def extract_section_lines(lines: list[str], keywords: list[str]) -> list[str]:
    start_index = find_section_start(lines, keywords)
    if start_index is None:
        return []

    end_index = find_next_section_start(lines, start_index + 1)
    section_lines = lines[start_index + 1 : end_index]

    return [line for line in section_lines if not is_section_heading(line)]


def find_section_start(lines: list[str], keywords: list[str]) -> int | None:
    normalized_keywords = [normalize_text(keyword) for keyword in keywords]

    for index, line in enumerate(lines):
        normalized_line = normalize_text(line)
        if any(keyword in normalized_line for keyword in normalized_keywords):
            return index

    return None


def find_next_section_start(lines: list[str], start_index: int) -> int:
    normalized_keywords = [normalize_text(keyword) for keyword in SECTION_KEYWORDS]

    for index in range(start_index, len(lines)):
        normalized_line = normalize_text(lines[index])
        if any(keyword in normalized_line for keyword in normalized_keywords):
            return index

    return len(lines)


def is_section_heading(line: str) -> bool:
    normalized_line = normalize_text(line)
    return any(normalize_text(keyword) in normalized_line for keyword in SECTION_KEYWORDS)


def clean_lines(text: str) -> list[str]:
    return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower().strip()


def add_source(professor: Professor, source_type: str, url: str) -> None:
    source = {"type": source_type, "url": url}

    if source not in professor.sources:
        professor.sources.append(source)
