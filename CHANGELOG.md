# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões em [SemVer](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- Núcleo importado do projeto anterior (`abandono-escolar` `878930f`, `Dados-do-Projeto` `969fc64`):
  pipeline estendido 2007–2025, réguas, métricas, bootstrap por escola, Holm, classificação como experimento.
- `dataset/escolas_rr.csv` e `dataset/DICIONARIO.md`, gerados por `python -m src.dataset`.
- Teste de equivalência com o projeto anterior (`testes/test_equivalencia.py`).
- `rodar_tudo.py`: regera tudo e roda os testes.

### Pendências abertas
- **Pipeline oficial 2019–2025 (TDI, ATU, IED) fora do núcleo.** Volta por pull request quando a meta M5
  começar, junto com o teste 07 e a comparação com a base v1.0 (ver `docs/DECISOES.md`, 2026-11-11).
- Variáveis novas para 2007–2018 (matrículas, escola indígena): meta M1.
