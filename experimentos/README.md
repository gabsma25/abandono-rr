# Experimentos

Cada pasta aqui é uma ideia em teste, de uma pessoa ou do grupo, **sem mexer no núcleo** (`src/`, `dataset/`,
`testes/`). Copie `_modelo/` para começar:

```
experimentos/<nome-curto>/
  README.md     a pergunta, o que se espera, como rodar, o que saiu (modelo em _modelo/README.md)
  *.py          o código do experimento
  saida/        o que ele gera
```

Regras:

- **Lê, não altera.** Um experimento lê o dataset (`dataset/escolas_rr_v*.csv`) e usa funções de `src/`, mas
  nunca escreve fora da própria pasta.
- **Protocolo antes de rodar**, quando a ideia for virar resultado: a pergunta, os anos de treino e teste, os
  modelos e a regra de leitura vão no `README.md` do experimento (e, se for decisão do grupo, no
  `docs/PROTOCOLO.md` e no `docs/DECISOES.md`) antes da execução.
- **O que for adotado passa para `src/` por pull request**, com teste e revisão de outra pessoa. O experimento fica
  como registro de onde a ideia veio.
- Pode abrir pull request de um experimento ainda não adotado, para guardar o registro no `main`; o revisor só
  confere que ele não mexe fora da pasta.

| Pasta | O que é | Estado |
|---|---|---|
| [`classificacao_2013_2018/`](classificacao_2013_2018/) | ferramenta de alerta precoce do projeto anterior: classificação de alto risco na janela segura | encerrado; executado uma vez em 2026-11-10 |
