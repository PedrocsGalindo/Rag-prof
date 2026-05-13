import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Professor
from .utils import generate_professor_id


DEFAULT_HEADERS = {
    "User-Agent": "academic-professor-ranker/0.1",
}


def extract_professors_from_department(
    department_url: str,
    department_name: str = "",
    institution_name: str = "",
) -> list[Professor]:
    html = fetch_department_html(department_url)
    return parse_sigaa_department_page(
        html=html,
        department_url=department_url,
        department_name=department_name,
        institution_name=institution_name,
    )


def fetch_department_html(department_url: str) -> str:
    response = requests.get(department_url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def parse_sigaa_department_page(
    html: str,
    department_url: str,
    department_name: str = "",
    institution_name: str = "",
) -> list[Professor]:
    soup = BeautifulSoup(html, "html.parser")
    found_department_name = department_name or extract_department_name(soup)
    found_institution_name = institution_name or extract_institution_name(soup)

    professors = []
    professor_tables = soup.select("#professores table[align='left']")

    for table in professor_tables:
        professor = parse_professor_table(
            table=table,
            source_url=department_url,
            department_name=found_department_name,
            institution_name=found_institution_name,
        )

        if professor:
            professors.append(professor)

    return professors


def extract_department_name(soup: BeautifulSoup) -> str:
    department_title = soup.select_one("#colDirTop h2")
    return clean_text(department_title.get_text(" ", strip=True)) if department_title else ""


def extract_institution_name(soup: BeautifulSoup) -> str:
    top_area = soup.select_one("#colDirTop")
    if not top_area:
        return ""

    for link in top_area.select("a"):
        text = clean_text(link.get_text(" ", strip=True))
        if "UNIVERSIDADE" in text.upper():
            return text

    return ""


def parse_professor_table(
    table,
    source_url: str,
    department_name: str,
    institution_name: str,
) -> Professor | None:
    name_tag = table.select_one("span.nome")
    if not name_tag:
        return None

    full_name = clean_professor_name(name_tag.get_text(" ", strip=True))
    if not full_name:
        return None

    department_text_tag = table.select_one("span.departamento")
    department_text = ""
    if department_text_tag:
        department_text = clean_text(department_text_tag.get_text(" ", strip=True))

    page_link = find_link(table, "Ver página", css_selector="span.pagina a")
    lattes_link = find_link(table, "Lattes", css_selector="span.enderecoLattes a")

    department_profile_url = absolute_url(page_link, source_url)
    lattes_url = absolute_url(lattes_link, source_url)
    email = find_email(table.get_text(" ", strip=True))

    return create_professor(
        full_name=full_name,
        email=email,
        department_profile_url=department_profile_url,
        lattes_url=lattes_url,
        department_name=department_name,
        institution_name=institution_name,
        department_text=department_text,
        sources=[{"type": "department", "url": source_url}],
    )


def find_link(table, label: str, css_selector: str = "") -> str:
    if css_selector:
        selected_link = table.select_one(css_selector)
        if selected_link and selected_link.get("href"):
            return selected_link["href"]

    for link in table.select("a"):
        text = clean_text(link.get_text(" ", strip=True))
        if label.lower() in text.lower() and link.get("href"):
            return link["href"]

    return ""


def absolute_url(url: str, base_url: str) -> str:
    if not url:
        return ""

    return urljoin(base_url, url)


def clean_professor_name(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text)
    return clean_text(text)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def find_email(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    return match.group(0) if match else ""


def create_professor(
    full_name: str,
    email: str = "",
    department_profile_url: str = "",
    lattes_url: str = "",
    department_name: str = "",
    institution_name: str = "",
    department_text: str = "",
    sources: list[dict[str, str]] | None = None,
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
