# Estudo exploratório E (v0) — colunas brutas do Censo

Gerado por `experimentos/censo_bruto_v0/estudo_e.py` a partir dos CSVs desta pasta (commit=b5c21a9e63e3965c6b77a81fce146af88462fdf8 branch=estudo/e-censo-bruto-v0 dataset_sha256=0dbdec151fea0d9a84c9b0bd5aa71e371b4ef93060019992882576706ecdf5f9 gerado=2026-11-20). Protocolo: `docs/PROTOCOLO.md`, seção E.

## Ressalvas (E.8 e E.9)

- **É exploratório** (E, abertura): o estudo foi desenhado depois de conhecidos os resultados do estudo C e da classificação (seção A).
- **Anos já vistos:** os desfechos 2016–2019 já foram olhados como teste, e os outros anos da janela também, no estudo C. O teste da Parte 2 (desfechos 2018–2019) é de anos já vistos.
- **Colunas brutas:** as 124 colunas saíram de um filtro mecânico que só olha preditores (E.2), sem a revisão coluna a coluna. Problemas conhecidos ficam dentro delas (E.7). Nenhuma coluna nova recebe coeficiente, veredito de fator nem frase de efeito; a tabela de fatores continua sendo a do estudo C.
- **As seis faixas de idade das matrículas são parcialmente mecânicas** (regra 6): acumulam a reprovação e o abandono de anos anteriores. A robustez S2r mostra o resultado sem elas.
- **Desvio declarado da regra B.6:** o protocolo foi para o branch por commit e push antes da execução, sem pull request revisado antes; a revisão vem no pull request da execução (docs/DECISOES.md, 2026-11-20).
- **Responde (E.9):** se as colunas brutas que passam no filtro aumentam o quanto se explica da diferença de abandono entre escolas (E1) e se melhoram a lista de risco do ano seguinte contra a régua e contra a B2 (E2), na versão 0, antes da limpeza.
- **Não responde (E.9):** o peso de cada coluna; causa; nada sobre 2025 (fechado para o teste limpo); se os dados limpos dariam outro resultado. A importância por permutação é descrição e roteiro da limpeza: nenhuma coluna entra, sai ou recebe veredito por ela (regra 7).

## Filtro mecânico (00)

| motivo | colunas |
|---|---|
| preenchimento | 154 |
| PASSA | 124 |
| informacao | 94 |
| tipo | 53 |
| escala | 27 |
| ja_usada | 22 |

## Universo (01)

| chave | parte1 AF | parte1 EM | parte2 AF | parte2 EM |
|---|---|---|---|---|
| colunas_constantes_retiradas | 4 | 16 | 4 | 16 |
| colunas_novas_no_modelo | 120 | 108 | 120 | 108 |
| escolas | 258 | 145 | 248 | 148 |
| escolas_ano | 1402 | 789 | 1347 | 789 |
| teste_escolas_ano |  |  | 455 | 288 |
| treino_escolas_ano |  |  | 892 | 501 |

## Controle negativo (02)

| etapa | conjunto | modelo | n_sementes | r2_cv_embaralhado | delta_r2_cv_embaralhado | limiar | passou |
|---|---|---|---|---|---|---|---|
| AF | S1 | linear | 1 | -0.0085 | -0.0063 | 0.0200 | True |
| AF | S1 | ridge | 1 | -0.0084 | -0.0062 | 0.0200 | True |
| AF | S1 | mlp | 10 | -0.0228 | -0.0081 | 0.0200 | True |
| AF | S2 | linear | 1 | -0.1642 | -0.1620 | 0.0200 | True |
| AF | S2 | ridge | 1 | -0.1568 | -0.1547 | 0.0200 | True |
| AF | S2 | mlp | 10 | -0.2998 | -0.2852 | 0.0200 | True |
| EM | S1 | linear | 1 | -0.0088 | -0.0110 | 0.0200 | True |
| EM | S1 | ridge | 1 | -0.0087 | -0.0110 | 0.0200 | True |
| EM | S1 | mlp | 10 | -0.0265 | -0.0003 | 0.0200 | True |
| EM | S2 | linear | 1 | -0.2732 | -0.2754 | 0.0200 | True |
| EM | S2 | ridge | 1 | -0.2607 | -0.2630 | 0.0200 | True |
| EM | S2 | mlp | 10 | -0.2475 | -0.2212 | 0.0200 | True |

## Equivalência com o estudo C (03)

