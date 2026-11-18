# Changelog

Todas as mudanças que importam ficam registradas aqui. Formato:
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões em [SemVer](https://semver.org/lang/pt-BR/).
A versão fica em `src/versao.py`, e o dataset leva a versão no nome do arquivo.

## [Não lançado]

Mudança de escopo: o projeto passa a estudar os fatores associados ao nível de abandono (`docs/DECISOES.md`,
2026-11-14). O dataset ganha as dimensões de infraestrutura em proporção; as 44 colunas da v0.1.0 não mudam.
Será lançado como 0.2.0 (`src/versao.py`); a data e a tag `v0.2.0` entram no dia do merge no `main`.

### Adicionado
- **Registro de anos novos no manifesto** (`src/aquisicao.py`, `--registrar ANOS` e `--aplicar-registro`): baixa ou
  copia os zips de microdados e de rendimento por escola para `dados/cache_download/registro/`, propõe as linhas do
  `dados/MANIFEST.csv` e acrescenta os links ao `src/fontes_inep.csv`; a proposta revisada entra no manifesto antes
  das linhas de 2019. Para trazer 2007–2018, que só existiam como cache (`docs/DECISOES.md`, 2026-11-18). Testes em
  `testes/test_registro.py`.
- `src/estendida/conferir_cache.py`: refaz numa pasta temporária o cache das etapas 01 e 03 de cada ano com zip e
  compara com `dados/cache/` célula a célula (`saida/relatorios/conferencia_cache.csv`); testes em
  `testes/test_conferir_cache.py`.
- **Dataset `v0.2.0`** (`dataset/escolas_rr_v0.2.0.csv`): cinco colunas novas, `dim_iib_prop`, `dim_ida_prop`,
  `dim_idp_prop`, `dim_iep_prop` (proporção dos itens de cada dimensão que a escola tem, calculada só com a própria
  linha; vazia se faltar item) e `iie_prop` (média simples das quatro). As 44 colunas da v0.1.0 ficam idênticas,
  valor a valor. A v0.1.0 continua na tag `v0.1.0`. Testes novos em `testes/test_dataset.py`: a proporção é a da
  linha, não muda quando outras escolas saem da base e coincide com `05_indices_infra.py --com-prop` nos anos
  que têm todos os itens.
- `docs/BASELINE.md`, gerado por `python src/relatorios/baseline.py`: a régua, a versão otimista, a B2 e o
  acaso, com os resultados da Etapa 1 (regerados), da Etapa 2 e da classificação (citados de
  `docs/projeto_anterior/`); `testes/test_baseline.py` exige que esteja em dia.
- `docs/projeto_anterior/classificacao/`: as saídas da execução única da classificação de 2026-11-10, copiadas do
  commit de origem, com sha256 no README da pasta; `testes/test_baseline.py` confere os hashes de todas as cópias
  congeladas, e o `docs/BASELINE.md` e o `testes/test_equivalencia.py` passam a ler a cópia versionada.
- `docs/tese_base/`: o exemplo do professor (MLPRegressor, King County House Sales), como referência de forma;
  o `kc_house_data.csv` fica fora do git, e o nbstripout não toca o notebook (`.gitattributes`,
  `testes/test_atributos.py`; instalação com `--attributes .gitattributes`, ver `CONTRIBUTING.md`).
- `docs/ROTEIRO.md`: as metas M1–M12 do projeto anterior, cópia literal do arquivo, todas "a revisar".
- Registro do desvio da regra 12 (pull requests #1 e #2 mergeados sem revisão) no `docs/DECISOES.md`.
- `experimentos/fatores_2013_2018/`: o código do estudo de fatores (`docs/PROTOCOLO.md`, seção C), com as travas
  da execução única e a conferência por dados sintéticos (`testes/test_fatores.py`). **Ainda não executado.**
  A conferência do código contra o protocolo e as correções estão no `docs/DECISOES.md`, 2026-11-15; a seção D
  do protocolo ganhou o item da falha técnica no meio da execução.

### Alterado
- **Procedência de 2007–2018 conferida:** os 38 zips do INEP de 2007–2025 foram baixados do zero em 2026-11-18, e o
  cache refeito a partir deles é idêntico ao versionado nos 19 anos (`docs/DECISOES.md`, 2026-11-18); a ressalva do
  `dataset/DICIONARIO.md` (via `src/dataset.py`) e do `README.md` muda de acordo. O `dados/MANIFEST.csv` ganha as 24
  linhas de 2007–2018, e o `src/fontes_inep.csv`, os links delas.
- **A pergunta do projeto muda** (`docs/DECISOES.md`, 2026-11-14): de antecipar as escolas de abandono alto no ano
  seguinte para os fatores estruturais associados ao nível de abandono da escola-ano (Q1–Q4). O `README.md` traz a
  pergunta nova, o que já foi respondido (a Q4) e o que o resultado não é. O artigo da disciplina de Mineração de
  Dados sai do repositório; só a cópia literal do roteiro antigo (`docs/ROTEIRO.md`) ainda o menciona.
- **Regras unificadas:** `CLAUDE.md` e `CONTRIBUTING.md` com as mesmas 12 regras e os mesmos números; mudam as
  regras 5 (associação no mesmo ano), 6 (identidade contábil no nível de abandono), 7 (escolher × reportar a
  relação com o desfecho; ressalva do R²) e 10 (toda decisão registrada; unidade dos anos de teste).
- `docs/BASELINE.md` (via `src/relatorios/baseline.py`): a régua passa a ser descrita como "quanto se acerta sem
  modelo, com o dado que a secretaria já tem", e o §5 diz que o nulo preditivo é o que responde à Q4.
- **`docs/PROTOCOLO.md` reescrito** (`docs/DECISOES.md`, 2026-11-15): o registro retroativo da classificação de
  2026-11-10, o desenho padrão do projeto como regra e o protocolo do estudo de fatores associados, escrito
  antes de rodar; nada foi executado. O protocolo da Etapa 4, nunca executado, fica guardado inteiro no fim do
  arquivo.
- Unidade dos intervalos de anos: anos de DESFECHO na regra 10; a linha de 2022–2023 do `dataset/DICIONARIO.md` e
  uma nota abaixo da tabela da janela; "taxa de abandono por ano civil, 2013–2019" no `docs/DECISOES.md` e aqui.
- Registro do segundo desvio da regra 12 (pull requests #5, #7 e #8 mergeados sem revisão e fora do `main`)
  no `docs/DECISOES.md`, 2026-11-15.
- `docs/PROTOCOLO.md`, seção D, "Depois da execução": por que a execução é única e o que acontece depois
  dela (saídas congeladas, relato, correção de erro declarada, estudo novo, controle negativo reprovado).
- Revisão do João no PR #9 (`docs/revisoes/2026-11-15_joao_pr9.md`; decisões no `docs/DECISOES.md`, 2026-11-15):
  a regra dos 30 passa a exigir também 10 escolas distintas por categoria de rede; o motivo da referência Urbana;
  a colinearidade entre localização e infraestrutura nas expectativas e na leitura; o `handle_unknown` do
  `OneHotEncoder`. Só texto da seção C do protocolo. O `README.md` pede Python 3.12 ou mais recente.

### Corrigido
- `testes/test_fatores.py::test_sem_executar_nada_roda` usa uma pasta temporária: falhava em qualquer clone depois
  de as saídas do estudo de fatores serem versionadas (`c2b9adb`). Mergeado direto, sem revisão (`docs/DECISOES.md`,
  2026-11-18).
- `testes/test_validacoes.py`: a conferência do teste 03 com os zips originais exige os anos que tiverem zip, e não
  só 2019–2025.
- **O `rodar_tudo.py` funciona num clone limpo, sem `dados/origem/`** (issue #6): a etapa 01 lê cada ano do
  cache versionado quando não há zips, em vez de parar com `FileNotFoundError`
  (`testes/test_etapa01_sem_origem.py`).
- **O dataset é o mesmo arquivo em qualquer máquina:** as colunas `_zano` saem com 9 casas decimais, e o
  `test_regerar_da_o_arquivo_versionado` deixa de falhar fora da máquina de quem gerou o arquivo
  (`docs/DECISOES.md`, 2026-11-15). As 39 colunas da v0.1.0 que não são `_zano` continuam idênticas; o
  `test_base_atual_identica` compara o `IIE_zano` com tolerância de 1e-12.
- `docs/PROTOCOLO.md`: os títulos do protocolo da Etapa 4 preservado descem dois níveis, sem mudar o texto
  (`testes/test_protocolo.py` confere contra o original).

### Pendências abertas
- **Pipeline oficial 2019–2025 (TDI, ATU, IED) fora do núcleo.** Volta por pull request quando a meta M5
  começar, junto com o teste 07 e a comparação com a base v1.0 do orientador (`docs/DECISOES.md`, 2026-11-11).
  Abrir como issue quando o repositório estiver no GitHub.
- Variáveis novas para 2007–2018, como matrículas e escola indígena: meta M1 (a revisar, `docs/ROTEIRO.md`).

## [0.1.0] — 2026-11-11

Cópia aparada e conferida do projeto anterior (`abandono-escolar` `878930f`, `Dados-do-Projeto` `969fc64`).

### Adicionado
- Núcleo importado: pipeline estendido 2007–2025 (`src/estendida/`), réguas, métricas, bootstrap por escola,
  Holm e funções da classificação (`src/avaliacao/`), funil e desfecho por ano (`src/relatorios/`), obtenção
  dos zips do INEP com conferência de sha256 (`src/aquisicao.py`), recorte de Roraima em `dados/cache/`.
- `dataset/escolas_rr_v0.1.0.csv` e `dataset/DICIONARIO.md`, gerados por `python -m src.dataset`.
- Réguas da janela segura regeradas sem modelo (`src/avaliacao/reguas.py`).
- Teste de equivalência com o projeto anterior: base, régua da Etapa 1, réguas da janela, funil e taxa de
  abandono por ano civil, 2013–2019, idênticos (`testes/test_equivalencia.py`).
- Testes do dataset, inclusive a regeração byte a byte (`testes/test_dataset.py`).
- `rodar_tudo.py`: regera tudo e roda os testes com um comando.
- A classificação de 2026-11-10 como experimento encerrado (`experimentos/classificacao_2013_2018/`).
- `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, modelo de pull request e guia de experimentos.
- `.gitattributes`: texto sempre em LF; arquivos com hash registrado nunca são normalizados.

### Retirado (em relação ao projeto anterior)
- Base oficial 2019–2025, teste 07 e comparação com a v1.0 (ver pendências).
- Degraus "Brasil" e "painel da Etapa 2" do funil; cobertura do painel; seções G e H do teste 04.
- Tabelas Turma, Matrícula e Docente de 2025, que só serviam à fase 2.

### Corrigido
- O teste 03 roda com `--completo`: sem os CSVs extraídos do projeto anterior, ele não conferia nenhum ano com
  os zips originais. Agora confere 2019–2025 célula a célula, e a falta dos zips aparece como teste pulado.
