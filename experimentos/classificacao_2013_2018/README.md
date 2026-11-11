# Classificação de alto risco na janela 2013–2018 (projeto anterior)

**Estado:** encerrado. Executado **uma única vez**, em 2026-11-10, no projeto anterior
(Dados-do-Projeto `969fc64`, `gustavo/avaliacao/03_classificacao.py`), depois de o protocolo estar registrado
(`abandono-escolar/docs/DECISOES.md`, commit `878930f`, entrada "Protocolo da ferramenta de classificação de
alto risco").

## A pergunta

Uma ferramenta de classificação (regressão logística, Random Forest e HistGradientBoosting, com 3 blocos de
informação) ordena as escolas melhor que a régua (o abandono de t−1), na janela segura?

## O que tem aqui

| Arquivo | O que é |
|---|---|
| `03_classificacao.py` | o script da execução única (só os caminhos foram adaptados ao abandono-rr) |
| `03b_verificacao_classificacao.py` | a verificação de que o modelo foi treinado (reexecução, coeficientes, permutação) |
| `saida/` | as saídas **da execução de 2026-11-10**, copiadas do projeto anterior, não regeradas |

**Não rode `03_classificacao.py` de novo para obter resultado:** a regra do protocolo é uma execução só. O
teste `testes/08_validar_classificacao.py` confere as funções sem treinar, e `testes/test_equivalencia.py`
confere que as réguas regeradas no abandono-rr batem com as de `saida/03_classificacao.csv`.

## O que saiu

O resumo, com os números, está em `saida/03_classificacao.md`; o resultado entra no `docs/BASELINE.md`.
