from .models import Professor
from .utils import generate_professor_id


def extract_professors_from_department(
    department_url: str,
    department_name: str = "",
    institution_name: str = "",
) -> list[Professor]:
    # TODO: implement department page extraction.
    return []


def create_professor(
    full_name: str,
    email: str = "",
    department_profile_url: str = "",
    lattes_url: str = "",
    department_name: str = "",
    institution_name: str = "",
    department_text: str = "",
    sources: list[str] | None = None,
) -> Professor:
    professor_id = generate_professor_id(
        full_name=full_name,
        institution_name=institution_name,
        department_name=department_name,
        lattes_url=lattes_url,
    )

    return Professor(
        id=professor_id,
        full_name=full_name,
        email=email,
        department_profile_url=department_profile_url,
        lattes_url=lattes_url,
        department_name=department_name,
        institution_name=institution_name,
        department_text=department_text,
        sources=sources or [],
    )
