from .models import Professor


def build_profile_text(professor: Professor) -> str:
    sections = [
        format_section("Nome", professor.full_name),
        format_section("E-mail", professor.email),
        format_section("Resumo do Lattes", professor.lattes_summary),
        format_section("Formação acadêmica", professor.academic_background),
        format_section("Áreas de atuação", professor.research_areas),
        format_section("Projetos atuais", professor.current_projects),
        format_section("Publicações", professor.publications),
        format_section("Texto do departamento", professor.department_text),
    ]

    return "\n\n".join(section for section in sections if section)


def build_profiles(professors: list[Professor]) -> list[Professor]:
    for professor in professors:
        professor.profile_text_for_ranking = build_profile_text(professor)

    return professors


def format_section(title: str, value: str | list[str]) -> str:
    text = format_value(value)

    if not text:
        return ""

    return f"{title}:\n{text}"


def format_value(value: str | list[str]) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value if item)

    return value.strip()
