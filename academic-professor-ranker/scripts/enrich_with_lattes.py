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
    parser.add_argument("--input", default=str(ROOT_DIR / "data" / "raw" / "professors_from_department.json"))
    parser.add_argument("--output", default=str(ROOT_DIR / "data" / "processed" / "professors_enriched.json"))
    parser.add_argument("--cache-dir", default=str(ROOT_DIR / "data" / "raw" / "lattes_cache"))
    args = parser.parse_args()

    data = load_json(args.input, default=[])
    professors = [Professor(**item) for item in data]
    professors_with_lattes = sum(1 for professor in professors if professor.lattes_url)

    print(f"Arquivo de entrada: {args.input}")
    print(f"Professores carregados: {len(professors)}")
    print(f"Professores com Lattes: {professors_with_lattes}")
    print(f"Diretorio de cache: {args.cache_dir}")

    enriched_professors = enrich_professors_with_lattes(
        professors,
        cache_dir=args.cache_dir,
        verbose=True,
    )

    save_json(args.output, enriched_professors)
    print(f"JSON salvo em: {args.output}")


if __name__ == "__main__":
    main()