| etapa | modelo | conjunto | metrica | estudo_e | estudo_c | diferenca_abs | tolerancia | decide | passou |
|---|---|---|---|---|---|---|---|---|---|
| AF | linear | S0 | r2_cv | 0.00160812 | 0.00160812 | 0.00000000 | 0.00000100 | True | True |
| AF | linear | S1 | r2_cv | 0.01313670 | 0.01313670 | 0.00000000 | 0.00000100 | True | True |
| AF | linear | S1 | delta_r2_cv | 0.01152858 | 0.01152858 | 0.00000000 | 0.00000100 | True | True |
| AF | ridge | S0 | r2_cv | 0.00163254 | 0.00163254 | 0.00000000 | 0.00000100 | True | True |
| AF | ridge | S1 | r2_cv | 0.01322929 | 0.01322929 | 0.00000000 | 0.00000100 | True | True |
| AF | ridge | S1 | delta_r2_cv | 0.01159675 | 0.01159675 | 0.00000000 | 0.00000100 | True | True |
| AF | mlp | S0 | r2_cv | -0.01474877 | -0.01474877 | 0.00000000 | 0.00000100 | False |  |
| AF | mlp | S1 | r2_cv | -0.00106148 | -0.00106148 | 0.00000000 | 0.00000100 | False |  |
| AF | mlp | S1 | delta_r2_cv | 0.01368729 | 0.01368729 | 0.00000000 | 0.00000100 | False |  |
| EM | linear | S0 | r2_cv | -0.00651718 | -0.00651718 | 0.00000000 | 0.00000100 | True | True |
| EM | linear | S1 | r2_cv | -0.01838831 | -0.01838831 | 0.00000000 | 0.00000100 | True | True |
| EM | linear | S1 | delta_r2_cv | -0.01187113 | -0.01187113 | 0.00000000 | 0.00000100 | True | True |
| EM | ridge | S0 | r2_cv | -0.00637814 | -0.00637814 | 0.00000000 | 0.00000100 | True | True |
| EM | ridge | S1 | r2_cv | -0.01803694 | -0.01803694 | 0.00000000 | 0.00000100 | True | True |
| EM | ridge | S1 | delta_r2_cv | -0.01165880 | -0.01165880 | 0.00000000 | 0.00000100 | True | True |
| EM | mlp | S0 | r2_cv | -0.02923229 | -0.02923229 | 0.00000000 | 0.00000100 | False |  |
| EM | mlp | S1 | r2_cv | -0.04032243 | -0.04032243 | 0.00000000 | 0.00000100 | False |  |
| EM | mlp | S1 | delta_r2_cv | -0.01109013 | -0.01109013 | 0.00000000 | 0.00000100 | False |  |

## Parte 1 — E1: quanto se explica (04)

| etapa | conjunto | modelo | n_colunas_novas | r2_dentro | r2_cv | r2_cv_dp | delta_r2_cv | mae_cv | rmse_cv |
|---|---|---|---|---|---|---|---|---|---|
| AF | S0 | linear | 0 | 0.0096 | 0.0016 |  |  | 4.6670 | 7.3255 |
| AF | S1 | linear | 0 | 0.0377 | 0.0131 |  | 0.0115 | 4.6033 | 7.2831 |
| AF | S2 | linear | 120 | 0.1967 | -0.0990 |  | -0.1006 | 4.8875 | 7.6856 |
| AF | S2r | linear | 114 | 0.1607 | -0.1164 |  | -0.1180 | 4.9491 | 7.7463 |
| AF | S0 | mlp | 0 | -0.0059 | -0.0147 | 0.0145 |  | 4.7042 | 7.3851 |
| AF | S1 | mlp | 0 | 0.0340 | -0.0011 | 0.0129 | 0.0137 | 4.6836 | 7.3351 |
| AF | S2 | mlp | 120 | 0.1585 | -0.2711 | 0.1716 | -0.2564 | 5.1293 | 8.2503 |
| AF | S2r | mlp | 114 | 0.1479 | -0.1977 | 0.0673 | -0.1829 | 5.0750 | 8.0205 |
| AF | S0 | ridge | 0 | 0.0096 | 0.0016 |  |  | 4.6668 | 7.3254 |
| AF | S1 | ridge | 0 | 0.0377 | 0.0132 |  | 0.0116 | 4.6030 | 7.2827 |
| AF | S2 | ridge | 120 | 0.1962 | -0.0880 |  | -0.0896 | 4.8494 | 7.6471 |
| AF | S2r | ridge | 114 | 0.1606 | -0.1104 |  | -0.1121 | 4.9274 | 7.7256 |
| EM | S0 | linear | 0 | 0.0126 | -0.0065 |  |  | 6.1892 | 8.0828 |
| EM | S1 | linear | 0 | 0.0362 | -0.0184 |  | -0.0119 | 6.2715 | 8.1303 |
| EM | S2 | linear | 108 | 0.2394 | -0.2070 |  | -0.2005 | 6.9047 | 8.8512 |
| EM | S2r | linear | 102 | 0.2055 | -0.2445 |  | -0.2379 | 6.9837 | 8.9875 |
| EM | S0 | mlp | 0 | 0.0014 | -0.0292 | 0.0161 |  | 6.2738 | 8.1733 |
| EM | S1 | mlp | 0 | 0.0118 | -0.0403 | 0.0264 | -0.0111 | 6.3300 | 8.2168 |
| EM | S2 | mlp | 108 | 0.1972 | -0.2345 | 0.0498 | -0.2053 | 6.9140 | 8.9500 |
| EM | S2r | mlp | 102 | 0.1817 | -0.2548 | 0.0438 | -0.2256 | 7.0076 | 9.0236 |
| EM | S0 | ridge | 0 | 0.0126 | -0.0064 |  |  | 6.1885 | 8.0822 |
| EM | S1 | ridge | 0 | 0.0362 | -0.0180 |  | -0.0117 | 6.2698 | 8.1289 |
| EM | S2 | ridge | 108 | 0.2389 | -0.1863 |  | -0.1799 | 6.8280 | 8.7750 |
| EM | S2r | ridge | 102 | 0.2054 | -0.2285 |  | -0.2221 | 6.9290 | 8.9297 |

