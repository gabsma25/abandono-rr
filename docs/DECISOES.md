# Decisões do abandono-rr

Registro curto, uma entrada por decisão: data, decisão, motivo e onde está a evidência. O histórico
completo do projeto anterior continua no arquivo: `abandono-escolar/docs/DECISOES.md` (commit `878930f`).

---

## 2026-11-11 — O abandono-rr começa como cópia aparada do projeto anterior

**Decisão (pesquisadora).** O `abandono-escolar` e o `Dados-do-Projeto` ficam congelados, só para
leitura. O `abandono-rr` importa só o que gera ou valida a base estendida 2007–2025, o funil, as réguas
(B1R_lag, B2 e acaso), o pipeline sem vazamento, as métricas, o bootstrap por escola, o Holm e o catálogo de
problemas dos dados.

**Origem:** `abandono-escolar` em `878930f` e `Dados-do-Projeto` em `969fc64`. A tabela do que ficou e
do que saiu foi aprovada na Etapa 0 da migração (conversa de 2026-11-11).

**Decisões tomadas na migração:**

1. `alto_risco_t1` segue a regra da classificação de 2026-11-10: 20% maiores da etapa no ano, abandono > 0,
   empates no limiar entram todos (definição completa em `dataset/DICIONARIO.md`).
2. O dataset cobre 2007–2025, uma linha por escola × ano × etapa, com a coluna `janela_segura`.
3. **A base oficial 2019–2025 (TDI, ATU, IED) não entra agora.** O escopo novo usa só a janela 2013–2018,
   que não tem esses indicadores. O pipeline oficial volta por pull request quando a meta M5 começar.
4. O recorte de Roraima de 2007–2025 (o antigo `gustavo/cache/`) é versionado em `dados/cache/`, com
   sha256 no `dados/MANIFEST.csv`.
5. O `docs/BASELINE.md` regera a régua da Etapa 1 por código e cita a Etapa 2 e a classificação dos CSVs
   do projeto anterior, sem rodar a classificação de novo.

**Consequência da decisão 3 — o que fica só no arquivo:**

- a comparação da base oficial regerada com a v1.0 do orientador: `abandono-escolar/src/base_longitudinal.py`
  e `abandono-escolar/docs/comparacao_base_v1.csv` (commit `878930f`);
- o teste 07, que confere o rendimento de 2019–2025 nas duas bases:
  `Dados-do-Projeto/gustavo/testes/07_validar_sobreposicao.py` e o relatório
  `gustavo/saida/relatorios/validacao_sobreposicao.txt` (25 checks, 0 falhas; commit `969fc64`);
- os degraus "Brasil" e "painel da Etapa 2" do funil e a cobertura do painel da Etapa 2;
- as seções G e H do teste 04 (painel e walk-forward da Etapa 2).

**Adaptações feitas na cópia** (só caminhos e imports, além do aparo acima): cada script acha a raiz do
`abandono-rr`; `gustavo/cache/` virou `dados/cache/`; `gustavo/programas/` virou `src/estendida/`;
`gustavo/avaliacao/` virou `src/avaliacao/`; `gustavo/analises/04` e `05` viraram `src/relatorios/`; a
classificação de 2026-11-10 virou `experimentos/classificacao_2013_2018/`, com as saídas da execução única
copiadas, não regeradas. O teste 03 passa a rodar com `--completo`. A comparação do teste 03 com o backup
de outubro (`_backup_2026-10-14`) não veio: o teste avisa e pula.

**Evidência de que nada mudou** (`testes/test_equivalencia.py`, igualdade exata): a `base_atual` 2007–2025
(12.597 × 55, mesmos tipos), a régua da Etapa 1, as réguas B1R_lag, B2 e acaso da janela (60 linhas × 15
métricas), o funil (degraus 2 a 7) e o desfecho de 2013–2019 são idênticos aos do projeto anterior. Os
testes herdados passam: 01 (45 OK), 02 (41 OK), 03 (2019–2025 conferem célula a célula com os zips
originais), 04 (46 OK) e 08 (65 OK).

**Ressalva mantida.** Os dados de 2007 a 2018 vêm só de `dados/cache/`. Foram conferidos contra a fonte do
INEP uma vez, em 14/10/2026, na máquina do Gustavo (`docs/procedencia/relatorio_04_*.md`, §4), e não podem
ser reverificados aqui: os zips originais desses anos não estão no projeto. A janela segura depende deles.

