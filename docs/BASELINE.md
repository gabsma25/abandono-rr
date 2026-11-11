# A régua: o que é e o que se sabe dela

Gerado por `python src/relatorios/baseline.py` (não edite à mão). Cada número vem de um CSV, citado ao lado.
Os números da Etapa 1 e das réguas da janela segura são **regerados** pelo abandono-rr; os da Etapa 2 e da
classificação são **citados** do projeto anterior, sem rodar nada de novo.

## 1. As réguas, em linguagem simples

Uma **régua** é uma forma simples de montar a lista de escolas de maior risco, sem modelo nenhum. Ela serve de
ponto de comparação: uma ferramenta só vale a pena se fizer uma lista melhor do que a régua.

**A régua (B1R_lag): o último abandono conhecido na hora de fazer a lista.** A lista do ano t+1 precisa estar
pronta no começo de t+1. Nesse momento, a taxa de abandono do ano t ainda não foi publicada pelo INEP (ela sai
durante t+1). O dado mais recente disponível é o **abandono de t−1**. A régua ordena as escolas por ele: quem teve
mais abandono em t−1 fica no topo.

**A versão otimista (B1R): o abandono de t.** Ordena as escolas pelo abandono do próprio ano t. Costuma acertar mais
(seção 3), porque usa um dado mais recente, mas esse dado ainda não existe quando a lista precisa ser feita. Por isso ela
é só um **limite superior**, nunca o adversário da ferramenta.

**B2: território e rede.** Para cada combinação de localização (urbana, rural) e rede (estadual, municipal,
federal), calcula a mediana do abandono nos anos de treino e dá esse valor a todas as escolas da combinação.
Não olha a história da própria escola: mostra quanto se acerta só sabendo onde a escola está e a que rede pertence.

**Acaso.** Uma lista sorteada. Numa lista com 20% das escolas, o acaso encontra, em média, 20% das escolas de
abandono alto; é o piso.

**Como se mede: Recall@20%.** Das escolas que de fato tiveram abandono alto, que fração estava entre os 20% do
topo da lista. Atenção: nas Etapas 1 e 2, "abandono alto" são os 20% de maior abandono observado; na
classificação, é o rótulo `alto_risco_t1` (os 20% maiores **e** abandono > 0). Os números de uma não se
comparam com os da outra.

## 2. Etapa 1: quanto a persistência acerta, sem modelo

Fonte: `saida/avaliacao/01_baselines.csv`, regerado pelo abandono-rr e idêntico ao do projeto anterior
(`testes/test_equivalencia.py`). Transições até o desfecho de 2024; escolas públicas com o desfecho conhecido.
A Etapa 1 só tem a **versão otimista** (abandono de t) e não tem intervalo de confiança.

| Etapa | Transições | Recall@20% da régua otimista: mín / mediana / máx | Anos acima do acaso | Acaso (mediana) |
|---|---|---|---|---|
| anos finais (AF) | 16 (2008→2009 a 2023→2024) | 0,28 / 0,42 / 0,49 | 16 de 16 | 0,20 |
| ensino médio (EM) | 16 (2008→2009 a 2023→2024) | 0,17 / 0,35 / 0,52 | 15 de 16 | 0,20 |

**Como ordem, a persistência acerta acima do acaso em quase todos os anos. Como valor, não:** repetir a taxa
de t como previsão de t+1 tem R² acima de zero em 0 de 16 transições no AF e 1 de 16 transições no EM, e erra menos que a média histórica em 10 de 16 no AF e 5 de 16 no EM. Por isso a decisão é sempre por ordenação (Recall@K), não por R² nem por erro médio.

## 3. Etapa 2: modelos de regressão contra a régua

Fonte: `docs/projeto_anterior/02d_testes.csv` e `02_walkforward.csv` (Dados-do-Projeto `969fc64`). Ridge e árvore, 4 blocos de
informação (inclusive TDI, ATU e IED), testados nos desfechos de 2021 a 2024; diferença das quatro transições
agrupadas, bootstrap por escola e correção de Holm, nos K de 10% e 20%.

