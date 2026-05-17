import json
from pathlib import Path


DEFAULT_RANKING_PROFILES_PATH = Path("config/ranking_profiles.json")


# Carrega o arquivo com perfis de ranking.
def load_ranking_profiles(path: str | Path = DEFAULT_RANKING_PROFILES_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


# Retorna o perfil escolhido ou o padrão do arquivo.
def get_ranking_profile(name: str | None = None, path: str | Path = DEFAULT_RANKING_PROFILES_PATH) -> tuple[str, dict]:
    config = load_ranking_profiles(path)
    profile_name = name or config.get("default")
    profiles = config.get("profiles", {})

    if profile_name not in profiles:
        raise ValueError(f"Perfil de ranking não suportado: {profile_name}")

    return profile_name, profiles[profile_name]
