# Contrato dos arquivos `pares.csv` e `importancias.csv`

**Issue:** #15 (R0a) · **Responsável:** João · **Estado:** proposta, aguardando a aprovação do Gustavo e da Gabriela

Os dois arquivos ligam as partes do esqueleto de previsão do ano seguinte:

```text
dados.py (#17) ──► pares.csv ──► recortes.py (#16) + modelos.py (#18) ──► importancias.csv (#19) ──► redes.py (#20) ──► rankings (#21)
```

Quem grava um dos dois arquivos chama `validar_pares` ou `validar_importancias` de [`contrato.py`](contrato.py)
antes de gravar. Quem lê usa `ler_pares` ou `ler_importancias`, que fixam os tipos e validam. Se este texto e o
`contrato.py` divergirem, vale o código, e o texto é corrigido no mesmo pull request. O teste
`testes/test_previsao_t1_contrato.py` confere que os exemplos abaixo passam no validador.

**Formato de arquivo, nos dois:** CSV em UTF-8, separador vírgula, ponto decimal, cabeçalho na primeira linha,
célula vazia = ausente, fim de linha LF (`contrato.gravar`). A ordem das colunas não importa.

## `pares.csv`

**Uma linha por escola × ano t × etapa**: as variáveis explicativas da escola até o ano t e o abandono da etapa
no ano t+1. É o mesmo desenho do `dataset/escolas_rr_v0.2.0.csv`, e as colunas têm os mesmos nomes do
`dataset/DICIONARIO.md` (regra 11 do `CLAUDE.md`). AF e EM ficam no mesmo arquivo, separados pela coluna
`etapa`; cada modelo é ajustado numa etapa só.

**Chave:** `co_entidade` + `ano` + `etapa`, sem repetição.

