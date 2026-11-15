# Changelog

Todas as mudanças que importam ficam registradas aqui. Formato:
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões em [SemVer](https://semver.org/lang/pt-BR/).
A versão fica em `src/versao.py`, e o dataset leva a versão no nome do arquivo.

## [Não lançado]

### Adicionado
- `docs/BASELINE.md`, gerado por `python src/relatorios/baseline.py`: a régua, a versão otimista, a B2 e o
  acaso, com os resultados da Etapa 1 (regerados), da Etapa 2 e da classificação (citados de
  `docs/projeto_anterior/`); `testes/test_baseline.py` exige que esteja em dia.
- `docs/projeto_anterior/classificacao/`: as saídas da execução única da classificação de 2026-11-10, copiadas do
  commit de origem, com sha256 no README da pasta; `testes/test_baseline.py` confere os hashes de todas as cópias
  congeladas, e o `docs/BASELINE.md` e o `testes/test_equivalencia.py` passam a ler a cópia versionada.
- `docs/tese_base/`: o exemplo do professor (MLPRegressor, King County House Sales), como referência de forma;
  o `kc_house_data.csv` fica fora do git, e o nbstripout não toca o notebook (`.gitattributes`,
  `testes/test_atributos.py`; instalação com `--attributes .gitattributes`, ver `CONTRIBUTING.md`).

- `docs/ROTEIRO.md`: as metas M1–M12 do projeto anterior, cópia literal do arquivo, todas "a revisar".
- Registro do desvio da regra 12 (pull requests #1 e #2 mergeados sem revisão) no `docs/DECISOES.md`.

### Alterado
- **A pergunta do projeto muda** (`docs/DECISOES.md`, 2026-11-14): de antecipar as escolas de abandono alto no ano
  seguinte para os fatores estruturais associados ao nível de abandono da escola-ano (Q1–Q4). O `README.md` traz a
  pergunta nova, o que já foi respondido (a Q4) e o que o resultado não é. O artigo da disciplina de Mineração de
  Dados sai do repositório; só a cópia literal do roteiro antigo (`docs/ROTEIRO.md`) ainda o menciona.
- **Regras unificadas:** `CLAUDE.md` e `CONTRIBUTING.md` com as mesmas 12 regras e os mesmos números; mudam as
  regras 5 (associação no mesmo ano), 6 (identidade contábil no nível de abandono), 7 (escolher × reportar a
  relação com o desfecho; ressalva do R²) e 10 (toda decisão registrada; unidade dos anos de teste).
- `docs/BASELINE.md` (via `src/relatorios/baseline.py`): a régua passa a ser descrita como "quanto se acerta sem
  modelo, com o dado que a secretaria já tem", e o §5 diz que o nulo preditivo é o que responde à Q4.
- Unidade dos intervalos de anos: anos de DESFECHO na regra 10; a linha de 2022–2023 do `dataset/DICIONARIO.md` e
  uma nota abaixo da tabela da janela; "taxa de abandono por ano civil, 2013–2019" no `docs/DECISOES.md` e aqui.

### Pendências abertas
- **Pipeline oficial 2019–2025 (TDI, ATU, IED) fora do núcleo.** Volta por pull request quando a meta M5
  começar, junto com o teste 07 e a comparação com a base v1.0 do orientador (`docs/DECISOES.md`, 2026-11-11).
  Abrir como issue quando o repositório estiver no GitHub.
- Variáveis novas para 2007–2018, como matrículas e escola indígena: meta M1 (a revisar, `docs/ROTEIRO.md`).

## [0.1.0] — 2026-11-11

Cópia aparada e conferida do projeto anterior (`abandono-escolar` `878930f`, `Dados-do-Projeto` `969fc64`).

### Adicionado
- Núcleo importado: pipeline estendido 2007–2025 (`src/estendida/`), réguas, métricas, bootstrap por escola,
  Holm e funções da classificação (`src/avaliacao/`), funil e desfecho por ano (`src/relatorios/`), obtenção
  dos zips do INEP com conferência de sha256 (`src/aquisicao.py`), recorte de Roraima em `dados/cache/`.
- `dataset/escolas_rr_v0.1.0.csv` e `dataset/DICIONARIO.md`, gerados por `python -m src.dataset`.
- Réguas da janela segura regeradas sem modelo (`src/avaliacao/reguas.py`).
- Teste de equivalência com o projeto anterior: base, régua da Etapa 1, réguas da janela, funil e taxa de
  abandono por ano civil, 2013–2019, idênticos (`testes/test_equivalencia.py`).
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
