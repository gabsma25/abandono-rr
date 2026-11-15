# 03 — Classificação de alto risco, janela 2013–2018 (alvos de teste 2016–2019)

Gerado por `gustavo/avaliacao/03_classificacao.py`. Protocolo: `abandono-escolar/docs/DECISOES.md`,
2026-11-10. Bootstrap por escola agrupado, 5000 reamostragens; IC 95% por percentis.
Valor agrupado = média simples das 4 transições de teste.

## AF

Escolas-ano de teste: 901; de alto risco: 180 (prevalência média 0,200).

| Nota | Bloco | PR-AUC [IC 95%] | Recall@20% [IC 95%] | ROC-AUC | Precisão (0,5) | Recall (0,5) | F1 (0,5) |
|---|---|---|---|---|---|---|---|
| B1R_lag | — | 0,374 [0,314; 0,459] | 0,397 [0,332; 0,473] | 0,675 | — | — | — |
| B2 | — | 0,241 [0,199; 0,287] | 0,244 [0,216; 0,275] | 0,598 | — | — | — |
| Regressão logística | 1 | 0,381 [0,320; 0,467] | 0,384 [0,317; 0,452] | 0,694 | 0,351 | 0,512 | 0,415 |
| Random Forest | 1 | 0,358 [0,298; 0,447] | 0,411 [0,343; 0,475] | 0,678 | 0,343 | 0,495 | 0,403 |
| HistGradientBoosting | 1 | 0,354 [0,292; 0,443] | 0,338 [0,280; 0,409] | 0,666 | 0,316 | 0,478 | 0,380 |
| Regressão logística | 2 | 0,385 [0,324; 0,471] | 0,411 [0,332; 0,466] | 0,710 | 0,315 | 0,534 | 0,395 |
| Random Forest | 2 | 0,339 [0,288; 0,424] | 0,422 [0,356; 0,486] | 0,689 | 0,335 | 0,517 | 0,405 |
| HistGradientBoosting | 2 | 0,345 [0,290; 0,430] | 0,350 [0,287; 0,418] | 0,681 | 0,318 | 0,511 | 0,392 |
| Regressão logística | 3 | 0,390 [0,327; 0,478] | 0,411 [0,335; 0,478] | 0,716 | 0,329 | 0,534 | 0,406 |
| Random Forest | 3 | 0,355 [0,299; 0,444] | 0,405 [0,342; 0,466] | 0,698 | 0,357 | 0,528 | 0,423 |
| HistGradientBoosting | 3 | 0,377 [0,315; 0,466] | 0,381 [0,325; 0,450] | 0,697 | 0,328 | 0,522 | 0,402 |
| acaso | — | 0,200 [0,166; 0,234] | 0,200 [0,199; 0,201] | 0,500 | — | — | — |

### AF: modelo − B1R_lag (família F6, Holm em 36 testes)

| Modelo | Bloco | Métrica | Diferença [IC 95%] | p Holm | Leitura | IC em escolas por ano |
|---|---|---|---|---|---|---|
| Regressão logística | 1 | PR_AUC | +0,006 [-0,021; +0,033] | 1,000 | INCONCLUSIVO | — |
| Regressão logística | 1 | Rec@20pct | -0,014 [-0,068; +0,027] | 1,000 | SEM GANHO PRÁTICO | -3,0 a +1,2 |
| Random Forest | 1 | PR_AUC | -0,017 [-0,058; +0,032] | 1,000 | INCONCLUSIVO | — |
| Random Forest | 1 | Rec@20pct | +0,014 [-0,035; +0,045] | 1,000 | SEM GANHO PRÁTICO | -1,6 a +2,0 |
| HistGradientBoosting | 1 | PR_AUC | -0,021 [-0,066; +0,029] | 1,000 | INCONCLUSIVO | — |
| HistGradientBoosting | 1 | Rec@20pct | -0,059 [-0,122; +0,001] | 1,000 | SEM GANHO PRÁTICO | -5,5 a +0,1 |
| Regressão logística | 2 | PR_AUC | +0,010 [-0,019; +0,039] | 1,000 | INCONCLUSIVO | — |
| Regressão logística | 2 | Rec@20pct | +0,014 [-0,051; +0,042] | 1,000 | SEM GANHO PRÁTICO | -2,3 a +1,9 |
| Random Forest | 2 | PR_AUC | -0,035 [-0,066; +0,004] | 1,000 | INCONCLUSIVO | — |
| Random Forest | 2 | Rec@20pct | +0,025 [-0,024; +0,059] | 1,000 | SEM GANHO PRÁTICO | -1,1 a +2,7 |
| HistGradientBoosting | 2 | PR_AUC | -0,030 [-0,072; +0,019] | 1,000 | INCONCLUSIVO | — |
| HistGradientBoosting | 2 | Rec@20pct | -0,048 [-0,110; +0,009] | 1,000 | SEM GANHO PRÁTICO | -4,9 a +0,4 |
| Regressão logística | 3 | PR_AUC | +0,016 [-0,016; +0,045] | 1,000 | INCONCLUSIVO | — |
| Regressão logística | 3 | Rec@20pct | +0,014 [-0,053; +0,057] | 1,000 | SEM GANHO PRÁTICO | -2,4 a +2,6 |
| Random Forest | 3 | PR_AUC | -0,020 [-0,051; +0,020] | 1,000 | INCONCLUSIVO | — |
| Random Forest | 3 | Rec@20pct | +0,008 [-0,051; +0,053] | 1,000 | SEM GANHO PRÁTICO | -2,3 a +2,4 |
| HistGradientBoosting | 3 | PR_AUC | +0,002 [-0,041; +0,051] | 1,000 | INCONCLUSIVO | — |
| HistGradientBoosting | 3 | Rec@20pct | -0,016 [-0,076; +0,046] | 1,000 | SEM GANHO PRÁTICO | -3,4 a +2,1 |

