# Relatório técnico 05 — Fechamento das 18 variáveis processadas (14/10/2026)

Relatório do dia. Resume o que foi feito em `gustavo/` em 14/10/2026, a decisão sobre os índices de infraestrutura e o estado final. Continua o relatório 04 (correção do Censo e primeira versão do 05 com 3 normalizações), que ficou desatualizado nos pontos indicados na seção 9.

## 0. Sumário executivo

- A base `saida/base_atual.parquet` está fechada para a etapa "18 variáveis processadas": **12.597 × 55**, 2007–2025, com as 18 variáveis do artigo (Almeida & Mussato, 2023), 4 dimensões, o IIE e um marcador de regime.
- **Método único e final:** z-score dentro de cada ano (`zano`) sobre a soma dos itens **disponíveis naquele ano**; IIE = primeiro componente principal das 4 dimensões, calculado no próprio ano. Colunas: `DIM_IIB_zano`, `DIM_IDA_zano`, `DIM_IDP_zano`, `DIM_IEP_zano`, `IIE_zano` e `INFRA_ITENS_COMPLETOS`.
- **Descartados:** `zref19` (usa média/desvio de 2019, o que é dado futuro nos folds anteriores a 2019, e depende de um recorte de referência que não replica o do artigo) e `prop` (mesma informação que o `zano`, só muda a escala; carrega as quebras de questionário). `prop` continua disponível com `05_indices_infra.py --com-prop`.
- **Cobertura:** as 4 dimensões e o IIE existem para **100%** das escolas em **todos** os 19 anos. Isso exigiu uma aproximação em 2007–2011 (seção 5), que fica registrada como limitação.
- **Validação:** teste 01 com 45 checks, teste 02 com 41 (44 com `--com-prop`), teste 03 com 35 (`--completo`), todos sem falhas; rodados também com pandas 3, o ambiente do Python 3.14 do Gustavo.

## 1. Ponto de partida do dia

Havia um pipeline de 5 etapas (01→05) e uma base com **erro de coleta**: o INEP mantém colunas no layout do Censo mesmo quando a pergunta não foi feita (valor 0 para todas as escolas). Água, banheiro e projetor estavam em 0,00 em 2019–2021 e vários itens em 0 em 2008–2011. Os 29 checks anteriores não pegavam isso. A correção (regra de fonte por variável e ano, relatório 04) e a conferência contra os microdados originais dos 19 anos foram feitas na primeira parte do dia.

## 2. O que foi feito, em ordem

1. **Conferência do escopo.** Releitura de `gustavo/` e do artigo. Respostas minhas dadas de memória estavam imprecisas sobre o conteúdo de `gustavo/` e sobre o artigo (o pátio coberto e o descoberto são variáveis separadas no Quadro 3, totalizando 18). Corrigidas após abrir a pasta e o PDF.
2. **Correção do 03/04** (relatório 04): regra "primeira coluna realmente coletada, senão NA, nunca 0"; tipagem da regra 6; 03 sequencial (resolve o estouro de memória de 2010).
3. **Testes.** `01_validar_base.py` (45 checks, incluindo comparação 01 bruto × 02b), `03_validar_censo_pos04.py` (recomputa a regra de fonte em 226.746 células e compara os 19 anos com o dado original do INEP).
4. **Primeiro 05 com 3 normalizações** (`prop`, `zano`, `zref19`) e teste 02 independente.
5. **Análise de escolha** (`analises/01_escolha_metodo_infra.py`). Compara os 3 métodos sem usar o desfecho (regra 3 do CLAUDE.md). Resultados no relatório 04, §7.
6. **Análise de preenchimento de 2007–2011** (`analises/02_preenchimento_2007_2011.py`). Compara três formas de lidar com os itens ausentes (seção 5 abaixo).
7. **Decisão do grupo** (conversa de 14/10): `zano` como método único; itens disponíveis por ano para IDA/IDP em 2007–2011; `zref19` e `prop` fora da base.
8. **Novo 05**, novo teste 02, ajustes no teste 01 e nas análises; pipeline rodado de ponta a ponta; verificação em pandas 3.

## 3. Decisão e justificativa

Critérios usados, todos sem o desfecho (relatório 04, §7 e `saida/relatorios/escolha_metodo_infra.txt`):

