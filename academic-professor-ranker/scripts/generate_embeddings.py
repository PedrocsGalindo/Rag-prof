import argparse
import sys
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.encoder import get_encoder
from src.models import Professor
from src.storage import load_json, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate professor profile embeddings.")
    parser.add_argument("--input", default=str(ROOT_DIR / "data" / "processed" / "professor_profiles.json"))
    parser.add_argument("--embeddings-output", default=str(ROOT_DIR / "data" / "embeddings" / "professor_embeddings.npy"))
    parser.add_argument("--index-output", default=str(ROOT_DIR / "data" / "embeddings" / "professor_embedding_index.json"))
    parser.add_argument("--encoder", default="local")
    args = parser.parse_args()

    data = load_json(args.input, default=[])
    professors = [Professor(**item) for item in data]
    texts = [professor.profile_text_for_ranking or "" for professor in professors]

    encoder = get_encoder(args.encoder)
    embeddings = encoder.encode(texts)
    embeddings = np.asarray(embeddings, dtype=np.float32)

    embeddings_path = Path(args.embeddings_output)
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_path, embeddings)

    index = build_embedding_index(professors)
    save_json(args.index_output, index)

    print(f"Quantidade de professores carregados: {len(professors)}")
    print(f"Quantidade de embeddings gerados: {len(embeddings)}")
    print(f"Caminho dos embeddings salvos: {args.embeddings_output}")
    print(f"Caminho do indice salvo: {args.index_output}")


def build_embedding_index(professors: list[Professor]) -> list[dict[str, str | int]]:
    return [
        {
            "index": index,
            "professor_id": professor.id,
            "full_name": professor.full_name,
        }
        for index, professor in enumerate(professors)
    ]


if __name__ == "__main__":
    main()
