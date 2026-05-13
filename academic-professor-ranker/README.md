# academic-professor-ranker

Projeto Python local para montar perfis simples de professores a partir de uma pagina de departamento universitario e, em uma etapa futura, enriquecer esses dados com o curriculo Lattes.

Esta primeira versao cria apenas a estrutura do projeto, os modelos, o armazenamento JSON e scripts basicos. O scraping completo e o ranking real ainda nao foram implementados.

## Estrutura

```text
academic-professor-ranker/
├── data/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── scripts/
│   ├── ingest_department.py
│   ├── enrich_with_lattes.py
│   ├── build_profiles.py
│   └── rank_professors.py
├── src/
│   ├── models.py
│   ├── department_extractor.py
│   ├── lattes_extractor.py
│   ├── encoder.py
│   ├── ranker.py
│   ├── storage.py
│   └── utils.py
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

## Como usar

Execute os comandos a partir da pasta `academic-professor-ranker`.

```bash
python scripts/ingest_department.py "https://exemplo.edu/departamento" --department-name "Departamento" --institution-name "Universidade"
python scripts/enrich_with_lattes.py
python scripts/build_profiles.py
python scripts/rank_professors.py "aprendizado de maquina"
```

## Estado atual

- `department_extractor.py` ainda retorna uma lista vazia.
- `lattes_extractor.py` ainda nao consulta o Lattes.
- `LocalEncoder` ainda retorna embeddings simples de placeholder.
- `rank_professors` ainda retorna score `0.0`.

## Principios

- Sem banco de dados.
- Sem Docker.
- Sem frontend.
- Sem Selenium ou Playwright.
- JSON local e codigo facil de alterar.
