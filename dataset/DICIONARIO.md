# Dicionário de dados — `escolas_rr.csv`

Gerado por `python -m src.dataset` a partir de `saida/base_atual.parquet` (não edite à mão).

**Uma linha por escola × ano (t) × etapa.** 7.550 linhas e 44 colunas; 353 escolas; anos t de 2007 a 2025. Entra a escola-ano que tem a taxa de abandono da etapa em t ou em t+1. Chave: `co_entidade` + `ano` + `etapa`. O nome da escola não é incluído.

**Papéis.** *Alvo*: o que se quer prever, sempre do ano t+1; nunca entra como variável explicativa. *Explicativa*: informação disponível sobre a escola até o ano t. *Identificação*: chave e descrição, não entram em modelo.

| Coluna | Papel | Significado | Unidade | Fonte | Anos t com valor |
|---|---|---|---|---|---|
| `co_entidade` | identificação | código INEP da escola (id) | código | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `ano` | identificação | ano t das variáveis explicativas | ano | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `ano_alvo` | identificação | ano t+1 dos alvos | ano | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2024 |
| `etapa` | identificação | AF = anos finais do ensino fundamental; EM = ensino médio | categoria | projeto | 2007–2025 |
| `co_municipio` | identificação | código IBGE do município | código | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `no_municipio` | identificação | nome do município | texto | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `janela_segura` | identificação | 1 se t está na janela segura (2013 a 2018); ver as faixas abaixo | 0/1 | projeto | 2007–2025 |
| `abandono_t1` | alvo | taxa de abandono da etapa no ano t+1 | % (0 a 100) | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2024 |
| `alto_risco_t1` | alvo | 1 se abandono_t1 está entre os 20% maiores da etapa no ano e é maior que zero (definição completa abaixo) | 0/1 | projeto | 2008–2024 |
| `localizacao` | explicativa | localização da escola (Urbana, Rural) | categoria | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `dependencia` | explicativa | rede (Estadual, Municipal, Federal, Privada) | categoria | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `rede_publica` | explicativa | 1 se a escola é pública (estadual, municipal ou federal) | 0/1 | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `aprovacao_t` | explicativa | taxa de aprovação da etapa em t | % (0 a 100) | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `reprovacao_t` | explicativa | taxa de reprovação da etapa em t | % (0 a 100) | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `abandono_t` | explicativa | taxa de abandono da etapa em t | % (0 a 100) | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2007–2025 |
| `abandono_tm1` | explicativa | taxa de abandono da etapa em t−1 (a régua B1R_lag) | % (0 a 100) | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2008–2025 |
| `reprovacao_tm1` | explicativa | taxa de reprovação da etapa em t−1 | % (0 a 100) | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2008–2025 |
| `abandono_tm2` | explicativa | taxa de abandono da etapa em t−2 | % (0 a 100) | INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend) | 2009–2025 |
| `variacao_abandono_defasada` | explicativa | abandono_tm1 − abandono_tm2 | pontos percentuais | projeto | 2009–2025 |
| `iib_agua_potavel` | explicativa | infraestrutura básica: agua potavel (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `iib_energia_rede` | explicativa | infraestrutura básica: energia rede (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `iib_coleta_lixo` | explicativa | infraestrutura básica: coleta lixo (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `iib_banheiro` | explicativa | infraestrutura básica: banheiro (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `ida_despensa` | explicativa | dependência administrativa: despensa (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2012–2025 |
| `ida_refeitorio` | explicativa | dependência administrativa: refeitorio (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2012–2025 |
| `ida_sala_diretoria` | explicativa | dependência administrativa: sala diretoria (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `ida_sala_professor` | explicativa | dependência administrativa: sala professor (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `ida_secretaria` | explicativa | dependência administrativa: secretaria (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2012–2025 |
| `idp_biblioteca` | explicativa | dependência pedagógica: biblioteca (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `idp_lab_informatica` | explicativa | dependência pedagógica: lab informatica (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `idp_patio_coberto` | explicativa | dependência pedagógica: patio coberto (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2012–2025 |
| `idp_patio_descoberto` | explicativa | dependência pedagógica: patio descoberto (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2012–2025 |
| `idp_quadra_esportes` | explicativa | dependência pedagógica: quadra esportes (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `iep_computador` | explicativa | equipamento pedagógico: computador (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `iep_impressora` | explicativa | equipamento pedagógico: impressora (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `iep_projetor` | explicativa | equipamento pedagógico: projetor (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `iep_internet` | explicativa | equipamento pedagógico: internet (1 = tem) | 0/1 | INEP, Censo Escolar (tabela de escolas) | 2007–2025 |
| `dim_iib_zano` | explicativa | dimensão de infraestrutura básica, padronizada dentro do ano | desvios-padrão | calculada pelo projeto (src/estendida/05_indices_infra.py) | 2007–2025 |
| `dim_ida_zano` | explicativa | dimensão de dependências administrativas, padronizada dentro do ano | desvios-padrão | calculada pelo projeto (src/estendida/05_indices_infra.py) | 2007–2025 |
| `dim_idp_zano` | explicativa | dimensão de dependências pedagógicas, padronizada dentro do ano | desvios-padrão | calculada pelo projeto (src/estendida/05_indices_infra.py) | 2007–2025 |
| `dim_iep_zano` | explicativa | dimensão de equipamentos pedagógicos, padronizada dentro do ano | desvios-padrão | calculada pelo projeto (src/estendida/05_indices_infra.py) | 2007–2025 |
| `iie_zano` | explicativa | índice de infraestrutura escolar (1ª componente principal das 4 dimensões, por ano) | desvios-padrão | calculada pelo projeto (src/estendida/05_indices_infra.py) | 2007–2025 |
| `infra_itens_completos` | explicativa | 1 se os 18 itens de infraestrutura estão preenchidos no ano | 0/1 | calculada pelo projeto (src/estendida/05_indices_infra.py) | 2007–2025 |
| `infra_fonte_artigo` | explicativa | 1 se todos os itens vieram das colunas do artigo de referência (Almeida & Mussato, 2023) | 0/1 | calculada pelo projeto (src/estendida/05_indices_infra.py) | 2007–2025 |

## Definição completa de `alto_risco_t1`

Para cada etapa e cada ano t+1:

1. **Universo:** escolas públicas (`rede_publica` = 1) com a taxa de abandono da etapa em t−1, t e t+1. Fora dele, `alto_risco_t1` fica vazio (não é 0).
2. **K** = arredondamento de 20% do número de escolas do universo naquele ano e etapa.
3. **Limiar** = o K-ésimo maior `abandono_t1` do universo.
4. `alto_risco_t1` = 1 se `abandono_t1` ≥ limiar **e** `abandono_t1` > 0; senão, 0. Empates no limiar entram todos, então a proporção de 1 pode passar um pouco de 20%.

É a regra da classificação de alto risco do projeto anterior (função `classificacao.rotular`), aplicada ao mesmo universo; na janela segura, o teste `testes/test_dataset.py` confere que os rótulos são idênticos. Linhas com rótulo: AF 3.750, EM 2.224.

## A janela segura e por que cada faixa de anos fica fora

| Anos t | Situação | Motivo |
|---|---|---|
| 2007–2010 | fora | o ensino fundamental passava de 8 para 9 anos (Lei 11.274/2006); as etapas não se comparam com as dos anos seguintes |
| 2011–2012 | fora | só entram como anos anteriores (t−1 e t−2) das primeiras transições da janela |
| 2013–2018 | **janela segura** | um único formato de dados e antes da pandemia; desfechos de 2014 a 2019 |
| 2019 | fora | o desfecho seria 2020, ano da pandemia |
| 2020–2021 | fora | pandemia: com as escolas fechadas, o abandono registrado despencou (ver saida/relatorios/desfecho_por_ano.csv) |
| 2022–2023 | fora | regime pós-pandemia; foram os anos de teste da Etapa 2 do projeto anterior |
| 2024–2025 | fora | começa o Pé-de-Meia no ensino médio; o desfecho de 2025 já foi usado em análises e testes de modelos |

Nenhum ano sai do dataset: `janela_segura` só marca os anos usados nas análises.

## Ressalva sobre a procedência

Os dados de 2007 a 2018 vêm do recorte de Roraima em `dados/cache/` (sha256 no `dados/MANIFEST.csv`). Eles foram conferidos contra a fonte do INEP uma vez, em 14/10/2026, na máquina do Gustavo (`docs/procedencia/relatorio_04_*.md`, §4), e não podem ser reverificados neste projeto, porque os zips originais desses anos não estão aqui. Os anos de 2019 a 2025 são conferidos célula a célula contra os zips originais em `dados/origem/` pelo teste 03 (`testes/03_validar_censo_pos04.py --completo`).
