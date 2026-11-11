"""
Equivalência com o projeto anterior (Etapa 1 da migração).

Depois da cópia aparada e da reescrita de caminhos e imports, o que o abandono-rr regera tem de
ser exatamente igual ao que o projeto anterior gerou:

  1. a base_atual 2007–2025, célula a célula, com os mesmos tipos;
  2. a régua da Etapa 1 (B0, B1, B1R) por transição e etapa;
  3. as réguas da janela segura (B1R_lag, B2 e acaso), por ano de teste, etapa e alvo,
     contra as linhas das réguas em 03_classificacao.csv;
  4. o funil (degraus 2 a 7) e o desfecho por ano, 2013–2019, ano a ano e etapa a etapa.

Igualdade exata: nenhuma tolerância. As referências estão em testes/referencias/ (README lá).
Pré-requisito: as saídas regeradas (python rodar_tudo.py, ou os scripts na ordem do README).
"""
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
REF = RAIZ / "testes" / "referencias" / "projeto_anterior"
SAIDA = RAIZ / "saida"
REF_CLASSIF = RAIZ / "experimentos" / "classificacao_2013_2018" / "saida" / "03_classificacao.csv"
ANOS = range(2013, 2020)
CHAVE_REGUA = ["alvo", "etapa", "modelo", "bloco", "periodo"]


def _ler(caminho, leitor=pd.read_csv, **kw):
    if not caminho.exists():
        pytest.fail(f"falta {caminho.relative_to(RAIZ)}: regere as saídas antes (python rodar_tudo.py)")
    return leitor(caminho, **kw)


def _celulas_diferentes(a, b, chave):
    """Compara dois quadros com a mesma chave; devolve {coluna: nº de células diferentes} (NaN = NaN)."""
    m = a.merge(b, on=chave, suffixes=("_novo", "_ant"), how="outer", validate="1:1", indicator=True)
    so_um = m[m["_merge"] != "both"]
    assert so_um.empty, f"linhas sem par:\n{so_um[chave + ['_merge']].to_string()}"
    dif = {}
    for c in [c for c in a.columns if c not in chave and c in b.columns]:
        x, y = m[f"{c}_novo"], m[f"{c}_ant"]
        iguais = (x == y) | (x.isna() & y.isna())
        if (~iguais).any():
            dif[c] = int((~iguais).sum())
    return dif


def test_base_atual_identica():
    novo = _ler(SAIDA / "base_atual.parquet", pd.read_parquet)
    ant = pd.read_parquet(REF / "base_atual.parquet")
    pd.testing.assert_frame_equal(novo, ant, check_exact=True)


def test_regua_etapa1_identica():
    novo = _ler(SAIDA / "avaliacao" / "01_baselines.csv")
    ant = pd.read_csv(REF / "01_baselines.csv")
    assert list(novo.columns) == list(ant.columns)
    dif = _celulas_diferentes(novo, ant, ["etapa", "ano_alvo"])
    assert not dif, f"01_baselines difere do projeto anterior: {dif}"


def test_reguas_janela_identicas():
    novo = _ler(SAIDA / "avaliacao" / "reguas_janela.csv")
    ant = pd.read_csv(REF_CLASSIF)
    ant = ant[ant["modelo"].isin(["B1R_lag", "B2", "acaso"])][novo.columns]
    assert len(novo) == len(ant) == 60       # 2 etapas × 2 alvos × 3 réguas × (4 anos + agrupado)
    dif = _celulas_diferentes(novo, ant, CHAVE_REGUA)
    assert not dif, f"réguas diferem do projeto anterior: {dif}"


def test_funil_2013_2019_identico():
    novo = _ler(SAIDA / "relatorios" / "funil_recorte.csv")
    ant = pd.read_csv(REF / "funil_recorte.csv")
    sel = lambda d: d[d["ano"].isin(ANOS) & d["ordem"].between(2, 7)][["ano", "etapa", "ordem", "degrau", "n"]]
    novo, ant = sel(novo), sel(ant)
    assert len(novo) == len(ant) == len(ANOS) * 2 * 6
    dif = _celulas_diferentes(novo, ant, ["ano", "etapa", "ordem"])
    assert not dif, f"funil 2013–2019 difere: {dif}"


def test_desfecho_2013_2019_identico():
    novo = _ler(SAIDA / "relatorios" / "desfecho_por_ano.csv")
    ant = pd.read_csv(REF / "desfecho_por_ano.csv")
    novo, ant = novo[novo["ano"].isin(ANOS)], ant[ant["ano"].isin(ANOS)]
    assert len(novo) == len(ant) == len(ANOS) * 2
    dif = _celulas_diferentes(novo, ant, ["ano", "etapa"])
    assert not dif, f"desfecho 2013–2019 difere: {dif}"
