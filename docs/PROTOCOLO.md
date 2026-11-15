# Protocolos do abandono-rr

Este arquivo guarda, nesta ordem:

- **A.** o registro **retroativo** da classificação de alto risco de 2026-11-10, escrito depois da execução e
  marcado assim;
- **B.** o desenho padrão de avaliação do projeto, que vale como regra para todo estudo novo;
- **C.** o protocolo do **estudo de fatores associados ao nível de abandono**, escrito **antes** de qualquer
  execução;
- **D.** o que acontece depois de uma execução (as saídas, o relato e a correção de erros);
- no fim, o protocolo da Etapa 4 (regressão do abandono em t+1), registrado em 2026-11-11, **nunca executado**,
  guardado inteiro na seção "Protocolo registrado, não executado, substituído em 2026-11-14".

As regras que regem este arquivo estão no `CLAUDE.md` (em especial as regras 5, 6, 7 e 10); as decisões e os
motivos, no `docs/DECISOES.md`. Nenhum número de resultado aparece aqui: resultado fica em arquivo gerado por
código (regra 3).

---

## A. Registro retroativo — a classificação de alto risco de 2026-11-10

**Este registro foi escrito em 2026-11-15, depois da execução.** Não é um protocolo prévio: é a descrição, para
consulta neste repositório, do desenho que foi registrado e executado no projeto anterior. O protocolo original,
escrito antes daquela execução, está no repositório `abandono-escolar` (commit `878930f`, `docs/DECISOES.md`,
entrada de 2026-11-10). O script está em `experimentos/classificacao_2013_2018/` e as saídas congeladas em
`docs/projeto_anterior/classificacao/` (sha256 conferidos por `testes/test_baseline.py`).

- **Pergunta:** o rótulo `alto_risco_t1` (os 20% de maior abandono da etapa em t+1, com abandono > 0) pode ser
  antecipado melhor do que pela régua?
- **Desenho:** walk-forward na janela segura (t = 2013–2018), com teste nos anos de desfecho 2016–2019; cada
  transição treina só com os anos anteriores a ela; o valor agrupado é a média simples das quatro transições.
  AF e EM separados. Universo: escolas públicas com o abandono da etapa em t−1, t e t+1.
- **Três blocos cumulativos de variáveis** (`src/avaliacao/classificacao.py`):
  1. abandono e reprovação de t−1 e a variação defasada (`abandono_tm1`, `reprovacao_tm1`,
     `variacao_abandono_defasada`);
  2. \+ localização e dependência (one-hot);
  3. \+ as quatro dimensões `dim_*_zano` e o `iie_zano`.
- **Três modelos** (hiperparâmetros fixos no código, nenhum ajustado por busca): regressão logística,
  Random Forest e HistGradientBoosting. Réguas B1R_lag e B2 e o acaso na mesma tabela.
- **Inferência:** bootstrap agrupado por escola (5.000 reamostragens, semente 20261111), as mesmas reamostragens
  para todos os comparados; famílias de teste declaradas no script, com Holm; a decisiva é a **F6**
  (modelo − régua, 2 etapas × 3 modelos × 3 blocos × 2 métricas = 36 testes).
- **Resultado:** está em `docs/BASELINE.md`, §4, gerado por código a partir das cópias congeladas. É o nulo
  preditivo que responde à Q4 (`docs/BASELINE.md`, §5).
- **Consequência para qualquer protocolo novo:** os anos de desfecho 2016–2019 foram olhados como teste. Pela
  regra 10, nenhuma escolha de protocolo pode depender deles.

---

## B. O desenho padrão do projeto (vale como regra)

Todo estudo novo segue este desenho, e o protocolo específico só diz o que acrescenta ou aperta:

1. **Régua primeiro.** Em estudo preditivo, a comparação obrigatória é a régua **B1R_lag** (o abandono de t−1,
   o último conhecido na hora da decisão); B2 e acaso aparecem na mesma tabela. Em estudo de associação, o
   equivalente é relatar o R² ao lado de referências simples declaradas no protocolo.
2. **Incerteza por bootstrap agrupado por escola** (`co_entidade`): sorteiam-se escolas com reposição, levando
   todas as linhas da escola sorteada. O número de reamostragens e a semente ficam fixados no protocolo, antes
   de rodar. As mesmas reamostragens servem para tudo o que se compara: as diferenças são pareadas. IC 95%
   pelos percentis 2,5 e 97,5; p bilateral por bootstrap (`src/avaliacao/bootstrap.p_bootstrap`).
3. **Correção de Holm por família declarada antes**, com α = 0,05. A família lista, no protocolo, cada teste
   que a compõe; nenhum teste entra ou sai depois de visto o resultado.
4. **Três vereditos, com margem prática fixada antes.** Em estudo preditivo: GANHO / SEM GANHO PRÁTICO /
   INCONCLUSIVO. Em estudo de associação: ASSOCIADO / SEM ASSOCIAÇÃO PRÁTICA / INCONCLUSIVO (definição na
   seção C.6). Resultado nulo é relatado como qualquer outro.
