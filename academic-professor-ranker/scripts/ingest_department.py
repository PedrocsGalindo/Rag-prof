import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.department_extractor import extract_professors_from_department
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

    department_name = professors[0].department_name if professors else args.department_name
    institution_name = professors[0].institution_name if professors else args.institution_name
    lattes_count = sum(1 for professor in professors if professor.lattes_url)

    save_json(args.output, professors)

    print(f"Nome do departamento encontrado: {department_name}")
    print(f"Nome da instituicao encontrada: {institution_name}")
    print(f"Quantidade de professores encontrados: {len(professors)}")
    print(f"Quantidade de links Lattes encontrados: {lattes_count}")
    print(f"Caminho do JSON salvo: {args.output}")


if __name__ == "__main__":
    main()
