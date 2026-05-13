import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Professor
from .utils import generate_professor_id


DEFAULT_HEADERS = {
    "User-Agent": "academic-professor-ranker/0.1",
}

# (Main) Extrai os professores a partir da URL do departamento.
def extract_professors_from_department(
    department_url: str,
    department_name: str = "",
    institution_name: str = "",
) -> list[Professor]:
    html = fetch_html(department_url)
    return parse_sigaa_department_page(
        html=html,
        department_url=department_url,
        department_name=department_name,
        institution_name=institution_name,
    )

# Faz a requisição HTTP e retorna o HTML da página.
def fetch_html(url: str, session: requests.Session | None = None) -> str:
    client = session or requests
    response = client.get(url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text

# Lê o HTML da página do SIGAA e transforma os dados em objetos Professor.
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

# Extrai o nome do departamento a partir do HTML da página.
def extract_department_name(soup: BeautifulSoup) -> str:
    department_title = soup.select_one("#colDirTop h2")
    return clean_text(department_title.get_text(" ", strip=True)) if department_title else ""

# Extrai o nome da instituição a partir do HTML da página.
def extract_institution_name(soup: BeautifulSoup) -> str:
    top_area = soup.select_one("#colDirTop")
    if not top_area:
        return ""

    for link in top_area.select("a"):
        text = clean_text(link.get_text(" ", strip=True))
        if "UNIVERSIDADE" in text.upper():
            return text

    return ""

# Extrai os dados de um professor a partir da tabela do SIGAA.
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

    department_text = get_text(table, "span.departamento")
    department_profile_url = absolute_url(get_href(table, "span.pagina a"), source_url)
    lattes_url = absolute_url(get_href(table, "span.enderecoLattes a"), source_url)
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

# Acessa os perfis individuais dos professores para complementar os dados.
def enrich_professors_with_department_profiles(
    professors: list[Professor],
    verbose: bool = False,
) -> int:
    updated_count = 0

    with requests.Session() as session:
        for professor in professors:
            if not professor.department_profile_url:
                continue

            if verbose:
                print(f"Processando professor: {professor.full_name}")

            try:
                html = fetch_html(professor.department_profile_url, session=session)
            except requests.RequestException as error:
                if verbose:
                    print(f"  Falha ao acessar perfil: {error}")
                continue

            profile_data = parse_department_profile_page(html, professor.department_profile_url)
            changed = update_professor_from_profile(professor, profile_data)

            if verbose:
                print(f"  Email encontrado: {profile_data['email'] or 'nao'}")
                print(f"  Lattes encontrado: {profile_data['lattes_url'] or 'nao'}")

            if changed:
                updated_count += 1

    return updated_count

# Extrai e-mail, Lattes e texto da página individual do professor.
def parse_department_profile_page(html: str, profile_url: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    page_text = extract_profile_text(soup)
    email = find_email(soup.get_text(" ", strip=True))
    lattes_url = find_lattes_url(soup, profile_url)

    return {
        "email": email,
        "lattes_url": lattes_url,
        "department_text": page_text,
        "source_url": profile_url,
    }

# Atualiza um professor com os dados encontrados no perfil individual.
def update_professor_from_profile(
    professor: Professor,
    profile_data: dict[str, str],
) -> bool:
    changed = False

    if profile_data["email"] and not professor.email:
        professor.email = profile_data["email"]
        changed = True

    if profile_data["lattes_url"] and not professor.lattes_url:
        professor.lattes_url = profile_data["lattes_url"]
        professor.id = generate_professor_id(
            full_name=professor.full_name,
            institution_name=professor.institution_name,
            department_name=professor.department_name,
            lattes_url=professor.lattes_url,
        )
        changed = True

    if profile_data["department_text"]:
        combined_text = append_text(professor.department_text, profile_data["department_text"])
        if combined_text != professor.department_text:
            professor.department_text = combined_text
            changed = True

    if profile_data["source_url"]:
        changed = add_source(professor, "department_profile", profile_data["source_url"]) or changed

    return changed


def extract_profile_text(soup: BeautifulSoup) -> str:
    parts = []

    for selector in ["#perfil-docente", "#formacao-academica"]:
        section = soup.select_one(selector)
        if section:
            remove_noise(section)
            parts.append(clean_text(section.get_text(" ", strip=True)))

    if not parts:
        center = soup.select_one("#center")
        if center:
            remove_noise(center)
            parts.append(clean_text(center.get_text(" ", strip=True)))

    return clean_text(" ".join(part for part in parts if part))

# Remove elementos desnecessários do HTML, como scripts e estilos.
def remove_noise(element) -> None:
    for tag in element.select("script, style"):
        tag.decompose()


def find_lattes_url(soup: BeautifulSoup, base_url: str) -> str:
    for link in soup.select("a"):
        href = link.get("href") or ""
        text = link.get_text(" ", strip=True)
        combined = f"{href} {text}".lower()

        if "lattes.cnpq.br" in combined:
            return absolute_url(href or text, base_url)

    match = re.search(r"https?://lattes\.cnpq\.br/\d+", soup.get_text(" ", strip=True))
    return match.group(0) if match else ""


def append_text(current_text: str, extra_text: str) -> str:
    current_text = clean_text(current_text)
    extra_text = clean_text(extra_text)

    if not extra_text:
        return current_text

    if not current_text:
        return extra_text

    if extra_text in current_text:
        return current_text

    return f"{current_text}\n\n{extra_text}"


def add_source(professor: Professor, source_type: str, url: str) -> bool:
    source = {"type": source_type, "url": url}

    if source in professor.sources:
        return False

    professor.sources.append(source)
    return True


def get_text(element, selector: str) -> str:
    selected = element.select_one(selector)
    return clean_text(selected.get_text(" ", strip=True)) if selected else ""


def get_href(element, selector: str) -> str:
    selected = element.select_one(selector)
    return selected.get("href", "") if selected else ""


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
