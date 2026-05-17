# academic-professor-ranker

Projeto Python local para encontrar professores com perfis próximos ao interesse de um aluno.

A ideia é extrair professores de uma página pública de corpo docente, enriquecer dados com texto manual do Currículo Lattes, gerar embeddings locais e ranquear professores por similaridade textual.

O projeto é simples por intenção: sem banco de dados, sem frontend, sem Docker e sem banco vetorial real.

## Pipeline

1. Extrair professores da página do departamento.
2. Enriquecer os professores com textos manuais do Lattes.
3. Construir um perfil textual para cada professor.
4. Gerar uma estrutura local parecida com vector store:
   - catálogo dos professores;
   - records gerais dos professores;
   - records de chunks específicos;
   - embeddings gerais e embeddings dos chunks.
5. Ranquear professores com ranking híbrido:
   - primeiro compara a query com o perfil geral do professor;
   - depois compara a query com chunks específicos como evidências.

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
cd academic-professor-ranker
pip install -r requirements.txt
```

## Como Rodar

Execute os comandos a partir da pasta `academic-professor-ranker`.

### 1. Extrair Professores

```bash
python scripts/ingest_department.py --url "URL_DO_DEPARTAMENTO"
```

Exemplo:

```bash
python scripts/ingest_department.py --url "https://sigs.ufrpe.br/sigaa/public/departamento/professores.jsf?id=530"
```

### 2. Enriquecer Com Lattes

```bash
python scripts/enrich_with_lattes.py
```

Esse script usa arquivos `.txt` em `data/raw/lattes-professors/`.
Se o arquivo de um professor ainda não existir, ele será criado vazio.

### 3. Construir Perfis Textuais

```bash
python scripts/build_profiles.py
```

### 4. Gerar Embeddings

```bash
python scripts/generate_embeddings.py
```

Essa etapa gera o catálogo, os records e os embeddings locais.

### 5. Ranquear Professores

Ranking híbrido, usando o perfil padrão do arquivo `config/ranking_profiles.json`:

```bash
python scripts/rank_professors.py --query "texto do aluno"
```

Usando perfil focado em pesquisa:

```bash
python scripts/rank_professors.py --query "quero pesquisar aprendizado de máquina e publicar artigos" --ranking-profile research_focused
```

Usando perfil focado em projetos:

```bash
python scripts/rank_professors.py --query "quero participar de projetos aplicados" --ranking-profile project_focused
```

Modo simples por chunks:

```bash
python scripts/rank_professors.py --query "texto do aluno" --mode chunks
```

## Arquivos Gerados

- `data/raw/professors_from_department.json`: professores extraídos do departamento.
- `data/raw/lattes-professors/`: textos manuais copiados do Lattes.
- `data/processed/professors_enriched.json`: professores com dados do Lattes.
- `data/processed/professor_profiles.json`: professores com texto de perfil.
- `data/processed/professor_catalog.json`: dados repetidos dos professores, como nome, e-mail, departamento e links.
- `data/processed/professor_profile_records.json`: um record geral por professor.
- `data/processed/professor_chunk_records.json`: records específicos por categoria, como formação, áreas, linhas, projetos e publicações.
- `data/embeddings/professor_profile_embeddings.npy`: embeddings dos records gerais.
- `data/embeddings/professor_profile_embedding_index.json`: índice dos embeddings gerais.
- `data/embeddings/professor_chunk_embeddings.npy`: embeddings dos chunks.
- `data/embeddings/professor_chunk_embedding_index.json`: índice dos embeddings dos chunks.
- `config/ranking_profiles.json`: pesos do ranking híbrido.

## Ranking Híbrido

O ranking híbrido usa dois níveis:

1. `professor_profile_records`: busca inicial por perfil geral do professor.
2. `professor_chunk_records`: busca por evidências específicas nos professores selecionados.

O arquivo `config/ranking_profiles.json` define pesos para combinar:

- `profile_score`
- `best_chunk_score`
- `avg_top_3_chunk_score`

Também define pesos por seção, como `current_projects`, `research_lines`, `publications` e `academic_background`.

## Limitações

- A extração depende da estrutura HTML do site do departamento.
- O enriquecimento do Lattes depende do texto manual copiado pelo usuário.
- O ranking usa similaridade textual, não uma avaliação real da qualidade do professor.
- Os resultados devem ser revisados manualmente.
