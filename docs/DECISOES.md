# Decisões do abandono-rr

Registro curto, uma entrada por decisão: data, decisão, motivo e onde está a evidência. O histórico
completo do projeto anterior continua no arquivo: `abandono-escolar/docs/DECISOES.md` (commit `878930f`).

---

## 2026-11-11 — O abandono-rr começa como cópia aparada do projeto anterior

**Decisão (pesquisadora).** O `abandono-escolar` e o `Dados-do-Projeto` ficam congelados, só para
leitura. O `abandono-rr` importa só o que gera ou valida a base estendida 2007–2025, o funil, as réguas
(B1R_lag, B2 e acaso), o pipeline sem vazamento, as métricas, o bootstrap por escola, o Holm e o catálogo de
problemas dos dados.

**Origem:** `abandono-escolar` em `878930f` e `Dados-do-Projeto` em `969fc64`. A tabela do que ficou e
do que saiu foi aprovada na Etapa 0 da migração (conversa de 2026-11-11).

**Decisões tomadas na migração:**

1. `alto_risco_t1` segue a regra da classificação de 2026-11-10: 20% maiores da etapa no ano, abandono > 0,
   empates no limiar entram todos (definição completa em `dataset/DICIONARIO.md`).
2. O dataset cobre 2007–2025, uma linha por escola × ano × etapa, com a coluna `janela_segura`.
3. **A base oficial 2019–2025 (TDI, ATU, IED) não entra agora.** O escopo novo usa só a janela 2013–2018,
   que não tem esses indicadores. O pipeline oficial volta por pull request quando a meta M5 começar.
4. O recorte de Roraima de 2007–2025 (o antigo `gustavo/cache/`) é versionado em `dados/cache/`, com
   sha256 no `dados/MANIFEST.csv`.
5. O `docs/BASELINE.md` regera a régua da Etapa 1 por código e cita a Etapa 2 e a classificação dos CSVs
   do projeto anterior, sem rodar a classificação de novo.

**Consequência da decisão 3 — o que fica só no arquivo:**

- a comparação da base oficial regerada com a v1.0 do orientador: `abandono-escolar/src/base_longitudinal.py`
  e `abandono-escolar/docs/comparacao_base_v1.csv` (commit `878930f`);
- o teste 07, que confere o rendimento de 2019–2025 nas duas bases:
  `Dados-do-Projeto/gustavo/testes/07_validar_sobreposicao.py` e o relatório
  `gustavo/saida/relatorios/validacao_sobreposicao.txt` (25 checks, 0 falhas; commit `969fc64`);
- os degraus "Brasil" e "painel da Etapa 2" do funil e a cobertura do painel da Etapa 2;
- as seções G e H do teste 04 (painel e walk-forward da Etapa 2).

**Adaptações feitas na cópia** (só caminhos e imports, além do aparo acima): cada script acha a raiz do
`abandono-rr`; `gustavo/cache/` virou `dados/cache/`; `gustavo/programas/` virou `src/estendida/`;
`gustavo/avaliacao/` virou `src/avaliacao/`; `gustavo/analises/04` e `05` viraram `src/relatorios/`; a
classificação de 2026-11-10 virou `experimentos/classificacao_2013_2018/`, com as saídas da execução única
copiadas, não regeradas. O teste 03 passa a rodar com `--completo`. A comparação do teste 03 com o backup
de outubro (`_backup_2026-10-14`) não veio: o teste avisa e pula.

**Evidência de que nada mudou** (`testes/test_equivalencia.py`, igualdade exata): a `base_atual` 2007–2025
(12.597 × 55, mesmos tipos), a régua da Etapa 1, as réguas B1R_lag, B2 e acaso da janela (60 linhas × 15
métricas), o funil (degraus 2 a 7) e a taxa de abandono por ano civil, 2013–2019, são idênticos aos do projeto
anterior. Os
testes herdados passam: 01 (45 OK), 02 (41 OK), 03 (2019–2025 conferem célula a célula com os zips
originais), 04 (46 OK) e 08 (65 OK).

**Ressalva mantida.** Os dados de 2007 a 2018 vêm só de `dados/cache/`. Foram conferidos contra a fonte do
INEP uma vez, em 14/10/2026, na máquina do Gustavo (`docs/procedencia/relatorio_04_*.md`, §4), e não podem
ser reverificados aqui: os zips originais desses anos não estão no projeto. A janela segura depende deles.

**Fica para depois, fora do prazo de 16/11:** variáveis novas para 2007–2018, como matrículas e escola
indígena (meta M1); a volta do pipeline oficial (meta M5).

---

## 2026-11-11 — Teste 03: a conferência de 2019–2025 com os originais

**O que acontecia.** O teste 03 (`testes/03_validar_censo_pos04.py`, seção F) só lê um zip do Censo
com a opção `--completo`. Sem ela, confere contra o original apenas os anos com CSV já extraído em
`dados/bruto/censo/`.

- **No projeto anterior**, desde que o teste existe (Dados-do-Projeto `f524873`, 2026-10-14), os CSVs de
  2019–2025 estavam extraídos em `abandono-escolar/dados/bruto/censo/`. Então, mesmo sem `--completo`,
  o teste comparava 2019–2025 célula a célula com o microdado original: o relatório do projeto anterior
  registra "7 anos conferem célula a célula com o microdado ORIGINAL: 2019–2025". Os anos de 2007–2018
  nunca foram conferidos por esse teste, com ou sem `--completo`, porque os zips desses anos não estavam
  na máquina.
- **No abandono-rr**, a cópia trouxe só os zips, não os CSVs extraídos. Na primeira execução da Etapa 1,
  sem `--completo`, o teste **não comparou nenhum ano** com o original e passou com um aviso. A lacuna foi
  criada pela migração, não existia antes.

**Decisão.** O teste 03 roda sempre com `--completo` (`testes/test_validacoes.py`). Com isso, 2019–2025
conferem célula a célula com os zips originais em `dados/origem/censo/`, como no projeto anterior. O teste
de equivalência confirma, além disso, que a base inteira é idêntica à do projeto anterior.

**A comparação com o backup de outubro** (seção I do teste 03: a base do 04 antes × depois da correção de
14/10/2026) não roda no abandono-rr, porque o backup ficou no projeto anterior. Ela aparece no pytest como
**pulada**, com o motivo (`test_03_comparacao_com_backup_de_outubro`), e não como aprovada.

---

## 2026-11-11 — Os zips de 2019–2025 e o que cada um alimenta

Os 14 zips ficam em `dados/origem/`, **fora do git**; o `dados/MANIFEST.csv` guarda o sha256 de cada um, e
`python -m src.aquisicao --origem-local PASTA` (ou `--baixar`) os obtém conferindo o hash.

| Zip | Tamanho | Quem usa |
|---|---|---|
| `censo/microdados_censo_escolar_2019.zip` | 25,0 MB | `src/estendida/03` (reconstrução do cache) e teste 03 (`--completo`) |
| `censo/microdados_censo_escolar_2020.zip` | 24,8 MB | idem |
| `censo/microdados_censo_escolar_2021.zip` | 24,7 MB | idem; também traz os 2 PDFs de documentação do MANIFEST |
| `censo/microdados_censo_escolar_2022.zip` | 25,2 MB | idem |
| `censo/microdados_censo_escolar_2023.zip` | 30,6 MB | idem |
| `censo/microdados_censo_escolar_2024.zip` | 32,3 MB | idem |
| `censo/microdados_censo_escolar_2025_.zip` | 512,3 MB | idem (só a tabela de escolas) |
| `indicadores/tx_rend_escolas_2019.zip` a `_2025.zip` | 58,0 a 69,0 MB cada | `src/estendida/01` (reconstrução do cache de rendimento) |

**Nenhum serve só à base oficial.** Prova: `python src/estendida/99_pipeline.py --force` reconstruiu o cache
de 2019–2025 a partir dos 14 zips, e o conteúdo dos 14 parquets saiu idêntico ao versionado (só os
metadados do arquivo mudam, porque o cache original foi gravado com outra versão do pyarrow); a base
regerada continuou idêntica à do projeto anterior. O cache versionado foi mantido, para valer o sha256 do
MANIFEST.

**Retirado:** as tabelas Turma, Matrícula e Docente de 2025 (linhas do MANIFEST e de `src/config.py`).
Não são zips, mas só serviam à fase 2 do projeto anterior; o pipeline estendido lê só a tabela de escolas.

---

## 2026-11-11 — A Etapa 4 passa a ser regressão com MLPRegressor

**O que estava planejado.** A Etapa 4 do abandono-rr estava planejada, no pedido de criação do projeto
(11/11/2026), como uma classificação de alto risco (regressão logística, Random Forest e HistGradientBoosting;
configurações A e B; treino t = 2013–2016, teste t = 2017–2018). **Esse plano nunca virou protocolo escrito nem
foi executado.**