| Critério | prop | zano | zref19 |
|---|---|---|---|
| Parâmetros das dimensões sem dado futuro | sim | sim | **não** (média/dp de 2019) |
| Quebra de questionário nas dimensões (pior salto da mesma escola, IIB/IEP) | 0,17 dp | 0,08 dp | 0,17 dp |
| Deslocamento treino→teste do IIB, máx. | 0,32 dp | 0,00 | 0,32 dp |
| Dependência de uma população de referência | não | não | sim (152 escolas, artigo: 165) |
| Ordenação dentro do ano (dimensões) | idêntica | idêntica | idêntica |

- Dentro de um mesmo ano os três métodos ordenam as escolas de forma idêntica nas dimensões (Spearman 1,0000) e quase idêntica no IIE (≥ 0,9986). A diferença está só no nível entre anos e na origem dos parâmetros.
- O `zano` usa só dados do próprio ano. O efeito-ano é pequeno (0,6% da variância do IIE), então ele descarta pouca informação.
- **Pesos do IIE.** A versão antiga usava pesos de 2019 para todos os anos; isso é dado futuro em folds anteriores. Os pesos agora saem do PC1 de cada ano. Eles variam pouco (normalizados para somar 1: IIB 0,23–0,25; IDA 0,25–0,26; IDP 0,24–0,25; IEP 0,25–0,27), e a ordenação do IIE quase não depende da ponderação (Spearman mínimo dentro do ano: 0,9992 contra a média simples das 4 dimensões; 0,9980 entre pesos de 2019 e pesos do ano, na análise 01).
- A comparação de desempenho preditivo **não** foi usada para escolher (regra 3). Se for desejada, entra na modelagem, com o método como hiperparâmetro dentro do walk-forward.

## 4. Como o 05 calcula

Entrada: `04_base_com_censo.parquet`. Para cada ano e dimensão:

1. **Itens disponíveis.** Um item está disponível num ano se alguma escola tem valor nele. A soma da dimensão usa todos os itens disponíveis do ano; a escola que não tiver algum deles recebe `NaN` (nunca se calcula "com menos itens" por escola).
2. **z-score do ano** da soma: média e desvio populacional (ddof=0) das escolas do ano; exige n ≥ 30 e desvio > 0.
3. **IIE** = soma(peso × dimensão), com os pesos do PC1 da matriz de correlação das 4 dimensões z do próprio ano (norma 1, soma > 0). Escala = autovalor do ano (desvio 1,7–1,9).
4. **`INFRA_ITENS_COMPLETOS`** = 1 quando as 4 dimensões do ano usam todos os itens do artigo (2012–2025), 0 em 2007–2011. Marcador de regime para filtrar e auditar; **não deve entrar como feature** (coincide com o período), como `INFRA_FONTE_ARTIGO`.

O cálculo fica na função pura `calcular(base)`, o que permite ao teste 02 provar a ausência de vazamento rodando o 05 de verdade em dados perturbados.

## 5. Disponibilidade das 18 variáveis e o tratamento de 2007–2011

| Dimensão | Itens em todos os anos (2007–2025) | Itens só de 2012 em diante |
|---|---|---|
| IIB (4) | água, energia da rede, coleta de lixo, banheiro | nenhum |
| IDA (5) | sala da diretoria, sala dos professores | despensa, refeitório, secretaria |
| IDP (5) | biblioteca, laboratório de informática, quadra | pátio coberto, pátio descoberto |
| IEP (4) | computador, impressora, projetor, internet | nenhum |

São 13 itens em todos os anos e 5 só a partir de 2012 (o Censo não perguntava). Quatro dos 13 mudaram de pergunta (água e banheiro até 2018; biblioteca em 2007–2008; projetor até 2011). Consequência: IIB e IEP seguem o artigo em todos os anos; IDA e IDP, e portanto o IIE, não podem ser calculados como no artigo em 2007–2011.

**Opções avaliadas** (`saida/relatorios/preenchimento_2007_2011.txt`), medindo a persistência da posição da mesma escola (Spearman t→t+1) na virada 2011→2012:

| Opção | IIE 2011→2012 | Observação |
|---|---|---|
| A. só IIB + IEP em todos os anos | 0,962 | sem quebra, mas concorda só 0,969 com o IIE completo |
| **B. itens disponíveis em cada ano (adotada)** | 0,961 | pequena queda; vizinhos 0,974–0,981 |
| C. núcleo fixo de 13 itens em todos os anos | 0,975 | sem quebra; é uma versão reduzida também depois de 2012 |

