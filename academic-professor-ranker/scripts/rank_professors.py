import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.models import Professor
from src.ranker import rank_professors
from src.storage import load_json, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank professors for a simple text query.")
    parser.add_argument("query")
    parser.add_argument("--input", default=str(ROOT_DIR / "data" / "processed" / "professors_profiles.json"))
    parser.add_argument("--output", default=str(ROOT_DIR / "data" / "processed" / "ranking.json"))
    args = parser.parse_args()

    data = load_json(args.input, default=[])
    professors = [Professor(**item) for item in data]
    ranking = rank_professors(professors, args.query)

    save_json(args.output, ranking)
    print(f"Saved {len(ranking)} ranked professors to {args.output}")


if __name__ == "__main__":
    main()
