# Relatório técnico 04 — 18 variáveis do artigo, correção do Censo e índices de infraestrutura

**Projeto:** Risco de abandono escolar em Roraima (PIBIC/UERR + Mineração de Dados)
**Data:** 2026-10-14
**Documentos anteriores:** `relatorio_01`, `relatorio_02`, `relatorio_03`

> **Atualização (14/10/2026, fim do dia):** as seções 3, 4 e 7 descrevem a fase com 3 normalizações
> (`prop`, `zano`, `zref19`) e pesos do IIE fixos de 2019. Essa fase foi substituída: o 05 atual gera
> só `zano` ano a ano, com PC1 por ano e itens disponíveis em cada ano (2007–2011 incluído). Ver
> `relatorio_05_fechamento_18_variaveis_2026-10-14.md`. Contagens de testes atuais: 01 = 45, 02 = 41,
> 03 = 35 (`--completo`). O instantâneo do 05 antigo está em `saida/_backup_2026-10-14/`.

---

## 0. Sumário executivo

Ao conferir a base contra o artigo (Almeida & Mussato, 2023) apareceram três coisas:

1. **Faltava uma variável** (`IDP_patio_descoberto`): o Quadro 3 do artigo lista 18 variáveis, a base tinha 17.
2. **Erro nos dados já entregues:** em **2019–2021**, `IIB_agua_potavel`, `IIB_banheiro` e `IEP_projetor` valiam **0,00 para todas as escolas**. O script `03` pegava a *primeira coluna não nula*, e as colunas antigas (`IN_AGUA_FILTRADA`, `IN_BANHEIRO_DENTRO_PREDIO`, `IN_EQUIP_RETROPROJETOR`) continuam no layout do INEP preenchidas com 0 depois que a pergunta deixou de existir. Os 29 checks do relatório 03 não pegavam isso (só verificavam 0/1 e cobertura).
3. **Zeros estruturais:** despensa, refeitório, secretaria e pátios valiam 0 em 2008–2011, anos em que esses itens não foram coletados.

Correções feitas e documentadas aqui; pipeline passou a ter a etapa **05** (dimensões e IIE).

## 1. Evidência: o que foi coletado em cada ano (Brasil inteiro)

Percentual de escolas com valor 1, pelos microdados nacionais (resumo; tabela completa em `saida/relatorios/fontes_features_censo.csv`):

| Variável (coluna) | Coletada em | Observação |
|---|---|---|
| Água: `IN_AGUA_FILTRADA` → `IN_AGUA_POTAVEL` | 2007–2018 → 2019+ | outra pergunta (filtrada x potável) |
| Banheiro: `IN_BANHEIRO_DENTRO_PREDIO` → `IN_BANHEIRO` | 2007–2018 → 2019+ | idem |
| Biblioteca: `IN_BIBLIOTECA_SALA_LEITURA` → `IN_BIBLIOTECA` | 2007–2008 → 2009+ | |
| Projetor: `IN_EQUIP_RETROPROJETOR` → `IN_EQUIP_MULTIMIDIA` | 2007–2011 → 2012+ | equipamentos diferentes |
| Despensa, refeitório, secretaria, pátio coberto, pátio descoberto | 2012+ | 2007–2011 não coletados |
| Demais 9 variáveis | 2007+ | estáveis |

## 2. Regra de fonte adotada (`03_censo_features.py`)

Para cada (variável, ano): usar a **primeira candidata coletada** (≥ 1 escola do Brasil com valor 1), começando pela coluna do artigo. Se nenhuma foi coletada: `NaN` (nunca 0). A coluna `INFRA_FONTE_ARTIGO` marca os anos em que as 18 vieram do artigo (2019–2025). O `03` agora lê os anos em sequência (resolve a pendência do `out of memory` em 2010) e grava, por ano, as colunas cruas de RR e a estatística nacional (`cache/censo/{ano}_nacional.json`).

Consequência: a série de água/banheiro/projetor tem **quebra de pergunta** (2018→2019 e 2011→2012). Como a coluna de fonte fica registrada, o modelo pode restringir o período (por exemplo, 2019+ para ficar 100% fiel ao artigo).

