# abandono-rr — risco de abandono escolar em Roraima

Projeto de pesquisa (PIBIC/UERR, Edital 35/2026) e artigo da disciplina de Mineração de Dados, orientado
pelo Prof. Bruno Cesar Barreto Figueiredo.

**A pergunta.** Olhando os dados de uma escola pública de Roraima num ano, dá para saber, com um ano de
antecedência, quais escolas vão ter abandono alto no ano seguinte? A unidade é a **escola-ano**: o projeto
não olha alunos. A lista de escolas de maior risco serve para **priorizar diagnóstico e apoio**, nunca para
ranquear ou punir escolas.

**De onde partimos.** O abandono-rr começou em 2026-11-11 como uma cópia aparada de dois repositórios
anteriores (`abandono-escolar` e `Dados-do-Projeto`), que ficaram congelados. Tudo o que foi copiado gera
exatamente os mesmos números de antes (`testes/test_equivalencia.py`). O que ficou e o que saiu está em
[`docs/DECISOES.md`](docs/DECISOES.md).

## Quem é quem

| Pessoa | Papel no projeto |
|---|---|
| Gabriela | ferramenta de alerta precoce, avaliação e resultados; manutenção do repositório |
| João | base de dados e régua (o último abandono conhecido) |
| Gustavo | pipeline estendido 2007–2025 e índices de infraestrutura |
| Prof. Bruno Cesar Barreto Figueiredo | orientador |

*Papéis a confirmar pelo grupo.*

## Instalação

Pré-requisitos: **Python 3.12** e Git. Cerca de 1,5 GB livres se for baixar os zips do INEP.

```bash
git clone <endereço-do-repositório> abandono-rr
cd abandono-rr
python -m venv .venv
.venv\Scripts\activate             # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

As versões do `requirements.txt` são fixas: são as que geraram os resultados (scikit-learn 1.8.0).

**Dados.** O que o pipeline precisa para rodar já vem no git: o recorte de Roraima de 2007 a 2025 em
`dados/cache/`, com o sha256 de cada arquivo no `dados/MANIFEST.csv`. Os zips originais do INEP (2019–2025,
cerca de 1,2 GB) **não** vão para o git. Eles só são necessários para conferir 2019–2025 contra a fonte e
para reconstruir o cache:

```bash
python -m src.aquisicao --origem-local C:\pasta\com\os\zips   # copia de uma pasta, conferindo o sha256
python -m src.aquisicao --baixar                              # ou baixa do INEP o que faltar
```

## Rodar tudo com um comando

```bash
python rodar_tudo.py
```

Regera, na ordem: a base 2007–2025 (`saida/base_atual.parquet`), o funil e o desfecho por ano, as réguas, o
dataset e o dicionário; depois roda todos os testes. Leva cerca de 1 minuto. Sem os zips do INEP, dois testes
aparecem como **pulados**, com o motivo: a conferência de 2019–2025 com a fonte e a comparação com um backup que
ficou no projeto anterior.

`python rodar_tudo.py --sem-testes` só regera.

## O dataset

[`dataset/escolas_rr_v0.1.0.csv`](dataset/) tem uma linha por escola × ano × etapa (AF = anos finais do
fundamental, EM = ensino médio), de 2007 a 2025, com os alvos em colunas próprias (`abandono_t1` e
`alto_risco_t1`) e as variáveis explicativas separadas. Cada coluna está descrita em
[`dataset/DICIONARIO.md`](dataset/DICIONARIO.md). A versão do dataset acompanha a do projeto
([`CHANGELOG.md`](CHANGELOG.md)).

**Ressalva.** Os anos de 2007 a 2018 vêm só do recorte em `dados/cache/`, conferido contra a fonte do INEP uma
vez, na máquina do Gustavo; os zips originais desses anos não estão no projeto. Os anos de 2019 a 2025 são
conferidos célula a célula contra os zips originais.

## Onde está cada coisa

```
dados/          MANIFEST.csv (hashes) e cache/ (recorte de RR 2007–2025) no git; origem/ fora do git
dataset/        o dataset versionado e o dicionário
src/
  estendida/    pipeline 2007–2025: rendimento, Censo, merge, índices de infraestrutura
  avaliacao/    réguas, métricas, bootstrap por escola, Holm, classificação (funções)
  relatorios/   funil e desfecho por ano
  dataset.py    gera o dataset e o dicionário
  aquisicao.py  obtém os zips do INEP conferindo o sha256 (com integridade.py e config.py)
testes/         pytest; os scripts 0*_validar_*.py vêm do projeto anterior
experimentos/   uma pasta por ideia em teste; ver experimentos/README.md
notebooks/      no máximo 2; só exibem o que o código gerou
docs/           DECISOES, problemas.csv (defeitos dos dados do INEP), procedência; BASELINE e PROTOCOLO a seguir
saida/          gerada por rodar_tudo.py; fora do git
```

## Como contribuir

Leia o [`CONTRIBUTING.md`](CONTRIBUTING.md): um branch por tarefa, `python rodar_tudo.py` antes de abrir o
pull request e revisão de outra pessoa antes de entrar no `main`. As regras que não se quebram estão no
mesmo arquivo, em linguagem simples, e no [`CLAUDE.md`](CLAUDE.md).
