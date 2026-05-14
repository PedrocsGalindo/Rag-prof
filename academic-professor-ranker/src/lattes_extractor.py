import re
import unicodedata
from pathlib import Path

from .models import Professor


DEFAULT_MANUAL_DIR = Path("data/raw/lattes-professors")

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
    manual_dir: str | Path = DEFAULT_MANUAL_DIR,
    verbose: bool = False,
) -> Professor:
    manual_file = get_manual_lattes_path(professor, manual_dir)
    professor.lattes_manual_file = manual_file.as_posix()

    if not manual_file.exists():
        manual_file.parent.mkdir(parents=True, exist_ok=True)
        manual_file.write_text("", encoding="utf-8")
        mark_manual_needed(professor, "manual_file_created_empty")
        return professor

    raw_text = manual_file.read_text(encoding="utf-8", errors="ignore")
    if not raw_text.strip():
        mark_manual_needed(professor, "manual_file_empty")
        return professor

    extracted = extract_lattes_data(raw_text)
    professor.lattes_raw_text = raw_text
    professor.lattes_clean_text = extracted["lattes_clean_text"]
    professor.lattes_summary = extracted["lattes_summary"] or professor.lattes_summary
    professor.academic_background = extracted["academic_background"] or professor.academic_background
    professor.research_areas = extracted["research_areas"] or professor.research_areas
    professor.current_projects = extracted["current_projects"] or professor.current_projects
    professor.publications = extracted["publications"] or professor.publications
    professor.lattes_status = "manual_text"
    professor.lattes_manual_needed = False
    add_source(professor, "lattes_manual_file", manual_file.as_posix())

    if verbose:
        print(f"Texto manual do Lattes encontrado: {professor.full_name}")

    return professor


def enrich_professors_with_lattes(
    professors: list[Professor],
    manual_dir: str | Path = DEFAULT_MANUAL_DIR,
    verbose: bool = False,
) -> list[Professor]:
    Path(manual_dir).mkdir(parents=True, exist_ok=True)

    for index, professor in enumerate(professors, start=1):
        if verbose:
            print(f"Processando Lattes manual {index}/{len(professors)}: {professor.full_name}")

        try:
            enrich_professor_with_lattes(professor, manual_dir=manual_dir, verbose=verbose)
        except Exception as error:
            professor.lattes_status = "manual_error"
            professor.lattes_manual_needed = True
            if verbose:
                print(f"  Falha ao processar arquivo manual: {error}")

    return professors


def get_manual_lattes_path(professor: Professor, manual_dir: str | Path) -> Path:
    return Path(manual_dir) / f"{slugify(professor.full_name)}.txt"


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def mark_manual_needed(professor: Professor, status: str) -> None:
    professor.lattes_status = status
    professor.lattes_manual_needed = True
    professor.lattes_raw_text = ""
    professor.lattes_clean_text = ""


def extract_lattes_data(raw_text: str) -> dict[str, str | list[str]]:
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
        "lattes_clean_text": clean_text_value,
    }


def extract_section_text(lines: list[str], keywords: list[str]) -> str:
    return clean_text(" ".join(extract_section_lines(lines, keywords)))


def extract_section_lines(lines: list[str], keywords: list[str]) -> list[str]:
    start_index = find_section_start(lines, keywords)
    if start_index is None:
        return []

    end_index = find_next_section_start(lines, start_index + 1)
    return lines[start_index + 1 : end_index]


def find_section_start(lines: list[str], keywords: list[str]) -> int | None:
    normalized_keywords = [normalize_text(keyword) for keyword in keywords]

    for index, line in enumerate(lines):
        normalized_line = normalize_text(line)
        if any(is_section_title(normalized_line, keyword) for keyword in normalized_keywords):
            return index

    return None


def find_next_section_start(lines: list[str], start_index: int) -> int:
    normalized_keywords = [normalize_text(keyword) for keyword in SECTION_KEYWORDS]

    for index in range(start_index, len(lines)):
        normalized_line = normalize_text(lines[index])
        if any(is_section_title(normalized_line, keyword) for keyword in normalized_keywords):
            return index

    return len(lines)


def is_section_title(normalized_line: str, normalized_keyword: str) -> bool:
    return (
        normalized_line == normalized_keyword
        or normalized_line.startswith(f"{normalized_keyword}:")
        or normalized_line.startswith(f"{normalized_keyword} ")
    )


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
