from .models import Professor, RankedProfessor


def build_profile_text(professor: Professor) -> str:
    parts = [
        professor.full_name,
        professor.department_name,
        professor.institution_name,
        professor.department_text,
        professor.lattes_summary,
        " ".join(professor.academic_background),
        " ".join(professor.research_areas),
        " ".join(professor.current_projects),
        " ".join(professor.publications),
    ]

    return "\n".join(part for part in parts if part)


def build_profiles(professors: list[Professor]) -> list[Professor]:
    for professor in professors:
        professor.profile_text_for_ranking = build_profile_text(professor)

    return professors


def rank_professors(professors: list[Professor], query: str) -> list[RankedProfessor]:
    # TODO: use embeddings to compare query and professor profiles.
    return [
        RankedProfessor(
            professor=professor,
            score=0.0,
            reason="Ranking ainda nao implementado.",
        )
        for professor in professors
    ]
