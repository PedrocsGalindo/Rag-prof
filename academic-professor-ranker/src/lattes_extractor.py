import re
import unicodedata
from pathlib import Path
from typing import Any

from .models import (
    Professor,
    academic_background_from_dict,
    publication_from_dict,
    research_project_from_dict,
)


DEFAULT_MANUAL_DIR = Path("data/raw/lattes-professors")

SECTION_KEYWORDS = [
    "Resumo",
    "Identificação",
    "Endereço",
    "Formação acadêmica/titulação",
    "Formação acadêmica",
    "Pós-doutorado",
    "Formação Complementar",
    "Atuação Profissional",
    "Linhas de pesquisa",
    "Projetos de pesquisa",
    "Projetos de desenvolvimento",
    "Outros Projetos",
    "Projetos",
    "Áreas de atuação",
    "Idiomas",
    "Prêmios e títulos",
    "Produções",
    "Produção bibliográfica",
    "Artigos completos publicados em periódicos",
    "Capítulos de livros publicados",
    "Textos em jornais de notícias/revistas",
    "Trabalhos completos publicados em anais de congressos",
    "Resumos expandidos publicados em anais de congressos",
    "Apresentações de Trabalho",
    "Demais tipos de produção técnica",
    "Bancas",
    "Eventos",
    "Orientações",
    "Outras informações relevantes",
]

NAVIGATION_LINES = {
    "curriculo lattes",
    "endereco",
    "dados gerais",
    "formacao",
    "atuacao",
    "projetos",
    "producoes",
    "eventos",
    "orientacoes",
    "bancas",
}

PUBLICATION_HEADER_TYPES = {
    "Artigos completos publicados em periódicos": "Artigo",
    "Capítulos de livros publicados": "Capítulo",
    "Textos em jornais de notícias/revistas": "Outro",
    "Trabalhos completos publicados em anais de congressos": "Congresso",
    "Resumos expandidos publicados em anais de congressos": "Resumo",
    "Apresentações de Trabalho": "Apresentação",
    "Demais tipos de produção técnica": "Produção técnica",
}

INVALID_PUBLICATION_HEADERS = [
    "Ordenar por",
    "Ordem Cronológica",
    "Capítulos de livros publicados",
    "Textos em jornais de notícias/revistas",
    "Trabalhos completos publicados em anais de congressos",
    "Resumos expandidos publicados em anais de congressos",
    "Apresentações de Trabalho",
    "Demais tipos de produção técnica",
    "Bancas",
    "Eventos",
    "Orientações",
    "Participação em bancas",
    "Participação em eventos",
]

PERIOD_RE = re.compile(r"^(\d{4})\s*-\s*(\d{4}|Atual|atual)$")
SINGLE_YEAR_RE = re.compile(r"^\d{4}$")
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")


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
    professor.lattes_url = extracted["lattes_url"] or professor.lattes_url
    professor.lattes_summary = extracted["lattes_summary"] or professor.lattes_summary
    professor.academic_background = [
        academic_background_from_dict(item)
        for item in extracted["academic_background"]
    ] or professor.academic_background
    professor.research_areas = extracted["research_areas"] or professor.research_areas
    professor.research_lines = extracted["research_lines"] or professor.research_lines
    professor.current_projects = [
        research_project_from_dict(item)
        for item in extracted["current_projects"]
    ] or professor.current_projects
    professor.publications = [
        publication_from_dict(item)
        for item in extracted["publications"]
    ] or professor.publications
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


def extract_lattes_data(raw_text: str) -> dict[str, Any]:
    clean_text_value = clean_text(raw_text)
    lines = clean_lines(raw_text)

    academic_lines = extract_section(
        lines,
        ["Formação acadêmica/titulação", "Formação acadêmica"],
        stop_keywords=["Formação Complementar", "Atuação Profissional"],
    )
    postdoc_lines = extract_section(
        lines,
        ["Pós-doutorado"],
        stop_keywords=["Formação Complementar", "Atuação Profissional"],
    )
    project_lines = collect_project_lines(lines)
    research_line_sections = extract_all_sections(lines, ["Linhas de pesquisa"])

    return {
        "lattes_url": extract_lattes_url(raw_text),
        "lattes_summary": parse_lattes_summary(raw_text),
        "academic_background": parse_academic_background(academic_lines + postdoc_lines),
        "research_areas": parse_research_areas(extract_section(lines, ["Áreas de atuação"])),
        "research_lines": parse_research_line_sections(research_line_sections),
        "current_projects": parse_projects(project_lines),
        "publications": parse_publications(lines),
        "lattes_clean_text": clean_text_value,
    }