**A troca (orientação do professor).** Antes disso, por orientação do professor, o novo escopo passou a seguir o
exemplo "MLPRegressor - House Sales Prediction" (`docs/tese_base/`) e o livro de Silva, Spatti e Flauzino, cap. 5
(Perceptron multicamadas): regressão da taxa de abandono em t+1 (`abandono_t1`) com MLPRegressor. **A troca
aconteceu antes de qualquer protocolo ou execução da Etapa 4.**

**Não se confunde com a classificação de 2026-11-10** do projeto anterior, que tem protocolo próprio
(`abandono-escolar/docs/DECISOES.md`, commit `878930f`), rodou uma vez (Dados-do-Projeto, commit `969fc64`) e
continua válida no arquivo (`experimentos/classificacao_2013_2018/`). Os resultados dela são citados no
`docs/BASELINE.md`.

**O que veio do professor e o que veio da pesquisadora.** Do professor: seguir o exemplo e o livro. Da
pesquisadora, para que o exemplo respeite o `CLAUDE.md`: a divisão temporal, a padronização dentro do `Pipeline`,
o alvo ÷ 100, as configurações A e B, as 10 sementes, a régua, a B2 e a Ridge, as métricas, o IC por bootstrap,
o Holm e a regra de leitura. **A validação cruzada para a topologia não foi pedida pelo professor**: veio da leitura
do livro (5.5.1) pela pesquisadora.

**Decisões tomadas na escrita do protocolo** (todas antes de rodar; texto completo em `docs/PROTOCOLO.md`):

1. **Seleção por redundância entre preditores, não por correlação com o alvo.** O exemplo exibe o mapa de
   correlação e exclui colunas por pertinência. Aqui, entre duas candidatas com |r| > 0,90 no treino, sai a de menor
   prioridade na lista pré-declarada. A regra 7 do `CLAUDE.md` fica sem exceção.
2. **Topologia principal fixada em 50 neurônios, porque segue o exemplo do professor, e não por validação.** A
   validação cruzada temporal com 10, 25 e 50 neurônios roda no treino e é só relatada: os desfechos de 2016 e
   2017 são anos de teste já usados, e a regra 10 fica sem exceção.
3. **Sensibilidade de topologia:** 10 e 25 neurônios também são avaliados no teste, com as mesmas métricas e
   sementes, e relatados ao lado. Nenhum substitui o resultado de 50, qualquer que seja o resultado.
4. **Configuração A só com t−1** (`abandono_tm1`, `reprovacao_tm1`, `variacao_abandono_defasada`, mais território,
   rede e infraestrutura): é a informação disponível no começo de t+1 e a mesma que a régua usa, a mesma escolha do
   antigo Cenário B. Nenhum dado de t entra em nenhuma configuração.
5. **A nova configuração B** tem só território, rede e infraestrutura. **Não é a B antiga**, que tinha os lags de
   rendimento. Comparação obrigatória B × B2.
6. **O teste (desfechos de 2018 e 2019) já foi visto** na classificação de 2026-11-10. O resultado será relatado como
   nova leitura de anos já usados, não como avaliação em dados virgens.

**Evidência:** `docs/PROTOCOLO.md` neste branch (`protocolo-novo-escopo`), escrito antes de qualquer execução.

---

## 2026-11-14 — Cópias congeladas no git: as saídas da classificação e o exemplo do professor

1. **As saídas da classificação de 2026-11-10 entram no git**, no mesmo padrão da Etapa 2: cópia em
   `docs/projeto_anterior/classificacao/`, tirada do commit de origem (Dados-do-Projeto `969fc64`,
   `gustavo/saida/avaliacao/`), com o sha256 de cada arquivo no `docs/projeto_anterior/README.md`, conferido pelo
   `testes/test_baseline.py`. Antes, elas ficavam em `experimentos/classificacao_2013_2018/saida/`, que o
   `.gitignore` exclui: o `docs/BASELINE.md` e o `testes/test_equivalencia.py` dependiam de arquivos que quem
   clonasse não receberia. Os dois passam a ler a cópia versionada. **Alternativa
   descartada:** abrir uma exceção no `.gitignore` para aquela pasta; assim, todas as cópias congeladas do projeto
   anterior ficam num só lugar, com o mesmo controle de hash, e o `.gitattributes` as protege de normalização
   (`docs/projeto_anterior/** -text`).
2. **O exemplo do professor entra no git** (`docs/tese_base/`), com um README de uma linha: é material de
   referência de forma, baseado no dataset King County House Sales (Kaggle), e não código do projeto. O notebook
   entra como foi recebido, com as saídas; o `kc_house_data.csv` fica fora (`.gitignore`).
3. **O nbstripout nunca toca o exemplo do professor.** O `.gitattributes` declara o filtro para `*.ipynb` e uma
   exceção para `docs/tese_base/*.ipynb`. A instalação passa a ser `nbstripout --install --attributes
   .gitattributes` (`CONTRIBUTING.md`): a instalação padrão grava em `.git/info/attributes`, que tem precedência
   sobre o `.gitattributes` e anularia a exceção (conferido com `git check-attr` num clone de teste, nesta data).
   O `testes/test_atributos.py` acusa a máquina em que isso acontecer.

---

## 2026-11-14 — A pergunta do projeto muda: fatores associados ao nível de abandono

**Decisão (pesquisadora).** O repositório passa a ter um objeto só, a pesquisa PIBIC, e a pergunta passa a ser:

> Quais características estruturais de uma escola pública de Roraima estão associadas ao seu nível de abandono
> escolar, e quanto delas permite prever esse nível? A unidade é a escola-ano; o projeto não olha alunos.
> Associação não é causa.

Subperguntas: **Q1**, quanto da diferença de abandono entre escolas essas características explicam; **Q2**, qual o
peso de cada uma, com que incerteza; **Q3**, se o peso se mantém entre anos finais (AF) e ensino médio (EM);
**Q4**, se elas antecipam a mudança no ano seguinte. A Q4 já está respondida e vira uma seção do
`docs/BASELINE.md` (§5), não um experimento novo. O projeto fala em "fatores associados", nunca em "variáveis
responsáveis" nem em "o que causa o abandono".

**Motivo.** A pergunta antiga (antecipar, com um ano de antecedência, as escolas de abandono alto) foi respondida
duas vezes, com desenhos diferentes, e a resposta é que nenhum modelo ordenou as escolas melhor do que a régua
(o último abandono conhecido):

- **Classificação de alto risco na janela segura** (2026-11-10, execução única): **0 GANHO em 36 testes** da
  família F6 (ferramenta − régua, com Holm). Nos anos finais, todas as comparações de Recall@20% são SEM GANHO
  PRÁTICO; no ensino médio, a maioria é INCONCLUSIVO.
- **Etapa 2 do projeto anterior** (desfechos de 2021–2024, inclusive com TDI, ATU e IED): **0 de 32** testes da
  família F5 (modelo − régua) resistem ao Holm.

**Evidência:** `docs/BASELINE.md`, §3 e §4, gerado por `src/relatorios/baseline.py` a partir de
`docs/projeto_anterior/02d_testes.csv` e `docs/projeto_anterior/classificacao/03_testes.csv`.

**Alternativa descartada: continuar melhorando o modelo preditivo** (mais modelos, ajuste fino, novas réguas).
O nulo se repetiu nos dois desenhos e em todos os blocos de informação, e a janela segura não tem as variáveis que
poderiam mudar isso: TDI, ATU, IED, matrículas, escola indígena, localização diferenciada, INSE e formação docente
não existem no repositório para 2013–2018 (diagnóstico da Etapa A, nesta data). As metas M1–M12 do projeto
anterior, quase todas preditivas, ficam em `docs/ROTEIRO.md`, copiadas do arquivo, todas "a revisar".

**O artigo da disciplina de Mineração de Dados sai do repositório.** Não faz parte da pesquisa PIBIC, e não há
nada a migrar. As menções a ele saem de todos os documentos, exceto da cópia literal do roteiro antigo
(`docs/ROTEIRO.md`), que fica como foi escrita.

**As regras ficam unificadas.** O `CLAUDE.md` e a seção "As regras que não se quebram" do `CONTRIBUTING.md`
passam a ter as mesmas 12 regras, na mesma ordem e com os mesmos números; o `CONTRIBUTING.md` diz o mesmo em
linguagem simples. Mudanças de conteúdo, nos dois:

- **regra 5:** acrescenta o estudo de associação no mesmo ano (nenhum preditor posterior a t nem derivado do
  desfecho; transformações ajustadas só na parte de treino de cada dobra);
- **regra 6:** no modelo do nível de abandono da etapa no ano t, nenhuma das três taxas de rendimento daquela etapa
  e ano entra em X (identidade contábil); o TDI, quando voltar, entra declarado como parcialmente mecânico. A
  exclusão de todo o rendimento no estudo de fatores é decisão do protocolo, não regra geral;