## Parte 1 — E1: S2 − S1 (05; a F8 é a Ridge)

| etapa | modelo | familia | diferenca | ic_lo | ic_hi | p | p_holm | veredito |
|---|---|---|---|---|---|---|---|---|
| AF | linear | descritiva | -0.1121 | -0.2536 | -0.0232 | 0.0128 |  |  |
| AF | ridge | F8 | -0.1012 | -0.2339 | -0.0164 | 0.0192 | 0.0192 | NÃO ACRESCENTA |
| AF | mlp | descritiva | -0.2701 | -0.6346 | -0.0877 | 0.0004 |  |  |
| EM | linear | descritiva | -0.1886 | -0.2855 | -0.1088 | 0.0004 |  |  |
| EM | ridge | F8 | -0.1683 | -0.2580 | -0.0921 | 0.0004 | 0.0008 | NÃO ACRESCENTA |
| EM | mlp | descritiva | -0.1942 | -0.2815 | -0.1209 | 0.0004 |  |  |

## Parte 2 — E2: métricas no teste (07)

| etapa | conjunto | modelo | metrica | valor | ic_lo | ic_hi |
|---|---|---|---|---|---|---|
| AF | régua | B1R_lag | Rec@20pct | 0.4122 | 0.3303 | 0.5142 |
| AF | régua | B1R_lag | Rec@20pct_t=2017 | 0.4222 |  |  |
| AF | régua | B1R_lag | Rec@20pct_t=2018 | 0.4022 |  |  |
| AF | régua | B2 | Rec@20pct | 0.2501 | 0.2184 | 0.2838 |
| AF | régua | B2 | Rec@20pct_t=2017 | 0.2558 |  |  |
| AF | régua | B2 | Rec@20pct_t=2018 | 0.2444 |  |  |
| AF | régua | B2 | mae | 4.3195 | 3.7482 | 4.9780 |
| AF | régua | B2 | rmse | 7.5424 | 5.3245 | 10.1593 |
| AF | régua | B2 | r2 | 0.0064 | -0.0288 | 0.0431 |
| AF | A | ridge | Rec@20pct | 0.4510 | 0.3616 | 0.5414 |
| AF | A | ridge | Rec@20pct_t=2017 | 0.4889 |  |  |
| AF | A | ridge | Rec@20pct_t=2018 | 0.4130 |  |  |
| AF | A | ridge | mae | 4.1391 | 3.5973 | 4.7663 |
| AF | A | ridge | rmse | 7.2143 | 5.0034 | 9.8974 |
| AF | A | ridge | r2 | 0.0909 | 0.0175 | 0.2103 |
| AF | A | mlp | Rec@20pct | 0.4002 | 0.3342 | 0.4738 |
| AF | A | mlp | Rec@20pct_t=2017 | 0.4222 |  |  |
| AF | A | mlp | Rec@20pct_t=2018 | 0.3783 |  |  |
| AF | A | mlp | mae | 4.2749 | 3.7499 | 4.8832 |
| AF | A | mlp | rmse | 7.2786 | 5.1065 | 9.9221 |
| AF | A | mlp | r2 | 0.0746 | 0.0142 | 0.1718 |
| AF | A+ | ridge | Rec@20pct | 0.3957 | 0.3007 | 0.4739 |
| AF | A+ | ridge | Rec@20pct_t=2017 | 0.4000 |  |  |
| AF | A+ | ridge | Rec@20pct_t=2018 | 0.3913 |  |  |
| AF | A+ | ridge | mae | 4.4593 | 3.9228 | 5.0655 |
| AF | A+ | ridge | rmse | 7.4160 | 5.3304 | 10.0116 |
| AF | A+ | ridge | r2 | 0.0394 | -0.0489 | 0.1369 |
| AF | A+ | mlp | Rec@20pct | 0.3528 | 0.2958 | 0.4118 |
| AF | A+ | mlp | Rec@20pct_t=2017 | 0.3556 |  |  |
| AF | A+ | mlp | Rec@20pct_t=2018 | 0.3500 |  |  |
| AF | A+ | mlp | mae | 5.1272 | 4.5859 | 5.7271 |
| AF | A+ | mlp | rmse | 8.2385 | 6.2003 | 10.6963 |
| AF | A+ | mlp | r2 | -0.1883 | -0.5038 | -0.0592 |
| AF | B | ridge | Rec@20pct | 0.3510 | 0.2452 | 0.4163 |
| AF | B | ridge | Rec@20pct_t=2017 | 0.2889 |  |  |
| AF | B | ridge | Rec@20pct_t=2018 | 0.4130 |  |  |
| AF | B | ridge | mae | 4.5676 | 4.0239 | 5.1949 |
| AF | B | ridge | rmse | 7.4457 | 5.2621 | 10.0591 |
| AF | B | ridge | r2 | 0.0317 | 0.0047 | 0.0724 |
| AF | B | mlp | Rec@20pct | 0.2862 | 0.2418 | 0.3324 |
| AF | B | mlp | Rec@20pct_t=2017 | 0.2800 |  |  |
| AF | B | mlp | Rec@20pct_t=2018 | 0.2924 |  |  |
| AF | B | mlp | mae | 4.5809 | 4.0405 | 5.2103 |
| AF | B | mlp | rmse | 7.5418 | 5.3611 | 10.1505 |
| AF | B | mlp | r2 | 0.0065 | -0.0153 | 0.0321 |
| AF | B+ | ridge | Rec@20pct | 0.3406 | 0.2511 | 0.4249 |
| AF | B+ | ridge | Rec@20pct_t=2017 | 0.3333 |  |  |
| AF | B+ | ridge | Rec@20pct_t=2018 | 0.3478 |  |  |
| AF | B+ | ridge | mae | 4.6286 | 4.0949 | 5.2538 |
| AF | B+ | ridge | rmse | 7.5113 | 5.4856 | 10.0355 |
| AF | B+ | ridge | r2 | 0.0145 | -0.0989 | 0.0947 |
| AF | B+ | mlp | Rec@20pct | 0.2899 | 0.2394 | 0.3389 |
| AF | B+ | mlp | Rec@20pct_t=2017 | 0.2667 |  |  |
| AF | B+ | mlp | Rec@20pct_t=2018 | 0.3130 |  |  |
| AF | B+ | mlp | mae | 5.1310 | 4.5962 | 5.7559 |
| AF | B+ | mlp | rmse | 8.2986 | 6.2016 | 10.8610 |
| AF | B+ | mlp | r2 | -0.2064 | -0.5233 | -0.0848 |
| EM | régua | B1R_lag | Rec@20pct | 0.2291 | 0.1481 | 0.3616 |
| EM | régua | B1R_lag | Rec@20pct_t=2017 | 0.2857 |  |  |
| EM | régua | B1R_lag | Rec@20pct_t=2018 | 0.1724 |  |  |
| EM | régua | B2 | Rec@20pct | 0.2790 | 0.2504 | 0.3169 |
| EM | régua | B2 | Rec@20pct_t=2017 | 0.2796 |  |  |
| EM | régua | B2 | Rec@20pct_t=2018 | 0.2784 |  |  |
| EM | régua | B2 | mae | 7.1372 | 6.3473 | 7.9706 |
| EM | régua | B2 | rmse | 9.6741 | 8.5374 | 10.7850 |
| EM | régua | B2 | r2 | 0.0013 | -0.0622 | 0.0443 |
| EM | A | ridge | Rec@20pct | 0.3337 | 0.2269 | 0.4457 |
| EM | A | ridge | Rec@20pct_t=2017 | 0.3571 |  |  |
| EM | A | ridge | Rec@20pct_t=2018 | 0.3103 |  |  |
| EM | A | ridge | mae | 6.9466 | 6.1924 | 7.7732 |
| EM | A | ridge | rmse | 9.4443 | 8.4035 | 10.5141 |
| EM | A | ridge | r2 | 0.0482 | -0.0279 | 0.1110 |
| EM | A | mlp | Rec@20pct | 0.3141 | 0.2286 | 0.3970 |
| EM | A | mlp | Rec@20pct_t=2017 | 0.3179 |  |  |
| EM | A | mlp | Rec@20pct_t=2018 | 0.3103 |  |  |
| EM | A | mlp | mae | 7.1027 | 6.3603 | 7.9126 |
| EM | A | mlp | rmse | 9.6141 | 8.5893 | 10.6567 |
| EM | A | mlp | r2 | 0.0130 | -0.0568 | 0.0691 |
| EM | A+ | ridge | Rec@20pct | 0.2635 | 0.1667 | 0.3821 |
| EM | A+ | ridge | Rec@20pct_t=2017 | 0.2857 |  |  |
| EM | A+ | ridge | Rec@20pct_t=2018 | 0.2414 |  |  |
| EM | A+ | ridge | mae | 7.6937 | 6.8357 | 8.6343 |
| EM | A+ | ridge | rmse | 10.4626 | 9.2132 | 11.6731 |
| EM | A+ | ridge | r2 | -0.1681 | -0.3175 | -0.0447 |
| EM | A+ | mlp | Rec@20pct | 0.3058 | 0.2216 | 0.3912 |
| EM | A+ | mlp | Rec@20pct_t=2017 | 0.3357 |  |  |
| EM | A+ | mlp | Rec@20pct_t=2018 | 0.2759 |  |  |
| EM | A+ | mlp | mae | 7.7058 | 6.9091 | 8.5812 |
| EM | A+ | mlp | rmse | 10.3615 | 9.2261 | 11.4745 |
| EM | A+ | mlp | r2 | -0.1475 | -0.2565 | -0.0589 |
| EM | B | ridge | Rec@20pct | 0.2814 | 0.1808 | 0.4040 |
| EM | B | ridge | Rec@20pct_t=2017 | 0.3214 |  |  |
| EM | B | ridge | Rec@20pct_t=2018 | 0.2414 |  |  |
| EM | B | ridge | mae | 7.1691 | 6.4096 | 7.9694 |
| EM | B | ridge | rmse | 9.5311 | 8.4661 | 10.5889 |
| EM | B | ridge | r2 | 0.0306 | -0.0181 | 0.0656 |
| EM | B | mlp | Rec@20pct | 0.2777 | 0.2197 | 0.3507 |
| EM | B | mlp | Rec@20pct_t=2017 | 0.2829 |  |  |
| EM | B | mlp | Rec@20pct_t=2018 | 0.2726 |  |  |
| EM | B | mlp | mae | 7.3035 | 6.5789 | 8.0750 |
| EM | B | mlp | rmse | 9.5568 | 8.5398 | 10.5762 |
| EM | B | mlp | r2 | 0.0252 | -0.0165 | 0.0559 |
| EM | B+ | ridge | Rec@20pct | 0.2980 | 0.1801 | 0.4152 |
| EM | B+ | ridge | Rec@20pct_t=2017 | 0.2857 |  |  |
| EM | B+ | ridge | Rec@20pct_t=2018 | 0.3103 |  |  |
| EM | B+ | ridge | mae | 7.6011 | 6.7469 | 8.5203 |
| EM | B+ | ridge | rmse | 10.2972 | 9.0792 | 11.4715 |
| EM | B+ | ridge | r2 | -0.1315 | -0.2676 | -0.0167 |
| EM | B+ | mlp | Rec@20pct | 0.3056 | 0.2225 | 0.3980 |
| EM | B+ | mlp | Rec@20pct_t=2017 | 0.3250 |  |  |
| EM | B+ | mlp | Rec@20pct_t=2018 | 0.2862 |  |  |
| EM | B+ | mlp | mae | 7.6013 | 6.8008 | 8.4672 |
| EM | B+ | mlp | rmse | 10.1991 | 9.0333 | 11.3608 |
| EM | B+ | mlp | r2 | -0.1105 | -0.2174 | -0.0230 |

