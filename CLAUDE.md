# CLAUDE.md — regras invioláveis do abandono-rr

Releia antes de qualquer commit. O mesmo conteúdo, com a mesma numeração, em linguagem simples, está no
`CONTRIBUTING.md`; o contexto e as decisões estão no `README.md` e no `docs/DECISOES.md`.

1. **`dados/origem/` e `dados/cache/` são somente leitura.** Não renomeie, não mova, não normalize, não regrave.
   Arquivo novo só entra por `src/aquisicao.py`, conferido contra o sha256 do `dados/MANIFEST.csv`;
   divergência é erro.
2. **Nenhum dado bruto no git.** Só `dados/MANIFEST.csv`, `dados/cache/` e o dataset versionado em `dataset/`.
3. **Toda contagem ou estatística publicada é gerada por código.** Nada digitado em `docs/`, notebook ou
   dicionário.
4. **Notebook exibe, não calcula.** Células só leem, filtram, selecionam e reorganizam; o número vem pronto de um
   CSV gerado por `src/` ou por um experimento.
5. **Nada de vazamento temporal.** Preditores até o ano t → desfecho de t+1. Toda transformação (padronização,
   imputação, quantis, limiares) é ajustada só no treino. Num estudo de associação no mesmo ano, nenhum preditor é
   posterior a t nem derivado do desfecho, e toda transformação é ajustada só na parte de treino de cada dobra.
6. **O alvo nunca entra em X.** Nunca as três taxas de rendimento (aprovação, reprovação, abandono) da mesma
   etapa e ano juntas: somam 100. Variáveis ligadas ao desfecho por identidade contábil nunca são preditoras do
   nível de abandono: no modelo do abandono da etapa no ano t, nenhuma das três taxas daquela etapa e ano entra em
   X. O TDI, quando voltar, entra declarado como parcialmente mecânico (acumula a reprovação e o abandono de anos
   anteriores) e nunca é lido como fator independente.
7. **Nunca escolha variável pela relação com o desfecho.** É proibido incluir, excluir, recodificar ou transformar
   uma variável olhando a correlação, o coeficiente, a importância ou qualquer outra relação dela com o desfecho.
   A seleção é por pertinência, cobertura, estabilidade e redundância entre preditores, e a lista é fixada no
   `docs/PROTOCOLO.md` antes de rodar. É permitido e esperado REPORTAR a relação de cada variável com o desfecho
   como resultado, desde que a lista tenha sido fixada antes e que todas sejam reportadas, inclusive as nulas;
   ordenar a apresentação dos resultados pelo efeito é permitido. Vale o mesmo para o R²: descrever quanto da
   variação é explicada é permitido e esperado; escolher modelo, variável ou limiar pelo R² continua proibido.
8. **Ausente estrutural nunca vira 0.** Escola sem a etapa sai do painel daquela etapa; `'--'` do INEP é ausente.
9. **Tipos:** `CO_ENTIDADE` e `CO_MUNICIPIO` como string; indicadores `Int8`; taxas `Float64` nullable. Todo
   `merge` com `validate=` explícito e `how="left"` a partir da tabela base.
10. **Protocolo antes de rodar, execução única, toda decisão registrada.** O desenho de cada avaliação fica em
    `docs/PROTOCOLO.md` e no `docs/DECISOES.md` antes da execução. Toda decisão de método ou de dados fica no
    `docs/DECISOES.md`: o que foi decidido, por quê e onde está a evidência. Os anos de DESFECHO já usados como
    teste, 2016–2019 e 2021–2024 (em ano t: 2015–2018 e 2020–2023), não escolhem nada. Resultado nulo é relatado
    como qualquer outro.
11. **Não invente nomes de coluna nem códigos.** Verifique no arquivo ou no `dataset/DICIONARIO.md`; se não
    der para verificar, pergunte.
12. **`main` só por pull request revisado**; um branch por tarefa; `python rodar_tudo.py` verde antes do pull
    request; commits no padrão `tipo: Descrição no presente`, em português.