5. **Anos de desfecho já usados como teste: 2016–2019 e 2021–2024** (em ano t: 2015–2018 e 2020–2023). Eles
   não escolhem variável, modelo, limiar nem janela (regra 10).
6. **Protocolo antes de rodar, execução única.** O protocolo entra no `main` por pull request revisado por
   outro integrante **antes** de qualquer execução; a execução acontece uma vez e as saídas são congeladas no
   git (política das cópias, `docs/DECISOES.md`, 2026-11-14).

---

## C. Protocolo do estudo de fatores associados ao nível de abandono

**Estado: escrito antes de qualquer execução.** Nenhum modelo deste estudo foi treinado, nenhuma associação da
janela foi olhada para escrever este texto, e nenhuma escolha abaixo depende dos anos de desfecho já usados como
teste: a lista de preditores é fechada, os hiperparâmetros vêm do exemplo do professor ou são fixados aqui, e a
margem prática está justificada sem olhar dado. A execução é única e só acontece depois que este protocolo
entrar no `main` por pull request revisado por outro integrante.

### C.1 Perguntas

- **Q1.** Quanto da diferença de abandono entre escolas essas características explicam?
- **Q2.** Qual o peso de cada característica, com que incerteza?
- **Q3.** O peso se mantém entre anos finais (AF) e ensino médio (EM)?

A **Q4** (antecipar a mudança do ano seguinte) já está respondida e fica no `docs/BASELINE.md`, §5; não há
experimento novo para ela. Este estudo fala em **fatores associados**, nunca em "variáveis responsáveis" nem em
"o que causa o abandono". **Associação não é causa**, e nada aqui sustenta recomendação de intervenção.

### C.2 Desfecho, universo e janela

- **Desfecho:** `abandono_t`, a taxa de abandono da etapa **no próprio ano t** (o nível, em % de 0 a 100). Não
  é previsão de t+1.
- **Unidade:** a escola-ano. **AF e EM sempre separados**, em tudo: universo, modelos, inferência, vereditos.
- **Universo de cada etapa:** escolas públicas (`rede_publica` = 1) com `abandono_t` da etapa não vazio,
  t = 2013–2018 (`janela_segura` = 1). Escola sem a etapa no ano está fora (regra 8; nada vira 0). Linha com
  algum preditor da lista fechada vazio sai da regressão da etapa, com a contagem relatada; na janela não se
  espera nenhum vazio de infraestrutura (`testes/test_dataset.py`).
- **Janela t = 2013–2018, e por quê.** A janela segura foi registrada e conferida nos estudos anteriores (um
  único formato de dados, antes da pandemia) e **não é reaberta**: "janela já registrada e conferida, não
  reaberta". As justificativas ano a ano da tabela do `dataset/DICIONARIO.md` são dos estudos t → t+1; para o
  estudo de nível, valem os mesmos motivos de comparabilidade (formato único, sem pandemia), e os anos de 2019
  em diante continuam fora pelos regimes atípicos (pandemia, pós-pandemia, Pé-de-Meia).
- **Anos já olhados.** As taxas de abandono de 2016, 2017 e 2018 foram desfecho de teste da classificação
  (seção A). Nenhuma escolha deste protocolo depende delas: a lista fechada da C.3 e os valores fixados aqui
  garantem isso, e o relatório da execução repete essa ressalva.
- **Identidade contábil (regra 6):** aprovação + reprovação + abandono = 100. Nenhuma das três taxas da etapa e
  ano entra em X — e, por decisão deste protocolo, **nenhuma variável de rendimento de nenhum ano** entra (C.3).

### C.3 A lista fechada de preditores

Fechada aqui, antes de rodar; nenhuma variável entra ou sai depois (regra 7). Nomes conferidos no
`dataset/DICIONARIO.md` (v0.2.0).

| Papel | Variável | Tipo | Observação |
|---|---|---|---|
| fator (território) | `localizacao` | categórica (Urbana, Rural) | referência: **Urbana**, nas duas etapas |
| fator (rede) | `dependencia` | categórica (Estadual, Municipal, Federal) | referência: **Estadual**, nas duas etapas; regra dos 30 e das 10 escolas abaixo |
| fator (infraestrutura) | `dim_iib_prop` | proporção 0–1 | 4 itens de infraestrutura básica |
| fator (infraestrutura) | `dim_ida_prop` | proporção 0–1 | 5 itens de dependência administrativa |
| fator (infraestrutura) | `dim_idp_prop` | proporção 0–1 | 5 itens de dependência pedagógica |
| fator (infraestrutura) | `dim_iep_prop` | proporção 0–1 | 4 itens de equipamento pedagógico |
| controle | `ano` | dummies por ano, referência 2013 | **não é fator**: absorve o nível do ano; não recebe efeito, IC nem veredito |

- **Referências declaradas, e por quê** (sem olhar associação): Urbana é a referência porque o fator de
  interesse é ser rural. Estadual é a referência porque é uma categoria ampla nas duas etapas e é a rede de
  referência da educação básica pública de RR. A referência não muda o ajuste, só a leitura dos coeficientes.