## Parte 2 — E2: F9, F10 e diferenças descritivas (08)

| familia | etapa | comparacao | diferenca | ic_lo | ic_hi | p | p_holm | veredito |
|---|---|---|---|---|---|---|---|---|
| F9 | AF | ridge A+ − B1R_lag | -0.0165 | -0.1299 | 0.0638 | 0.5031 | 1.0000 | SEM GANHO PRÁTICO |
| F9 | AF | mlp A+ − B1R_lag | -0.0594 | -0.1479 | 0.0118 | 0.0956 | 0.3823 | SEM GANHO PRÁTICO |
| F9 | EM | ridge A+ − B1R_lag | 0.0345 | -0.1146 | 0.1545 | 0.8146 | 1.0000 | INCONCLUSIVO |
| F9 | EM | mlp A+ − B1R_lag | 0.0767 | -0.0564 | 0.1685 | 0.3351 | 1.0000 | INCONCLUSIVO |
| F10 | AF | ridge B+ − B2 | 0.0905 | -0.0067 | 0.1829 | 0.0668 | 0.2671 | INCONCLUSIVO |
| F10 | AF | mlp B+ − B2 | 0.0397 | -0.0207 | 0.0964 | 0.1952 | 0.5855 | SEM GANHO PRÁTICO |
| F10 | EM | ridge B+ − B2 | 0.0191 | -0.1042 | 0.1366 | 0.8254 | 1.0000 | INCONCLUSIVO |
| F10 | EM | mlp B+ − B2 | 0.0266 | -0.0622 | 0.1175 | 0.5435 | 1.0000 | INCONCLUSIVO |
| descritiva | AF | ridge A+ − ridge A | -0.0553 | -0.1576 | 0.0270 | 0.1704 |  |  |
| descritiva | AF | ridge B+ − ridge B | -0.0104 | -0.0885 | 0.1026 | 0.8638 |  |  |
| descritiva | AF | mlp A+ − mlp A | -0.0475 | -0.1003 | 0.0017 | 0.0568 |  |  |
| descritiva | AF | mlp B+ − mlp B | 0.0037 | -0.0525 | 0.0522 | 0.9654 |  |  |
| descritiva | AF | ridge A − mlp A | 0.0507 | 0.0057 | 0.0933 | 0.0220 |  |  |
| descritiva | AF | ridge A+ − mlp A+ | 0.0429 | -0.0275 | 0.0970 | 0.2915 |  |  |
| descritiva | AF | ridge B − mlp B | 0.0648 | -0.0241 | 0.1093 | 0.2164 |  |  |
| descritiva | AF | ridge B+ − mlp B+ | 0.0507 | -0.0176 | 0.1202 | 0.1504 |  |  |
| descritiva | EM | ridge A+ − ridge A | -0.0702 | -0.1976 | 0.0693 | 0.3775 |  |  |
| descritiva | EM | ridge B+ − ridge B | 0.0166 | -0.1423 | 0.1556 | 0.9558 |  |  |
| descritiva | EM | mlp A+ − mlp A | -0.0083 | -0.1031 | 0.0975 | 0.9386 |  |  |
| descritiva | EM | mlp B+ − mlp B | 0.0279 | -0.0791 | 0.1292 | 0.6463 |  |  |
| descritiva | EM | ridge A − mlp A | 0.0196 | -0.0221 | 0.0716 | 0.3523 |  |  |
| descritiva | EM | ridge A+ − mlp A+ | -0.0422 | -0.1089 | 0.0382 | 0.3539 |  |  |
| descritiva | EM | ridge B − mlp B | 0.0037 | -0.0721 | 0.0807 | 0.9506 |  |  |
| descritiva | EM | ridge B+ − mlp B+ | -0.0076 | -0.0942 | 0.0593 | 0.7379 |  |  |

