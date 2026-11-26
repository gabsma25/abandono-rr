# Grupos de colunas

Cada arquivo desta pasta é um **grupo**: um conjunto de colunas que se acrescenta à base longitudinal (a saída do
`02`). A etapa `src/estendida/03_grupos.py` lê a base longitudinal e, para cada grupo listado em
[`ligados.txt`](ligados.txt), junta as colunas do grupo. A saída é `saida/base_atual.parquet`.

Grupos de hoje:

| Grupo | Colunas | Fonte |
|---|---|---|
| [`infraestrutura`](infraestrutura.py) | 18 itens do Almeida & Mussato (2023), `INFRA_FONTE_ARTIGO`; derivadas: 4 dimensões e o IIE padronizados no ano, `INFRA_ITENS_COMPLETOS` | `dados/cache/censo_completo/` |

## Contrato

Um grupo é um módulo `<nome>.py` com:

- `NOME`: igual ao nome do arquivo;
- `COLUNAS`: as colunas que `extrair` acrescenta, em ordem;
- `extrair(relatorios: Path) -> DataFrame`: uma linha por (`ANO`, `CO_ENTIDADE`), com exatamente
  `["ANO", "CO_ENTIDADE", *COLUNAS]`; pode gravar relatórios na pasta `relatorios`;
- opcionais: `DERIVADAS` e `derivar(tab, relatorios) -> DataFrame`. `derivar` recebe só `ANO` e as `COLUNAS` do
  próprio grupo, nas linhas da base, e devolve exatamente as `DERIVADAS`, no mesmo índice.

O `03_grupos.py` confere o contrato e para com erro se ele for quebrado.

## Regras

1. **Só acrescenta.** O grupo não tira linhas nem mexe em colunas de outro grupo, e nenhum nome de coluna pode se
   repetir. A junção é `how="left"` a partir da base, com `validate="1:1"` (regra 9).
2. **Não lê o rendimento.** `extrair` lê só o cache completo do Censo (`dados/cache/censo_completo/`); assim nenhuma
   coluna de grupo pode ser derivada do abandono (regras 6 e 7). Uma fonte fora do Censo entra declarada no próprio
   grupo, com sha256 no `dados/MANIFEST.csv`.
3. **Linha a linha.** Grupo novo calcula cada linha só com a própria escola e ano. Contas que usam outras escolas
   (z-score no ano, quantis) vazam informação entre treino e validação (regra 5) e ficam para o passo do modelo,
   ajustadas só no treino. O `_zano` do grupo infraestrutura é herança declarada (`docs/DECISOES.md`, 2026-11-19).
4. **A regra de "coletada" é do grupo.** O cache traz, por coluna, as contagens do Brasil
   (`{ano}_{tabela}_nacional.csv`: preenchidas, numéricas, iguais a 1, maiores que 0). "Alguma escola com valor 1"
   serve para indicadores 0/1; contagens e categorias precisam de outra regra, escrita no grupo.
5. **Ausente estrutural nunca vira 0** (regra 8); `'--'` e texto vazio do INEP são ausentes. O cache guarda o
   texto como o INEP publicou: converter é papel do grupo.
6. **Colunas por etapa.** Quando o Censo tem uma coluna para os anos finais e outra para o ensino médio, o grupo
   devolve as duas, com nomes que digam a etapa; quem divide por etapa é o `src/dataset.py`.
7. **Não invente nomes de coluna** (regra 11): verifique no cache ou em
   `experimentos/levantamento_colunas_censo/saida/`.

## Ligar um grupo

A lista em `ligados.txt` faz parte da versão do dataset. Ligar ou desligar um grupo é decisão registrada no
`docs/DECISOES.md`, por pull request; para um estudo, a lista é fixada no `docs/PROTOCOLO.md` antes de rodar. Nunca se
liga ou desliga um grupo olhando o resultado (regra 7).
