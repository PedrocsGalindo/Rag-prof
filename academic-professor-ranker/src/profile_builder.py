from dataclasses import asdict, is_dataclass
from typing import Any

from .models import Professor


def build_profile_text(professor: Professor) -> str:
    sections = [
        format_section("Nome", professor.full_name),
        format_section("E-mail", professor.email),
        format_section("Resumo do Lattes", professor.lattes_summary),
        format_section("Formação acadêmica", professor.academic_background),
        format_section("Áreas de atuação", professor.research_areas),
        format_section("Linhas de pesquisa", professor.research_lines),
        format_section("Projetos atuais", professor.current_projects),
        format_section("Publicações", professor.publications),
        format_section("Texto do departamento", professor.department_text),
    ]

    return "\n\n".join(section for section in sections if section)


def build_profiles(professors: list[Professor]) -> list[Professor]:
    for professor in professors:
        professor.profile_text_for_ranking = build_profile_text(professor)

    return professors


def format_section(title: str, value: Any) -> str:
    text = format_value(value)

    if not text:
        return ""

    return f"{title}:\n{text}"


def format_value(value: Any) -> str:
    if isinstance(value, list):
        lines = [format_value(item) for item in value]
        return "\n".join(f"- {line}" for line in lines if line)

    if is_dataclass(value):
        value = asdict(value)

    if isinstance(value, dict):
        parts = [str(item).strip() for item in value.values() if str(item or "").strip()]
        return " ".join(parts)

    return str(value or "").strip()
