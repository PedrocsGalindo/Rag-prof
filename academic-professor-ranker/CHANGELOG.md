# CHANGELOG

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
