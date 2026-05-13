from .models import Professor


def enrich_professor_with_lattes(professor: Professor) -> Professor:
    # TODO: implement Lattes extraction.
    return professor


def enrich_professors_with_lattes(professors: list[Professor]) -> list[Professor]:
    return [enrich_professor_with_lattes(professor) for professor in professors]