## Importância por permutação (06; descrição, não decide nada)

### Blocos

| etapa | modelo | alvo | n_colunas | queda_r2 | ic_lo | ic_hi |
|---|---|---|---|---|---|---|
| AF | mlp | bloco:matriculas | 35 | 0.5212 | 0.0350 | 1.6853 |
| AF | mlp | bloco:oferta_turno | 14 | 0.2815 | 0.0115 | 1.1706 |
| AF | mlp | bloco:turmas_salas | 16 | 0.2689 | -0.0137 | 1.0560 |
| AF | mlp | bloco:docentes | 15 | 0.2529 | -0.4596 | 1.1366 |
| AF | mlp | bloco:predio_servicos | 29 | 0.0245 | -0.1495 | 0.3284 |
| AF | mlp | bloco:infraestrutura | 4 | 0.0189 | -0.0802 | 0.1975 |
| AF | mlp | bloco:ano | 1 | 0.0169 | -0.0219 | 0.0669 |
| AF | mlp | bloco:territorio | 1 | 0.0124 | -0.0243 | 0.0873 |
| AF | mlp | bloco:rede | 1 | 0.0045 | -0.0257 | 0.0430 |
| AF | mlp | bloco:equipamentos | 10 | 0.0041 | -0.1061 | 0.1602 |
| AF | mlp | bloco:escola_indigena | 1 | 0.0034 | -0.0493 | 0.0532 |
| AF | ridge | bloco:matriculas | 35 | 0.7365 | 0.0779 | 1.7981 |
| AF | ridge | bloco:docentes | 15 | 0.4522 | 0.0104 | 1.3378 |
| AF | ridge | bloco:oferta_turno | 14 | 0.3973 | 0.0843 | 1.1045 |
| AF | ridge | bloco:turmas_salas | 16 | 0.3528 | -0.0011 | 0.7702 |
| AF | ridge | bloco:ano | 1 | 0.0192 | -0.0250 | 0.0644 |
| AF | ridge | bloco:infraestrutura | 4 | 0.0159 | -0.0335 | 0.0739 |
| AF | ridge | bloco:territorio | 1 | 0.0146 | -0.0056 | 0.0689 |
| AF | ridge | bloco:predio_servicos | 29 | 0.0048 | -0.1494 | 0.1959 |
| AF | ridge | bloco:rede | 1 | 0.0039 | -0.0164 | 0.0285 |
| AF | ridge | bloco:escola_indigena | 1 | -0.0014 | -0.0207 | 0.0127 |
| AF | ridge | bloco:equipamentos | 10 | -0.0114 | -0.0300 | 0.0081 |
| EM | mlp | bloco:matriculas | 32 | 0.4143 | 0.0287 | 1.1360 |
| EM | mlp | bloco:docentes | 12 | 0.3048 | -0.0565 | 0.8618 |
| EM | mlp | bloco:turmas_salas | 13 | 0.2974 | -0.0184 | 0.8517 |
| EM | mlp | bloco:predio_servicos | 28 | 0.0740 | -0.1085 | 0.3128 |
| EM | mlp | bloco:equipamentos | 10 | 0.0602 | -0.0816 | 0.2658 |
| EM | mlp | bloco:oferta_turno | 12 | 0.0581 | -0.1040 | 0.3010 |
| EM | mlp | bloco:escola_indigena | 1 | 0.0243 | -0.0879 | 0.2382 |
| EM | mlp | bloco:ano | 1 | 0.0142 | -0.0486 | 0.0753 |
| EM | mlp | bloco:infraestrutura | 4 | 0.0086 | -0.0779 | 0.1173 |
| EM | mlp | bloco:territorio | 1 | 0.0079 | -0.0250 | 0.0717 |
| EM | mlp | bloco:rede | 1 | 0.0000 | 0.0000 | 0.0000 |
| EM | ridge | bloco:turmas_salas | 13 | 0.8293 | 0.2607 | 1.3220 |
| EM | ridge | bloco:docentes | 12 | 0.5565 | 0.2392 | 1.2970 |
| EM | ridge | bloco:matriculas | 32 | 0.3665 | 0.1615 | 0.6997 |
| EM | ridge | bloco:escola_indigena | 1 | 0.1089 | -0.0172 | 0.3629 |
| EM | ridge | bloco:oferta_turno | 12 | 0.0888 | -0.0870 | 0.2664 |
| EM | ridge | bloco:predio_servicos | 28 | 0.0765 | -0.0884 | 0.2279 |
| EM | ridge | bloco:equipamentos | 10 | 0.0413 | -0.0558 | 0.1779 |
| EM | ridge | bloco:ano | 1 | 0.0103 | -0.0445 | 0.0687 |
| EM | ridge | bloco:territorio | 1 | 0.0049 | -0.0193 | 0.0409 |
| EM | ridge | bloco:rede | 1 | 0.0000 | 0.0000 | 0.0000 |
| EM | ridge | bloco:infraestrutura | 4 | -0.0113 | -0.0908 | 0.0471 |