def extract_lattes_url(raw_text: str) -> str:
    match = re.search(r"https?://lattes\.cnpq\.br/\d+", raw_text)
    return match.group(0) if match else ""


def parse_lattes_summary(raw_text: str) -> str:
    lines = clean_lines(raw_text)
    end_index = find_text_line(lines, "(Texto informado pelo autor)")
    if end_index is None:
        return ""

    start_index = 0
    for index in range(end_index):
        if normalize_text(lines[index]).startswith("ultima atualizacao do curriculo em"):
            start_index = index + 1
            break

    summary_lines = []
    for line in lines[start_index : end_index + 1]:
        if is_navigation_line(line):
            continue
        summary_lines.append(line)

    summary = clean_text(" ".join(summary_lines))
    summary = re.sub(r"\(?Texto informado pelo autor\)?", "", summary, flags=re.IGNORECASE)
    return clean_text(summary)


def extract_section(
    lines: list[str],
    start_keywords: list[str],
    stop_keywords: list[str] | None = None,
) -> list[str]:
    start_index = find_section_start(lines, start_keywords)
    if start_index is None:
        return []

    end_index = find_next_section_start(lines, start_index + 1, stop_keywords=stop_keywords)
    return lines[start_index + 1 : end_index]


def extract_all_sections(lines: list[str], start_keywords: list[str]) -> list[list[str]]:
    sections = []

    for index, line in enumerate(lines):
        if matches_any_section(line, start_keywords):
            end_index = find_next_section_start(lines, index + 1)
            sections.append(lines[index + 1 : end_index])

    return sections


def parse_academic_background(lines: list[str]) -> list[dict[str, str]]:
    items = []

    for block in split_period_blocks(lines, allow_single_year_postdoc=True):
        degree, course = find_degree_and_course(block)
        if not degree:
            continue

        start_year, end_year = parse_period_years(block[0])
        description = join_lines(block)
        items.append(
            {
                "start_year": start_year,
                "end_year": end_year,
                "degree": degree,
                "course": course,
                "institution": find_institution(block),
                "description": description,
            }
        )

    return items


def parse_research_areas(lines: list[str]) -> list[str]:
    areas = []

    for line in lines:
        if is_number_marker(line) or is_blocked_area_line(line):
            continue

        normalized_line = normalize_text(line)
        if not any(keyword in normalized_line for keyword in ["grande area:", "area:", "subarea:"]):
            continue

        areas.append(clean_text(line))

    return dedupe_texts(areas)[:20]


def parse_research_lines(lines: list[str]) -> list[str]:
    numbered_blocks = split_numbered_blocks(lines)
    if numbered_blocks:
        return [join_lines(block) for block in numbered_blocks if len(join_lines(block)) >= 30]

    fallback_lines = []
    for line in lines:
        if is_number_marker(line) or PERIOD_RE.match(line) or is_section_noise(line):
            continue
        if len(line) >= 30:
            fallback_lines.append(line)

    return dedupe_texts(fallback_lines)


def parse_research_line_sections(sections: list[list[str]]) -> list[str]:
    has_numbered_section = any(any(is_number_marker(line) for line in section) for section in sections)
    research_lines = []

    for section in sections:
        if has_numbered_section and not any(is_number_marker(line) for line in section):
            continue
        research_lines.extend(parse_research_lines(section))

    return dedupe_texts(research_lines)


def parse_projects(lines: list[str]) -> list[dict[str, str]]:
    projects = []

    for block in split_period_blocks(lines):
        if len(block) < 2:
            continue

        start_year, end_year = parse_period_years(block[0])
        title = clean_text(block[1])
        description = join_lines(block[2:])
        status = extract_project_status(description, end_year)

        if not title and not description:
            continue

        projects.append(
            {
                "start_year": start_year,
                "end_year": end_year,
                "title": title,
                "description": description,
                "status": status,
            }
        )

    return dedupe_dicts(projects, ["start_year", "end_year", "title", "description"])