## EM

Escolas-ano de teste: 550; de alto risco: 110 (prevalência média 0,200).

| Nota | Bloco | PR-AUC [IC 95%] | Recall@20% [IC 95%] | ROC-AUC | Precisão (0,5) | Recall (0,5) | F1 (0,5) |
|---|---|---|---|---|---|---|---|
| B1R_lag | — | 0,335 [0,266; 0,432] | 0,275 [0,209; 0,370] | 0,613 | — | — | — |
| B2 | — | 0,235 [0,192; 0,284] | 0,209 [0,164; 0,253] | 0,565 | — | — | — |
| Regressão logística | 1 | 0,329 [0,261; 0,436] | 0,274 [0,200; 0,362] | 0,609 | 0,267 | 0,374 | 0,311 |
| Random Forest | 1 | 0,312 [0,244; 0,417] | 0,264 [0,191; 0,355] | 0,608 | 0,258 | 0,318 | 0,284 |
| HistGradientBoosting | 1 | 0,329 [0,260; 0,433] | 0,328 [0,248; 0,417] | 0,622 | 0,286 | 0,391 | 0,330 |
| Regressão logística | 2 | 0,359 [0,294; 0,465] | 0,337 [0,250; 0,419] | 0,670 | 0,307 | 0,495 | 0,377 |
| Random Forest | 2 | 0,344 [0,274; 0,454] | 0,318 [0,242; 0,407] | 0,656 | 0,328 | 0,426 | 0,366 |
| HistGradientBoosting | 2 | 0,355 [0,287; 0,466] | 0,355 [0,259; 0,420] | 0,632 | 0,300 | 0,453 | 0,359 |
| Regressão logística | 3 | 0,357 [0,289; 0,463] | 0,337 [0,254; 0,429] | 0,659 | 0,298 | 0,504 | 0,374 |
| Random Forest | 3 | 0,321 [0,261; 0,432] | 0,290 [0,210; 0,380] | 0,644 | 0,286 | 0,527 | 0,370 |
| HistGradientBoosting | 3 | 0,332 [0,271; 0,434] | 0,317 [0,244; 0,408] | 0,634 | 0,288 | 0,451 | 0,350 |
| acaso | — | 0,200 [0,160; 0,242] | 0,200 [0,197; 0,201] | 0,500 | — | — | — |

### EM: modelo − B1R_lag (família F6, Holm em 36 testes)

| Modelo | Bloco | Métrica | Diferença [IC 95%] | p Holm | Leitura | IC em escolas por ano |
|---|---|---|---|---|---|---|
| Regressão logística | 1 | PR_AUC | -0,007 [-0,042; +0,034] | 1,000 | INCONCLUSIVO | — |
| Regressão logística | 1 | Rec@20pct | -0,001 [-0,080; +0,051] | 1,000 | SEM GANHO PRÁTICO | -2,2 a +1,4 |
| Random Forest | 1 | PR_AUC | -0,024 [-0,055; +0,013] | 1,000 | INCONCLUSIVO | — |
| Random Forest | 1 | Rec@20pct | -0,011 [-0,096; +0,050] | 1,000 | SEM GANHO PRÁTICO | -2,6 a +1,4 |
| HistGradientBoosting | 1 | PR_AUC | -0,006 [-0,061; +0,053] | 1,000 | INCONCLUSIVO | — |
| HistGradientBoosting | 1 | Rec@20pct | +0,053 [-0,042; +0,123] | 1,000 | INCONCLUSIVO | -1,1 a +3,4 |
| Regressão logística | 2 | PR_AUC | +0,024 [-0,017; +0,075] | 1,000 | INCONCLUSIVO | — |
| Regressão logística | 2 | Rec@20pct | +0,062 [-0,037; +0,121] | 1,000 | INCONCLUSIVO | -1,0 a +3,3 |
| Random Forest | 2 | PR_AUC | +0,009 [-0,030; +0,057] | 1,000 | INCONCLUSIVO | — |
| Random Forest | 2 | Rec@20pct | +0,043 [-0,037; +0,105] | 1,000 | INCONCLUSIVO | -1,0 a +2,9 |
| HistGradientBoosting | 2 | PR_AUC | +0,020 [-0,039; +0,090] | 1,000 | INCONCLUSIVO | — |
| HistGradientBoosting | 2 | Rec@20pct | +0,080 [-0,033; +0,130] | 1,000 | INCONCLUSIVO | -0,9 a +3,6 |
| Regressão logística | 3 | PR_AUC | +0,021 [-0,027; +0,073] | 1,000 | INCONCLUSIVO | — |
| Regressão logística | 3 | Rec@20pct | +0,062 [-0,035; +0,135] | 1,000 | INCONCLUSIVO | -0,9 a +3,7 |
| Random Forest | 3 | PR_AUC | -0,015 [-0,056; +0,048] | 1,000 | INCONCLUSIVO | — |
| Random Forest | 3 | Rec@20pct | +0,015 [-0,082; +0,087] | 1,000 | SEM GANHO PRÁTICO | -2,3 a +2,4 |
| HistGradientBoosting | 3 | PR_AUC | -0,003 [-0,056; +0,064] | 1,000 | INCONCLUSIVO | — |
| HistGradientBoosting | 3 | Rec@20pct | +0,042 [-0,058; +0,123] | 1,000 | INCONCLUSIVO | -1,6 a +3,4 |