- **Regra dos 30 e das 10 escolas:** uma categoria de `dependencia` só entra na regressão da etapa se tiver
  **pelo menos 30 escolas-ano e pelo menos 10 escolas distintas** na etapa. Com menos de 30 escolas-ano ou
  menos de 10 escolas distintas, ela sai, junto com as suas linhas, e aparece no relatório só com as duas
  contagens (tabela 0, C.13). Motivo do mínimo de escolas: o bootstrap sorteia escolas, então a regra conta
  na unidade da inferência; uma categoria com escolas-ano suficientes, mas de poucas escolas, apoiaria o seu
  coeficiente em poucas unidades. A regra é mecânica e usa só contagens de preditores: aplicá-la não é
  escolher por associação. Consequência esperada, pelas contagens do revisor (que só usam preditores;
  `docs/revisoes/2026-11-15_joao_pr9.md`): no EM, a Federal e a Municipal saem. Nesse caso sobra só a
  Estadual, e **a rede deixa de ser fator no EM**: aparece só com as contagens.
- **O que não entra, e por quê:**
  - **nenhuma variável de rendimento, de nenhum ano** (`abandono_tm1`, `abandono_tm2`, `reprovacao_tm1`,
    `variacao_abandono_defasada`, `aprovacao_t`, `reprovacao_t`): decisão deste protocolo, mais apertada que a
    regra 6. A pergunta é sobre características **estruturais**; a persistência do abandono já foi medida
    (`docs/BASELINE.md`) e, misturada aos fatores, absorveria o peso deles sem responder a Q2;
  - `rede_publica`: constante no universo;
  - `dim_*_zano` e `iie_zano`: padronizadas com todas as escolas do ano — vazariam entre as dobras da validação
    cruzada agrupada (`docs/DECISOES.md`, 2026-11-14, dimensões em proporção);
  - `infra_itens_completos`, `infra_fonte_artigo`: qualidade do dado, não característica da escola;
  - **os 18 itens** `iib_*`, `ida_*`, `idp_*`, `iep_*`: só descrição (prevalência por etapa e ano, C.13), nunca
    em modelo. Nunca dois níveis da mesma informação (itens, dimensões, índice) no mesmo modelo.

### C.4 Modelos da tabela de fatores (Q2)

- **Modelo principal:** regressão linear (OLS, `LinearRegression`) de `abandono_t` (em pp) sobre os fatores e o
  controle da C.3, por etapa, nas escolas-ano da janela. Preditores entram na escala original (proporções 0–1 e
  dummies); sem imputação. É um modelo **descritivo da associação na janela inteira**: não há divisão
  treino/teste nesta parte, então a cláusula de dobras da regra 5 se aplica à parte preditiva (C.7), não a
  esta.
- **Modelo secundário:** o mesmo, com `iie_prop` no lugar das quatro dimensões. Serve para ler o nível agregado
  da infraestrutura. **Nunca** as quatro dimensões e o índice no mesmo modelo.
- **Colinearidade relatada, não decisora:** VIF de cada coluna de X do modelo principal (regressões auxiliares
  entre preditores, VIF = 1/(1−R²); implementado no código do estudo, sem dependência nova). VIF alto alarga os
  ICs, e os ICs por bootstrap já mostram isso; nenhum VIF exclui variável.

### C.5 Efeitos relatados

Para cada fator, por etapa e modelo:

- **efeito em pp:** o coeficiente. Para categórica, a diferença da categoria para a referência; para dimensão e
  para o `iie_prop`, o efeito de ir de 0 a 1 na proporção (a amplitude toda);
- **efeito por item:** o coeficiente da dimensão ÷ número de itens da dimensão — quanto muda o abandono, em pp,
  associado a **um item a mais**; para o `iie_prop`, o equivalente é o efeito de um passo de 0,25 (coeficiente
  × 0,25), uma dimensão inteira a mais. É este o **efeito que decide** o veredito (C.6);
- **efeito padronizado:** pp por +1 desvio-padrão do preditor, com o desvio calculado no universo da etapa
  (escala de leitura, não transformação do ajuste); só para os contínuos;
- IC 95%, p, p Holm e o veredito (C.6). **Todos os fatores aparecem, inclusive os nulos**; ordenar a
  apresentação pelo efeito é permitido (regra 7).

**Figura principal: forest plot** dos **efeitos que decidem o veredito** (C.6), em pp com IC 95%, AF e EM lado
a lado (é também a figura da Q3); o efeito da amplitude 0→1 fica na tabela.

### C.6 Inferência, família de Holm, margem prática e vereditos

- **Bootstrap agrupado por escola**, como na regra B: **5.000 reamostragens, semente 20261115**, as mesmas para
  os dois modelos da etapa. Em cada reamostragem, o modelo é reajustado e os coeficientes guardados. IC 95%
  pelos percentis; p bilateral por `src/avaliacao/bootstrap.p_bootstrap`.
- **Reamostragem sem uma categoria:** se uma reamostragem não tiver nenhuma escola-ano de uma categoria do
  modelo, os coeficientes dessa categoria ficam NA nela; o IC usa as reamostragens válidas e a fração de
  inválidas é relatada. Se mais de 10% forem inválidas para um coeficiente, o veredito dele é INCONCLUSIVO,
  por regra.