**Fica para depois, fora do prazo de 16/11:** variáveis novas para 2007–2018, como matrículas e escola
indígena (meta M1); a volta do pipeline oficial (meta M5).

---

## 2026-11-11 — Teste 03: a conferência de 2019–2025 com os originais

**O que acontecia.** O teste 03 (`testes/03_validar_censo_pos04.py`, seção F) só lê um zip do Censo
com a opção `--completo`. Sem ela, confere contra o original apenas os anos com CSV já extraído em
`dados/bruto/censo/`.

- **No projeto anterior**, desde que o teste existe (Dados-do-Projeto `f524873`, 2026-10-14), os CSVs de
  2019–2025 estavam extraídos em `abandono-escolar/dados/bruto/censo/`. Então, mesmo sem `--completo`,
  o teste comparava 2019–2025 célula a célula com o microdado original: o relatório do projeto anterior
  registra "7 anos conferem célula a célula com o microdado ORIGINAL: 2019–2025". Os anos de 2007–2018
  nunca foram conferidos por esse teste, com ou sem `--completo`, porque os zips desses anos não estavam
  na máquina.
- **No abandono-rr**, a cópia trouxe só os zips, não os CSVs extraídos. Na primeira execução da Etapa 1,
  sem `--completo`, o teste **não comparou nenhum ano** com o original e passou com um aviso. A lacuna foi
  criada pela migração, não existia antes.

**Decisão.** O teste 03 roda sempre com `--completo` (`testes/test_validacoes.py`). Com isso, 2019–2025
conferem célula a célula com os zips originais em `dados/origem/censo/`, como no projeto anterior. O teste
de equivalência confirma, além disso, que a base inteira é idêntica à do projeto anterior.

**A comparação com o backup de outubro** (seção I do teste 03: a base do 04 antes × depois da correção de
14/10/2026) não roda no abandono-rr, porque o backup ficou no projeto anterior. Ela aparece no pytest como
**pulada**, com o motivo (`test_03_comparacao_com_backup_de_outubro`), e não como aprovada.

---

## 2026-11-11 — Os zips de 2019–2025 e o que cada um alimenta

Os 14 zips ficam em `dados/origem/`, **fora do git**; o `dados/MANIFEST.csv` guarda o sha256 de cada um, e
`python -m src.aquisicao --origem-local PASTA` (ou `--baixar`) os obtém conferindo o hash.

| Zip | Tamanho | Quem usa |
|---|---|---|
| `censo/microdados_censo_escolar_2019.zip` | 25,0 MB | `src/estendida/03` (reconstrução do cache) e teste 03 (`--completo`) |
| `censo/microdados_censo_escolar_2020.zip` | 24,8 MB | idem |
| `censo/microdados_censo_escolar_2021.zip` | 24,7 MB | idem; também traz os 2 PDFs de documentação do MANIFEST |
| `censo/microdados_censo_escolar_2022.zip` | 25,2 MB | idem |
| `censo/microdados_censo_escolar_2023.zip` | 30,6 MB | idem |
| `censo/microdados_censo_escolar_2024.zip` | 32,3 MB | idem |
| `censo/microdados_censo_escolar_2025_.zip` | 512,3 MB | idem (só a tabela de escolas) |
| `indicadores/tx_rend_escolas_2019.zip` a `_2025.zip` | 58,0 a 69,0 MB cada | `src/estendida/01` (reconstrução do cache de rendimento) |

**Nenhum serve só à base oficial.** Prova: `python src/estendida/99_pipeline.py --force` reconstruiu o cache
de 2019–2025 a partir dos 14 zips, e o conteúdo dos 14 parquets saiu idêntico ao versionado (só os
metadados do arquivo mudam, porque o cache original foi gravado com outra versão do pyarrow); a base
regerada continuou idêntica à do projeto anterior. O cache versionado foi mantido, para valer o sha256 do
MANIFEST.

**Retirado:** as tabelas Turma, Matrícula e Docente de 2025 (linhas do MANIFEST e de `src/config.py`).
Não são zips, mas só serviam à fase 2 do projeto anterior; o pipeline estendido lê só a tabela de escolas.
