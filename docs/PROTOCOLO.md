# Protocolo da Etapa 4 — regressão do abandono em t+1 com MLPRegressor

**Estado:** escrito **antes** de qualquer execução. Nenhum modelo da Etapa 4 foi treinado, nenhuma métrica foi
calculada e nenhum dado do teste foi olhado para escrever este texto. A execução é **única** (`CLAUDE.md`,
regra 10) e só acontece depois que este protocolo entrar no `main` por pull request revisado por outro integrante.

**Origem de cada parte** (detalhe no `docs/DECISOES.md`, entrada de 2026-11-11 "A Etapa 4 passa a ser regressão com
MLPRegressor"):

- **Orientação do professor:** seguir o máximo possível o exemplo "MLPRegressor - House Sales Prediction"
  (`docs/tese_base/MLPRegressorHouseSalesPrediction (6).ipynb`) e o livro de Silva, Spatti e Flauzino, cap. 5
  (Perceptron multicamadas).
- **Decisão da pesquisadora**, para que o exemplo caiba nas regras do projeto: todas as correções listadas na
  seção 11 (divisão temporal, padronização no `Pipeline`, alvo ÷ 100, seleção por redundância, configurações A e B,
  validação cruzada só descritiva, sensibilidade de topologia, 10 sementes, réguas e Ridge, métricas, IC e Holm).
  A ideia de validação cruzada para a topologia veio da leitura do livro (5.5.1) feita pela pesquisadora, **não**
  do professor.

---

## 1. As perguntas

Uma pergunta por configuração de variáveis, cada uma com a sua comparação obrigatória:

- **Configuração A:** a rede supera a régua (o abandono de t−1), usando a mesma informação que ela?
- **Configuração B:** sem nenhum histórico de rendimento, território, rede e infraestrutura identificam o risco?
  Comparação obrigatória **B × B2**, porque a B2 já é território × rede.

A régua, a B2 e a Ridge entram nas duas, na mesma tabela.

## 2. Dados e universo

- **Fonte:** `dataset/escolas_rr_v0.1.0.csv` (dicionário em `dataset/DICIONARIO.md`), lido como está, com
  `co_entidade` e `co_municipio` como string. Nenhuma coluna nova entra no dataset.
- **Unidade:** uma linha por escola × ano t × etapa; **cada etapa (AF e EM) é avaliada separadamente**, e cada etapa
  só vê as variáveis da própria etapa.
- **Universo de cada etapa e ano:** escolas públicas (`rede_publica` = 1) com a taxa de abandono da etapa em
  t−1, t e t+1 (`abandono_tm1`, `abandono_t` e `abandono_t1` não vazios). É o universo de `alto_risco_t1` e o da
  régua no `docs/BASELINE.md`, para que as comparações se refiram às mesmas escolas. O `abandono_t` serve **só** para
  delimitar o universo e nunca entra em X.
- **Ausente estrutural** (`CLAUDE.md`, regra 8): escola sem a etapa no ano não está no universo daquele ano e
  etapa. Nada vira 0.

## 3. Divisão temporal (fixa, decidida antes)

| Papel | Anos t (preditores) | Anos t+1 (desfecho `abandono_t1`) |
|---|---|---|
| treino | 2013, 2014, 2015, 2016 | 2014, 2015, 2016, 2017 |
| teste | 2017, 2018 | 2018, 2019 |

- Não há sorteio de linhas entre treino e teste: o `train_test_split` do exemplo sai (seção 11).
- **Anos já vistos.** Os desfechos de 2016 a 2019 foram o teste da classificação de alto risco do projeto anterior
  (2026-11-10, `experimentos/classificacao_2013_2018/`). Portanto o teste desta etapa (desfechos 2018 e 2019) **já
  foi visto**, e dois anos do treino (desfechos 2016 e 2017) também. Por isso, pela regra 10, **nenhuma escolha
  deste protocolo é feita por esses anos**: variáveis, topologia, hiperparâmetros, limiares e regra de leitura estão
  fixados neste texto. A validação cruzada da seção 6.3 roda nesses anos, mas só é relatada e não escolhe nada.
- O resultado desta etapa é, então, uma **nova leitura de anos já usados**, com outra pergunta (o valor da taxa, e não
  o rótulo de alto risco). Não é uma avaliação em dados virgens, e o relatório tem que dizer isso.

## 4. Variáveis

### 4.1 O que fica fora antes de tudo (por pertinência, decidido agora)

Equivale à célula `df.drop([...])` do exemplo. Nenhuma exclusão usa o desfecho.

| Coluna(s) | Por que sai |
|---|---|
| `co_entidade`, `ano`, `ano_alvo`, `etapa`, `co_municipio`, `no_municipio`, `janela_segura` | identificação; não descrevem a escola (como `id` e `date` no exemplo) |
| `abandono_t1`, `alto_risco_t1` | são o alvo e o rótulo (`CLAUDE.md`, regra 6) |
| `aprovacao_t`, `reprovacao_t`, `abandono_t` | dado de t: ainda não publicado no começo de t+1, quando a lista é feita; nenhuma configuração usa dado de t |
| `abandono_tm2` | redundância exata: `abandono_tm1` − `variacao_abandono_defasada` = `abandono_tm2` |
| `rede_publica` | constante no universo (todas as escolas são públicas) |
| os 18 itens `iib_*`, `ida_*`, `idp_*`, `iep_*` | resumidos pelas quatro dimensões e pelo IIE, como na classificação de 2026-11-10 |
| `infra_itens_completos`, `infra_fonte_artigo` | marcadores de qualidade do dado, não características da escola |

### 4.2 As candidatas de cada configuração

A lista vem nesta ordem, que é também a **ordem de prioridade** usada na regra de redundância (4.3).

| Configuração | Variáveis candidatas |
|---|---|
| **A** (com o histórico de rendimento) | `abandono_tm1`, `reprovacao_tm1`, `variacao_abandono_defasada`, `localizacao`, `dependencia`, `dim_iib_zano`, `dim_ida_zano`, `dim_idp_zano`, `dim_iep_zano`, `iie_zano` |
| **B** (sem nenhuma variável de rendimento) | `localizacao`, `dependencia`, `dim_iib_zano`, `dim_ida_zano`, `dim_idp_zano`, `dim_iep_zano`, `iie_zano` |

- **A usa só t−1**: é a informação disponível no começo de t+1, quando a lista é feita, e é a mesma que a régua
  usa. É a mesma escolha do antigo Cenário B do projeto anterior.
- **A nova B não é a B antiga.** A B antiga tinha os lags de rendimento de t−1; esta não tem nenhuma taxa de
  rendimento, de nenhum ano.
- Nunca entram juntas as três taxas de rendimento da mesma etapa e ano (`CLAUDE.md`, regra 6): A só tem abandono e
  reprovação de t−1.
- As dimensões `*_zano` são padronizadas dentro de cada ano, com as escolas daquele ano
  (`src/estendida/05_indices_infra.py`). Isso usa só dados do próprio ano t, disponíveis em t; não usa o desfecho.

### 4.3 A regra de seleção: redundância entre preditores, só no treino

Equivale aos mapas de correlação do exemplo, mas a correlação é **entre preditores**, nunca com o desfecho
(`CLAUDE.md`, regra 7).

1. Para cada etapa e configuração, calcula-se a correlação de Pearson entre as candidatas numéricas (tudo menos
   `localizacao` e `dependencia`), **só nas linhas de treino**, com os pares completos de cada par.
2. Percorre-se a lista na ordem de prioridade da 4.2. Uma candidata sai se tiver |r| > **0,90** com alguma
   candidata anterior que ficou.
3. Entre duas candidatas redundantes, fica a anterior na lista. A ordem põe o rendimento primeiro e o `iie_zano`
   por último, porque ele é derivado das quatro dimensões.
4. `localizacao` e `dependencia` sempre ficam (são a B2; a pergunta da configuração B depende delas).
5. O desfecho (`abandono_t1`) **não entra** na matriz de correlação usada para decidir. O mapa exibido no notebook
   pode mostrá-lo à parte, marcado como "só exibição, não decide".

A lista final de cada etapa × configuração e o motivo de cada exclusão vão para
`saida/04_variaveis.csv` antes do ajuste de qualquer modelo. Os mesmos conjuntos valem para a rede (as três
topologias) e para a Ridge.

## 5. Pré-processamento (dentro do `Pipeline`, ajustado só no treino)

- **Numéricas:** `SimpleImputer(strategy="median", add_indicator=True)` e depois `StandardScaler()`, como na
  classificação de 2026-11-10. A imputação é necessária porque a infraestrutura tem vazios; o exemplo não tem.
- **Categóricas** (`localizacao`, `dependencia`): `OneHotEncoder(handle_unknown="ignore")`.
- **Tudo dentro de um `Pipeline`** (`ColumnTransformer` + modelo), ajustado com `fit` só nas linhas de treino e
  aplicado ao teste com `predict`. No exemplo, o `StandardScaler` era ajustado com o conjunto inteiro, antes da
  divisão: aqui não.
- **Alvo:** `abandono_t1 / 100`, pelo domínio conhecido da taxa (0 a 100). O exemplo dividia pelo máximo dos dados
  (`y.max()`), o que usa o teste. As previsões voltam para pontos percentuais (× 100) antes de qualquer métrica.
  As previsões **não são cortadas** em [0, 100] (o exemplo não corta); o relatório conta quantas ficaram fora.

## 6. Modelos

### 6.1 A rede (resultado principal)

`MLPRegressor` com os parâmetros do exemplo, sem nenhum ajuste:

```python
MLPRegressor(hidden_layer_sizes=(50,), activation="logistic", solver="adam",
             max_iter=5000, tol=1e-7, momentum=0.8, early_stopping=True, epsilon=1e-08,
             n_iter_no_change=10, random_state=semente)
```

- **A topologia de 50 neurônios segue o exemplo do professor**, e não uma validação. Ela é fixada aqui e é a única
  usada na leitura principal (seção 9).
- `momentum=0.8` fica como no exemplo, mas não tem efeito com `solver="adam"` (no scikit-learn, só vale para
  `solver="sgd"`).
- `early_stopping=True` separa, ao acaso, 10% das linhas **de treino** (`validation_fraction=0.1`, o padrão) para
  decidir quando parar. Só usa anos de treino; não é uma divisão temporal. Fica registrado como diferença conhecida.

### 6.2 Sensibilidade de topologia (decidida antes, não substitui o principal)

A mesma rede, com as mesmas variáveis, sementes e métricas, também com `hidden_layer_sizes=(10,)` e `(25,)`.
Os resultados são relatados **ao lado** do principal. **Nenhum deles substitui o resultado de 50 neurônios,
qualquer que seja o resultado.** Não entram nas famílias de Holm e não sustentam nenhuma frase de "supera".

### 6.3 Validação cruzada temporal no treino (livro, 5.5.1) — só descritiva

Dentro do treino, janela expansiva por ano do desfecho: treina até o desfecho de 2014 e valida no de 2015; treina até
2015 e valida em 2016; treina até 2016 e valida em 2017. Cada dobra roda com 10, 25 e 50 neurônios e as 10
sementes, e relata o MAE médio e o desvio. **Não escolhe nada**: a topologia principal já está fixada em 6.1, e os
desfechos de 2016 e 2017 são anos de teste já usados (regra 10).

### 6.4 Comparações obrigatórias (na mesma tabela)

| Nome | Previsão de `abandono_t1` | Ajuste |
|---|---|---|
| **régua** (B1R_lag) | `abandono_tm1` da própria escola | nenhum |
| **B2** | mediana de `abandono_t1` no treino por `localizacao` × `dependencia`; célula sem escola no treino recebe a mediana geral do treino (`src/avaliacao/baselines.b2_mediana_estrato`) | só treino |
| **Ridge** | `Ridge(alpha=1.0)`, com o mesmo `Pipeline`, as mesmas variáveis e o mesmo alvo ÷ 100 da rede, em cada configuração | só treino; `alpha` fixo, não ajustado |

## 7. Sementes (livro, 5.5.5)

- A rede é treinada com **10 sementes** fixas: `random_state` = 1, 2, …, 10. A semente controla a inicialização dos
  pesos e o sorteio interno do `early_stopping`.
- Para cada métrica, relata-se a **média e o desvio-padrão** (com `ddof=1`) nas 10 sementes.
- A estimativa pontual da rede é a **média das 10 sementes** de cada métrica. Não se faz média das previsões
  (seria outro modelo, um comitê).
- A régua, a B2 e a Ridge são determinísticas: uma execução, desvio não se aplica.

## 8. Métricas

Calculadas em pontos percentuais, por etapa e configuração:

- **MAE**: `sklearn.metrics.mean_absolute_error`;
- **RMSE**: `sklearn.metrics.root_mean_squared_error` (o argumento `squared=False` do exemplo foi removido no
  scikit-learn 1.8, a versão fixada no `requirements.txt`);
- **R²**: `sklearn.metrics.r2_score`;
- **Recall@20%** (complemento): em cada ano de teste, as escolas são ordenadas pela previsão; das que têm
  `alto_risco_t1` = 1, a fração que está entre os 20% do topo. Empates na fronteira pelo valor esperado
  (`src/avaliacao/metricas.prob_topk`, como na classificação). O valor relatado é a média simples dos dois anos.

MAE, RMSE e R² são calculados sobre todas as linhas de teste dos dois anos juntos; cada ano também é relatado
separadamente, como descrição.

**Não se usa o MAPE.** O abandono tem muitos zeros, e o erro percentual divide por eles. A curva de perda do
treinamento (`loss_curve_`) é guardada para cada semente, mas não é métrica de avaliação.

## 9. Intervalos, testes e a regra de leitura (escrita antes)

### 9.1 Intervalo de confiança

- **Bootstrap por escola** (cluster): sorteiam-se escolas (`co_entidade`) com reposição, mantendo os dois anos de
  teste de cada escola sorteada (`src/avaliacao/bootstrap.Agrupado`). **5.000 reamostragens**, semente fixa
  20261111.
- As **mesmas** reamostragens servem para todos os modelos e réguas da etapa: as diferenças são pareadas.
- Para a rede, em cada reamostragem calcula-se a métrica de cada uma das 10 sementes e tira-se a média. O
  intervalo é o da média das sementes.
- IC 95%: percentis 2,5 e 97,5. O p-valor de uma diferença é o bootstrap bilateral de `bootstrap.p_bootstrap`.

### 9.2 As famílias de teste e a correção de Holm

| Família | Diferença testada (MAE) | Testes |
|---|---|---|
| **F1** (decide a pergunta A, e também é lida para B) | rede de 50 neurônios − régua | 2 etapas × 2 configurações = 4 |
| **F2** (decide a pergunta B) | rede de 50 neurônios, configuração B − B2 | 2 etapas = 2 |

O Holm é aplicado dentro de cada família, com α = 0,05.

### 9.3 A regra de leitura

A rede **"supera a régua"** (F1) numa etapa e configuração **só se as duas coisas** acontecerem:

1. o limite superior do IC 95% da diferença de MAE (rede − régua) ficar **abaixo de zero**; e
2. o p ajustado por Holm na família F1 for ≤ 0,05.

Em qualquer outro caso, a frase é "não superou a régua". Se o limite inferior do IC ficar acima de zero, a
frase é "errou mais que a régua". A F2 se lê do mesmo jeito, com a B2 no lugar da régua.

Tudo o mais é **descritivo**, com IC e sem frase de "supera": a rede − Ridge, a Ridge − régua, a configuração A ×
B2, as diferenças em RMSE, R² e Recall@20%, a sensibilidade de topologia (6.2) e a validação cruzada (6.3).
Resultado nulo também é resultado, e é relatado do mesmo jeito.

## 10. O que a execução grava

Código em `experimentos/regressao_mlp_2013_2018/04_regressao_mlp.py`, que lê o dataset e as funções de `src/` e
não escreve fora da própria pasta. Saídas em `experimentos/regressao_mlp_2013_2018/saida/`:

| Arquivo | Conteúdo |
|---|---|
| `04_correlacao_treino.csv` | matriz de correlação das candidatas, só no treino, por etapa × configuração (forma longa) |
| `04_variaveis.csv` | cada candidata: fica ou sai, e o motivo (seção 4) |
| `04_previsoes.csv` | uma linha por escola × ano de teste × etapa × configuração × modelo × semente: desejado e estimado (pp) |
| `04_amostra_grafico.csv` | as 40 escolas-ano do gráfico desejado × estimado, sorteadas com semente fixa entre as de teste |
| `04_curva_perda.csv` | `loss_curve_` por etapa × configuração × topologia × semente, e a perda da régua no treino na mesma escala |
| `04_cv_temporal.csv` | a validação cruzada descritiva (6.3) |
| `04_metricas.csv` | MAE, RMSE, R² e Recall@20%: média, desvio nas sementes, IC 95%, por etapa × configuração × modelo |
| `04_testes.csv` | F1 e F2: diferença, IC, p, p Holm e a leitura da 9.3; e as diferenças descritivas |

**Pendência antes da execução.** O `.gitignore` ignora toda pasta `saida/`, inclusive a dos experimentos. Hoje as
saídas de `experimentos/classificacao_2013_2018/saida/`, citadas no `docs/BASELINE.md` e lidas pelo
`testes/test_equivalencia.py`, existem só na máquina de quem as copiou, e não no git. O pull request da execução
precisa abrir uma exceção para `experimentos/*/saida/`, ou o resultado desta etapa também não chega a quem clonar o
repositório.

## 11. O que mudou em relação ao exemplo, e por quê

| No exemplo | Aqui | Por quê | Livro |
|---|---|---|---|
| `train_test_split(test_size=0.30)` ao acaso | treino t = 2013–2016, teste t = 2017–2018 | prever o futuro com o passado; linhas da mesma escola em anos diferentes não podem cair dos dois lados (regra 5) | a conferir |
| `StandardScaler().fit(x)` no conjunto todo, antes da divisão | dentro do `Pipeline`, ajustado só no treino | o teste não pode influenciar a padronização (regra 5) | a conferir |
| `y / y.max()` | `y / 100` | o máximo dos dados inclui o teste; o domínio da taxa é conhecido | a conferir |
| exclusão de colunas por pertinência, depois do mapa de correlação | igual, mais a regra de redundância entre preditores escrita antes (4.3) | a correlação com o alvo não escolhe variável (regra 7) | — |
| uma configuração de variáveis | A e B | separar o que vem do histórico do que vem do território e da infraestrutura | — |
| sem imputação, sem categóricas | imputação pela mediana com indicador; one-hot | a infraestrutura tem vazios; localização e rede são categorias | — |
| `hidden_layer_sizes=50`, uma semente (12) | 50 como principal; 10 sementes; 10 e 25 só como sensibilidade | variância do treinamento (5.5.5); a topologia não é escolhida pelo teste | 5.5.1, 5.5.5 |
| sem validação cruzada | validação cruzada temporal no treino, só descritiva | relatar a estabilidade das topologias sem usar anos já vistos para escolher | 5.5.1 |
| só o modelo | régua, B2 e Ridge na mesma tabela | um número sozinho não diz se a rede vale a pena | — |
| MAE, MSE, RMSE (`squared=False`), MAPE, R² | MAE, RMSE (`root_mean_squared_error`), R², Recall@20% | MAPE divide pelos zeros do abandono; `squared=False` foi removido no scikit-learn 1.8 | — |
| sem intervalo | IC por bootstrap de escolas e Holm | a diferença precisa de incerteza para ser lida | — |
| gráfico desejado × estimado de 40 amostras | igual, com a régua ao lado | a régua aparece em todo gráfico e tabela | — |

Os números 5.5.1 (validação cruzada) e 5.5.5 (várias execuções) vêm do pedido da pesquisadora. Onde está "a
conferir", a seção do cap. 5 ainda precisa ser localizada no exemplar antes do merge; nenhum número de seção foi
atribuído sem conferência.

## 12. O que esta avaliação responde e o que não responde

- **Responde:** se a rede prevê o **valor** do abandono de t+1 com erro absoluto menor que repetir o abandono de t−1,
  nas mesmas escolas, nos desfechos de 2018 e 2019.
- **Não responde, sozinha:** se a rede faz uma **lista** de escolas de risco melhor que a régua. A régua erra muito
  como valor (R² baixo nas Etapas 1 e 2, `docs/BASELINE.md`, seção 2) mas ordena bem. Uma previsão que só puxa
  todas as escolas para perto da média pode ganhar dela no MAE sem ordenar melhor. Por isso o Recall@20% é relatado
  ao lado, e uma vitória em MAE com Recall@20% igual ou pior que o da régua deve ser lida como "prevê o nível
  melhor, mas não identifica melhor quem está em risco".
- **Não é avaliação em dados virgens** (seção 3).