- **Família de Holm (uma por etapa): F7-AF e F7-EM.** Cada família contém **todos os coeficientes que recebem
  veredito na etapa**: as dummies de `localizacao` e `dependencia` e as quatro dimensões, do modelo principal,
  mais o `iie_prop`, do secundário. As dummies de `ano` ficam fora (controle, sem veredito). O tamanho exato de
  cada família sai na tabela 0, antes dos modelos, pela regra dos 30 e das 10 escolas.
- **Margem prática: 1,0 pp, sobre o efeito que decide.** O efeito que decide o veredito é: para categórica, a
  diferença da categoria para a referência; para cada dimensão, o **efeito por item a mais** (coeficiente ÷
  número de itens); para o `iie_prop`, o efeito de um passo de **0,25** (coeficiente × 0,25) — no índice, que
  é a média simples das quatro dimensões, 0,25 é exatamente uma dimensão inteira a mais. O efeito da amplitude
  0→1 continua relatado, mas **não decide**: ir de 0 a 1 extrapola para escolas sem nenhum item ou com todos
  os itens, que podem nem existir na janela, sobretudo na infraestrutura básica. Justificativa do 1,0 pp,
  fixada sem olhar nenhuma associação: 1 pp de abandono é 1 aluno a cada 100 matriculados da etapa deixando a
  escola no ano — a menor diferença que ainda tem leitura prática para gestão; abaixo disso, mesmo uma
  associação certa não distingue escolas de forma útil. É o mesmo espírito da margem de ganho prático dos
  estudos anteriores (traduzir o efeito em alunos e escolas antes de chamá-lo de relevante).
- **Vereditos**, avaliados nesta ordem, sempre sobre o **efeito que decide**:
  1. **ASSOCIADO:** p **com Holm** ≤ 0,05 **e** |efeito que decide| ≥ 1,0 pp;
  2. **SEM ASSOCIAÇÃO PRÁTICA:** o IC 95% **sem correção** do efeito que decide, inteiro dentro de
     (−1,0; +1,0) pp;
  3. **INCONCLUSIVO:** qualquer outro caso.

  Como nos estudos anteriores do projeto (famílias F5 e F6): a afirmação positiva é a protegida pela correção
  de Holm; a leitura de ausência prática usa o IC 95% padrão, sem correção; o INCONCLUSIVO cobre o resto.

### C.7 Q1 — quanto se explica (R² dentro da amostra e em validação cruzada agrupada)

- **Modelos:** a regressão linear da C.4, `Ridge(alpha=1.0)` (fixo, não ajustado) e o `MLPRegressor` **como no
  exemplo do professor**, sem nenhum ajuste:

  ```python
  MLPRegressor(hidden_layer_sizes=(50,), activation="logistic", solver="adam",
               max_iter=5000, tol=1e-7, momentum=0.8, early_stopping=True, epsilon=1e-08,
               n_iter_no_change=10, random_state=semente)
  ```

  (`momentum` não tem efeito com `solver="adam"`; fica como no exemplo.) **Declarado:** o `early_stopping`
  separa, ao acaso, 10% das **linhas** de treino para decidir quando parar — uma divisão por linha, não por
  escola; escolas-ano da mesma escola podem cair dos dois lados dessa validação interna. Fica registrado como
  limitação conhecida; afeta só o ponto de parada do treino.
- **Modelo de referência só com o ano:** para separar o nível do ano do que as características explicam, cada
  classe de modelo também roda **só com as dummies de `ano`** (mesmo pipeline, mesmas dobras; no MLP, as
  mesmas 10 sementes). O **ΔR²** de um modelo é o R² da validação cruzada agrupada dele menos o R² do modelo
  só com o ano da mesma classe.
- **Pipeline único para os três** (`ColumnTransformer`): `StandardScaler` nas quatro dimensões,
  `OneHotEncoder(handle_unknown="ignore")` em `localizacao`, `dependencia` e `ano`, tudo ajustado **só na
  parte de treino de cada dobra** (regra 5). Com `handle_unknown="ignore"`, uma categoria presente na
  validação e ausente no treino da dobra fica com todas as dummies em zero, em vez de parar a execução.
  Alvo `abandono_t / 100` (domínio conhecido da taxa); as previsões voltam a pp (× 100) antes de qualquer
  métrica, sem corte em [0, 100]; o relatório conta quantas ficaram fora.
- **Validação cruzada:** `GroupKFold(n_splits=5)` com grupo = `co_entidade`, por etapa; as **mesmas dobras**
  para os três modelos. O R² da validação é calculado sobre as previsões fora-da-dobra **agrupadas** (um valor
  por semente), não por dobra.
- **Sementes:** o MLP roda com 10 sementes (`random_state` = 1 a 10); média e desvio-padrão (`ddof=1`) nas
  sementes; a estimativa pontual é a média. Linear e Ridge são determinísticos nas mesmas dobras.