- **regra 7:** é proibido escolher (incluir, excluir, recodificar ou transformar) variável pela relação com o
  desfecho; é permitido e esperado reportar essa relação como resultado, com a lista fixada antes no
  `docs/PROTOCOLO.md` e todas as variáveis reportadas, inclusive as nulas; ordenar a apresentação pelo efeito é
  permitido. O R² pode descrever quanto da variação é explicada, mas não escolhe modelo, variável nem limiar;
- **regra 10:** passa a incluir "toda decisão fica registrada no `docs/DECISOES.md`" (antes, a regra 10 do
  `CONTRIBUTING.md`) e o relato do resultado nulo, e diz a unidade dos anos de teste já usados: anos de DESFECHO
  2016–2019 e 2021–2024 (em ano t, 2015–2018 e 2020–2023).

**Consequência.** O `docs/PROTOCOLO.md` que está no `main` (a "Etapa 4", entrada de 2026-11-11) responde à
pergunta antiga e nunca foi executado. Ele será movido, sem apagar nada, para uma seção "Protocolo registrado, não
executado, substituído em 2026-11-14", no pull request do protocolo do estudo de fatores.

---

## 2026-11-14 — Desvio da regra 12: dois pull requests entraram no `main` sem revisão

**O que aconteceu.** Os pull requests #1 (`docs/fluxo-do-grupo`, fluxo de trabalho do grupo) e #2
(`protocolo-novo-escopo`, protocolo da Etapa 4 e esqueleto do notebook) foram mergeados no `main` pela conta
`gabsma25` em 2026-11-11, **sem nenhuma revisão registrada** no GitHub. Isso fere a regra 12 (`main` só por pull
request revisado por outra pessoa).

**Alcance.** Os dois só mudaram documentação e um notebook sem saídas. **Nada foi executado a partir deles**: a
pasta `experimentos/regressao_mlp_2013_2018/`, onde o protocolo da Etapa 4 gravaria as saídas, não existe.

**Decisão.** A partir de agora, nenhum merge entra no `main` sem a aprovação de outro integrante, também quando o
GitHub não impedir (ver `CONTRIBUTING.md`, "Quando o repositório estiver no GitHub").

---

## 2026-11-14 — Todo intervalo de anos diz a sua unidade

Onde a unidade não era óbvia, o texto passa a dizê-la:

- a regra 10, no `CLAUDE.md` e no `CONTRIBUTING.md`: anos de DESFECHO 2016–2019 e 2021–2024 (em ano t, 2015–2018
  e 2020–2023);
- a linha de 2022–2023 da tabela da janela no `dataset/DICIONARIO.md` (gerada por `src/dataset.py`), e uma nota
  logo abaixo da tabela: as justificativas são dos estudos de previsão do ano seguinte (t → t+1), e o motivo da
  janela no estudo de nível fica no `docs/PROTOCOLO.md`;
- a evidência de equivalência da entrada de 2026-11-11 acima: "a taxa de abandono por ano civil, 2013–2019", que é
  o que o `desfecho_por_ano.csv` descreve.

---

## 2026-11-14 — Dimensões de infraestrutura em proporção, linha a linha (dataset v0.2.0)

**Decisão (pesquisadora).** O dataset ganha, para cada uma das 4 dimensões de infraestrutura, a **proporção dos
itens que a escola tem** (`dim_iib_prop`, `dim_ida_prop`, `dim_idp_prop`, `dim_iep_prop`, de 0 a 1), e um índice
geral, `iie_prop`, que é a **média simples das quatro**. O estudo de fatores usa essas colunas, padronizadas dentro
do `Pipeline` com a parte de treino de cada dobra. As colunas `dim_*_zano` e `iie_zano` continuam no dataset, sem
mudança, mas **não entram no estudo de fatores**. A versão sobe para **0.2.0**.

**Motivo.** As `_zano` são padronizadas dentro do ano com a média e o desvio de **todas as escolas** daquele ano,
e o `iie_zano` usa a componente principal do ano. Numa validação cruzada agrupada por escola, isso faz a
padronização de uma escola de treino depender das escolas da dobra de validação, o que a regra 5 proíbe
("toda transformação é ajustada só na parte de treino de cada dobra"). A proporção não depende de nenhuma outra
escola, e a padronização passa para dentro do `Pipeline`.

**Definição** (`src/dataset.py`, função `proporcoes`): proporção = soma dos itens ÷ número de itens da dimensão,
com os itens de `src/estendida/05_indices_infra.DIMENSOES`. **Fica vazia se algum item da dimensão estiver vazio**
(regra 8). Isso só acontece em 2007–2011, quando o Censo não perguntava alguns itens das dependências
administrativas e pedagógicas; na janela 2013–2018 não há nenhum vazio (`testes/test_dataset.py`).

**Diferença em relação ao `05_indices_infra.py --com-prop`.** O relatório de procedência 05 (14/10/2026) já tinha
uma versão "prop", descartada como padrão por trazer a mesma informação que a `_zano` em outra escala. O motivo de
agora é outro (não usar outras escolas). A versão antiga divide pelos itens **disponíveis no ano**, e um item é
"disponível" se **alguma escola** respondeu a ele. Isso usa informação de outras escolas, e por isso ela não foi
reaproveitada como está. Nos anos em que todos os itens existem (2012 em diante), as duas coincidem exatamente
(teste `test_prop_igual_ao_05_onde_o_ano_tem_todos_os_itens`). Em 2007–2011, a proporção nova é vazia, e a antiga
usa menos itens.

**Ressalva mantida.** O relatório 05 registra quebras de pergunta no Censo (água e banheiro até 2018, projetor até
2011, biblioteca em 2007–2008). Na janela 2013–2018, a coluna de origem de cada item é a mesma em todos os anos
(`infra_fonte_artigo` = 0 em toda a janela: água e banheiro vêm das colunas substitutas), então as quebras não
caem dentro da janela.

**Alternativa descartada:** recalcular a `_zano` dentro de cada dobra. Exigiria repetir a padronização por ano e a
componente principal dentro do código do estudo, para chegar a uma escala que o `StandardScaler` do `Pipeline` já
dá a partir da proporção.

**Evidência:** `testes/test_dataset.py` (proporção da própria linha; nada muda quando metade das escolas sai da
base; igualdade com o `05_indices_infra.py` de 2012 em diante) e a comparação com a v0.1.0 lida da tag (as 44
colunas antigas são idênticas valor a valor).

---

## 2026-11-15 — Protocolo do estudo de fatores associados, escrito antes de rodar

**Decisão (pesquisadora).** O `docs/PROTOCOLO.md` é reescrito com três partes: **A**, o registro retroativo da
classificação de 2026-11-10, marcado como escrito depois da execução; **B**, o desenho padrão do projeto, que
passa a valer como regra para todo estudo novo; **C**, o protocolo do estudo de fatores associados ao nível de
abandono, escrito **antes** de qualquer execução. O protocolo da Etapa 4, nunca executado, fica guardado
inteiro no fim do arquivo, na seção "Protocolo registrado, não executado, substituído em 2026-11-14" (a
preservação byte a byte foi conferida por código ao gravar). Nada rodou nesta tarefa; a execução só acontece
depois que o protocolo entrar no `main` por pull request revisado por outro integrante.

**O que o protocolo fixa além do que já estava decidido** — valores que estavam em aberto, todos fixados sem
olhar nenhuma associação da janela:

- **bootstrap:** 5.000 reamostragens, semente 20261115; reamostragem que perde uma categoria deixa os
  coeficientes dela NA; mais de 10% de reamostragens inválidas força INCONCLUSIVO, por regra;
- **família de Holm:** uma por etapa (F7-AF e F7-EM), com as dummies de `localizacao` e `dependencia` e as
  quatro dimensões do modelo principal, mais o `iie_prop` do secundário; as dummies de `ano` ficam fora
  (controle, sem veredito);
- **margem prática: 1,0 pp sobre o efeito que decide** (diferença de categoria; efeito por item a mais nas
  dimensões; passo de 0,25 no `iie_prop`), justificada antes: 1 pp é 1 aluno a cada 100 matriculados da etapa
  deixando a escola no ano;
- **categorias de referência:** Urbana e Estadual, nas duas etapas (categorias amplas e termo natural da
  pergunta; a referência não muda o ajuste, só a leitura);
- **validação cruzada:** `GroupKFold` de 5 dobras por escola, as mesmas para os três modelos; sementes do MLP
  de 1 a 10; importância por permutação com 20 repetições, fora da dobra;
- **controle negativo com critério numérico:** desfecho embaralhado entre escolas dentro de cada ano; o ΔR²
  da validação cruzada sobre o modelo só com o ano abaixo de 0,02 para todo modelo, senão a execução para;
- **Q3 sem teste formal da diferença entre etapas** (motivo no C.11 do protocolo);
- **robustez de janela com t = 2012–2019, e não 2011–2019:** `dim_ida_prop` e `dim_idp_prop` só existem de
  2012 em diante, então 2011 não tem as quatro dimensões completas.