A opção B foi adotada por manter, de 2012 em diante, exatamente as definições do artigo, e por gerar um único conjunto de colunas.

**Limitação registrada (a modificação a levantar):**

- Em 2007–2011, IDA usa 2 itens (3 valores distintos; 44% das escolas empatadas) e IDP usa 3 itens (4 valores; 56% empatadas). Em 2019, com 5 itens, os maiores grupos empatados são 33% e 49%.
- Quanto fica imperfeito, medido em 2012–2025 comparando a versão parcial com a completa (Spearman dentro do ano): **IDA 0,89–0,90, IDP 0,89–0,93, IIE 0,987–0,989**.
- Na virada 2011→2012 a persistência cai em IDA (0,888, contra 0,951 nos anos vizinhos) e IDP (0,927 contra 0,951); no IIE a queda é pequena (0,961 contra 0,977).
- Com `prop` o nível também saltaria na virada (IDA −0,22 dp, IDP −0,12 dp); o z por ano remove esse salto de nível, mas não a mudança de posição.
- Se a modelagem mostrar problema nessa virada, a opção C (núcleo fixo) pode ser acrescentada sem refazer nada, em 3 colunas.

## 6. Colunas finais

`saida/base_atual.parquet` (= `etapas/05_base_com_indices.parquet`): 12.597 × 55.

| Grupo | Colunas | Tipo |
|---|---|---|
| tx_rend longitudinal | 30 colunas (02b) | conforme 02b |
| Censo | 18 variáveis `IIB_*`, `IDA_*`, `IDP_*`, `IEP_*` + `INFRA_FONTE_ARTIGO` | `Int8` |
| Dimensões | `DIM_IIB_zano`, `DIM_IDA_zano`, `DIM_IDP_zano`, `DIM_IEP_zano` | `Float64` |
| Índice | `IIE_zano` | `Float64` |
| Marcador | `INFRA_ITENS_COMPLETOS` | `Int8` |

Níveis de uso no modelo: nenhuma infraestrutura; 18 itens; 4 dimensões; IIE. Basta escolher as colunas. Em 2007–2011, 5 dos 18 itens são `NaN` (ausência estrutural, nunca 0).

## 7. Testes e verificações

| Teste | Resultado | Observação |
|---|---|---|
| `testes/01_validar_base.py` | 45 OK, 0 falhas | integridade de todos os estágios; 05 acrescenta exatamente 6 colunas ao 04 |
| `testes/02_validar_indices.py` | 41 OK, 0 falhas (44 com `--com-prop`) | recomputa itens, z, PC1 e IIE de forma independente; checa média 0/dp 1, Kaiser e > 60% em todos os anos; teste de vazamento executando o 05 em dados perturbados, com controle negativo (um z global mudaria 2019 em até 0,73) |
| `testes/03_validar_censo_pos04.py --completo` | 35 OK, 0 falhas | 19 de 19 anos batem com o dado original do INEP; sem `--completo`: 35 OK + 1 aviso (2007–2018 não conferidos) |
| pandas 3.0.6 (venv do container) | 01: 45 OK; 02: 41 OK e 44 OK com `--com-prop`; 05 e análise 02 reproduzem os mesmos números | replica o ambiente Python 3.14 do Gustavo |

As análises `analises/01` e `analises/02` também rodaram sem erro; a 01 reproduz o IIE_zref19 do 05 antigo com erro de 4e-16.

## 8. Arquivos

**Criados:** `analises/01_escolha_metodo_infra.py`, `analises/02_preenchimento_2007_2011.py`, `docs/relatorio_05_fechamento_18_variaveis_2026-10-14.md` (este), `saida/relatorios/escolha_metodo_infra.txt` e `_metricas.csv`, `saida/relatorios/preenchimento_2007_2011.txt`.

**Reescritos:** `programas/05_indices_infra.py`, `testes/02_validar_indices.py`.

**Alterados:** `testes/01_validar_base.py` (esperado de colunas do 05), `analises/01_escolha_metodo_infra.py` (autossuficiente; lê o instantâneo de 3 métodos), documentação (seção 9).

