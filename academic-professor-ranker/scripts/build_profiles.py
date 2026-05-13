import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.models import Professor
from src.ranker import build_profiles
from src.storage import load_json, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Build text profiles used for ranking.")
    parser.add_argument("--input", default=str(ROOT_DIR / "data" / "processed" / "professors_lattes.json"))
    parser.add_argument("--output", default=str(ROOT_DIR / "data" / "processed" / "professors_profiles.json"))
    args = parser.parse_args()

    data = load_json(args.input, default=[])
    professors = [Professor(**item) for item in data]
    profiled_professors = build_profiles(professors)

    save_json(args.output, profiled_professors)
    print(f"Saved {len(profiled_professors)} profiles to {args.output}")


if __name__ == "__main__":
    main()
