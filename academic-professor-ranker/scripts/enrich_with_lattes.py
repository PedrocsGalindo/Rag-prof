import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.lattes_extractor import enrich_professors_with_lattes
from src.models import Professor
from src.storage import load_json, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich professor data with Lattes data.")
    parser.add_argument("--input", default=str(ROOT_DIR / "data" / "raw" / "department_professors.json"))
    parser.add_argument("--output", default=str(ROOT_DIR / "data" / "processed" / "professors_lattes.json"))
    args = parser.parse_args()

    data = load_json(args.input, default=[])
    professors = [Professor(**item) for item in data]
    enriched_professors = enrich_professors_with_lattes(professors)

    save_json(args.output, enriched_professors)
    print(f"Saved {len(enriched_professors)} enriched professors to {args.output}")


if __name__ == "__main__":
    main()