**Backup do estado anterior (3 normalizações)**, em `saida/_backup_2026-10-14/`: `05_base_com_indices_3metodos.parquet`, `05_indices_infra_3metodos.py`, `02_validar_indices_3metodos.py`, `indices_infra_3metodos.txt`, `indices_infra_parametros_3metodos.json`. O `rm` está bloqueado na pasta conectada, então nada foi apagado.

**Removidos da base:** as 15 colunas `DIM_*`/`IIE_*` de `prop`, `zano` (versão com pesos de 2019) e `zref19`; entra `INFRA_ITENS_COMPLETOS`. `base_atual.parquet` mudou de 64 para 55 colunas. Qualquer notebook que use `*_prop`, `*_zref19` ou o `IIE_zano` antigo precisa ser ajustado (o `IIE_zano` mudou de valor porque os pesos agora são anuais).

## 9. Documentos de `gustavo/` revisados

- `README.md`, `COMO_RODAR.md`, `saida/README.md`: contagem de colunas, método, testes, análises e pendências atualizados.
- `docs/relatorio_04_...md`: nota de atualização no topo apontando para este relatório (as seções 3, 4 e 7 descrevem a fase com 3 normalizações).
- `docs/relatorio_03_reorganizacao.md`: nota apontando para os relatórios 04 e 05.
- Não precisaram de mudança: `docs/relatorio_01` e `02`, `programas/01..04`, `programas/99_pipeline.py` (já executa 01→05; o 05 não recebe flags do pipeline), `testes/03`.

## 10. Como reproduzir

```bash
python programas/99_pipeline.py --from 04      # 04 e 05 (cache do 03 quente)
python testes/01_validar_base.py
python testes/02_validar_indices.py
python testes/03_validar_censo_pos04.py --completo
python analises/02_preenchimento_2007_2011.py   # números da seção 5
python analises/01_escolha_metodo_infra.py      # lê o instantâneo de 3 métodos (seção 3)
python programas/05_indices_infra.py --com-prop # opcional: acrescenta *_prop
```

## 11. Pendências e próximos passos

- **Recorte de referência do artigo (152 × 165):** deixou de afetar a base (sem `zref19`), mas reproduzir a Tabela 1 do artigo ainda exigiria extrair do Censo 2019 as colunas de filtro e a de escola indígena.
- **Tabela 1 do artigo:** as linhas de IDP e IEP trazem somas idênticas em três regiões; parece erro de impressão.
- **D8 (indígena, localização diferenciada, matrículas AF/EM) e TDI/ATU/IED:** continuam não construídos.
- **Scripts de `programas/diagnostico/`:** caminhos corrigidos em 14/10, mas os scripts não foram reexecutados.
- **README raiz antigo e cache antigo do Censo** não foram preservados no backup parcial de 14/10 (o README pode ser recuperado pelo histórico de versões do Drive).
- **Modelagem (próximo passo):** testes A/B/C por bloco de features em walk-forward, lendo `saida/base_atual.parquet`. Lembrar: `INFRA_FONTE_ARTIGO` e `INFRA_ITENS_COMPLETOS` não são features; treinar com a série completa exige decidir como tratar a virada de 2012 (usar só IIB/IEP em 2007–2011, ou aceitar as dimensões parciais).
- Modelos treinados antes de 14/10 com `IIB_agua_potavel`, `IIB_banheiro` ou `IEP_projetor` em 2019–2021 usaram dados errados.

## 12. Erros do dia (para registro)

- Respostas dadas de memória, antes de abrir `gustavo/` e o artigo, estavam imprecisas; corrigidas após a leitura direta.
- A base entregue no início do dia tinha o erro de coleta do Censo; os 29 checks daquela época não o detectavam. Corrigido e coberto por testes novos.
- Tipagem fora da regra 6 (`CO_ENTIDADE` como objeto, flags `float64`/`int8`), corrigida em 03/04/05 e nos testes.
- Incompatibilidade com pandas 3 (`ArrowExtensionArray` sem `.sum()`), corrigida e verificada no venv com pandas 3.0.6.
- Associei por engano o "método mais lógico" do Gustavo (cada ano com os seus dados) ao `zref19`; era o `zano`. Corrigido na conversa antes de qualquer alteração de código.
- O backup parcial perdeu o README raiz antigo (um `cp` encadeado parou num conflito de nome).
