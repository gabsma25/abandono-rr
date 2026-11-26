# Notebooks

No máximo 2 notebooks, e eles **só exibem**: leem o que `src/` ou um experimento gravou em `saida/` e mostram
tabelas e figuras. Nenhuma conta é feita numa célula (`CLAUDE.md`, regra 4).

**Exceção declarada:** o `05_apresentacao_censo.ipynb`, que apresenta o trabalho ao professor, **ajusta modelos**:
as células da exploração chamam o `apoio_apresentacao.py` (com testes em `testes/test_apoio_apresentacao.py`), e o
número não vem de um CSV gravado antes. Ele é **exploratório**: usa anos de teste já vistos, não tem protocolo de
execução única e não decide nada. O desfecho de 2025 fica fechado por uma trava no código. Registro:
`docs/DECISOES.md`, 2026-11-20, "Notebook de apresentação (exploratório)".
