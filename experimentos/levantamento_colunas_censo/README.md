# Levantamento das colunas do Censo Escolar, 2007–2025

**Quem:** Gustavo · **Branch:** `feat/levantamento-colunas-censo` · **Estado:** em andamento (resultado vai ao
grupo antes de qualquer coluna nova entrar no dataset)

## A pergunta

Que colunas os microdados do Censo Escolar oferecem em cada ano de 2007 a 2025, e em quais anos existem as
candidatas a características estruturais novas (escola indígena, localização diferenciada, matrículas, turmas e
docentes por etapa, turno noturno, tempo integral)? É o início das metas M1/M6 do `docs/ROTEIRO.md`.

## O que se espera e como se vai ler

- **Só cabeçalhos.** O script lê a primeira linha de cada CSV dentro dos zips de `dados/origem/censo/`. Não lê
  nenhum valor, nem o rendimento, nem o dataset: não olha o desfecho (regra 7).
- **"Existe no cabeçalho" não é "foi coletada".** O INEP mantém colunas no layout mesmo quando a pergunta não foi
  feita (regra de fonte do `src/estendida/03_censo_features.py`). Conferir se foi coletada (alguma escola do Brasil
  com valor 1, ou com contagem maior que 0) é um segundo passo, só para as candidatas que o grupo escolher.
- **Os padrões de nome** (`PADROES` em `levantar.py`) foram escritos por pertinência, antes de ver os cabeçalhos,
  só para achar as colunas no meio de centenas. A lista que entra no dataset é decisão do grupo, registrada no
  `docs/DECISOES.md`, sem olhar a relação com o abandono.
- **Tabela principal** de cada ano = o maior CSV do zip, a mesma regra do `03`. Em 2025 o INEP dividiu os
  microdados em tabelas (Escola, Matrícula, Turma, Docente, Gestor, Curso Técnico); as colunas das outras tabelas
  ficam em `saida/colunas_outras_2025.csv`, com a marca de quais também estão na tabela principal.

## Como rodar

Precisa dos zips em `dados/origem/censo/` (`python -m src.aquisicao --origem-local PASTA`). Leva poucos segundos.

```bash
python experimentos/levantamento_colunas_censo/levantar.py
```

## O que saiu

Tudo em `saida/`, que se regera com o comando acima. A pasta inteira é versionada (exceção no `.gitignore`),
porque só quem tem os zips consegue regerá-la (`docs/DECISOES.md`, 2026-11-18). As contagens estão no
`saida/resumo.txt`, geradas pelo script.

| Arquivo | Conteúdo |
|---|---|
| `arquivos.csv` | cada CSV de cada zip: tamanho, nº de colunas, separador, se é a tabela principal |
| `colunas_por_ano.csv` | matriz coluna × ano da tabela principal (1 = existe) |
| `candidatas.csv` | colunas que casam com os padrões, com o primeiro e o último ano e os anos que faltam no meio |
| `colunas_outras_2025.csv` | colunas das tabelas de 2025 que não são a principal |
| `resumo.txt` | contagens e as mudanças de layout de um ano para o outro |

Pontos para o grupo (conferir nos arquivos acima):

- As colunas de contagem por escola (`QT_MAT_*`, `QT_TUR_*`, `QT_DOC_*`) e o `IN_NOTURNO` estão na tabela de escolas
  de 2007 a 2024. Em 2025 saíram dela e estão nas tabelas de Matrícula, Turma e Docente, que também têm
  `CO_ENTIDADE`; usar 2025 exige ler essas tabelas.
- Várias colunas desagregadas (por série, por turno, transporte) só existem em 2023–2024: servem para descrever,
  não para a janela 2013–2018.
- O significado dos sufixos (por exemplo `_N`, `_D`, `_ND`, `_INT`) tem de ser conferido no dicionário de dados do
  INEP de cada ano antes de qualquer uso (regra 11); este levantamento só lista nomes.