## 3. Etapa 05 — dimensões e IIE

Seguindo o artigo: IIB (4 itens), IDA (5), IDP (5), IEP (4); soma por dimensão; IIE = primeiro componente principal das 4 dimensões. Como o artigo trabalha com uma foto de 2019 (165 escolas estaduais de ensino médio) e a base é um painel de 19 anos, foram implementadas **3 normalizações**, todas gravadas:

| Sufixo | O que faz | Parâmetros |
|---|---|---|
| `_prop` | soma / nº de itens | nenhum |
| `_zano` | z-score dentro de cada ano | média e desvio do próprio ano (n ≥ 30, dp > 0) |
| `_zref19` | z-score com média/desvio fixos de 2019 | 152 escolas estaduais com taxa de EM em 2019 (artigo: 165) |

IIE: pesos do PC1 calculados em 2019 e **fixos**; aplicados às 4 dimensões de cada normalização. Resultado em 2019: PC1 com autovalor 3,05 e 76,2 % da variância (critérios do artigo: > 1 e > 60 %); pesos IIB 0,496 / IDA 0,509 / IDP 0,519 / IEP 0,475. Uma dimensão só existe se todos os itens existem → IDA, IDP e IIE ficam vazios em 2007–2011.

Achado: as três normalizações ordenam as escolas quase igual (Spearman ≥ 0,999 por ano). A escolha importa para modelos lineares (escala), pouco para árvores.

## 4. Testes

- `testes/01_validar_base.py`: 45 checks, 0 falhas. Novos: 18 variáveis; ausência real x zero estrutural (compara com `fontes_features_censo.csv`); `05` preserva o `04`; seção 14 compara o 01 bruto com o 02b (mesmo conjunto de escola-ano). Um check antigo (`for/else`) nunca falhava — corrigido.
- `testes/02_validar_indices.py`: 46 checks, 0 falhas. Recalcula cada método de forma independente, verifica média 0/desvio 1, ausência de vazamento (parâmetros de 2019 recomputados só com dados ≤ 2019), pesos/autovalores, consistência entre métodos e sanidade (infra urbana > rural em 2019).
- `testes/03_validar_censo_pos04.py` (36 checks no modo padrão, 35 com `--completo`; 0 falhas): auditoria do parquet pós-04. Recomputa a regra de fonte do zero (cache + estatística nacional), compara célula a célula (226.746 células) e confere com o dado original do INEP (padrão: CSVs de 2019–2025; com `--completo`, também os zips de 2007–2018, 19 de 19 anos conferem); mostra prevalência e ausência por variável × ano; compara com o 04 anterior à correção.
- Efeito da correção (teste 03, seção I): `IIB_agua_potavel`, `IIB_banheiro` e `IEP_projetor` passaram de média 0,00 para 0,61 / 0,71 / 0,34 em 2019–2021; as 9 variáveis de coluna única ficaram idênticas.
- O teste do `05` achou um erro meu: a conversão de `ANO` para `int64` quebrava a regra de tipagem (`Int16`). Corrigido.

## 5. Limitações e pendências

- **Cobertura 2007–2011 (falta de dado, não erro).** Despensa, refeitório, secretaria, pátio coberto e pátio descoberto não foram coletados nesses anos. Como uma dimensão só existe quando todos os itens existem, ficam ausentes **IDA e IDP (2 das 4 dimensões) e o IIE**. IIB e IEP cobrem 2007–2025. O IIE existe apenas em 2012–2025 (9.409 de 12.597 linhas). Qualquer modelo que use a série inteira precisa tratar esse período (blocos de features por período ou só IIB/IEP).
- Recorte de referência: 152 escolas, não 165. Reproduzir a Tabela 1 do artigo exige extrair do Censo 2019 as colunas de filtro e a de escola indígena (o D8 da base oficial é relacionado).
- Na Tabela 1 do artigo, as linhas de IDP e IEP trazem somas idênticas em três regiões (37, 13, 3); parece erro de impressão.
- O artigo seleciona as variáveis também por correlação (0,3–0,7); não replicamos esse filtro, usamos as 18 finais.
- Normalização padrão a decidir (plano: testar as três).
- Modelos treinados antes de 14/10 com `IIB_agua_potavel`, `IIB_banheiro` ou `IEP_projetor` em 2019–2021 usaram dados errados.
- Backup parcial em `saida/_backup_2026-10-14/` (um `cp` encadeado parou num conflito de nome): contém scripts 03/04/99, teste 01, `COMO_RODAR.md`, `saida_README.md` e o `base_atual.parquet` antigo (= 04 antigo, copiado também para `etapas/`). Não foram preservados o README raiz antigo nem o cache antigo do Censo.