- **Métricas:** MAE, RMSE (`sklearn.metrics.root_mean_squared_error`) e R², dentro da amostra e na validação
  cruzada agrupada, em pp. **Sem MAPE** (o abandono tem muitos zeros).
- **Leitura declarada antes:** o número que responde à Q1 é o **ΔR² da validação cruzada agrupada da
  regressão linear** — o ganho sobre o modelo só com o ano, que é o que as características explicam além do
  nível do ano. O R² total e o R² do modelo só com o ano são relatados ao lado. Ridge e MLP dizem se
  flexibilidade acrescenta algo (cada um com o seu ΔR²); a diferença é relatada com as métricas, **sem troca
  de modelo** por R² (regra 7) e sem frase de "supera" — não há família de Holm na C.7. **ΔR² baixo é resposta
  da Q1, não defeito** (C.12).

### C.8 Importância por permutação (comparada à tabela de fatores)

- Só para o MLP (a tabela da C.5 já lê a linear). Calculada **fora da dobra**: em cada dobra da GroupKFold,
  permuta-se cada preditor na parte de validação, com `n_repeats = 20` e semente fixa 20261115; a queda de R²
  é agregada nas dobras e nas 10 sementes, com IC pelos percentis das repetições.
- **Por variável e por grupo:** território (`localizacao`), rede (dummies de `dependencia` juntas),
  infraestrutura (as quatro dimensões juntas) e ano (controle, só relatado). Permutação em grupo = as colunas
  do grupo permutadas com o **mesmo** sorteio de linhas (implementada no código do estudo; preditores
  correlacionados repartem importância, e o grupo soma o que a divisão esconde).
- **Leitura:** a ordem das importâncias é **comparada** à ordem dos efeitos padronizados da tabela da C.5,
  como descrição. Divergência é relatada, não resolvida: nenhum fator muda de veredito por importância.

### C.9 Controle negativo (declarado antes; pode parar a execução)

Dentro de cada etapa e **dentro de cada ano**, o `abandono_t` é embaralhado entre as escolas (semente fixa
20261115), e o pipeline inteiro da C.7 roda de novo, inclusive o modelo só com o ano. O embaralhamento dentro
do ano preserva o nível do ano **de propósito** — por isso o critério é sobre o ganho, não sobre o R² total,
que pode ficar alto mesmo com o código certo.

**Critério, fixado aqui:** o **ΔR² da validação cruzada agrupada sobre o modelo só com o ano**, no desfecho
embaralhado, deve ficar **abaixo de 0,02** para cada um dos três modelos (no MLP, a média das 10 sementes).
Justificativa do 0,02, fixada sem olhar dado: com o desfecho embaralhado entre as escolas, tudo o que as
características poderiam explicar além do nível do ano foi destruído, então o ganho verdadeiro é zero e o
estimado só pode ser ruído da validação cruzada; 0,02 (dois centésimos da variância) é folga pequena para esse
ruído e muito menor do que o ganho que um vazamento real produziria ao reidentificar as escolas. Se algum
modelo chegar a 0,02, **a execução para**, o resultado não é relatado e a causa (vazamento no código ou no
dado) é investigada e registrada no `docs/DECISOES.md` antes de qualquer nova execução.

### C.10 Robustez (declarada antes; nunca substitui o resultado principal)

1. **Média por escola na janela:** cada escola vira uma linha (média dos preditores e do desfecho nos seus
   anos da janela; `ano` sai), e a regressão principal roda de novo, com bootstrap simples de escolas. Lê se o
   resultado do painel vem do peso desigual das escolas com mais anos.
2. **Janela t = 2012–2019:** a mesma análise com dois anos a mais. 2012, e não 2011, porque `dim_ida_prop` e
   `dim_idp_prop` só existem de 2012 em diante (o Censo não perguntava todos os itens antes); 2019 entra porque
   o desfecho aqui é do próprio ano (o abandono de 2019 é pré-pandemia; o motivo que tirava 2019 da janela
   t → t+1 era o desfecho de 2020).

As duas aparecem ao lado do principal, como direção e ordem de grandeza; não têm família de Holm nem veredito,
e **nenhuma substitui a janela principal, qualquer que seja o resultado**.

### C.11 Q3 — AF × EM, lado a lado

As duas etapas são relatadas lado a lado (tabela da C.5 e o forest plot), como **descrição**: direção, ordem de
grandeza e veredito de cada fator nas duas etapas. **Não há teste formal da diferença entre etapas**, por
decisão deste protocolo: o painel do EM é bem menor, um teste de interação teria pouco poder e aumentaria a
família de Holm, enfraquecendo a Q2 — e a leitura pré-registrada da Q3 é qualitativa. Fica declarado também o
contrário: **IC que se sobrepõem não mostram igualdade**; onde um fator for ASSOCIADO numa etapa e
INCONCLUSIVO na outra, a frase é "não dá para afirmar que o peso difere", nunca "o peso é igual". Um teste
formal de diferença, se o grupo quiser, exige protocolo novo antes de rodar.

### C.12 Expectativas registradas antes de rodar

