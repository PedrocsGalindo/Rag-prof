# academic-professor-ranker

Projeto Python local para encontrar professores com perfis próximos ao interesse de um aluno.

A ideia é partir de uma página pública de corpo docente, extrair os professores, complementar dados com o Currículo Lattes quando possível, montar um texto de perfil para cada professor e ranquear os mais similares a uma query.

O projeto é simples por intenção: sem banco de dados, sem frontend, sem Docker e sem banco vetorial.

## Pipeline

1. Extrair professores da página do departamento.
2. Enriquecer os professores com textos manuais do Lattes.
3. Construir um perfil textual para ranking.
4. Gerar embeddings dos perfis.
5. Ranquear professores por similaridade com a query do aluno.

## Instalação

Crie e ative um ambiente virtual, se quiser:

```bash
python -m venv .venv
.venv\Scripts\activate
```
Entre no diretorio
```bash
cd academic-professor-ranker
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Como Rodar

Execute os comandos a partir da pasta `academic-professor-ranker`.

### 1. Extrair Professores

```bash
python scripts/ingest_department.py --url "URL_DO_DEPARTAMENTO"
python scripts/ingest_department.py --url "https://sigs.ufrpe.br/sigaa/public/departamento/professores.jsf?id=530"

```

### 2. Enriquecer Com Lattes

```bash
python scripts/enrich_with_lattes.py
```

Esse script usa arquivos `.txt` em `data/raw/lattes-professors/`.
Se o arquivo de um professor ainda não existir, ele será criado vazio com instruções no terminal.

### 3. Construir Perfis Textuais

```bash
python scripts/build_profiles.py
```

### 4. Gerar Embeddings

```bash
python scripts/generate_embeddings.py
```

### 5. Ranquear Professores

```bash
python scripts/rank_professors.py --query "texto do aluno"
```

Exemplo:

```bash
python scripts/rank_professors.py --query "Tenho interesse em inteligência artificial aplicada à saúde"
```

## Arquivos Gerados

- `data/raw/professors_from_department.json`: professores extraídos do departamento.
- `data/raw/lattes-professors/`: textos manuais copiados do Lattes, um arquivo por professor.
- `data/processed/professors_enriched.json`: professores com dados complementares do Lattes.
- `data/processed/professor_profiles.json`: professores com `profile_text_for_ranking`.
- `data/embeddings/professor_embeddings.npy`: matriz NumPy com embeddings dos perfis.
- `data/embeddings/professor_embedding_index.json`: índice que liga cada embedding ao professor.

## Limitações

- A extração depende da estrutura HTML do site do departamento.
- O enriquecimento do Lattes depende do texto manual copiado pelo usuário.
- O ranking usa similaridade textual, não uma avaliação real da qualidade ou adequação do professor.
- Os resultados devem ser revisados pelo usuário antes de qualquer decisão.

## Estrutura

```text
academic-professor-ranker/
├── data/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── scripts/
├── src/
├── requirements.txt
├── README.md
└── CHANGELOG.md
```
