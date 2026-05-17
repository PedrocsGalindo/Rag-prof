# CHANGELOG

## 2026-05-17 - Documentação do fluxo atual

### Alterado
- README.md: melhora a explicação do fluxo atual, uso manual do Lattes, organização dos records, embeddings, ranking e evidências.
- README.md: documenta a possibilidade futura de reranker sem implementar mudanças no ranking.
- CHANGELOG.md: registra as mudanças desta tarefa.

### Observação
- Nenhuma mudança relevante na lógica dos scripts.

## 2026-05-17 - Vector store local

### Criado
- config/ranking_profiles.json: adiciona perfis project_focused e research_focused.
- src/ranking_config.py: carrega a configuração de perfis de ranking.
- data/processed/professor_catalog.json: arquivo gerado com catálogo de professores.
- data/processed/professor_profile_records.json: arquivo gerado com records gerais.
- data/processed/professor_chunk_records.json: arquivo gerado com records de chunks.
- data/embeddings/professor_profile_embeddings.npy: arquivo gerado com embeddings gerais.
- data/embeddings/professor_profile_embedding_index.json: arquivo gerado com índice dos embeddings gerais.

### Alterado
- scripts/generate_embeddings.py: gera catálogo, records gerais, records de chunks e dois conjuntos de embeddings.
- src/ranker.py: adiciona ranking híbrido configurável com primeira etapa por perfil geral e segunda por chunks.
- scripts/rank_professors.py: adiciona --mode e --ranking-profile.
- README.md: documenta catálogo, records, ranking híbrido e perfis de ponderação.

## 2026-05-16 - Parser Lattes estruturado

### Alterado
- src/lattes_extractor.py: corrige parser do Lattes para extrair URL, resumo, formação, linhas de pesquisa, projetos e publicações em blocos estruturados.
- scripts/enrich_with_lattes.py: adiciona contagens de dados extraídos ao resumo final e reduz logs por professor.
- scripts/generate_embeddings.py: evita chunk geral com perfil completo, ignora placeholders do departamento e filtra chunks inválidos.
- CHANGELOG.md: registra as mudanças desta tarefa.

## 2026-05-16 - Lattes estruturado

### Alterado
- src/models.py: adiciona AcademicBackground, ResearchProject, Publication e conversores compatíveis com JSON antigo.
- src/lattes_extractor.py: salva formação, projetos e publicações como itens estruturados simples.
- src/profile_builder.py: formata campos estruturados no texto de ranking.
- scripts/build_profiles.py: carrega professores usando conversor compatível com JSON antigo.
- scripts/enrich_with_lattes.py: carrega professores usando conversor compatível com JSON antigo.
- scripts/generate_embeddings.py: gera chunks a partir dos campos estruturados e ignora textos muito curtos.
- src/ranker.py: ignora chunks antigos sem texto e evita erro com metadados ausentes.

## 2026-05-16 - Ranking por chunks

### Alterado
- src/ranker.py: passa a ranquear professores usando embeddings por chunk e evidências.
- scripts/rank_professors.py: imprime total de chunks comparados e top professores com até 3 evidências.
- src/models.py: adiciona evidências ao resultado do ranking.
- src/encoder.py: adia import do sentence-transformers até a criação do LocalEncoder.
- README.md: documenta o ranking baseado em chunks.

## 2026-05-16 - Embeddings por chunks

### Criado
- data/processed/professor_chunks.json: arquivo gerado com chunks textuais por professor.
- data/embeddings/professor_chunk_embeddings.npy: arquivo gerado com embeddings dos chunks.
- data/embeddings/professor_chunk_embedding_index.json: arquivo gerado com índice dos embeddings dos chunks.

### Alterado
- scripts/generate_embeddings.py: passa a gerar chunks e embeddings por chunk.
- README.md: documenta a geração de embeddings por chunks.

## 2026-05-16 - Encoder local

### Alterado
- src/encoder.py: simplifica BaseEncoder, LocalEncoder e get_encoder para geração local de embeddings.
- CHANGELOG.md: registra as mudanças desta tarefa.

## 2026-05-13 - Logs resumidos dos scripts

### Alterado
- scripts/ingest_department.py: remove logs por professor e adiciona resumo com listas de Lattes encontrados e pendentes.
- scripts/enrich_with_lattes.py: remove instruções repetidas por professor e adiciona resumo final com listas de arquivos manuais.
- src/lattes_extractor.py: deixa de imprimir instruções longas durante o processamento individual.

## 2026-05-13 - Lattes manual por txt

### Alterado
- src/lattes_extractor.py: troca download online por leitura de arquivos `.txt` manuais em `data/raw/lattes-professors/`.
- scripts/enrich_with_lattes.py: cria arquivos manuais vazios quando faltam e salva status de preenchimento.
- src/models.py: adiciona status e caminho do arquivo manual do Lattes.
- README.md: documenta o fluxo manual de textos do Lattes.

## 2026-05-13 - Revisão de simplificação

### Alterado
- src/department_extractor.py: remove download duplicado e simplifica leitura de texto e links do SIGAA.
- src/lattes_extractor.py: remove filtro redundante na extração de seções.
- src/ranker.py: simplifica o uso do índice de embeddings no ranking.

## 2026-05-13 - README inicial open source

### Alterado
- README.md: reescreve documentacao com objetivo, pipeline, instalacao, comandos, arquivos gerados e limitacoes.

## 2026-05-13 - Ranking por similaridade

### Alterado
- src/ranker.py: carrega perfis, embeddings e indice para ranquear professores por similaridade cosseno.
- scripts/rank_professors.py: recebe `--query` e imprime os top professores com score e dados principais.
- README.md: atualiza o comando de ranking e o estado atual do ranker.

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