- **ΔR² baixo é a resposta da Q1, não um defeito.** Os estudos anteriores já mostraram que mesmo a história da
  própria escola erra muito o valor da taxa (`docs/BASELINE.md`, §2); características estruturais fixas devem
  explicar ainda menos da variação ano a ano.
- **No EM, muitos INCONCLUSIVO são esperados.** O painel do EM é bem menor que o do AF — as contagens exatas
  de escolas e escolas-ano por etapa saem por código na tabela 0, antes de qualquer modelo (regra 3) — e, com
  menos escolas, os ICs por bootstrap de escola saem largos. Isso repete o padrão da classificação
  (`docs/BASELINE.md`, §4). INCONCLUSIVO no EM será relatado como tal, sem releitura.
- **Nas dimensões de infraestrutura, muitos INCONCLUSIVO são esperados nas duas etapas**, não só no EM. As
  dimensões são colineares com a `localizacao` (as escolas rurais têm menos itens em todas elas) e entre si,
  o que alarga os ICs de cada uma (relações entre preditores, sem o desfecho;
  `docs/revisoes/2026-11-15_joao_pr9.md`). O VIF da C.4 mostra o quanto.
- O abandono tem **muitos zeros** e é limitado a [0, 100]; a regressão linear lê diferenças de média, e a
  inferência não depende de normalidade (bootstrap). Fica como limitação conhecida (C.14), não como motivo
  para trocar de modelo depois de ver resultado.

### C.13 O que a execução grava

Código em `experimentos/fatores_2013_2018/`, lendo `dataset/escolas_rr_v0.2.0.csv` e as funções de `src/`, sem
escrever fora da própria pasta. A execução é única, na ordem abaixo; a tabela 0 vem **antes** dos modelos e é o
único lugar onde a regra dos 30 e das 10 escolas é aplicada (mecanicamente).

| Arquivo | Conteúdo |
|---|---|
| `00_universo.csv` | tabela 0: escolas e escolas-ano por etapa, ano e categoria; aplicação da regra dos 30 e das 10 escolas, com as duas contagens de cada categoria; tamanho das famílias F7 |
| `01_itens.csv` | os 18 itens: prevalência por etapa e ano (só descrição, nunca modelo) |
| `02_correlacao.csv` | correlações entre os preditores; o desfecho à parte, marcado "só exibição, não decide" |
| `03_vif.csv` | VIF das colunas de X do modelo principal, por etapa |
| `04_fatores.csv` | a tabela de fatores (C.5): modelo principal e secundário × etapa, com efeito em pp, por item, padronizado, IC 95%, p, p Holm, veredito e fração de reamostragens inválidas |
| `05_r2.csv` | Q1 (C.7): MAE, RMSE e R², dentro da amostra e na validação cruzada, por modelo × etapa, inclusive o modelo só com o ano e o ΔR² (média e desvio nas sementes) |
| `06_permutacao.csv` | importância por permutação (C.8), por variável e por grupo, com IC |
| `07_controle_negativo.csv` | o controle da C.9, por modelo × etapa: R², ΔR² sobre o modelo só com o ano e o critério passou/parou |
| `08_robustez.csv` | as duas análises da C.10 |
| `fig_forest.png` | figura principal: efeitos em pp com IC, AF e EM lado a lado |

As saídas entram no git no pull request da execução (política das cópias congeladas, `docs/DECISOES.md`,
2026-11-14), e o relatório que as cita só exibe números desses arquivos (regras 3 e 4).

### C.14 O que este estudo responde e o que não responde

- **Responde:** quais características estruturais estão **associadas** ao nível de abandono da escola-ano na
  janela, com que peso e com que incerteza (Q2); quanto da variação elas explicam além do nível do ano (Q1);
  e como isso se compara entre AF e EM (Q3).
- **Como ler cada efeito:** o efeito de um fator é lido **com os outros constantes**. Como a localização e
  a infraestrutura são colineares (C.12), a divisão do efeito entre "ser rural" e "ter menos infraestrutura"
  é instável: o que o modelo atribui a uma pode ser da outra. E **"Rural" soma perfis diferentes**: inclui
  escolas indígenas e de difícil acesso, que ainda não têm marcação no dataset (meta M1,
  `docs/ROTEIRO.md`); o coeficiente de Rural é a soma desses perfis, não o efeito de um deles.
- **Não responde:** causa, efeito de intervenção, ou qualquer coisa sobre alunos. Também não melhora a previsão
  do ano seguinte: isso é a Q4, já respondida (`docs/BASELINE.md`, §5).
- **Limitações declaradas:** desfecho com muitos zeros lido por modelo linear de média; `early_stopping` do MLP
  com divisão por linha; três dos seis anos de desfecho da janela já tinham sido olhados como teste da
  classificação (C.2); e a janela principal reusa a janela segura por decisão, não por nova análise.

---

## D. Depois da execução (vale para todo estudo)

A execução é única porque o valor do resultado está em ele não ter sido escolhido: se fosse possível rodar,
olhar, ajustar e rodar de novo, o resultado seria o que as escolhas quisessem, e o p, o IC e o Holm deixariam de
valer (eles supõem uma análise fixada antes de ver o desfecho). Isto diz o que acontece depois.

