# Inventário das colunas do Censo Escolar — Roraima, 2007–2025

Gerado por `experimentos/selecao_grupos/01_inventario_colunas.py`. Todos os números deste arquivo vêm do código. Serve para escolher **grupos de colunas** novos (`src/estendida/grupos/README.md`).

## Regras para quem for escolher (pessoa ou IA)

- Escolher por **pertinência** (o que a literatura e o problema dizem), **cobertura** (anos coletados, preenchimento em RR), **estabilidade** (mesmo significado entre anos; veja `notas_inep`) e **redundância** entre colunas. É **proibido** escolher pela relação com o abandono (`CLAUDE.md`, regra 7); este inventário não contém o desfecho de propósito.
- **Existir no layout não é ser coletada.** O INEP mantém colunas sem a pergunta (vazias ou só zeros). Use `anos_coletada_br` e a matriz (`C`), não só `anos_layout`.
- Os estudos usam a **janela 2013–2018** (`coletada_toda_janela_2013_2018`); colunas que só existem a partir de 2019 não servem para ela.
- Em **2025** o INEP dividiu os microdados em tabelas: `curso_tecnico`, `docente`, `escola`, `gestor_escolar`, `matricula`, `turma`. Contagens por escola (`QT_MAT_*`, `QT_TUR_*`, `QT_DOC_*`) saíram da tabela de escolas e estão nas outras; a coluna aparece com o mesmo nome, em outra tabela (campo `tabelas`).
- Ausente estrutural nunca vira 0 (regra 8); `'--'` e texto vazio do INEP são ausentes.
- Não invente nomes de coluna (regra 11): todo nome está em `colunas.csv`.
- Colunas de identificação e localização (`CO_*`, `NO_*`, `SG_*`, `NU_ANO_CENSO`) são chaves e rótulos, não preditores.

## Os arquivos

| Arquivo | Uma linha por | Para quê |
|---|---|---|
| `colunas.csv` | coluna | a tabela principal para escolher |
| `presenca_por_ano.csv` | coluna | ver de relance em que anos cada coluna existe e foi coletada |
| `por_ano.csv` | ano × tabela × coluna | o detalhe que gera as duas acima |
| `dicionario_inep.csv` | versão do dicionário × tabela × coluna | o texto do INEP, sem resumo |

### `colunas.csv`

| Campo | Significado |
|---|---|
| `coluna` | nome da variável no microdado do INEP |
| `prefixo` | início do nome: `IN` indicador 0/1, `QT` contagem, `TP` código de categoria, `CO` código, `NO` nome, `NU` número, `DT` data, `TX` texto |
| `tabelas` | tabela(s) do cache em que aparece (`escola` é a principal; 2023–2025 têm outras) |
| `n_anos_layout`, `anos_layout` | anos em que a coluna está no arquivo do INEP (faixas, ex.: `2007-2014 2019`) |
| `n_anos_coletada_br`, `anos_coletada_br` | anos em que alguma escola do Brasil tem valor (> 0 se numérica, não vazio se texto) |
| `coletada_todos_2007_2024` | 1 se coletada em todos os anos de 2007 a 2024 |
| `coletada_toda_janela_2013_2018` | 1 se coletada em todos os anos da janela dos estudos |
| `coletada_2025` | 1 se coletada em 2025 |
| `pct_preenchido_ativas_medio`, `_min` | % das escolas de RR **em atividade** com valor não vazio, nos anos coletados (média e mínimo). Escolas paralisadas ou extintas ficam de fora: de 2022 em diante o INEP as deixa em branco |
| `tipo_valor_rr` | `binario` (0/1), `contagem_ou_codigo` (inteiros), `decimal`, `texto` ou `vazio`, pelos valores de RR |
| `n_distintos_rr_max` | maior número de valores distintos em RR num ano |
| `descricao`, `tipo_inep`, `categorias` | do dicionário do INEP (versão mais nova que cita a coluna); `categorias` no formato `código=rótulo` |
| `anos_coleta_inep` | anos marcados com "s" (coletada) no dicionário do INEP |
| `notas_inep` | notas do INEP sobre mudanças entre anos (quando há) |
| `versao_dicionario` | de que versão do dicionário vieram a descrição e as marcas |

### `presenca_por_ano.csv`

Uma coluna por ano, 2007 a 2025. Código de cada célula: **`C`** = no layout e coletada no Brasil; **`L`** = no layout, mas vazia ou só zeros no Brasil (pergunta não feita); **vazio** = fora do layout.

### `por_ano.csv`

`n_brasil` (linhas do Brasil), `n_preenchido_br`, `n_numerico_br`, `n_um_br` (valor 1), `n_positivo_br` (> 0), `coletada_br` (0/1, a regra acima), `n_rr` (linhas de RR, todas as situações), `n_preenchido_rr`, `pct_preenchido_rr`, `n_rr_ativas` e `pct_preenchido_rr_ativas` (só escolas em atividade), `n_distintos_rr`, `tipo_valor_rr`.

## Contagens

- Colunas distintas (todas as tabelas, todos os anos): **1071**.
- No layout em todos os 19 anos: **282**.
- Coletadas em todos os anos de 2007 a 2024: **168**.
- Coletadas em toda a janela 2013–2018: **240**.
- Coletadas na janela e com pelo menos 90% das escolas de RR em atividade preenchidas (mínimo nos anos): **218**.
- Registros (ano × tabela × coluna) em que `coletada_br` discorda da marca "s" do dicionário do INEP: **26** (só colunas que o dicionário marca).
- Com descrição no dicionário do INEP: **1071**.
- Versões distintas do dicionário lidas: **5** (2007-2021, 2022, 2023, 2024, 2025).

Colunas por prefixo:

| prefixo | colunas | coletadas em toda a janela 2013–2018 |
|---|---|---|
| `QT` | 728 | 88 |
| `IN` | 282 | 112 |
| `CO` | 19 | 10 |
| `TP` | 17 | 12 |
| `NO` | 13 | 7 |
| `NU` | 6 | 6 |
| `DS` | 2 | 2 |
| `DT` | 2 | 2 |
| `ID` | 1 | 0 |
| `SG` | 1 | 1 |

Colunas por ano (no layout / coletadas no Brasil):

| ano | no layout | coletadas |
|---|---|---|
| 2007 | 370 | 192 |
| 2008 | 370 | 196 |
| 2009 | 370 | 203 |
| 2010 | 370 | 203 |
| 2011 | 370 | 207 |
| 2012 | 370 | 226 |
| 2013 | 370 | 240 |
| 2014 | 370 | 240 |
| 2015 | 370 | 247 |
| 2016 | 370 | 247 |
| 2017 | 370 | 247 |
| 2018 | 370 | 247 |
| 2019 | 370 | 328 |
| 2020 | 370 | 334 |
| 2021 | 370 | 334 |
| 2022 | 385 | 341 |
| 2023 | 424 | 424 |
| 2024 | 442 | 442 |
| 2025 | 967 | 967 |
