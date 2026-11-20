# Estudo exploratório E (v0) — colunas brutas do Censo, por filtro mecânico

Implementação da **seção E do `docs/PROTOCOLO.md`** (escrita em 2026-11-20, antes de qualquer execução; decisão no
`docs/DECISOES.md`, 2026-11-20). Lê `dataset/escolas_rr_v0.2.0.csv`, o cache do Censo por meio do grupo
`src/estendida/grupos/censo_bruto_v0.py` (que **não** é ligado: o dataset não muda), as funções de `src/avaliacao/`
e as do estudo C (`experimentos/fatores_2013_2018/fatores.py`, reutilizadas por `importlib`). Escreve só em
`saida/`.

**É exploratório:** foi desenhado depois de conhecidos os resultados do estudo C e da classificação, e os anos de
desfecho da janela já foram vistos. As colunas entram brutas, sem a revisão coluna a coluna.

## Como rodar (uma única vez, depois do push do protocolo)

```
python experimentos/censo_bruto_v0/estudo_e.py
```

Travas (E.8 e seção D):

- com `saida/` existente, o script recusa: a execução é única;
- recusa se algum arquivo rastreado tiver conteúdo diferente do commit, se houver arquivo não rastreado no código
  que roda (`src/`, esta pasta, o estudo C) ou se o commit não estiver em nenhum branch remoto: o push é a data
  pública de que o protocolo veio antes do resultado. A conferência olha o conteúdo, não a data dos arquivos (a
  pasta é sincronizada pelo Google Drive);
- nenhuma linha com t fora de 2013–2018 entra em cálculo: o dataset tem t = 2024 (desfecho 2025), que fica
  fechado; o cache de 2025 nunca é lido;
- toda saída começa com `# commit=… branch=… dataset_sha256=… gerado=…`;
- ordem: filtro (confere a lista fechada) → controle negativo → equivalência com o estudo C → Parte 1 → Parte 2.
  Tudo é calculado em memória e gravado no fim; se parar, grava **só** o arquivo que levou à parada.

As saídas entram no git no pull request da execução, por decisão do Gustavo (seção D).

## Seção do protocolo → função → teste

| Protocolo | Função | Teste |
|---|---|---|
| E.2 filtro mecânico, lista fechada, blocos | `censo_bruto_v0.filtro_mecanico`, `COLUNAS`, `USADAS_INFRA`, `BLOCOS`, `FAIXAS_IDADE` | `test_censo_bruto_v0.py` (`test_filtro_na_ordem_das_regras`, `test_filtro_no_cache_real_devolve_exatamente_as_colunas`, `test_listas_iguais_as_do_protocolo`) |
| E.2 extração e junção ao dataset | `censo_bruto_v0.extrair`, `juntar_censo` | `test_contrato_do_03_grupos`, `test_traco_e_vazio_viram_ausente_nunca_zero`, `test_extrair_nunca_le_2025` |
| E.2 colunas constantes na etapa | `constantes` | `test_universo_identico_em_s0_s1_s2_e_s2r`, `test_execucao_completa…` |
| E.3 o que vale do estudo C | `F.universo_pronto`, `F.dobras_por_escola`, `F._pipeline_q1`, `F._metricas`, `F.cabecalho`, `F.gravar` | `test_s0_s1_reproduzem_o_codigo_do_estudo_c` |
| E.4 conjuntos S0, S1, S2, S2r e pipeline | `pipeline_p1`, `rodada_p1`, `prever_p1`, `tabela_r2` | `test_universo_identico…`, `test_imputador_ajustado_so_no_treino` |
| E.4 controle negativo | `embaralhar`, `controle_negativo` | `test_embaralhamento_igual_ao_da_c9`, `test_controle_negativo_reprovado_grava_so_o_02` |
| E.4 equivalência com o estudo C | `equivalencia` | `test_equivalencia_para_so_em_linear_e_ridge`, `test_equivalencia_reprovada_grava_so_o_03` |
| E.4 F8 (S2 − S1, Ridge), bootstrap pareado, vereditos | `dif_r2_bootstrap`, `f8`, `veredito_f8` | `test_diferenca_s2_menos_s1_pareada_no_bootstrap`, `test_f8_holm_so_na_ridge_af_em`, `test_veredito_f8_na_ordem_do_protocolo` |
| E.5 universo, divisão, conjuntos A, A+, B, B+ e réguas | `universo_p2`, `dividir_p2`, `numericas_p2`, `pipeline_p2`, `prever_p2` | `test_previsoes_de_teste_da_parte2_sem_linhas_de_teste`, `test_numericas_dos_conjuntos_da_parte2` |
| E.5 Recall@20%, métricas com IC, F9 e F10 | `metricas_p2`, `testes_p2` | `test_familias_f9_f10_com_holm_e_leitura`, `test_execucao_completa…` |
| E.6 permutação por coluna e por bloco | `permutar`, `alvos_permutacao`, `permutacao` | `test_permutacao_em_bloco_mesmo_sorteio_e_ausente_acompanha` |
| E.8 ordem, paradas, gravação e relatório | `executar`, `relatorio`, `main`, `estado_git` | `test_filtro_diferente_da_lista_para`, `test_execucao_completa_grava_tudo_com_cabecalho_e_relatorio`, `test_main_recusa_saida_existente`, `test_main_recusa_sem_push_ou_com_arvore_suja`, `test_nenhuma_linha_fora_da_janela` |
| valores fixados (sementes, reamostragens, margens, anos) | constantes do topo de `estudo_e.py` | `test_valores_fixados_iguais_aos_do_protocolo` |

Os testes estão em `testes/test_estudo_e.py` e `testes/test_censo_bruto_v0.py`. Todos usam **dados sintéticos** (o do
filtro também roda no cache real do Censo, que só tem preditores); nenhum número do desfecho real é calculado antes
da execução única.
