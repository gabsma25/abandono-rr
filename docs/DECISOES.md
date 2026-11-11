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
