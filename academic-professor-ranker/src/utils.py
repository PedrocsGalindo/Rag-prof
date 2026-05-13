import uuid


PROFESSOR_ID_NAMESPACE = uuid.UUID("c4a0a28b-e691-4d55-bc9f-e38167c3f50f")


def generate_professor_id(
    full_name: str,
    institution_name: str,
    department_name: str,
    lattes_url: str,
) -> str:
    raw_id = "|".join(
        [
            full_name.strip().lower(),
            institution_name.strip().lower(),
            department_name.strip().lower(),
            lattes_url.strip().lower(),
        ]
    )

    return str(uuid.uuid5(PROFESSOR_ID_NAMESPACE, raw_id))