**A contagem de escolas do EM não é digitada (regra 3).** O pedido era declarar, antes de rodar, quantas
escolas o EM tem e se bastam. Contagem publicada é gerada por código, então o protocolo registra a expectativa
em palavras (painel bem menor, muitos INCONCLUSIVO esperados) e manda a contagem para a tabela 0
(`00_universo.csv`), gerada antes de qualquer modelo.

**Quatro ajustes da revisão da pesquisadora (2026-11-15, antes do pull request), com os motivos:**

1. **A Q1 vira ΔR² sobre um modelo só com o ano** (C.7). O R² de um modelo com as dummies de ano mistura o
   efeito do ano com o das características; o ganho sobre o modelo só com o ano é o que as características
   explicam de fato. O R² total e o do modelo só com o ano ficam relatados ao lado, para os três modelos,
   cada um contra a referência da própria classe.
2. **O controle negativo passa a olhar o ΔR², com limiar 0,02** (C.9). O embaralhamento dentro de cada ano
   preserva o nível do ano de propósito, então o R² total pode ficar alto mesmo com o código certo; o que tem
   de ir a zero é o ganho sobre o modelo só com o ano. O 0,02 é folga pequena para o ruído da validação
   cruzada e muito menor que o ganho que um vazamento real produziria.
3. **A margem prática decide no efeito por item** (C.6). O contraste 0→1 extrapola para escolas sem nenhum
   item ou com todos, que podem nem existir na janela. O veredito usa o efeito por item a mais (coeficiente ÷
   número de itens) e, no `iie_prop`, um passo de 0,25 — uma dimensão inteira a mais, já que o índice é a
   média simples das quatro. O efeito 0→1 continua relatado, sem decidir; a figura principal mostra o efeito
   que decide.
4. **Os vereditos dizem qual p e qual IC usam** (C.6). ASSOCIADO exige o p com Holm; SEM ASSOCIAÇÃO PRÁTICA
   usa o IC 95% sem correção, como nas famílias F5 e F6 dos estudos anteriores.

**Alternativa descartada:** um teste formal de interação etapa × fator para a Q3. Com o painel menor do EM o
teste teria pouco poder, e os testes a mais aumentariam a família de Holm, enfraquecendo a Q2. Se o grupo
quiser esse teste, é protocolo novo, escrito antes de rodar.

**Evidência:** o próprio `docs/PROTOCOLO.md` (seções A, B e C e a seção final preservada).

---

## 2026-11-15 — Segundo desvio da regra 12: a pilha #5 → #7 → #8 foi mergeada sem revisão, fora do `main`

**O que aconteceu.** Os pull requests #5 (`docs/novo-escopo`), #7 (`feat/dimensoes-proporcao`) e #8
(`docs/protocolo-fatores`) foram mergeados em 2026-11-15 pela conta `gabsma25`, **sem nenhuma revisão
registrada** no GitHub. Eles estavam empilhados (a base de cada um era o branch do anterior), e os branches não
foram apagados depois de cada merge; por isso o GitHub não trocou as bases para o `main`, e cada merge entrou
no branch do PR anterior. O `main` ficou no #4: a pergunta nova, o dataset v0.2.0 e o protocolo do estudo de
fatores **não estão no `main`**. Isso fere a regra 12 duas vezes (sem revisão, e o `main` não é o que o grupo
pensa que é) e repete o desvio registrado em 2026-11-14, apesar da decisão tomada lá.

**Alcance.** Nada foi executado a partir desses pull requests: o estudo de fatores não rodou com o desfecho
real, e a pasta `experimentos/fatores_2013_2018/saida/` não existe.

**Decisão.**

- O conteúdo completo dos três entra no `main` por **um pull request novo, revisado e aprovado por outro
  integrante** (este, a partir do topo da pilha). A revisão deste PR vale como a revisão que faltou ao #5, ao
  #7 e ao #8.
- **Nada de pull request empilhado daqui em diante** sem que o anterior já esteja no `main`; e o branch é
  apagado logo depois do merge, para o GitHub trocar a base dos PRs seguintes.
- O protocolo da seção C só vale como "registrado antes de rodar" depois que este PR entrar no `main`. A
  execução do estudo de fatores espera por isso **e** pela revisão independente do código contra o protocolo.

**Evidência:** `gh pr view 5 / 7 / 8` (base de cada PR, `mergedBy`, lista de revisões vazia); `git log
origin/main` termina no merge do #4.

---

## 2026-11-15 — As colunas `_zano` do dataset são gravadas com 9 casas decimais

**Decisão (pesquisadora, com o ajuste de método abaixo).** O `src/dataset.py` grava as cinco colunas `_zano`
(`dim_iib_zano`, `dim_ida_zano`, `dim_idp_zano`, `dim_iep_zano`, `iie_zano`) arredondadas a 9 casas decimais
(`CASAS_ZANO`), para o `dataset/escolas_rr_v0.2.0.csv` ser o mesmo arquivo em qualquer máquina. As demais
colunas de ponto flutuante não são arredondadas. A versão continua 0.2.0 (não lançada).

**Motivo.** O `iie_zano` é a componente principal das quatro dimensões, calculada pelo numpy/LAPACK, e a ordem
das operações de ponto flutuante muda entre plataformas: ele difere na 15ª casa decimal entre Windows e Linux
(diferença máxima medida pela pesquisadora, `RUIDO_PLATAFORMA` em `src/dataset.py`). Por isso o
`test_regerar_da_o_arquivo_versionado` falhava fora da máquina de quem gerou o arquivo, e o `rodar_tudo.py`
deixava o dataset modificado no `git status`.

**Por que 9 casas, e não 12 algarismos significativos (o pedido original).** Arredondar não garante, sozinho, o
mesmo arquivo: um valor que esteja mais perto de uma fronteira de arredondamento do que a diferença entre as
plataformas pode ir para lados diferentes em cada máquina. Medido por código antes da escolha: com 12
algarismos significativos, e também com 12 casas decimais, há valores do `iie_zano` muito mais perto de uma
fronteira do que essa diferença; com 9 casas, todos os valores ficam a uma distância bem maior. O
`testes/test_dataset.py::test_zano_longe_das_fronteiras_de_arredondamento` exige que cada valor fique a pelo
menos 10 vezes essa diferença de uma fronteira (`FOLGA_MINIMA`). Se um dado novo cair perto de uma fronteira, o
teste falha antes de o arquivo divergir entre máquinas. A escolha usou só os valores das `_zano`, que nenhum
estudo do projeto usa, e nenhuma relação com o desfecho.

**Por que só as `_zano`.** As outras colunas de ponto flutuante vêm da leitura de texto do INEP ou de contas
IEEE simples (diferença, divisão por um inteiro, média de quatro termos), que dão o mesmo resultado em qualquer
máquina. O teste confere que o arredondamento não as toca.

**Teste de equivalência.** O `testes/test_equivalencia.py::test_base_atual_identica` comparava a base com
igualdade exata. Agora compara o `IIE_zano` com tolerância absoluta de 1e-12 (`TOLERANCIA_PLATAFORMA`), muito
acima da diferença entre plataformas e muito abaixo de qualquer diferença com significado. É a única coluna
com diferença observada; as outras continuam exatas.

**Consequência.** Das 44 colunas da v0.1.0, as 39 que não são `_zano` continuam idênticas valor a valor; as 5
`_zano` diferem da v0.1.0 só pelo arredondamento (menos de meio passo de 9 casas). O estudo de fatores não usa
nenhuma `_zano` (`docs/PROTOCOLO.md`, C.3).

**Evidência:** `testes/test_dataset.py` (regeração byte a byte, folga às fronteiras de arredondamento) e
`testes/test_equivalencia.py`.

---

## 2026-11-15 — A etapa 01 roda num clone limpo, sem `dados/origem/` (issue #6)

**Decisão.** Sem a pasta `dados/origem/indicadores/`, que fica fora do git (regra 2), a etapa 01
(`src/estendida/01_tx_rend_bruto.py`) não para mais com `FileNotFoundError`. Ela avisa que não há zips e lê
cada ano do cache versionado em `dados/cache/tx_rend/`, o mesmo caminho que já seguia para qualquer ano sem
zip. Com isso, o `python rodar_tudo.py` funciona num clone limpo, como o `README.md` diz.

**Alternativa descartada:** criar as pastas vazias automaticamente. Seria escrever em `dados/origem/`, que é
somente leitura (regra 1), e esconderia o fato de que nenhum zip foi conferido.

**Evidência:** `testes/test_etapa01_sem_origem.py` (sem a pasta, nenhum zip e nenhum erro; o cache cobre todos
os anos da etapa) e o `rodar_tudo.py` num clone limpo, sem `dados/origem/`.

---

## 2026-11-15 — PROTOCOLO: o que acontece depois da execução, e os títulos do protocolo preservado

