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

    save_json(args.output, enriched_professors)

    print()
    print("Resumo do enriquecimento Lattes:")
    print(f"- Total de professores: {len(enriched_professors)}")
    print(f"- Textos manuais lidos: {len(with_manual_text)}")
    print(f"- Textos manuais pendentes: {len(pending)}")
    print(f"- Pendentes com link direto do Lattes: {len(pending_with_lattes)}")
    print(f"- Pendentes sem link direto do Lattes: {len(pending_without_lattes)}")
    print(f"- JSON salvo em: {args.output}")

    print()
    print("Professores com texto Lattes já disponível:")
    print_professors_with_manual_text(with_manual_text)

    print()
    print("Professores pendentes COM link direto do Lattes:")
    print_pending_with_lattes(pending_with_lattes)

    print()
    print("Professores pendentes SEM link direto do Lattes:")
    print_pending_without_lattes(pending_without_lattes)

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


def print_professors_with_manual_text(professors) -> None:
    if not professors:
        print("- Nenhum")
        return

    for professor in professors:
        print(f"- {professor.full_name} | {professor.lattes_manual_file}")


def print_pending_with_lattes(professors) -> None:
    if not professors:
        print("- Nenhum")
        return

    for professor in professors:
        print(f"- {professor.full_name}")
        print(f"  Link: {professor.lattes_url}")
        print(f"  Arquivo: {professor.lattes_manual_file}")


def print_pending_without_lattes(professors) -> None:
    if not professors:
        print("- Nenhum")
        return

    for professor in professors:
        print(f"- {professor.full_name}")
        print("  Buscar em: https://buscatextual.cnpq.br/buscatextual/busca.do")
        print(f"  Nome para pesquisar: {professor.full_name}")
        print(f"  Arquivo: {professor.lattes_manual_file}")


if __name__ == "__main__":
    main()
