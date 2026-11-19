# Estudo de fatores associados ao nível de abandono (t = 2013–2018)

Implementação da **seção C do `docs/PROTOCOLO.md`**. Lê só `dataset/escolas_rr_v0.2.0.csv` e as funções
de `src/`; escreve só em `saida/`, que é versionada. **Executado uma única vez em 2026-11-15**, no commit
`2deb135` do branch `integracao/gabriela`, antes da aprovação formal do PR #9 (desvio registrado no
`docs/DECISOES.md`, 2026-11-15). As saídas estão em `saida/`, com o commit no cabeçalho de cada arquivo.

## Como rodar (uma única vez; já rodou)

```
python experimentos/fatores_2013_2018/fatores.py --executar
```

Travas (regra 10 e C.13):

- sem `--executar`, nada é calculado;
- com `saida/` existente, o script recusa: a execução é única, e uma nova exigiria decisão registrada
  no `docs/DECISOES.md`;
- com a árvore do git suja (arquivo modificado ou não rastreado), o script recusa: o commit gravado tem de
  ser o código que rodou;
- toda saída começa com `# commit=… branch=… dataset_sha256=… gerado=…` (a figura leva o mesmo texto);
- a pasta `saida/` deste experimento entra no git (exceção no `.gitignore`), então a recusa vale em
  qualquer clone depois que as saídas forem versionadas;
- ordem: tabela 0 → controle negativo (C.9) → se passar, o resto; se o controle reprovar, grava **só**
  o `07_controle_negativo.csv` e para.

O plano era executar só depois que o código entrasse no `main` por pull request revisado **e** de uma revisão
independente do código contra o protocolo, por outro integrante. A execução de 2026-11-15 veio antes disso; o
desvio e a consequência (o protocolo fica congelado) estão no `docs/DECISOES.md`.

## Seção do protocolo → função → teste

| Protocolo | Função em `fatores.py` | Teste em `testes/test_fatores.py` |
|---|---|---|
| C.2 universo e janela | `c2_universo` | `test_recupera_efeitos…` (universo), `test_valores_fixados…` (janela) |
| C.3 lista fechada e referências | constantes `CATEGORICAS`, `DIMENSOES`, `INDICE`, `CONTROLE` | `test_lista_de_preditores_igual_ao_protocolo` |
| C.3 regra dos 30 e das 10 escolas | `c3_regra_dos_30` | `test_regra_dos_30_exclui_categoria_rara_com_contagem`, `test_categoria_com_escolas_ano_suficientes_e_poucas_escolas_sai`, `test_etapa_so_com_a_rede_estadual_roda_sem_fator_de_rede` |
| C.4 modelos e matriz | `matriz_x`, `_ols` | `test_recupera_efeitos…`, `test_reamostragem_sem_a_categoria…` |
| C.4 VIF | `c4_vif` | coberto por `test_executar_ordem_cabecalho_e_saidas` (03_vif.csv) |
| C.5 efeitos relatados | `c5_efeitos`, `_escala_decide` | `test_recupera_efeitos…` (escala pp × decide) |
| C.6 bootstrap por escola, Holm, margem, vereditos | `c6_inferencia`, `c6_veredito`, `_sorteios_escolas`, `_coef_reamostra` | `test_recupera_efeitos…`, `test_vereditos_na_ordem_do_protocolo`, `test_reamostragem_sem_a_categoria…` |
| C.7 Q1 (ΔR² sobre o modelo só com o ano) | `c7_q1`, `_pipeline_q1`, `dobras_por_escola` | `test_sem_efeito_alem_do_ano`, `test_vazamento_plantado_e_denunciado`, `test_groupkfold…`, `test_c7_e_c8…` |
| C.8 importância por permutação | `c8_permutacao` | `test_c7_e_c8_rodam_com_o_mlp_em_miniatura` |
| C.9 controle negativo | `c9_controle_negativo` | `test_sem_efeito_alem_do_ano`, `test_controle_negativo_reprovado_grava_so_o_07` |
| C.10 robustez | `c10_media_por_escola`, `c10_janela_2012_2019` | `test_robustez_usa_as_categorias_da_tabela_0`, `test_executar_ordem_cabecalho_e_saidas` |
| C.13 tabela 0, itens, correlação, saídas e figura | `c13_tabela0`, `c13_itens`, `c13_correlacao`, `executar`, `gravar`, `cabecalho`, `fig_forest` | `test_executar_ordem_cabecalho_e_saidas`, `test_controle_negativo_reprovado_grava_so_o_07` |
| travas da execução única | `main`, `estado_git`, `executar` | `test_sem_executar_nada_roda`, `test_executar_recusa_saida_existente`, `test_executar_recusa_arvore_suja` |
| C.5 figura principal | `fig_forest` | `test_forest_cada_painel_com_os_seus_fatores` |
| valores fixados (sementes, reamostragens, margem, limiares) | constantes do topo | `test_valores_fixados_iguais_aos_do_protocolo` |

Todos os testes usam **dados sintéticos com efeitos conhecidos**; nenhum número do desfecho real é
calculado antes da execução única.