**Decisão (pesquisadora).**

- O `docs/PROTOCOLO.md` ganha a **seção D, "Depois da execução"**, que vale para todo estudo. Ela diz por que a
  execução é única e o que acontece depois: as saídas ficam congeladas; tudo é relatado como saiu; um erro
  descoberto depois só justifica nova execução se for um defeito em relação ao protocolo, registrado antes, com
  os dois resultados relatados lado a lado; mudar o desenho depois de ver o resultado é estudo novo; e o controle
  negativo reprovado é a exceção, porque a execução para antes de qualquer associação real ser vista. Nada no
  desenho da seção C muda.
- Os títulos do protocolo da Etapa 4, preservado no fim do arquivo, descem dois níveis (`#` → `###`), para não
  ficarem no mesmo nível das seções A a D. O texto não muda. A entrada de 2026-11-15 acima (o protocolo do
  estudo de fatores) dizia que o protocolo antigo estava preservado byte a byte; a partir daqui, ele está
  preservado **com o texto igual e os títulos rebaixados**, e isso deixa de ser uma conferência feita uma vez:
  o `testes/test_protocolo.py` confere o texto contra o original (`a56482d`) a cada execução dos testes.

**Evidência:** `testes/test_protocolo.py`.

---

## 2026-11-15 — Conferência do código do estudo de fatores contra o protocolo, e o que foi corrigido

**O que foi feito.** O `experimentos/fatores_2013_2018/fatores.py` foi conferido contra as seções B, C e D do
`docs/PROTOCOLO.md`, seção por seção, antes de qualquer execução. **Essa conferência não foi independente:** foi
feita pelo mesmo autor do código (o assistente de programação, na mesma sessão). Ela não substitui a revisão do
código por outro integrante, que continua sendo condição para a execução.

**Corrigido antes de qualquer execução** (um commit cada, todos com teste em `testes/test_fatores.py`):

1. **As saídas não podiam entrar no git**, porque o `.gitignore` ignorava toda pasta `saida/`. Há agora uma
   exceção para `experimentos/fatores_2013_2018/saida/`. Com a pasta versionada, a trava "recusa se `saida/`
   existe" vale em qualquer clone depois que as saídas forem commitadas.
2. **A figura principal trocava os rótulos** quando o AF e o EM tinham fatores diferentes (a regra dos 30 pode
   excluir categorias diferentes em cada etapa): os dois painéis compartilhavam o eixo y. Cada painel tem
   agora o seu eixo.
3. **O commit do cabeçalho podia não ser o código que rodou.** `executar()` recusa rodar com a árvore do git
   suja, antes de calcular qualquer coisa, e o cabeçalho leva o commit e o branch.
4. **A robustez da janela 2012–2019 reaplicava a regra dos 30**, contra o C.13 (a tabela 0 é o único lugar).
   Ela usa agora as categorias de `dependencia` da tabela 0 da janela principal, e as linhas retiradas vão
   para o `08_robustez.csv`.

**Corrigido junto, sem efeito em nenhum veredito:** o `07_controle_negativo.csv` ganhou os R² do desfecho
embaralhado; a tabela 0 ganhou a contagem por ano; o `02_correlacao.csv` passou a incluir as dummies das
categóricas; a contagem de previsões fora de [0, 100] deixou de truncar a média das sementes e existe também
dentro da amostra; a figura leva o commit, o branch e o sha256 do dataset.

**Conhecidas, não corrigidas; não mudam vereditos:**

- **A comparação da C.8 não sai pronta num arquivo.** O `06_permutacao.csv` traz as importâncias e o
  `04_fatores.csv` os efeitos padronizados; pôr as duas ordens lado a lado fica para o relatório, que só
  reorganiza os dois arquivos (regra 4).
- **A família de Holm é calculada sobre os p que existem.** Um coeficiente sem nenhuma reamostragem válida
  sairia da família, e o `n_familia` do 04 ficaria diferente do `familia_f7` da tabela 0. Depois da regra dos
  30 isso é praticamente impossível; se acontecer, as duas contagens ficam nos arquivos e a diferença é
  relatada.
- **O modelo só com o ano passa por outro caminho numérico.** Com só as dummies de ano, o pré-processamento
  devolve uma matriz esparsa, e a regressão linear e a Ridge usam outro algoritmo para ela. A diferença, medida
  em dados sintéticos, fica na última casa de ponto flutuante das previsões e não aparece no R².
- **`executar()` pode ser chamada direto**, sem passar pelo `main()` e pela recusa de `saida/` existente. A
  recusa da árvore suja vale nos dois caminhos; a de `saida/` existente, só na linha de comando.

**Leituras que o código fez onde o protocolo não é explícito** (ficam registradas; nenhuma muda veredito): do
modelo secundário só o `iie_prop` é relatado; o IC da importância por permutação junta sementes, dobras e
repetições; na janela 2012–2019, o ano de referência das dummies é 2012.

**Seção D do protocolo.** Acrescentado o item 6, a falha técnica no meio da execução: as saídas parciais são
guardadas numa pasta separada, a falha é registrada aqui e a execução é refeita com o mesmo commit; como as
sementes são fixas, os números são idênticos.

**Evidência:** `testes/test_fatores.py` (rótulos da figura com exclusões diferentes, recusa da árvore suja,
robustez com as categorias da tabela 0, colunas das saídas) e `git check-ignore` na pasta de saídas.

---

## 2026-11-15 — Revisão do João no PR #9: o que mudou no protocolo antes do merge

**A revisão.** O João revisou o pull request #9 em 2026-11-15: clone limpo, `rodar_tudo.py` verde, leitura do
código do dataset e das seções C e D do protocolo. Ele pediu quatro ajustes de texto na seção C antes do
merge, porque depois dele o desenho do estudo congela. O texto dele está, literal, em
`docs/revisoes/2026-11-15_joao_pr9.md`. Todos os pedidos usam só contagens e relações entre preditores, sem o
desfecho (regra 7). Nenhum ajuste exigiu rodar o estudo.

**Decisões (pesquisadora), item por item:**

1. **Regra dos 30 (C.3): opção (a) do revisor.** Uma categoria de `dependencia` só entra na regressão da
   etapa com pelo menos 30 escolas-ano **e** pelo menos 10 escolas distintas; senão sai, com as duas contagens
   na tabela 0. Motivo: o bootstrap sorteia escolas, então a regra tem de contar na unidade da inferência; uma
   categoria que passa nas escolas-ano com poucas escolas apoiaria o coeficiente em poucas unidades.
   Consequência esperada, pelas contagens do revisor: no EM, a Federal e a Municipal saem, e a rede deixa de
   ser fator nessa etapa. **Alternativa descartada:** a opção (b), manter a regra e avisar no C.12 que o
   coeficiente sairia INCONCLUSIVO; ela deixaria na família de Holm um teste que já se sabe sem apoio.
2. **Referência Urbana (C.3).** O motivo passa a ser só "o fator de interesse é ser rural"; a localização
   urbana não é a categoria mais ampla. Para Estadual, "categoria ampla" continua valendo. O ajuste do modelo
   não muda.
3. **Colinearidade (C.12 e C.14).** Fica registrada antes de rodar a expectativa de muitos INCONCLUSIVO nas
   dimensões de infraestrutura nas duas etapas, e a leitura: cada efeito vale com os outros constantes; a
   divisão entre localização e infraestrutura é instável; "Rural" soma escolas indígenas e de difícil acesso,
   ainda sem marcação no dataset (meta M1).
4. **`OneHotEncoder(handle_unknown="ignore")` (C.7).** Declarado, para uma categoria ausente no treino de uma
   dobra não parar a execução única.

**O que o revisor viu antes da execução.** Durante a revisão, o João olhou, por engano, a **média de
`abandono_t` por etapa × localização na janela 2013–2018** (um comando de conferência que incluiu o desfecho).
**Nenhuma decisão acima se baseou nisso:** os itens 1 a 4 usam só contagens e relações entre preditores, e a
escolha da opção (a) no item 1 é sobre a rede, não sobre a localização. Fica registrado no mesmo espírito dos
"anos já olhados" (C.2): uma pessoa do grupo conhece essas médias antes da execução, e nada no desenho pode
mudar por causa delas.

**Fora do protocolo.** O `README.md` passa a pedir Python 3.12 ou mais recente (o revisor rodou em 3.14). As
outras duas notas opcionais do revisor (o rótulo `GUSTAVO:` no cabeçalho do pipeline e o aviso da etapa 01 para
quem quer reconstruir o cache a partir dos zips) ficam para depois.

**Evidência:** `docs/revisoes/2026-11-15_joao_pr9.md` e os commits de texto do protocolo neste pull request.

---

## 2026-11-15 — Execução do estudo de fatores antes da aprovação formal do PR #9

