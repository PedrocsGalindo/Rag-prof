import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.department_extractor import (
    enrich_professors_with_department_profiles,
    extract_professors_from_department,
)
from src.storage import save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract professors from a department page.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--department-name", default="")
    parser.add_argument("--institution-name", default="")
    parser.add_argument("--output", default=str(ROOT_DIR / "data" / "raw" / "professors_from_department.json"))
    args = parser.parse_args()

    print(f"URL acessada: {args.url}")

    professors = extract_professors_from_department(
        department_url=args.url,
        department_name=args.department_name,
        institution_name=args.institution_name,
    )

    enrich_professors_with_department_profiles(professors, verbose=False)

    with_email = [professor for professor in professors if professor.email]
    without_email = [professor for professor in professors if not professor.email]
    with_lattes = [professor for professor in professors if professor.lattes_url]
    without_lattes = [professor for professor in professors if not professor.lattes_url]

    save_json(args.output, professors)

    print(f"Total de professores encontrados: {len(professors)}")
    print(f"Total com e-mail: {len(with_email)}")
    print(f"Total sem e-mail: {len(without_email)}")
    print(f"Total com link Lattes: {len(with_lattes)}")
    print(f"Total sem link Lattes: {len(without_lattes)}")
    print(f"Caminho do JSON salvo: {args.output}")

    print()
    print("Professores com link Lattes encontrado:")
    print_professors_with_lattes(with_lattes)

    print()
    print("Professores sem link Lattes:")
    print_professors_without_lattes(without_lattes)


def print_professors_with_lattes(professors) -> None:
    if not professors:
        print("- Nenhum")
        return

    for professor in professors:
        print(f"- {professor.full_name} | {professor.lattes_url}")


def print_professors_without_lattes(professors) -> None:
    if not professors:
        print("- Nenhum")
        return

    for professor in professors:
        print(f"- {professor.full_name}")


if __name__ == "__main__":
    main()
