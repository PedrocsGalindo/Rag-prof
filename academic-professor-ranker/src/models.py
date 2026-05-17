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