**Decisão (pesquisadora).** Execução do estudo de fatores no branch `integracao/gabriela`, antes da aprovação
formal do PR #9 e sem PR do código. O protocolo recebeu a revisão do João, com os comentários aplicados
(commits `76e2256` a `15181ae`), mas ainda não a aprovação. O código foi conferido pela autora-agente (revisão
não independente) e por testes com dados sintéticos em Windows (Claude Code) e em Linux (Claude, sessão de
chat, no commit `9678207`: `rodar_tudo.py` com 109 aprovados e 2 pulados, por falta dos zips do INEP;
`test_fatores.py` com 21 de 21; `git status` limpo depois de regerar).

**Desvio registrado.** Isso desvia da regra 10 e da seção B.6 do `docs/PROTOCOLO.md` (o protocolo no `main`
por pull request revisado antes de qualquer execução) e da regra 12.

**Consequência.** A partir desta execução, o protocolo fica congelado: a aprovação do #9 passa a confirmar o
que rodou, e qualquer mudança pedida depois vira um estudo novo, com protocolo próprio.

**Data pública do protocolo.** O protocolo não foi depositado em repositório externo: ele tem data pública só
pelo push no GitHub (branches `docs/leva-pilha-ao-main` e `integracao/gabriela`), feito antes da execução.

---

## 2026-11-18 — Merge direto da correção do `test_sem_executar_nada_roda` (desvio da regra 12)

**O que aconteceu.** Depois do commit `c2b9adb` (saídas do estudo de fatores versionadas), a pasta
`experimentos/fatores_2013_2018/saida/` existe em todo clone, e o `testes/test_fatores.py::test_sem_executar_nada_roda`,
que conferia a pasta real, falhava em qualquer máquina (os "109 aprovados" de 2026-11-15 são do commit `9678207`,
anterior às saídas). O teste passou a usar uma pasta temporária, como o `test_executar_recusa_saida_existente`
(commit `62e66a9`). O Gustavo mergeou direto na `integracao/gabriela`, sem revisão, em 2026-11-18.

**Alcance.** Duas linhas num teste; o que ele confere não mudou. `python rodar_tudo.py` no Windows, sem os zips:
109 aprovados, 2 pulados.

---

## 2026-11-18 — Os zips de 2007–2018 entram no manifesto (registro, depois conferência)

**O que faltava.** Na migração (2026-11-11), o `src/aquisicao.py` veio do `abandono-escolar`, onde o manifesto só
tinha 2019–2025; de 2007–2018 veio só o cache do Gustavo (`dados/cache/`). A aquisição só obtém o que o manifesto
lista, com sha256, e não havia como pôr um ano novo nele. Por isso 2007–2018, que contêm a janela de todas as
análises, "não podem ser reverificados" (`dataset/DICIONARIO.md`), e nenhuma coluna nova do Censo pode entrar
nesses anos (o cache só tem as 22 colunas dos 18 itens).

**Decisão (Gustavo).** O `src/aquisicao.py` ganha o registro de anos novos, em dois passos com revisão no meio:

1. `python -m src.aquisicao --registrar 2007-2018 --baixar` (ou `--origem-local PASTA`): raspa as páginas do INEP
   (microdados e aba de cada ano de tx_rend), baixa os zips de microdados e de rendimento por escola dos anos que o
   manifesto ainda não tem para `dados/cache_download/registro/` (nunca para `dados/origem/`), grava a proposta de
   linhas em `dados/cache_download/registro/manifesto_proposto.csv` e acrescenta os links novos ao
   `src/fontes_inep.csv`, sem mexer nas linhas existentes;
2. depois de revisada a proposta, `python -m src.aquisicao --aplicar-registro` acrescenta as linhas ao
   `dados/MANIFEST.csv`, antes das de 2019 da mesma tabela; recusa tudo se um arquivo já registrado vier com outro
   sha256.

Depois disso, a aquisição normal (`--baixar` ou `--origem-local`) leva os zips para `dados/origem/` conferindo o hash,
como para 2019–2025. O nome registrado é o publicado pelo INEP, que muda de padrão ao longo dos anos
(`tx_rendimento_escolas_2007.zip`, `TX_REND_ESCOLAS_2018.zip`, `tx_rend_escolas_2019.zip`, conferidos nas abas do
INEP nesta data); a tabela do zip sai do nome pela mesma regra do `01_tx_rend_bruto.mapear_zips_escola`.

**Os links de 2007–2018 no fallback estático.** Na primeira execução (2026-11-18), o `www.gov.br` derrubou todas
as conexões do script (ConnectionResetError 10054), e a raspagem não achou nenhum link. O registro passou a usar o
fallback estático para o que a raspagem não achar, como a aquisição normal já fazia, e o `src/fontes_inep.csv`
ganhou os 24 links: os 12 de microdados lidos da captura de 2026-09-30 (`testes/fixtures/html/`, a mesma página
real, com o "Atualizado em" de cada item); os 12 de rendimento por escola lidos nas abas de cada ano do INEP em
2026-11-18, pelo assistente, fora do script. Os nomes mudam quase todo ano (`tx_rendimento_escola_2008.zip`,
`tx_rendimento_escolas_2010_19082011.zip`, `tx_rendimento_escolas_2011_2.zip`, `TAXA_REND_2016_ESCOLAS.zip`). Um
link errado não passa despercebido: o download falha ou a conferência do conteúdo diverge.

**Registrar não é conferir.** O sha256 só garante que o arquivo é o mesmo daqui em diante. A conferência do conteúdo
é feita por:

- `python src/estendida/conferir_cache.py`: refaz numa pasta temporária, com as mesmas funções das etapas 01 e 03, o
  cache de cada ano que tem zip, e compara com `dados/cache/` célula a célula (e a estatística nacional do Censo);
  grava `saida/relatorios/conferencia_cache.csv` e nunca escreve em `dados/cache/`;
- o teste 03 (`--completo`), que já lia os zips de 2007–2018 quando presentes (relatório 04, §4: 19 de 19 anos em
  14/10/2026). O `testes/test_validacoes.py` passa a exigir a frase com os anos que tiverem zip, e não só 2019–2025.

**Alternativas descartadas:** gravar o sha256 direto no manifesto ao baixar (o manifesto deixaria de ser a
especificação revisada do que se obtém); copiar à mão os zips antigos do projeto anterior sem registro (repetiria a
situação de outubro, com 179 zips fora do manifesto).

**O INEP recusou o Python; o download foi feito com o `curl.exe`.** Em 2026-11-18, também o
`download.inep.gov.br` derrubou toda conexão do `requests`, com qualquer User-Agent (diagnóstico com o do projeto e
com o de um navegador), mas aceitou o navegador e o `curl.exe` do Windows. Os 38 zips de 2007–2025 foram baixados
do zero com o `curl.exe`, a partir dos links do `src/fontes_inep.csv`, para `dados/cache_download/inep_curl/`, e
entraram pelo caminho normal: `--registrar 2007-2018 --origem-local`, `--aplicar-registro` e `--origem-local`. O
`--baixar` do projeto continua dependente do `requests` e, enquanto o INEP recusar o Python, falha: levar o download
para o `curl.exe` dentro do `src/aquisicao.py` fica como pendência.

**Resultado (2026-11-18, Windows, Gustavo).**

- **Registro:** 24 linhas novas no `dados/MANIFEST.csv` (2007–2018, microdados e rendimento por escola), o
  sha256 de cada zip baixado nesta data.
- **2019–2025 conferem com o manifesto de setembro:** os 14 zips baixados de novo têm o mesmo sha256 registrado pela
  Gabriela em 2026-09-02/15 (`adquirir`: 38 copiados, 0 faltando). O INEP não mudou esses arquivos desde então.
- **O cache é o dos zips:** `src/estendida/conferir_cache.py`, 19 anos × 2 etapas, **38 de 38 idênticos**
  (rendimento por escola da etapa 01; colunas cruas de RR e estatística nacional da etapa 03), em
  `saida/relatorios/conferencia_cache.csv`.
- A ressalva de procedência (`dataset/DICIONARIO.md`, gerada por `src/dataset.py`, e `README.md`) passa a dizer
  que os 19 anos foram conferidos contra os zips originais.

**Evidência:** `testes/test_registro.py` (servidor falso com o layout real das páginas; nomes reais de 2007, 2014
e 2018; página HTML no lugar do zip; idempotência; linhas existentes do manifesto e do fallback intocadas, byte a
byte) e `testes/test_conferir_cache.py` (zip sintético do Censo: idêntico, célula alterada, estatística nacional
alterada; `dados/cache/` não muda).

---

## 2026-11-18 — As saídas do levantamento das colunas do Censo entram no git

**O que é.** `experimentos/levantamento_colunas_censo/levantar.py` lê só os cabeçalhos dos CSV dos zips do Censo
Escolar 2007–2025 (`dados/origem/censo/`) e lista as colunas de cada ano e as candidatas a características novas
(início de M1/M6). Não lê nenhum valor nem o rendimento: não olha o desfecho (regra 7).

