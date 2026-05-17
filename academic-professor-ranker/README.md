# academic-professor-ranker

Sistema local em Python para recomendar professores de um departamento universitário com base na query ou no currículo de um aluno.

O projeto extrai professores de uma página pública do departamento, organiza informações do Lattes em arquivos locais, gera embeddings com um modelo local e retorna professores recomendados com evidências textuais.

## Como o Fluxo Funciona

1. O sistema extrai professores do site do departamento, como uma página pública do SIGAA.
2. Os dados básicos dos professores são salvos em JSON.
3. O sistema cria arquivos `.txt` manuais para cada professor em `data/raw/lattes-professors/`.
4. O usuário abre o currículo Lattes no navegador, copia o conteúdo e cola no arquivo `.txt`.
5. O sistema processa esse texto manual do Lattes.
6. O sistema cria um catálogo de professores, perfis gerais e chunks por categoria.
7. O sistema gera embeddings locais para perfis gerais e chunks.
8. O sistema faz ranking semântico usando similaridade textual.
9. O resultado mostra professores recomendados e evidências encontradas nos chunks.

## Por Que o Lattes é Manual

O Lattes pode ter captcha, verificação anti-bot ou bloqueios de acesso automatizado.

Este projeto não tenta burlar captcha, anti-bot, bloqueio, proxy ou qualquer proteção do site. O fluxo principal é manual: o usuário copia o texto público do currículo no navegador e cola em um arquivo `.txt` local.

## Instalação

Execute dentro da pasta do projeto:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Pipeline

### 1. Extrair Professores

```bash
python scripts/ingest_department.py --url "URL_DO_DEPARTAMENTO"
```

Exemplo:

```bash
python scripts/ingest_department.py --url "https://sigs.ufrpe.br/sigaa/public/departamento/professores.jsf?id=530"
```

Saída principal:

- `data/raw/professors_from_department.json`

### 2. Preparar e Ler Textos Manuais do Lattes

```bash
python scripts/enrich_with_lattes.py
```

Na primeira execução, o script cria arquivos vazios em:

```text
data/raw/lattes-professors/
```

Para cada professor pendente:

1. Abra o currículo Lattes no navegador.
2. Use `Ctrl + A` para selecionar o conteúdo da página.
3. Use `Ctrl + C` para copiar.
4. Abra o arquivo `.txt` indicado.
5. Cole com `Ctrl + V`.
6. Salve o arquivo.
7. Rode `python scripts/enrich_with_lattes.py` novamente.

Saída principal:

- `data/processed/professors_enriched.json`

### 3. Construir Perfis Textuais

```bash
python scripts/build_profiles.py
```

Saída principal:

- `data/processed/professor_profiles.json`

### 4. Gerar Records e Embeddings

```bash
python scripts/generate_embeddings.py
```

Essa etapa monta uma estrutura local parecida com uma vector store simples, usando apenas JSON e NumPy.

Saídas principais:

- `data/processed/professor_catalog.json`
- `data/processed/professor_profile_records.json`
- `data/processed/professor_chunk_records.json`
- `data/embeddings/professor_profile_embeddings.npy`
- `data/embeddings/professor_chunk_embeddings.npy`
- `data/embeddings/professor_profile_embedding_index.json`
- `data/embeddings/professor_chunk_embedding_index.json`

### 5. Ranquear Professores

```bash
python scripts/rank_professors.py --query "Tenho interesse em inteligência artificial aplicada à saúde"
```

Também é possível escolher um perfil de ranking:

```bash
python scripts/rank_professors.py --query "quero participar de projetos aplicados" --ranking-profile project_focused
```

```bash
python scripts/rank_professors.py --query "quero pesquisar aprendizado de máquina e publicar artigos" --ranking-profile research_focused
```

## Organização dos Dados

### Dados Fixos do Professor

Arquivo:

```text
data/processed/professor_catalog.json
```

Guarda informações que não precisam ser repetidas em todos os chunks:

- nome;
- e-mail;
- departamento;
- instituição;
- link do Lattes;
- link do perfil no departamento.

### Perfil Geral do Professor

Arquivo:

```text
data/processed/professor_profile_records.json
```

Cada professor tem um record geral curto e representativo. Ele combina resumo do Lattes, áreas, linhas de pesquisa, projetos e publicações principais.

Esse record é usado na primeira etapa do ranking híbrido.

### Chunks Específicos

Arquivo:

```text
data/processed/professor_chunk_records.json
```

Cada chunk representa uma evidência específica, por exemplo:

- `lattes_summary`
- `academic_background`
- `research_areas`
- `research_lines`
- `current_projects`
- `publications`
- `department_text`

Os chunks são usados na segunda etapa do ranking para encontrar evidências mais precisas.

### Embeddings

Arquivos:

```text
data/embeddings/professor_profile_embeddings.npy
data/embeddings/professor_chunk_embeddings.npy
```

Os embeddings são vetores numéricos gerados localmente com `sentence-transformers`.

Hoje o modelo local padrão é:

```text
paraphrase-multilingual-MiniLM-L12-v2
```

### Ranking

O ranking padrão é híbrido:

1. Compara a query com os perfis gerais dos professores.
2. Seleciona os professores mais promissores.
3. Compara a query com os chunks desses professores.
4. Combina os scores usando pesos.
5. Retorna os professores com evidências.

Os pesos ficam em:

```text
config/ranking_profiles.json
```

Por enquanto, a forma mais simples de ajustar o ranking é editar esse arquivo.

Perfis disponíveis:

- `research_focused`: dá mais peso para linhas de pesquisa, áreas e publicações.
- `project_focused`: dá mais peso para projetos atuais e evidências práticas.

### Evidências

As evidências são os chunks que mais se aproximaram da query.

Na saída do ranking, cada professor pode aparecer com evidências como:

- um projeto relevante;
- uma linha de pesquisa;
- uma área de atuação;
- uma publicação;
- um trecho do resumo do Lattes.

## Reranker Futuro

Hoje o sistema usa embeddings e similaridade semântica.

No futuro, depois que o ranking selecionar os professores mais similares, um reranker poderia analisar os chunks desses professores para melhorar a ordenação final.

Um formato simples para dados de treino ou avaliação poderia ser:

```text
query | professor_id | chunk_id | label
```

Exemplo:

```text
"quero trabalhar com IA aplicada à saúde" | prof_123 | prof_123_current_projects_001 | relevante
```

Isso não está implementado agora. A ideia está documentada apenas como caminho futuro.

## Limitações

- A extração depende da estrutura do site do departamento.
- O Lattes precisa ser preenchido manualmente em arquivos `.txt`.
- O ranking mede similaridade textual
- Os resultados devem ser revisados pelo usuário.