## Contagem das leituras da F6

- AF, PR_AUC: INCONCLUSIVO 9
- AF, Rec@20pct: SEM GANHO PRÁTICO 9
- EM, PR_AUC: INCONCLUSIVO 9
- EM, Rec@20pct: INCONCLUSIVO 6; SEM GANHO PRÁTICO 3

## Acima do acaso (IC 95% de métrica − acaso acima de zero; sem Holm)

- AF, PR_AUC: modelos 9 de 9; B1R_lag sim; B2 sim
- AF, Rec@20pct: modelos 9 de 9; B1R_lag sim; B2 sim
- EM, PR_AUC: modelos 9 de 9; B1R_lag sim; B2 sim
- EM, Rec@20pct: modelos 8 de 9; B1R_lag sim; B2 não

## Sensibilidade: alvo com limiar absoluto (abandono ≥ 10), estimativa pontual

| Etapa | Nota | Bloco | Prevalência | PR-AUC | Recall@20% | ROC-AUC |
|---|---|---|---|---|---|---|
| AF | B1R_lag | — | 0,163 | 0,351 | 0,440 | 0,684 |
| AF | B2 | — | 0,163 | 0,200 | 0,245 | 0,602 |
| AF | Regressão logística | 1 | 0,163 | 0,358 | 0,427 | 0,704 |
| AF | Random Forest | 1 | 0,163 | 0,295 | 0,410 | 0,671 |
| AF | HistGradientBoosting | 1 | 0,163 | 0,293 | 0,390 | 0,639 |
| AF | Regressão logística | 2 | 0,163 | 0,363 | 0,446 | 0,721 |
| AF | Random Forest | 2 | 0,163 | 0,306 | 0,437 | 0,693 |
| AF | HistGradientBoosting | 2 | 0,163 | 0,295 | 0,368 | 0,643 |
| AF | Regressão logística | 3 | 0,163 | 0,362 | 0,443 | 0,729 |
| AF | Random Forest | 3 | 0,163 | 0,325 | 0,410 | 0,708 |
| AF | HistGradientBoosting | 3 | 0,163 | 0,313 | 0,377 | 0,680 |
| AF | acaso | — | 0,163 | 0,163 | 0,200 | 0,500 |
| EM | B1R_lag | — | 0,407 | 0,545 | 0,260 | 0,638 |
| EM | B2 | — | 0,407 | 0,435 | 0,195 | 0,540 |
| EM | Regressão logística | 1 | 0,407 | 0,536 | 0,263 | 0,636 |
| EM | Random Forest | 1 | 0,407 | 0,536 | 0,273 | 0,635 |
| EM | HistGradientBoosting | 1 | 0,407 | 0,543 | 0,260 | 0,630 |
| EM | Regressão logística | 2 | 0,407 | 0,540 | 0,285 | 0,658 |
| EM | Random Forest | 2 | 0,407 | 0,541 | 0,283 | 0,648 |
| EM | HistGradientBoosting | 2 | 0,407 | 0,542 | 0,264 | 0,636 |
| EM | Regressão logística | 3 | 0,407 | 0,542 | 0,277 | 0,654 |
| EM | Random Forest | 3 | 0,407 | 0,561 | 0,259 | 0,653 |
| EM | HistGradientBoosting | 3 | 0,407 | 0,546 | 0,287 | 0,645 |
| EM | acaso | — | 0,407 | 0,407 | 0,200 | 0,500 |