def parse_publications(lines: list[str]) -> list[dict[str, str]]:
    publications = []
    current_type = ""
    current_lines = []
    inside_publications = False

    for line in lines:
        if matches_any_section(line, ["Produção bibliográfica", "Artigos completos publicados em periódicos"]):
            inside_publications = True

        if not inside_publications:
            continue

        if matches_any_section(line, ["Bancas", "Eventos", "Orientações", "Outras informações relevantes"]):
            break

        publication_type = get_publication_type_from_header(line)
        if publication_type:
            add_publication(publications, current_lines, current_type)
            current_lines = []
            current_type = publication_type
            continue

        if is_number_marker(line):
            add_publication(publications, current_lines, current_type)
            current_lines = []
            continue

        if not current_type or is_invalid_publication_line(line):
            continue

        current_lines.append(line)

    add_publication(publications, current_lines, current_type)
    return dedupe_dicts(publications, ["description"])


def collect_project_lines(lines: list[str]) -> list[str]:
    project_lines = []

    for keyword in ["Projetos de pesquisa", "Projetos de desenvolvimento", "Outros Projetos"]:
        project_lines.extend(extract_section(lines, [keyword]))

    if not project_lines:
        project_lines = extract_section(lines, ["Projetos"])

    return project_lines


def split_period_blocks(lines: list[str], allow_single_year_postdoc: bool = False) -> list[list[str]]:
    blocks = []
    current = []

    for index, line in enumerate(lines):
        if PERIOD_RE.match(line) or (
            allow_single_year_postdoc and is_single_year_postdoc_start(lines, index)
        ):
            if current:
                blocks.append(current)
            current = [line]
            continue

        if current:
            current.append(line)

    if current:
        blocks.append(current)

    return blocks


def split_numbered_blocks(lines: list[str]) -> list[list[str]]:
    blocks = []
    current = []
    started = False

    for line in lines:
        if is_number_marker(line):
            if current:
                blocks.append(current)
            current = []
            started = True
            continue

        if started:
            current.append(line)

    if current:
        blocks.append(current)

    return blocks


def parse_period_years(line: str) -> tuple[str, str]:
    period_match = PERIOD_RE.match(line)
    if period_match:
        return period_match.group(1), period_match.group(2)

    if SINGLE_YEAR_RE.match(line):
        return line, ""

    return "", ""


def is_single_year_postdoc_start(lines: list[str], index: int) -> bool:
    line = lines[index]
    if not SINGLE_YEAR_RE.match(line):
        return False

    nearby = " ".join(lines[index + 1 : index + 4])
    return "pos-doutorado" in normalize_text(nearby)


def find_degree_and_course(block: list[str]) -> tuple[str, str]:
    degree_patterns = [
        ("Pós-Doutorado", r"P[oó]s[-\s]?Doutorado\.?(?:\s+em\s+(.+))?"),
        ("Curso técnico/profissionalizante", r"Curso\s+t[eé]cnico/profissionalizante\.?(?:\s+em\s+(.+))?"),
        ("Livre-docência", r"Livre[-\s]?doc[eê]ncia\.?(?:\s+em\s+(.+))?"),
        ("Doutorado", r"Doutorado(?:\s+em\s+(.+))?"),
        ("Mestrado", r"Mestrado(?:\s+em\s+(.+))?"),
        ("Graduação", r"Gradua[cç][aã]o(?:\s+em\s+(.+))?"),
        ("Especialização", r"Especializa[cç][aã]o(?:\s+em\s+(.+))?"),
    ]

    for line in block:
        for degree, pattern in degree_patterns:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                return degree, clean_course(match.group(1) or "")

    return "", ""


def clean_course(course: str) -> str:
    return clean_text(course).rstrip(".")


def find_institution(block: list[str]) -> str:
    institution_words = ["universidade", "instituto", "faculdade", "centro"]

    for line in block:
        normalized_line = normalize_text(line)
        if any(word in normalized_line for word in institution_words):
            return line

    return ""


def extract_project_status(description: str, end_year: str) -> str:
    status_match = re.search(r"Situa[cç][aã]o:\s*([^;.]+)", description, flags=re.IGNORECASE)
    if status_match:
        return clean_text(status_match.group(1))

    if normalize_text(end_year) == "atual":
        return "Em andamento"

    return ""