## 6. Tipagem (regra 6 do CLAUDE.md) — achado do teste 03

O 03/04/05 entregavam `CO_ENTIDADE` como `object`, `ANO` como `int64` no 03, as 18 variáveis como `float64` e `INFRA_FONTE_ARTIGO` como `int8`. O teste 01 só checava a tipagem do 02a, por isso não pegou. Corrigido: `CO_ENTIDADE` `string`, `ANO` `Int16`, 18 variáveis e `INFRA_FONTE_ARTIGO` `Int8` nullable, colunas derivadas do 05 `Float64` nullable. O teste 01 agora confere os 4 estágios.

## 7. Escolha do método de normalização (`analises/01_escolha_metodo_infra.py`)

Análise de decisão, fora de `testes/` (não valida o pipeline). Não usa o desfecho como critério (regra 3 do CLAUDE.md); a única leitura de taxa é a presença de `APROVACAO_MED`, como filtro de "tem ensino médio" para reconstruir o recorte de referência do 05. Saídas: `saida/relatorios/escolha_metodo_infra.txt` e `escolha_metodo_infra_metricas.csv`. Rodada na série 2007–2025 (IIE: 2012–2025), conferida também com pandas 3.

Resultados (limites de leitura declarados no topo do script; são regras práticas, não testes estatísticos):

- **Ordenação dentro do ano.** As 4 dimensões têm ordenação idêntica nos três métodos (Spearman 1,0000); o IIE difere no máximo na 3ª casa (mínimo 0,9986). O método só importa ao empilhar anos no mesmo modelo.
- **Tendência entre anos.** Só 0,6 % da variância do IIE é diferença de média entre anos (IEP: 3,1 %; IIB: 1,6 %). O `zano` descarta pouca informação.
- **Quebras de questionário.** Na mesma escola, o salto IIB 2018→2019 (água/banheiro) é +0,174 dp em `prop` e `zref19` e +0,013 dp em `zano`. No IIE agregado o pior salto é 0,064 dp (prop), 0,063 (zref19) e 0,046 (zano).
- **Estacionariedade treino→teste.** Deslocamento máximo da média, em dp do treino: IIE 0,13 (prop), 0,12 (zref19), 0,00 (zano); IIB 0,32 e IEP 0,27 em prop/zref19. O KS do `zano` é inflado pela discretização (as somas caem em posições diferentes do z a cada ano).
- **Persistência.** Spearman t→t+1 do IIE ≈ 0,98 nos três métodos.
- **Pesos do IIE.** Pesos de 2019 versus pesos do ano, acumulados até t ou iguais: Spearman ≥ 0,998 dentro do ano. Os pesos fixos de 2019 usam dado de 2019 em folds anteriores, nos três métodos; trocar por pesos acumulados é barato.
- **Dado futuro.** `zref19` usa média/dp de 2019 e vaza em folds com teste anterior a 2019. `prop` e `zano` não.
- **Recorte de referência.** Reamostrando as 152 escolas, o nível do `IIE_zref19` muda até 0,155 dp (p95). Outras populações de referência (373 ou 667 escolas) deslocam o nível em 0,5–0,7 dp: o zref19 é relativo à população escolhida.

Decisão: pendente (do grupo). A comparação preditiva fica para a modelagem, com o método tratado como hiperparâmetro dentro do walk-forward.
