import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.department_extractor import extract_professors_from_department
from src.storage import save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract professors from a department page.")
    parser.add_argument("department_url")
    parser.add_argument("--department-name", default="")
    parser.add_argument("--institution-name", default="")
    parser.add_argument("--output", default=str(ROOT_DIR / "data" / "raw" / "department_professors.json"))
    args = parser.parse_args()

    professors = extract_professors_from_department(
        department_url=args.department_url,
        department_name=args.department_name,
        institution_name=args.institution_name,
    )

    save_json(args.output, professors)
    print(f"Saved {len(professors)} professors to {args.output}")


if __name__ == "__main__":
    main()