| Coluna | Tipo | Regra |
|---|---|---|
| `co_entidade` | texto, 8 dígitos | código INEP da escola; nunca vazio; lido como texto (regra 9) |
| `ano` | inteiro | ano t das variáveis explicativas; nunca vazio |
| `ano_alvo` | inteiro | sempre `ano + 1` |
| `etapa` | texto | `AF` ou `EM` |
| `abandono_t1` | decimal, 0 a 100 | **alvo**: taxa de abandono da etapa em t+1; **nunca vazio** (par sem desfecho não entra) |
| `abandono_t` | decimal, 0 a 100 | abandono da etapa em t; é a régua de persistência (#18); pode ficar vazio |
| *demais colunas* | decimal, inteiro ou texto | **preditores**: toda coluna que não está acima é preditora |

**Preditores.**
- Têm o nome que a coluna tem no `dataset/DICIONARIO.md`. Uma coluna nova (#17, D1) entra no dicionário antes de
  entrar aqui.
- Número (taxa, proporção, 0/1) ou categoria em texto (`localizacao`, `dependencia`). A codificação das
  categorias, a imputação e a padronização ficam dentro do pipeline, ajustadas só no treino (regra 5). Por isso
  as colunas `_zano` não entram: elas são padronizadas com todas as escolas do ano.
- Ausente fica vazio, nunca 0 (regra 8). Uma coluna vazia em todas as linhas não entra.
- **Não entram como preditores:** nenhuma coluna terminada em `_t1` (inclusive `alto_risco_t1`), nenhuma `_zano`,
  nem `co_municipio`, `no_municipio` e `janela_segura`.
- **As três taxas do mesmo ano nunca entram juntas** (`aprovacao_t`, `reprovacao_t` e `abandono_t`; o mesmo para
  `_tm1`): somam 100 (regra 6).
- **Histórico de abandono:** `abandono_t`, `abandono_tm1`, `abandono_tm2` e `variacao_abandono_defasada`
  (`contrato.HISTORICO`). Os modelos "sem histórico" (#18) tiram essas colunas de X.

**Exemplo** (sintético, com o código de escola inventado):

```csv
co_entidade,ano,ano_alvo,etapa,abandono_t1,abandono_t,localizacao,dim_iib_prop,reprovacao_t,iep_internet
99000001,2015,2016,AF,4.2,5.1,Urbana,0.75,8.3,1
99000001,2016,2017,AF,3.9,4.2,Urbana,0.75,,1
99000001,2015,2016,EM,12.0,10.4,Urbana,0.75,14.9,1
99000002,2015,2016,AF,9.8,,Rural,0.25,11.0,0
```

## `importancias.csv`

**Uma linha por modelo × recorte × etapa × semente × variável**: a importância por permutação de uma variável
num modelo ajustado num recorte, medida na validação daquele recorte com uma semente de permutação (#19). As
sementes ficam em linhas separadas; quem lê agrega (média, desvio) como precisar.

**Chave:** `algoritmo` + `historico` + `recorte` + `etapa` + `semente` + `variavel`, sem repetição.

| Coluna | Tipo | Regra |
|---|---|---|
| `algoritmo` | texto | nome do modelo, em minúsculas: `ridge`, `random_forest`, ... |
| `historico` | 0/1 | 1 se o modelo usa o histórico de abandono; com 0, nenhuma variável do histórico aparece |
| `recorte` | texto | identificador do recorte de `recortes.py` (#16), por exemplo `expansiva_2016` |
| `ano_validacao` | inteiro | t_v: a validação usa os pares de `ano` = t_v (desfecho de t_v + 1); um só por recorte |
| `etapa` | texto | `AF` ou `EM` |
| `semente` | inteiro | semente da permutação |
| `variavel` | texto | nome de um preditor do `pares.csv` |
| `importancia` | decimal | ΔMAE = MAE com a variável permutada − MAE original, em pontos percentuais; pode ser negativa |
| `supera_persistencia` | 0/1 | 1 se o MAE de validação do modelo é menor que o da persistência no mesmo recorte e etapa; igual em todas as linhas do mesmo modelo × recorte × etapa |

**Completo por modelo.** Todas as sementes de um mesmo `algoritmo` × `historico` × `recorte` × `etapa` têm o
mesmo conjunto de variáveis: todas as que entraram em X daquele modelo, inclusive as de importância nula ou
negativa (regra 7: todas são reportadas). A normalização e o truncamento dos negativos são do `redes.py` (#20),
não deste arquivo.

**Exemplo:**

```csv
algoritmo,historico,recorte,ano_validacao,etapa,semente,variavel,importancia,supera_persistencia
ridge,1,expansiva_2016,2016,AF,0,abandono_t,1.52,1
ridge,1,expansiva_2016,2016,AF,0,dim_iib_prop,0.31,1
ridge,1,expansiva_2016,2016,AF,1,abandono_t,1.47,1
ridge,1,expansiva_2016,2016,AF,1,dim_iib_prop,0.28,1
ridge,0,expansiva_2016,2016,AF,0,dim_iib_prop,0.40,0
ridge,0,expansiva_2016,2016,AF,1,dim_iib_prop,0.37,0
```

## O gerador sintético

`python -m experimentos.previsao_t1.sintetico` grava os dois arquivos em `experimentos/previsao_t1/saida/sintetico/`
(fora do git, porque se regera). Não lê nenhum dado real.

- **`pares.csv`:** 120 escolas inventadas (códigos começando por 99, que não é UF), anos t de 2009 a 2023, AF e
  metade com EM. As variáveis "verdadeiras" e o efeito plantado de cada uma ficam em `sintetico.PLANTADAS`
  (`abandono_t`, `localizacao` Rural e `dim_iib_prop`). As de `sintetico.RUIDO` não têm relação com o desfecho,
  e duas delas têm 5% de vazios.
- **`importancias.csv`:** valores **falsos**, que não vêm de modelo nenhum, para quem lê o arquivo (#20, #21):
  as plantadas têm ΔMAE claramente maior que as de ruído, e cada algoritmo tem a sua escala.

O teste de sanidade da #21 (as plantadas no topo dos três rankings) pode usar `sintetico.PLANTADAS`.
