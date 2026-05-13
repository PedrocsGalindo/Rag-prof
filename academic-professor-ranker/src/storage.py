import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def save_json(path: str | Path, data: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(_to_jsonable(data), file, ensure_ascii=False, indent=2)


def load_json(path: str | Path, default: Any = None) -> Any:
    input_path = Path(path)

    if not input_path.exists():
        return default

    with input_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]

    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}

    return value