| Comparação | AF | EM | Total |
|---|---|---|---|
| modelo melhor que a **régua** (família F5), testes que resistem ao Holm | 0 de 16 | 0 de 16 | 0 de 32 |
| idem, somando as comparações entre blocos | | | 0 de 56 |
| modelo melhor que a **B2** (família F4), testes que resistem ao Holm | 14 de 16 | 1 de 16 | 15 de 32 |

**Leitura.** Nenhum modelo ordenou melhor que a régua. Contra a B2, os modelos ganham nos anos finais
(ganhos de +0,11 a +0,22 no Recall@K): a história da própria escola diz mais do que
o território e a rede.

**As duas réguas ano a ano** (Recall@20%, definição da Etapa 2). A régua acerta menos que a versão otimista em
6 dos 8 anos-etapa, e oscila mais no ensino médio (de 0,062 a 0,353):

| Etapa | Desfecho | Régua (abandono de t−1) | Otimista (abandono de t) | B2 |
|---|---|---|---|---|
| AF | 2021 | 0,303 | 0,270 | 0,202 |
| AF | 2022 | 0,340 | 0,383 | 0,075 |
| AF | 2023 | 0,348 | 0,440 | 0,245 |
| AF | 2024 | 0,420 | 0,427 | 0,255 |
| EM | 2021 | 0,219 | 0,172 | 0,192 |
| EM | 2022 | 0,062 | 0,469 | 0,075 |
| EM | 2023 | 0,273 | 0,333 | 0,257 |
| EM | 2024 | 0,353 | 0,390 | 0,279 |

## 4. A classificação de alto risco na janela segura

Fontes: as réguas, em `saida/avaliacao/reguas_janela.csv`, **regeradas** pelo abandono-rr e idênticas às do
projeto anterior; a ferramenta e os intervalos, em `experimentos/classificacao_2013_2018/saida/` (Dados-do-Projeto `969fc64`),
da execução única de 2026-11-10. Desfechos de 2016 a 2019, quatro anos juntos; IC de 95% por bootstrap
sorteando escolas (5.000 reamostragens).

| Etapa | Acaso | B2 | **Régua** [IC 95%] | Ferramenta (regressão logística, bloco 3) [IC 95%] |
|---|---|---|---|---|
| anos finais (AF) | 0,200 | 0,244 | **0,397** [0,332; 0,473] | 0,411 [0,335; 0,478] |
| ensino médio (EM) | 0,200 | 0,209 | **0,275** [0,209; 0,370] | 0,337 [0,254; 0,429] |

*Recall@20%, sobre o rótulo de alto risco.*

**O teste que decide** (família F6: ferramenta − régua, 2 etapas × 3 modelos × 3 blocos × 2 métricas, com Holm):
**0 GANHO em 36 testes**; o menor p ajustado é 1,000. No Recall@20%:

- anos finais (AF): 9 SEM GANHO PRÁTICO
- ensino médio (EM): 6 INCONCLUSIVO, 3 SEM GANHO PRÁTICO

**Leitura.** A ferramenta fica bem acima do acaso, mas não se distingue da régua. Nos anos finais, o ganho
possível é pequeno demais para valer a pena; no ensino médio, os intervalos são largos demais para decidir.

## 5. O que isso diz para o projeto

- A régua é o adversário certo: é a regra que a secretaria poderia usar hoje, sem modelo, com o dado que já tem.
- Nenhum modelo, na Etapa 2 nem na classificação, ordenou melhor do que ela.
- A versão otimista acerta mais, mas usa um dado que não existe na hora da decisão; nunca é adversária.
- A B2 é o piso informativo: ganhar dela mostra que a história da escola importa, não que a ferramenta é útil.
