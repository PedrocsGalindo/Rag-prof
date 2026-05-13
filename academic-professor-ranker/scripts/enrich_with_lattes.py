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
    parser.add_argument("--manual-dir", default="data/raw/lattes-professors")
    args = parser.parse_args()

    data = load_json(args.input, default=[])
    professors = [Professor(**item) for item in data]

    print(f"Arquivo de entrada: {args.input}")
    print(f"Professores carregados: {len(professors)}")
    print(f"Diretorio dos textos manuais: {args.manual_dir}")

    enriched_professors = enrich_professors_with_lattes(
        professors,
        manual_dir=args.manual_dir,
        verbose=True,
    )
    manual_needed = sum(1 for professor in enriched_professors if professor.lattes_manual_needed)
    manual_texts = sum(1 for professor in enriched_professors if professor.lattes_status == "manual_text")

    save_json(args.output, enriched_professors)
    print(f"Textos manuais lidos: {manual_texts}")
    print(f"Textos manuais pendentes: {manual_needed}")
    print(f"JSON salvo em: {args.output}")


if __name__ == "__main__":
    main()