1. **As saídas ficam congeladas.** Entram no git no pull request da execução, cada uma com o commit e o sha256
   do dataset na primeira linha, e nunca são regravadas: o script recusa rodar se a pasta de saídas existir.
2. **Tudo é relatado como saiu**, inclusive os nulos e os INCONCLUSIVO, com a leitura da seção do protocolo
   (os vereditos e as frases já fixados), nunca com a leitura que se preferiria. O relatório só exibe números
   dos arquivos de saída (regras 3 e 4).
3. **Um erro descoberto depois não apaga o resultado.** Só justifica nova execução um defeito em relação ao
   protocolo: o código fazendo algo diferente do que o protocolo diz, ou um dado de entrada errado. Discordar
   do resultado não justifica. Nesse caso:
   - o defeito, a evidência e a correção ficam no `docs/DECISOES.md` **antes** da nova execução;
   - a correção do código entra por pull request revisado;
   - as saídas da primeira execução continuam no git (movidas para uma pasta com o número da execução) e
     **os dois resultados são relatados lado a lado**, com o motivo da segunda.
4. **Mudar o desenho depois de ver o resultado é estudo novo:** exige protocolo novo, escrito antes de rodar,
   e o relato diz que ele foi desenhado depois de conhecido o primeiro resultado (é exploratório).
5. **Controle negativo reprovado é a exceção:** ele roda primeiro, com o desfecho embaralhado, e a execução para
   antes de calcular qualquer associação real. Nenhum resultado foi visto, então, corrigida a causa e
   registrada no `docs/DECISOES.md`, a execução pode ser feita de novo; o 07 reprovado fica no git.
6. **Falha técnica no meio da execução:** as saídas parciais são guardadas numa pasta separada, a falha é
   registrada no `docs/DECISOES.md` e a execução é refeita com o mesmo commit; como as sementes são fixas, os
   números são idênticos.

---

## Protocolo registrado, não executado, substituído em 2026-11-14

O protocolo abaixo (a "Etapa 4": regressão do abandono em t+1 com MLPRegressor) foi registrado em
2026-11-11 e **nunca foi executado**: a pasta `experimentos/regressao_mlp_2013_2018/` nunca existiu. Com a
mudança de pergunta do projeto (`docs/DECISOES.md`, 2026-11-14), ele foi substituído pela seção C, que
aproveita a forma do exemplo do professor para o estudo de nível. O texto segue **inteiro**; a única
mudança são os títulos, rebaixados dois níveis (`#` → `###`) para ficarem abaixo desta seção
(`testes/test_protocolo.py` confere isso contra o original).

### Protocolo da Etapa 4 — regressão do abandono em t+1 com MLPRegressor

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

#### 1. As perguntas

Uma pergunta por configuração de variáveis, cada uma com a sua comparação obrigatória:

- **Configuração A:** a rede supera a régua (o abandono de t−1), usando a mesma informação que ela?
- **Configuração B:** sem nenhum histórico de rendimento, território, rede e infraestrutura identificam o risco?
  Comparação obrigatória **B × B2**, porque a B2 já é território × rede.

A régua, a B2 e a Ridge entram nas duas, na mesma tabela.

#### 2. Dados e universo

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

#### 3. Divisão temporal (fixa, decidida antes)

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

#### 4. Variáveis

##### 4.1 O que fica fora antes de tudo (por pertinência, decidido agora)

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

##### 4.2 As candidatas de cada configuração

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

##### 4.3 A regra de seleção: redundância entre preditores, só no treino

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

#### 5. Pré-processamento (dentro do `Pipeline`, ajustado só no treino)

- **Numéricas:** `SimpleImputer(strategy="median", add_indicator=True)` e depois `StandardScaler()`, como na
  classificação de 2026-11-10. A imputação é necessária porque a infraestrutura tem vazios; o exemplo não tem.
- **Categóricas** (`localizacao`, `dependencia`): `OneHotEncoder(handle_unknown="ignore")`.
- **Tudo dentro de um `Pipeline`** (`ColumnTransformer` + modelo), ajustado com `fit` só nas linhas de treino e
  aplicado ao teste com `predict`. No exemplo, o `StandardScaler` era ajustado com o conjunto inteiro, antes da
  divisão: aqui não.
- **Alvo:** `abandono_t1 / 100`, pelo domínio conhecido da taxa (0 a 100). O exemplo dividia pelo máximo dos dados
  (`y.max()`), o que usa o teste. As previsões voltam para pontos percentuais (× 100) antes de qualquer métrica.
  As previsões **não são cortadas** em [0, 100] (o exemplo não corta); o relatório conta quantas ficaram fora.

#### 6. Modelos

##### 6.1 A rede (resultado principal)

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

##### 6.2 Sensibilidade de topologia (decidida antes, não substitui o principal)

A mesma rede, com as mesmas variáveis, sementes e métricas, também com `hidden_layer_sizes=(10,)` e `(25,)`.
Os resultados são relatados **ao lado** do principal. **Nenhum deles substitui o resultado de 50 neurônios,
qualquer que seja o resultado.** Não entram nas famílias de Holm e não sustentam nenhuma frase de "supera".

