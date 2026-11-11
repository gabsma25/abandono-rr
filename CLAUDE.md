# CLAUDE.md — regras invioláveis do abandono-rr

Releia antes de qualquer commit. O mesmo conteúdo, em linguagem simples, está no `CONTRIBUTING.md`; o
contexto e as decisões estão no `README.md` e no `docs/DECISOES.md`.

1. **`dados/origem/` e `dados/cache/` são somente leitura.** Não renomeie, não mova, não normalize, não regrave.
   Arquivo novo só entra por `src/aquisicao.py`, conferido contra o sha256 do `dados/MANIFEST.csv`;
   divergência é erro.
2. **Nenhum dado bruto no git.** Só `dados/MANIFEST.csv`, `dados/cache/` e o dataset versionado em `dataset/`.
3. **Toda contagem ou estatística publicada é gerada por código.** Nada digitado em `docs/`, notebook ou
   dicionário.
4. **Notebook exibe, não calcula.** Células só leem, filtram, selecionam e reorganizam; o número vem pronto de um
   CSV gerado por `src/` ou por um experimento.
5. **Nada de vazamento temporal.** Preditores até o ano t → desfecho de t+1. Toda transformação (padronização,
   imputação, quantis, limiares) é ajustada só no treino.
6. **O alvo nunca entra em X.** Nunca as três taxas de rendimento (aprovação, reprovação, abandono) da mesma
   etapa e ano juntas: somam 100.
7. **Nunca selecione variável pela correlação com o desfecho.** Seleção por pertinência, cobertura, estabilidade
   e redundância entre preditores, decidida antes de rodar.
8. **Ausente estrutural nunca vira 0.** Escola sem a etapa sai do painel daquela etapa; `'--'` do INEP é ausente.
9. **Tipos:** `CO_ENTIDADE` e `CO_MUNICIPIO` como string; indicadores `Int8`; taxas `Float64` nullable. Todo
   `merge` com `validate=` explícito e `how="left"` a partir da tabela base.
10. **Protocolo antes de rodar, execução única.** O desenho de cada avaliação fica em `docs/PROTOCOLO.md` e no
    `docs/DECISOES.md` antes da execução. Anos de teste já usados (2016–2019, 2021–2024) não escolhem nada.
11. **Não invente nomes de coluna nem códigos.** Verifique no arquivo ou no `dataset/DICIONARIO.md`; se não
    der para verificar, pergunte.
12. **`main` só por pull request revisado**; um branch por tarefa; `python rodar_tudo.py` verde antes do pull
    request; commits no padrão `tipo: Descrição no presente`, em português.
