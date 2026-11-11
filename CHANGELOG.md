# Changelog

Todas as mudanças que importam ficam registradas aqui. Formato:
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões em [SemVer](https://semver.org/lang/pt-BR/).
A versão fica em `src/versao.py`, e o dataset leva a versão no nome do arquivo.

## [Não lançado]

### Pendências abertas
- **Pipeline oficial 2019–2025 (TDI, ATU, IED) fora do núcleo.** Volta por pull request quando a meta M5
  começar, junto com o teste 07 e a comparação com a base v1.0 do orientador (`docs/DECISOES.md`, 2026-11-11).
  Abrir como issue quando o repositório estiver no GitHub.
- Variáveis novas para 2007–2018, como matrículas e escola indígena: meta M1.

## [0.1.0] — 2026-11-11

Cópia aparada e conferida do projeto anterior (`abandono-escolar` `878930f`, `Dados-do-Projeto` `969fc64`).

### Adicionado
- Núcleo importado: pipeline estendido 2007–2025 (`src/estendida/`), réguas, métricas, bootstrap por escola,
  Holm e funções da classificação (`src/avaliacao/`), funil e desfecho por ano (`src/relatorios/`), obtenção
  dos zips do INEP com conferência de sha256 (`src/aquisicao.py`), recorte de Roraima em `dados/cache/`.
- `dataset/escolas_rr_v0.1.0.csv` e `dataset/DICIONARIO.md`, gerados por `python -m src.dataset`.
- Réguas da janela segura regeradas sem modelo (`src/avaliacao/reguas.py`).
- Teste de equivalência com o projeto anterior: base, régua da Etapa 1, réguas da janela, funil e desfecho
  2013–2019 idênticos (`testes/test_equivalencia.py`).
- Testes do dataset, inclusive a regeração byte a byte (`testes/test_dataset.py`).
- `rodar_tudo.py`: regera tudo e roda os testes com um comando.
- A classificação de 2026-11-10 como experimento encerrado (`experimentos/classificacao_2013_2018/`).
- `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, modelo de pull request e guia de experimentos.
- `.gitattributes`: texto sempre em LF; arquivos com hash registrado nunca são normalizados.

### Retirado (em relação ao projeto anterior)
- Base oficial 2019–2025, teste 07 e comparação com a v1.0 (ver pendências).
- Degraus "Brasil" e "painel da Etapa 2" do funil; cobertura do painel; seções G e H do teste 04.
- Tabelas Turma, Matrícula e Docente de 2025, que só serviam à fase 2.

### Corrigido
- O teste 03 roda com `--completo`: sem os CSVs extraídos do projeto anterior, ele não conferia nenhum ano com
  os zips originais. Agora confere 2019–2025 célula a célula, e a falta dos zips aparece como teste pulado.
