# Resultados do projeto anterior (cópias congeladas)

Saídas do projeto anterior citadas pelo `docs/BASELINE.md`. Não são regeradas no abandono-rr e não devem ser
editadas: o `testes/test_baseline.py` confere o sha256 de cada uma contra a tabela abaixo.

## Etapa 2

A Etapa 2 dependia da base oficial 2019–2025, que ficou fora (ver `docs/DECISOES.md`, 2026-11-11).

| Arquivo | Origem (Dados-do-Projeto `969fc64`) | sha256 |
|---|---|---|
| `02_walkforward.csv` | `gustavo/saida/avaliacao/02_walkforward.csv` (Recall@K por ano, réguas e modelos da Etapa 2) | `76c22b54fa84e45e22c38f83827942f2f9b0fcccc6b7668eae1ce79cd523129c` |
| `02d_testes.csv` | `gustavo/saida/avaliacao/02d_testes.csv` (famílias de testes com Holm) | `4d300d0064beddd1c7d04bfad1640fdd5b731f5923a5bc4c98434201b3eea45d` |

## Classificação de alto risco de 2026-11-10 (`classificacao/`)

As saídas da execução única, feita pelo script que está em `experimentos/classificacao_2013_2018/`. Elas foram copiadas
do commit de origem em 2026-11-14 e são idênticas às da pasta `experimentos/classificacao_2013_2018/saida/` de
quem as copiou antes; aquela pasta fica fora do git (`.gitignore`), esta não.

| Arquivo | Origem (Dados-do-Projeto `969fc64`) | sha256 |
|---|---|---|
| `classificacao/03_classificacao.csv` | `gustavo/saida/avaliacao/03_classificacao.csv` (métricas por etapa × modelo × bloco × período) | `7fbf05dd0724ed3808119077d6a2572e6f8aaff41d4abc2ca0a324bd68e8cc19` |
| `classificacao/03_classificacao.md` | `gustavo/saida/avaliacao/03_classificacao.md` (resumo da execução) | `f1d12371a7d634e851c9241996cb3a7fccb75d4c38db36ca75110d4e549a141b` |
| `classificacao/03_previsoes.csv` | `gustavo/saida/avaliacao/03_previsoes.csv` (uma linha por escola-ano de teste × modelo × bloco) | `1131e2edbfe7ee2da61ad66b06c9a36a5e6e5e05c0984014da826071bed02a88` |
| `classificacao/03_testes.csv` | `gustavo/saida/avaliacao/03_testes.csv` (famílias de testes, inclusive a F6, com Holm) | `e7e9992c5a1f77419ae8f587eb4079c0a397dfb67501dd123310ce50e8456f3d` |
| `classificacao/03b_controle_permutacao.csv` | `gustavo/saida/avaliacao/03b_controle_permutacao.csv` (verificação do treino) | `58223244cb65dd83e1cf3ff9210511cfecf65e6f1598aebcd1b29d2bdd00a65e` |
