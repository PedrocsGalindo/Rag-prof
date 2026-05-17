import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.lattes_extractor import enrich_professors_with_lattes
from src.models import professor_from_dict
from src.storage import load_json, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich professor data with Lattes data.")
    parser.add_argument("--input", default=str(ROOT_DIR / "data" / "raw" / "professors_from_department.json"))
    parser.add_argument("--output", default=str(ROOT_DIR / "data" / "processed" / "professors_enriched.json"))
    parser.add_argument("--manual-dir", default="data/raw/lattes-professors")
    args = parser.parse_args()

    data = load_json(args.input, default=[])
    professors = [professor_from_dict(item) for item in data]

    enriched_professors = enrich_professors_with_lattes(
        professors,
        manual_dir=args.manual_dir,
        verbose=False,
    )
    with_manual_text = [professor for professor in enriched_professors if professor.lattes_status == "manual_text"]
    pending = [professor for professor in enriched_professors if professor.lattes_manual_needed]
    pending_with_lattes = [professor for professor in pending if professor.lattes_url]
    pending_without_lattes = [professor for professor in pending if not professor.lattes_url]
    total_summaries = sum(1 for professor in enriched_professors if professor.lattes_summary)
    total_background = sum(len(professor.academic_background) for professor in enriched_professors)
    total_areas = sum(len(professor.research_areas) for professor in enriched_professors)
    total_lines = sum(len(professor.research_lines) for professor in enriched_professors)
    total_projects = sum(len(professor.current_projects) for professor in enriched_professors)
    total_publications = sum(len(professor.publications) for professor in enriched_professors)

    save_json(args.output, enriched_professors)

    print()
    print("Resumo do enriquecimento Lattes:")
    print(f"- Total de professores: {len(enriched_professors)}")
    print(f"- Textos manuais lidos: {len(with_manual_text)}")
    print(f"- Textos manuais pendentes: {len(pending)}")
    print(f"- Pendentes com link direto do Lattes: {len(pending_with_lattes)}")
    print(f"- Pendentes sem link direto do Lattes: {len(pending_without_lattes)}")
    print(f"- Total com resumo Lattes extraído: {total_summaries}")
    print(f"- Total de formações extraídas: {total_background}")
    print(f"- Total de áreas de atuação extraídas: {total_areas}")
    print(f"- Total de linhas de pesquisa extraídas: {total_lines}")
    print(f"- Total de projetos extraídos: {total_projects}")
    print(f"- Total de publicações extraídas: {total_publications}")
    print(f"- JSON salvo em: {args.output}")

    print()
    print("Como preencher os arquivos pendentes:")
    print("1. Se o professor tiver link direto do Lattes, abra o link.")
    print("2. Se não tiver link direto, acesse:")
    print("   https://buscatextual.cnpq.br/buscatextual/busca.do")
    print("   e pesquise pelo nome exato do professor.")
    print("3. Abra o currículo correto.")
    print("4. Na página do currículo, use Ctrl + A para selecionar o conteúdo.")
    print("5. Use Ctrl + C para copiar.")
    print("6. Abra o arquivo .txt indicado para aquele professor.")
    print("7. Cole com Ctrl + V.")
    print("8. Salve o arquivo.")
    print("9. Rode scripts/enrich_with_lattes.py novamente.")


if __name__ == "__main__":
    main()
