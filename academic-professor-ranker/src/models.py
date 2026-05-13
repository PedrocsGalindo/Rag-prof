from dataclasses import dataclass, field


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
    academic_background: list[str] = field(default_factory=list)
    research_areas: list[str] = field(default_factory=list)
    current_projects: list[str] = field(default_factory=list)
    publications: list[str] = field(default_factory=list)
    profile_text_for_ranking: str = ""
    sources: list[str] = field(default_factory=list)


@dataclass
class RankedProfessor:
    professor: Professor
    score: float
    reason: str = ""
