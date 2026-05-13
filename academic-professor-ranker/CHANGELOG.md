# CHANGELOG

## 2026-05-13 - Geração de embeddings

### Criado
- scripts/generate_embeddings.py: gera embeddings dos perfis e salva matriz `.npy` com indice JSON.

### Alterado
- README.md: adiciona o script e o comando de geracao de embeddings e atualiza o estado do `LocalEncoder`.

## 2026-05-13 - Encoder local

### Alterado
- src/encoder.py: implementa `LocalEncoder` com sentence-transformers e `get_encoder("local")`.
- requirements.txt: adiciona numpy e sentence-transformers.

## 2026-05-13 - Builder de perfis

### Criado
- src/profile_builder.py: monta `profile_text_for_ranking` a partir dos campos existentes do professor.

### Alterado
- scripts/build_profiles.py: le `professors_enriched.json`, gera perfis e salva `professor_profiles.json`.
- README.md: adiciona `src/profile_builder.py` na estrutura documentada.

## 2026-05-13 - Extrator Lattes inicial

### Alterado
- src/lattes_extractor.py: implementa cache HTML, download simples e extracao basica de secoes do Lattes.
- scripts/enrich_with_lattes.py: le professores brutos, enriquece com Lattes e salva JSON processado.
- src/models.py: adiciona campos `lattes_raw_text` e `lattes_clean_text`.
- README.md: atualiza o estado atual do extrator Lattes.

## 2026-05-13 - Enriquecimento por perfil SIGAA

### Alterado
- src/department_extractor.py: acessa perfis individuais dos docentes e complementa e-mail, Lattes e texto do perfil.
- scripts/ingest_department.py: processa perfis individuais e imprime progresso por professor.
- README.md: atualiza o estado atual do extrator SIGAA.

## 2026-05-13 - Extrator SIGAA do departamento

### Alterado
- scripts/ingest_department.py: recebe `--url`, executa a ingestao SIGAA e imprime resumo simples.
- src/department_extractor.py: baixa HTML com requests e extrai docentes, links e metadados da pagina SIGAA.
- src/models.py: ajusta o tipo de `sources` para lista de objetos.
- requirements.txt: adiciona requests e beautifulsoup4.
- README.md: atualiza o exemplo de uso do script de ingestao.

## 2026-05-12 - Estrutura inicial

### Criado
- data/raw/: pasta para dados brutos.
- data/processed/: pasta para dados processados.
- data/embeddings/: pasta para embeddings locais.
- scripts/ingest_department.py: script inicial para ingestao da pagina do departamento.
- scripts/enrich_with_lattes.py: script inicial para enriquecimento com Lattes.
- scripts/build_profiles.py: script inicial para montar textos de perfil.
- scripts/rank_professors.py: script inicial para ranking.
- src/models.py: dataclasses principais do projeto.
- src/department_extractor.py: esqueleto do extrator de departamento.
- src/lattes_extractor.py: esqueleto do extrator de Lattes.
- src/encoder.py: interface de encoder e encoder local inicial.
- src/ranker.py: funcoes basicas para perfil e ranking.
- src/storage.py: funcoes simples para salvar e carregar JSON.
- src/utils.py: geracao deterministica de id com uuid5.
- requirements.txt: arquivo inicial de dependencias.
- README.md: documentacao inicial do projeto.
- CHANGELOG.md: registro inicial de mudancas.