##### 6.3 Validação cruzada temporal no treino (livro, 5.5.1) — só descritiva

Dentro do treino, janela expansiva por ano do desfecho: treina até o desfecho de 2014 e valida no de 2015; treina até
2015 e valida em 2016; treina até 2016 e valida em 2017. Cada dobra roda com 10, 25 e 50 neurônios e as 10
sementes, e relata o MAE médio e o desvio. **Não escolhe nada**: a topologia principal já está fixada em 6.1, e os
desfechos de 2016 e 2017 são anos de teste já usados (regra 10).

##### 6.4 Comparações obrigatórias (na mesma tabela)

| Nome | Previsão de `abandono_t1` | Ajuste |
|---|---|---|
| **régua** (B1R_lag) | `abandono_tm1` da própria escola | nenhum |
| **B2** | mediana de `abandono_t1` no treino por `localizacao` × `dependencia`; célula sem escola no treino recebe a mediana geral do treino (`src/avaliacao/baselines.b2_mediana_estrato`) | só treino |
| **Ridge** | `Ridge(alpha=1.0)`, com o mesmo `Pipeline`, as mesmas variáveis e o mesmo alvo ÷ 100 da rede, em cada configuração | só treino; `alpha` fixo, não ajustado |

#### 7. Sementes (livro, 5.5.5)

- A rede é treinada com **10 sementes** fixas: `random_state` = 1, 2, …, 10. A semente controla a inicialização dos
  pesos e o sorteio interno do `early_stopping`.
- Para cada métrica, relata-se a **média e o desvio-padrão** (com `ddof=1`) nas 10 sementes.
- A estimativa pontual da rede é a **média das 10 sementes** de cada métrica. Não se faz média das previsões
  (seria outro modelo, um comitê).
- A régua, a B2 e a Ridge são determinísticas: uma execução, desvio não se aplica.

#### 8. Métricas

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

#### 9. Intervalos, testes e a regra de leitura (escrita antes)

##### 9.1 Intervalo de confiança

- **Bootstrap por escola** (cluster): sorteiam-se escolas (`co_entidade`) com reposição, mantendo os dois anos de
  teste de cada escola sorteada (`src/avaliacao/bootstrap.Agrupado`). **5.000 reamostragens**, semente fixa
  20261111.
- As **mesmas** reamostragens servem para todos os modelos e réguas da etapa: as diferenças são pareadas.
- Para a rede, em cada reamostragem calcula-se a métrica de cada uma das 10 sementes e tira-se a média. O
  intervalo é o da média das sementes.
- IC 95%: percentis 2,5 e 97,5. O p-valor de uma diferença é o bootstrap bilateral de `bootstrap.p_bootstrap`.

##### 9.2 As famílias de teste e a correção de Holm

| Família | Diferença testada (MAE) | Testes |
|---|---|---|
| **F1** (decide a pergunta A, e também é lida para B) | rede de 50 neurônios − régua | 2 etapas × 2 configurações = 4 |
| **F2** (decide a pergunta B) | rede de 50 neurônios, configuração B − B2 | 2 etapas = 2 |

O Holm é aplicado dentro de cada família, com α = 0,05.

##### 9.3 A regra de leitura

A rede **"supera a régua"** (F1) numa etapa e configuração **só se as duas coisas** acontecerem:

1. o limite superior do IC 95% da diferença de MAE (rede − régua) ficar **abaixo de zero**; e
2. o p ajustado por Holm na família F1 for ≤ 0,05.

Em qualquer outro caso, a frase é "não superou a régua". Se o limite inferior do IC ficar acima de zero, a
frase é "errou mais que a régua". A F2 se lê do mesmo jeito, com a B2 no lugar da régua.

Tudo o mais é **descritivo**, com IC e sem frase de "supera": a rede − Ridge, a Ridge − régua, a configuração A ×
B2, as diferenças em RMSE, R² e Recall@20%, a sensibilidade de topologia (6.2) e a validação cruzada (6.3).
Resultado nulo também é resultado, e é relatado do mesmo jeito.

#### 10. O que a execução grava

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

#### 11. O que mudou em relação ao exemplo, e por quê

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

#### 12. O que esta avaliação responde e o que não responde

- **Responde:** se a rede prevê o **valor** do abandono de t+1 com erro absoluto menor que repetir o abandono de t−1,
  nas mesmas escolas, nos desfechos de 2018 e 2019.
- **Não responde, sozinha:** se a rede faz uma **lista** de escolas de risco melhor que a régua. A régua erra muito
  como valor (R² baixo nas Etapas 1 e 2, `docs/BASELINE.md`, seção 2) mas ordena bem. Uma previsão que só puxa
  todas as escolas para perto da média pode ganhar dela no MAE sem ordenar melhor. Por isso o Recall@20% é relatado
  ao lado, e uma vitória em MAE com Recall@20% igual ou pior que o da régua deve ser lida como "prevê o nível
  melhor, mas não identifica melhor quem está em risco".
- **Não é avaliação em dados virgens** (seção 3).