**Decisão (Gustavo).** A pasta `experimentos/levantamento_colunas_censo/saida/` ganha uma exceção no `.gitignore`,
como a `experimentos/fatores_2013_2018/saida/`, e a pasta inteira é versionada: `arquivos.csv`, `candidatas.csv`,
`colunas_outras_2025.csv`, `colunas_por_ano.csv` e `resumo.txt`.

**Por quê.** O levantamento só se regera com os zips do INEP, e hoje só o Gustavo os tem: o INEP recusa as
conexões do Python (`--baixar` falha; ver a entrada "Os zips de 2007–2018 entram no manifesto"). Sem os arquivos
no git, o grupo não teria como ver o resultado antes de decidir quais colunas entram no dataset.

**O que não é.** Não é a escolha das colunas: essa é do grupo, por pertinência, cobertura e estabilidade, e fica
registrada aqui quando for feita. "Existe no cabeçalho" não é "foi coletada"; essa conferência é um segundo passo,
só para as candidatas escolhidas.

**Evidência:** `experimentos/levantamento_colunas_censo/README.md` e os arquivos em `saida/`.

---

## 2026-11-18 — Pequenas correções de texto e de formato

**O que mudou (Gustavo).**

- O cabeçalho do `src/estendida/99_pipeline.py` passa a imprimir "Raiz do projeto:" no lugar do rótulo `GUSTAVO:`,
  resto da migração (nota opcional do João no PR #9, que tinha ficado para depois). Só muda o texto impresso.
- O `experimentos/fatores_2013_2018/README.md`, o `CHANGELOG.md` e o índice `experimentos/README.md` deixam de dizer
  que o estudo de fatores não foi executado: ele rodou uma vez em 2026-11-15 (entrada desse dia).
- O `README.md` diz quanto o `rodar_tudo.py` leva com e sem os zips do INEP.
- O levantamento das colunas do Censo grava as saídas com quebra de linha LF, como o `.gitattributes` as guarda no
  git; antes gravava CRLF, e regerar deixaria a pasta versionada aparecendo como modificada.

**Evidência:** os próprios arquivos; `python rodar_tudo.py` verde depois das mudanças.

---

## 2026-11-19 — Cache completo do Censo: todas as colunas de RR, extraídas uma vez

**O problema.** O cache do Censo (`dados/cache/censo/`) só guarda as 22 colunas dos 18 itens de infraestrutura.
Qualquer coluna nova (metas M1/M6 do `docs/ROTEIRO.md`; candidatas em `experimentos/levantamento_colunas_censo/`)
exigiria voltar aos zips, que hoje só o Gustavo tem, e mexer no 03, que é o único que lê o Censo. Cada grupo novo
de colunas seria mais uma leitura dos ~2 GB de zips e mais uma mudança na sequência do pipeline.

**Decisão (Gustavo, 2026-11-19).** Extrair uma única vez, de cada zip registrado no `dados/MANIFEST.csv`, as linhas
de Roraima com TODAS as colunas de TODAS as tabelas (inclusive as seis de 2025 e o suplemento de cursos técnicos de
2023–2024), para `dados/cache/censo_completo/`, por um script novo fora do fluxo normal,
`src/estendida/extrair_censo.py`. É o primeiro passo da reorganização do pipeline em grupos de colunas; os outros
(a pasta de grupos com o de infraestrutura, e o primeiro grupo novo) vêm em pull requests próprios.

- **Valores como texto, exatamente como no CSV.** O cache não converte, não troca `''` ou `'--'` por ausente e não
  renomeia (regra 1); a conversão e a regra de ausente (regra 8) ficam com quem usa a coluna.
- **Contagens nacionais por coluna** (`{ano}_{tabela}_nacional.csv`: linhas, preenchidas, numéricas, iguais a 1,
  maiores que 0). A regra de "coletada" do 03 (alguma escola do Brasil com valor 1) serve para indicadores 0/1;
  contagens precisam de outra, e cada grupo declara a sua. Com o Brasil todo contado agora, nenhum grupo precisa
  voltar aos zips.
- **Recorte por `SG_UF == "RR"`**, a mesma regra do 03; todas as tabelas têm `SG_UF` e `CO_ENTIDADE`
  (`experimentos/levantamento_colunas_censo/saida/`).
- **O cache antigo de 22 colunas fica onde está e não muda:** o 03, a base e os resultados publicados continuam
  lendo dele. Trocar o 03 para ler o cache completo é o passo seguinte, com teste de equivalência byte a byte.
- **Só leitura depois de gravado.** O script confere o sha256 de cada zip contra o manifesto antes de ler, grava
  numa pasta `.parcial` e só a renomeia para `dados/cache/censo_completo/` se todos os anos deram certo; recusa
  gravar se a pasta já existe. Para refazer e comparar, `--destino PASTA_NOVA`. Cada arquivo gravado entra no
  `dados/MANIFEST.csv` (estágio `cache`, tabela `cache_censo_completo`) com o sha256; o nome-base inclui o ano
  (`2013_escola.parquet`), porque o manifesto identifica arquivos pelo nome-base.

**Alternativas descartadas:** acrescentar colunas ao cache de 22 (regravaria `dados/cache/censo/`, contra a regra 1,
e mudaria os arquivos que os resultados publicados usam); guardar só as colunas candidatas do levantamento (cada
escolha nova do grupo voltaria aos zips); guardar o Brasil inteiro (centenas de MB no git, sem uso: o estudo é de RR).

**Aprovação.** O cache entra em `dados/cache/`, que pede o aval do grupo; o aval é a revisão do pull request.

**Evidência:** `testes/test_cache_censo_completo.py`: nos 19 anos, o cache completo tem as mesmas escolas, na mesma
ordem, e os mesmos valores nas 22 colunas do cache antigo, e as mesmas contagens nacionais (`n_numerico` e `n_um`
contra `nao_nulo` e `uns`); só linhas de RR, tudo texto; todo arquivo da pasta está no manifesto com o sha256 certo.
O extrator é testado com zips sintéticos (texto preservado, contagens, recusa de pasta existente).

---

## 2026-11-19 — O pipeline passa a acrescentar grupos de colunas numa etapa única

**O problema.** Depois da base longitudinal (02), o pipeline era uma sequência fixa só para a infraestrutura: o 03
lia os zips (ou o cache de 22 colunas) e montava os 18 itens, o 04 juntava com a base e o 05 calculava os índices.
Cada conjunto novo de colunas (metas M1/M6) exigiria mais um script na sequência, mexendo em todos os seguintes, e
voltaria aos zips.

**Decisão (Gustavo, 2026-11-19).** O 03, o 04 e o 05 viram:

- **`src/estendida/03_grupos.py`**, a etapa única que lê o 02b e, para cada grupo listado em
  `src/estendida/grupos/ligados.txt`, junta as colunas do grupo (`how="left"` a partir da base, `validate="1:1"`) e
  as derivadas, se houver; grava `saida/base_atual.parquet`;
- **`src/estendida/grupos/infraestrutura.py`**, o primeiro grupo: a regra de fonte do antigo 03 (os 18 itens e o
  `INFRA_FONTE_ARTIGO`) e o método do antigo 05 (dimensões e IIE `_zano`, `INFRA_ITENS_COMPLETOS`), sem mudança,
  lendo o cache completo do Censo (`dados/cache/censo_completo/`, entrada anterior) no lugar do de 22 colunas.

O 01 e o 02 não mudam de papel. A sequência fica 01 (rendimento) → 02 (base longitudinal) → 03 (grupos).

**O contrato dos grupos** (`src/estendida/grupos/README.md`), conferido pelo `03_grupos.py`, que para com erro:
um grupo só acrescenta colunas (nenhum nome repetido, nenhuma linha a mais ou a menos, chave única); `extrair` lê só
o cache do Censo, nunca o rendimento (regras 6 e 7); `derivar` recebe só `ANO` e as colunas do próprio grupo. Grupo
novo calcula linha a linha (regra 5); o z-score no ano da infraestrutura usa as outras escolas da base e fica como
herança declarada, porque mudá-lo mudaria os resultados publicados.

**A lista de grupos ligados é versionada e faz parte da versão do dataset.** Fica num arquivo, não numa opção da
linha de comando, para que dois datasets com o mesmo nome não tenham grupos diferentes. Ligar ou desligar um grupo é
decisão registrada aqui, por pull request; para um estudo, a lista é fixada no `docs/PROTOCOLO.md` antes de rodar.
Nunca se liga ou desliga um grupo olhando o resultado (regras 7 e 10).

**Nada muda nos resultados.** Com só a infraestrutura ligada, a `saida/base_atual.parquet` saiu idêntica byte a byte
à da sequência antiga (mesmo sha256), e a tabela do grupo é idêntica ao antigo `03_censo_features.parquet`; os
relatórios `fontes_features_censo.csv` e `indices_infra_parametros.json` também saíram idênticos. O `docs/PROTOCOLO.md`
(congelado desde 2026-11-15) cita `src/estendida/05_indices_infra.py` para o `_zano`: o código citado está, sem
mudança, em `src/estendida/grupos/infraestrutura.py`.

**O que mudou junto.**

- Os arquivos intermediários `03_censo_features.parquet`, `04_base_com_censo.parquet` e `05_base_com_indices.parquet`
  dão lugar a `03_grupo_infraestrutura.parquet` e `03_base_com_grupos.parquet`. Os validadores (`testes/01`, `02` e
  `03_validar_*`) leem os arquivos novos; o "04" deles é a base com os itens, sem as derivadas. A seção E do
  `testes/03_validar_censo_pos04.py` continua recomputando a regra de fonte a partir do cache ANTIGO de 22 colunas,
  agora como conferência independente da fonte que o pipeline lê.
- O `src/estendida/conferir_cache.py` confere o cache completo do Censo contra os zips (todas as tabelas e as
  contagens nacionais), refazendo-o numa pasta temporária com o `extrair_censo.py`.
- `--force` e `--force-year` do `01_tx_rend_bruto.py` regravavam `dados/cache/tx_rend/` a partir dos zips, contra a
  regra 1; passam a ser recusados, e o `99_pipeline.py` perde o `--force`. A conferência contra os zips é a do
  `conferir_cache.py`.
- O `--com-prop` do antigo 05 não vira opção do grupo (o pipeline nunca o usava): continua em
  `infraestrutura.calcular(..., com_prop=True)`, que o `testes/test_dataset.py` usa como implementação independente.
- Limpeza: caminhos antigos nos comentários (`gustavo/`, `programas/`), `RAIZ` definido duas vezes no 01 e no 02.

**Alternativas descartadas:** manter o 03, o 04 e o 05 e só acrescentar scripts depois do 05 (cada grupo novo
mudaria a sequência e reabriria os zips); escolher os grupos por opção de linha de comando (datasets diferentes
com o mesmo nome).

**Evidência:** `testes/test_grupos.py`: nos 19 anos, o grupo infraestrutura lendo o cache completo dá o mesmo
quadro e as mesmas fontes que o antigo 03 lendo o cache de 22 colunas; o contrato com grupos sintéticos (acrescenta
sem mudar a base, recusa chave repetida, coluna repetida, colunas não declaradas e `derivar` fora do contrato;
`derivar` não vê o rendimento). O `testes/test_equivalencia.py` (base célula a célula contra o projeto anterior) e o
`testes/test_dataset.py` (dataset byte a byte) passam sem mudança.

---

## 2026-11-20 — Inventário das colunas para escolher os grupos

**O que é (Gustavo).** O primeiro passo da escolha dos grupos de colunas novos:
`experimentos/selecao_grupos/01_inventario_colunas.py` lista todas as colunas do Censo de Roraima, ano a ano
(2007–2025, todas as tabelas), com a presença no layout, a coleta no Brasil, o preenchimento nas escolas de RR em
atividade e a descrição, as categorias e as notas do dicionário de dados do INEP (as 5 versões que vêm nos zips). As
saídas são CSV e um `LEIA_ME.md` gerado pelo script, feitos para outra pessoa ou outra IA ler e propor os grupos.

**Decisões dentro do script.**

- **Coletada** = alguma escola do Brasil com valor no ano (numérica > 0, ou texto não vazio), medida no cache
  completo; a marca "s" do dicionário do INEP vem ao lado, e o número de discordâncias sai no `LEIA_ME.md`.
- **Preenchimento em RR só nas escolas em atividade** (`TP_SITUACAO_FUNCIONAMENTO` = 1): de 2022 em diante o INEP
  deixa em branco as escolas paralisadas ou extintas, que não têm rendimento.
- **Sem desfecho.** O script não lê o rendimento, o dataset nem a base; a escolha dos grupos não pode olhar a relação
  com o abandono (regra 7).

**A pasta `saida/` é versionada** (exceção no `.gitignore`, como a do levantamento): o dicionário só se regera com
os zips, que hoje só o Gustavo tem.

**A escolha dos grupos não é feita aqui.** A IA ou a pessoa propõe; o grupo decide por pertinência, cobertura,
estabilidade e redundância, registra aqui e, para um estudo, fixa no `docs/PROTOCOLO.md` antes de rodar.

**O painel de resultados fica de lado.** O notebook `05_painel_resultados.ipynb` (proposto em 2026-11-19, não
versionado) foi guardado num stash local (`git stash list`, "painel de resultados"); o gráfico de fatores dele usava
a escala 0→1 e precisa ser trocado pelo efeito que decide antes de voltar.

**Evidência:** `experimentos/selecao_grupos/saida/LEIA_ME.md`.

---

## 2026-11-20 — Estudo E (v0): as colunas do Censo entram brutas, por filtro mecânico, num estudo exploratório

**Decisão (Gustavo).** Para ter um resultado ainda nesta data, as colunas do cache completo do Censo entram nos
modelos **brutas**, escolhidas por um filtro mecânico de saúde que só olha preditores (`docs/PROTOCOLO.md`, E.2):
- prefixo `QT_`/`IN_`;
- fora as proibidas e as 22 colunas-fonte da infraestrutura;
- ≥ 95% preenchidas em cada ano de 2013 a 2024;
- inteiras e não negativas, `IN_` só 0/1;
- nenhum valor com mais de 99% em 2013–2018.

Resultado: 124 colunas, lista fechada no protocolo. As seis faixas de idade das matrículas ficam declaradas
parcialmente mecânicas (regra 6). Nenhuma coluna calculada é criada: só a infraestrutura (18 → 4 → 1) tem base
em artigo publicado. As outras derivações, como razões e transformações, ficam para depois da revisão coluna a
coluna.

**Motivo.** A mudança de pergunta de 2026-11-14 registrou que a janela não tinha matrículas, escola indígena nem
dados de docentes. O cache completo do Censo (2026-11-19) passou a ter essas colunas. A revisão coluna a coluna
pela metodologia de grupos (`docs/notas/METODOLOGIA_GRUPOS.md`) leva semanas. A versão 0 mede, com as colunas
como estão, se elas mudam o quanto se explica e a lista de risco.

**Travas, aceitas pelo Gustavo:**
1. o filtro é mecânico e decidido antes, sem desfecho (regra 7);
2. há protocolo antes de rodar, e o estudo é marcado exploratório (anos já vistos);
3. o desfecho de 2025 fica fechado;
4. a limpeza que vem depois é guiada pela qualidade do dado e nunca por "a métrica subiu". O desempenho só volta
   a ser medido em marcos com protocolo próprio.

**Desvio da regra B.6 e da regra 12.** O protocolo vai para o branch `estudo/e-censo-bruto-v0` por commit e
push antes da execução, o que lhe dá data pública. Ele não passa antes por pull request revisado. A revisão
acontece no pull request da execução.

**Alternativa descartada:** revisar cada grupo de colunas antes de qualquer modelo. É o caminho certo para a
versão final e continua sendo o próximo passo, mas não cabe no prazo.

**Consequências:**
- o `dataset/escolas_rr_v0.2.0.csv` e o `src/estendida/grupos/ligados.txt` não mudam;
- o grupo `censo_bruto_v0` existe, mas não é ligado;
- os resultados dos estudos anteriores continuam valendo.

**Evidência:** `docs/PROTOCOLO.md`, seção E.

**Interpretação registrada antes de rodar (Gustavo).** "Coluna constante na etapa" (E.2) é medida separadamente no universo da Parte 1 (S2, S2r) e no da Parte 2 (A+, B+), só com os preditores; as duas contagens saem no `01_universo.csv`.

---

## 2026-11-20 — Resultado do estudo E (v0)

**O que aconteceu.** A execução única (commit `b5c21a9`) terminou sem parar: o filtro devolveu a lista fechada,
o controle negativo passou e a equivalência com o estudo C passou.

**Resultado.**
- **E1:** NÃO ACRESCENTA nas duas etapas (AF e EM). Com as colunas brutas, o R² fora da amostra cai em relação
  ao S1.
- **E2:** F9 e F10 sem GANHO em nenhuma comparação (cada uma deu SEM GANHO PRÁTICO ou INCONCLUSIVO).

**Auditoria (Gustavo).** A auditoria das saídas encontrou **sobreajuste**, por dois motivos:
1. **colunas redundantes:** o protocolo E não incluiu a regra de redundância |r| > 0,90 entre preditores;
2. **escala e valores extremos das contagens brutas.**

Por isso, o ranking da importância por permutação (`06_permutacao.csv`) **não deve ser lido como importância**.
Ele é só descrição do modelo sobreajustado.

**As saídas entram no git** com este registro, como previsto no `experimentos/censo_bruto_v0/README.md` (seção D).

**Evidência:** `experimentos/censo_bruto_v0/saida/` (`RELATORIO.md`, `05_f8.csv`, `08_previsao_testes.csv`).