### As 15 colunas com maior queda de R², por etapa e modelo

| etapa | modelo | alvo | bloco | queda_r2 | ic_lo | ic_hi |
|---|---|---|---|---|---|---|
| AF | mlp | QT_DOC_PROF | docentes | 0.1106 | -0.0659 | 1.1060 |
| AF | mlp | QT_MAT_MED | matriculas | 0.1069 | -0.0454 | 0.8531 |
| AF | mlp | QT_MAT_BAS_15_17 | matriculas | 0.1025 | -0.0754 | 0.7308 |
| AF | mlp | QT_MAT_BAS_11_14 | matriculas | 0.0888 | -0.0503 | 0.5820 |
| AF | mlp | QT_TUR_BAS | turmas_salas | 0.0856 | -0.0304 | 0.6686 |
| AF | mlp | IN_COZINHA | predio_servicos | 0.0835 | -0.0118 | 0.3483 |
| AF | mlp | QT_DOC_FUND | docentes | 0.0809 | -0.0281 | 0.4667 |
| AF | mlp | QT_MAT_BAS | matriculas | 0.0752 | -0.0308 | 0.3951 |
| AF | mlp | QT_MAT_INF_PRE | matriculas | 0.0751 | -0.0143 | 0.5010 |
| AF | mlp | QT_MAT_ESP_CC | matriculas | 0.0715 | -0.0384 | 0.4359 |
| AF | mlp | QT_TUR_ESP_CC | turmas_salas | 0.0681 | -0.0428 | 0.4409 |
| AF | mlp | IN_PROF | oferta_turno | 0.0664 | -0.3557 | 1.1968 |
| AF | mlp | IN_INF_PRE | oferta_turno | 0.0650 | -0.0515 | 0.5181 |
| AF | mlp | QT_MAT_BAS_N | matriculas | 0.0620 | -0.0687 | 0.5869 |
| AF | mlp | IN_EJA | oferta_turno | 0.0590 | -0.0224 | 0.4453 |
| AF | ridge | QT_MAT_BAS_18_MAIS | matriculas | 3.4130 | 0.4906 | 8.1996 |
| AF | ridge | QT_MAT_MED | matriculas | 2.4957 | 0.2448 | 5.7050 |
| AF | ridge | QT_MAT_BAS_11_14 | matriculas | 2.0099 | 0.2195 | 3.8979 |
| AF | ridge | QT_MAT_BAS_15_17 | matriculas | 1.2272 | 0.3293 | 3.0364 |
| AF | ridge | QT_MAT_FUND | matriculas | 0.8145 | 0.1069 | 1.8124 |
| AF | ridge | QT_MAT_FUND_AF | matriculas | 0.6661 | 0.0616 | 1.7764 |
| AF | ridge | QT_MAT_EJA_MED | matriculas | 0.6575 | 0.0076 | 1.4504 |
| AF | ridge | QT_MAT_EJA | matriculas | 0.6057 | 0.0108 | 1.5497 |
| AF | ridge | QT_DOC_EJA_MED | docentes | 0.4076 | 0.0279 | 0.8285 |
| AF | ridge | QT_DOC_INF | docentes | 0.4023 | -0.0003 | 1.1271 |
| AF | ridge | QT_MAT_BAS_6_10 | matriculas | 0.3851 | 0.0613 | 1.0688 |
| AF | ridge | QT_MAT_BAS_FEM | matriculas | 0.3848 | -0.0038 | 1.4088 |
| AF | ridge | QT_DOC_INF_PRE | docentes | 0.3224 | -0.0375 | 0.7835 |
| AF | ridge | IN_ESGOTO_FOSSA | predio_servicos | 0.2356 | -0.0081 | 1.1654 |
| AF | ridge | IN_EJA_MED | oferta_turno | 0.2191 | 0.0112 | 0.4415 |
| EM | mlp | QT_MAT_BAS_18_MAIS | matriculas | 0.0801 | -0.0335 | 0.5170 |
| EM | mlp | QT_TUR_EJA | turmas_salas | 0.0753 | -0.0267 | 0.3640 |
| EM | mlp | QT_MAT_BAS | matriculas | 0.0723 | -0.0240 | 0.4868 |
| EM | mlp | QT_DOC_PROF_TEC | docentes | 0.0461 | -0.0178 | 0.2884 |
| EM | mlp | QT_MAT_PROF | matriculas | 0.0429 | -0.0208 | 0.3184 |
| EM | mlp | IN_COZINHA | predio_servicos | 0.0422 | -0.0244 | 0.2398 |
| EM | mlp | QT_MAT_FUND_AF | matriculas | 0.0420 | -0.0269 | 0.3238 |
| EM | mlp | QT_DOC_FUND_AF | docentes | 0.0412 | -0.0340 | 0.2657 |
| EM | mlp | QT_MAT_MED | matriculas | 0.0408 | -0.0374 | 0.2443 |
| EM | mlp | IN_PROF_TEC | oferta_turno | 0.0401 | -0.0199 | 0.2411 |
| EM | mlp | QT_TUR_MED | turmas_salas | 0.0400 | -0.0483 | 0.2131 |
| EM | mlp | QT_MAT_BAS_11_14 | matriculas | 0.0384 | -0.0493 | 0.1878 |
| EM | mlp | QT_TUR_FUND_AF | turmas_salas | 0.0377 | -0.0319 | 0.3202 |
| EM | mlp | QT_DOC_PROF | docentes | 0.0375 | -0.0208 | 0.3096 |
| EM | mlp | QT_DOC_BAS | docentes | 0.0357 | -0.0545 | 0.2437 |
| EM | ridge | QT_MAT_BAS_18_MAIS | matriculas | 1.9056 | 0.1049 | 3.2737 |
| EM | ridge | QT_MAT_BAS_11_14 | matriculas | 1.0040 | 0.1228 | 2.9566 |
| EM | ridge | QT_MAT_FUND_AI | matriculas | 0.6689 | 0.0225 | 1.6797 |
| EM | ridge | QT_MAT_BAS_6_10 | matriculas | 0.5722 | -0.0145 | 1.4571 |
| EM | ridge | QT_MAT_FUND | matriculas | 0.4706 | 0.0278 | 1.8673 |
| EM | ridge | QT_MAT_FUND_AF | matriculas | 0.3268 | -0.0062 | 1.5973 |
| EM | ridge | QT_MAT_EJA_MED | matriculas | 0.3053 | -0.0015 | 0.6270 |
| EM | ridge | QT_MAT_BAS_MASC | matriculas | 0.2326 | 0.0570 | 0.5505 |
| EM | ridge | QT_DOC_FUND | docentes | 0.2250 | -0.0213 | 1.1854 |
| EM | ridge | QT_MAT_EJA | matriculas | 0.2112 | -0.0078 | 0.5602 |
| EM | ridge | QT_MAT_MED | matriculas | 0.1856 | -0.0317 | 0.7200 |
| EM | ridge | QT_DOC_BAS | docentes | 0.1302 | 0.0029 | 0.3646 |
| EM | ridge | QT_DOC_EJA_FUND | docentes | 0.1269 | 0.0019 | 0.4506 |
| EM | ridge | QT_TUR_ESP_CC | turmas_salas | 0.1149 | -0.0019 | 0.2804 |
| EM | ridge | QT_TUR_ESP | turmas_salas | 0.1118 | -0.0133 | 0.2632 |
