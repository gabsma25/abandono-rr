# Seleção de grupos de colunas

**Quem:** Gustavo · **Branch:** `feat/inventario-colunas` · **Estado:** em andamento (passo 1 de vários)

## A pergunta

Que colunas do Censo Escolar existem, foram coletadas e estão preenchidas em Roraima em cada ano de 2007 a 2025, e
como agrupá-las em **grupos de colunas** novos para o pipeline (`src/estendida/grupos/`)?

## Os passos

| Script | O que faz | Estado |
|---|---|---|
| `01_inventario_colunas.py` | inventário de todas as colunas, ano a ano: presença no layout, coleta no Brasil, preenchimento em RR, descrição do dicionário do INEP | feito |

Os próximos passos (proposta de grupos, conferência de cada grupo) entram aqui quando forem escritos.

## Como as saídas devem ser lidas

As saídas foram feitas para outra pessoa ou outra IA ler e **propor** os grupos. Comece pelo `saida/LEIA_ME.md`, que
explica cada arquivo e cada campo e traz as contagens geradas pelo script.

- **Sem desfecho.** O inventário lê só o cache completo do Censo e os dicionários do INEP. Não lê o rendimento, o
  dataset nem a base: ninguém escolhe coluna pela relação com o abandono (regra 7).
- **Existir não é ser coletada.** "Coletada" é ter valor no Brasil naquele ano (numérica > 0 ou texto preenchido),
  medido no cache. A marca "s" do dicionário do INEP vem ao lado, para conferência.
- **A escolha é do grupo.** A IA propõe; o grupo decide por pertinência, cobertura, estabilidade e redundância,
  registra no `docs/DECISOES.md` e, para um estudo, fixa no `docs/PROTOCOLO.md` antes de rodar (regras 7 e 10).

## Como rodar

Precisa do cache completo do Censo (`dados/cache/censo_completo/`, versionado) e, para o dicionário, dos zips em
`dados/origem/censo/` (`python -m src.aquisicao --origem-local PASTA`). Leva cerca de 1 minuto.

```bash
python experimentos/selecao_grupos/01_inventario_colunas.py
```

## O que saiu

Tudo em `saida/`. A pasta inteira é versionada (exceção no `.gitignore`): o dicionário só se regera com os zips, que
hoje só o Gustavo tem (`docs/DECISOES.md`, 2026-11-20).

| Arquivo | Conteúdo |
|---|---|
| `LEIA_ME.md` | o que é cada arquivo e campo, as regras para escolher, as contagens |
| `colunas.csv` | uma linha por coluna: descrição, tabelas, anos no layout, anos coletados, cobertura em RR |
| `presenca_por_ano.csv` | matriz coluna × ano: `C` coletada, `L` só no layout, vazio fora do layout |
| `por_ano.csv` | uma linha por ano × tabela × coluna, com as contagens |
| `dicionario_inep.csv` | as 5 versões do dicionário do INEP, unificadas |

O levantamento anterior (`experimentos/levantamento_colunas_censo/`) lia só os cabeçalhos dos zips; este inventário o
amplia com a coleta, o preenchimento e o dicionário, e lê o cache, não os zips.
