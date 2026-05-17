from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AcademicBackground:
    start_year: str = ""
    end_year: str = ""
    degree: str = ""
    course: str = ""
    institution: str = ""
    description: str = ""


@dataclass
class ResearchProject:
    start_year: str = ""
    end_year: str = ""
    title: str = ""
    description: str = ""
    status: str = ""


@dataclass
class Publication:
    year: str = ""
    title: str = ""
    authors: str = ""
    publication_type: str = ""
    description: str = ""


@dataclass
class Professor:
    id: str
    full_name: str
    email: str = ""
    department_profile_url: str = ""
    lattes_url: str = ""
    department_name: str = ""
    institution_name: str = ""
    department_text: str = ""
    lattes_summary: str = ""
    academic_background: list[AcademicBackground] = field(default_factory=list)
    research_areas: list[str] = field(default_factory=list)
    research_lines: list[str] = field(default_factory=list)
    current_projects: list[ResearchProject] = field(default_factory=list)
    publications: list[Publication] = field(default_factory=list)
    lattes_raw_text: str = ""
    lattes_clean_text: str = ""
    lattes_status: str = ""
    lattes_manual_needed: bool = False
    lattes_manual_file: str = ""
    profile_text_for_ranking: str = ""
    sources: list[dict[str, str]] = field(default_factory=list)


@dataclass
class RankedProfessor:
    professor: Professor
    score: float
    reason: str = ""
    evidences: list[dict[str, str | float]] = field(default_factory=list)


def academic_background_from_dict(data: Any) -> AcademicBackground:
    if isinstance(data, AcademicBackground):
        return data

    if isinstance(data, str):
        return AcademicBackground(description=data)

    if not isinstance(data, dict):
        return AcademicBackground(description=to_text(data))

    return AcademicBackground(
        start_year=to_text(data.get("start_year")),
        end_year=to_text(data.get("end_year")),
        degree=to_text(data.get("degree")),
        course=to_text(data.get("course")),
        institution=to_text(data.get("institution")),
        description=to_text(data.get("description")),
    )


def research_project_from_dict(data: Any) -> ResearchProject:
    if isinstance(data, ResearchProject):
        return data

    if isinstance(data, str):
        return ResearchProject(description=data)

    if not isinstance(data, dict):
        return ResearchProject(description=to_text(data))

    return ResearchProject(
        start_year=to_text(data.get("start_year")),
        end_year=to_text(data.get("end_year")),
        title=to_text(data.get("title")),
        description=to_text(data.get("description")),
        status=to_text(data.get("status")),
    )


def publication_from_dict(data: Any) -> Publication:
    if isinstance(data, Publication):
        return data

    if isinstance(data, str):
        return Publication(description=data)

    if not isinstance(data, dict):
        return Publication(description=to_text(data))

    return Publication(
        year=to_text(data.get("year")),
        title=to_text(data.get("title")),
        authors=to_text(data.get("authors")),
        publication_type=to_text(data.get("publication_type") or data.get("type")),
        description=to_text(data.get("description")),
    )


def professor_from_dict(data: dict) -> Professor:
    return Professor(
        id=to_text(data.get("id")),
        full_name=to_text(data.get("full_name")),
        email=to_text(data.get("email")),
        department_profile_url=to_text(data.get("department_profile_url")),
        lattes_url=to_text(data.get("lattes_url")),
        department_name=to_text(data.get("department_name")),
        institution_name=to_text(data.get("institution_name")),
        department_text=to_text(data.get("department_text")),
        lattes_summary=to_text(data.get("lattes_summary")),
        academic_background=[
            academic_background_from_dict(item)
            for item in as_list(data.get("academic_background"))
            if item
        ],
        research_areas=to_text_list(data.get("research_areas")),
        research_lines=to_text_list(data.get("research_lines")),
        current_projects=[
            research_project_from_dict(item)
            for item in as_list(data.get("current_projects"))
            if item
        ],
        publications=[
            publication_from_dict(item)
            for item in as_list(data.get("publications"))
            if item
        ],
        lattes_raw_text=to_text(data.get("lattes_raw_text")),
        lattes_clean_text=to_text(data.get("lattes_clean_text")),
        lattes_status=to_text(data.get("lattes_status")),
        lattes_manual_needed=bool(data.get("lattes_manual_needed", False)),
        lattes_manual_file=to_text(data.get("lattes_manual_file")),
        profile_text_for_ranking=to_text(data.get("profile_text_for_ranking")),
        sources=as_list(data.get("sources")),
    )


def professor_to_dict(professor: Professor) -> dict:
    return asdict(professor)


def as_list(value: Any) -> list:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def to_text_list(value: Any) -> list[str]:
    return [text for text in (to_text(item) for item in as_list(value)) if text]


def to_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()