def add_publication(publications: list[dict[str, str]], lines: list[str], publication_type: str) -> None:
    publication = build_publication(lines, publication_type)
    if publication:
        publications.append(publication)


def build_publication(lines: list[str], publication_type: str) -> dict[str, str] | None:
    description = clean_text(" ".join(lines))
    if not is_valid_publication(description):
        return None

    years = YEAR_RE.findall(description)
    authors = ""
    title = ""

    parts = re.split(r"\s+\.\s+", description, maxsplit=1)
    if len(parts) == 2:
        authors = clean_text(parts[0])
        title = clean_text(re.split(r"\.\s+", parts[1], maxsplit=1)[0])

    return {
        "year": years[-1] if years else "",
        "title": title,
        "authors": authors,
        "publication_type": publication_type or "Outro",
        "description": description,
    }


def is_valid_publication(description: str) -> bool:
    if len(description) <= 50:
        return False

    if not YEAR_RE.search(description):
        return False

    if is_number_marker(description) or matches_any_section(description, INVALID_PUBLICATION_HEADERS):
        return False

    return True


def get_publication_type_from_header(line: str) -> str:
    for header, publication_type in PUBLICATION_HEADER_TYPES.items():
        if matches_any_section(line, [header]):
            return publication_type

    return ""


def is_invalid_publication_line(line: str) -> bool:
    return is_number_marker(line) or matches_any_section(line, INVALID_PUBLICATION_HEADERS)


def find_section_start(lines: list[str], keywords: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if matches_any_section(line, keywords):
            return index

    return None


def find_next_section_start(
    lines: list[str],
    start_index: int,
    stop_keywords: list[str] | None = None,
) -> int:
    keywords = SECTION_KEYWORDS + (stop_keywords or [])

    for index in range(start_index, len(lines)):
        if matches_any_section(lines[index], keywords):
            return index

    return len(lines)


def matches_any_section(line: str, keywords: list[str]) -> bool:
    normalized_line = normalize_text(line)
    return any(is_section_title(normalized_line, normalize_text(keyword)) for keyword in keywords)


def is_section_title(normalized_line: str, normalized_keyword: str) -> bool:
    return normalized_line == normalized_keyword or normalized_line.startswith(f"{normalized_keyword}:")


def is_navigation_line(line: str) -> bool:
    normalized_line = normalize_text(line)
    if normalized_line in NAVIGATION_LINES:
        return True

    return normalized_line.startswith("dados gerais formacao atuacao")


def is_number_marker(line: str) -> bool:
    return bool(re.match(r"^\d+\.$", clean_text(line)))


def is_blocked_area_line(line: str) -> bool:
    blocked_words = [
        "idiomas",
        "ingles",
        "espanhol",
        "premios e titulos",
        "professor homenageado",
        "producoes",
        "producao bibliografica",
    ]
    normalized_line = normalize_text(line)
    return any(word in normalized_line for word in blocked_words)


def is_section_noise(line: str) -> bool:
    return matches_any_section(line, SECTION_KEYWORDS + INVALID_PUBLICATION_HEADERS)


def find_text_line(lines: list[str], text: str) -> int | None:
    normalized_text = normalize_text(text)

    for index, line in enumerate(lines):
        if normalized_text in normalize_text(line):
            return index

    return None


def dedupe_texts(values: list[str]) -> list[str]:
    seen = set()
    result = []

    for value in values:
        cleaned_value = clean_text(value)
        key = normalize_text(cleaned_value)
        if not cleaned_value or key in seen:
            continue

        seen.add(key)
        result.append(cleaned_value)

    return result


def dedupe_dicts(items: list[dict[str, str]], key_fields: list[str]) -> list[dict[str, str]]:
    seen = set()
    result = []

    for item in items:
        key = tuple(normalize_text(item.get(field, "")) for field in key_fields)
        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


def join_lines(lines: list[str]) -> str:
    parts = []

    for line in lines:
        cleaned_line = clean_text(line)
        if not cleaned_line:
            continue

        parts.append(cleaned_line if cleaned_line.endswith((".", ";", ":")) else f"{cleaned_line}.")

    return clean_text(" ".join(parts))


def clean_lines(text: str) -> list[str]:
    return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower().strip()


def add_source(professor: Professor, source_type: str, url: str) -> None:
    source = {"type": source_type, "url": url}

    if source not in professor.sources:
        professor.sources.append(source)
