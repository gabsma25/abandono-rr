"""notebooks/apoio_apresentacao.py: o apoio do notebook de apresentação (exploratório), com dados sintéticos.

  1. a trava do 2025: nenhuma linha com t > 2023 em treino ou teste; o último ano de teste é t = 2023;
  2. ano a ano: o treino de cada ano de teste só tem anos anteriores, e nenhuma linha de teste entra no ajuste;
  3. saúde e redundância usam só as linhas de treino;
  4. as métricas (Recall, Precisão e F1 nas 20% com maior nota; R²; MAE) batem com contas feitas à mão.

Nenhum teste lê o dataset real nem o desfecho real."""
from __future__ import annotations

import importlib.util
import pathlib

import numpy as np
import pandas as pd
import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("apoio_apresentacao_t", RAIZ / "notebooks" / "apoio_apresentacao.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

SENTINELA = 9.87e6      # desfecho de t = 2024: se entrar em qualquer conta, os números explodem
COLS = {"infraestrutura": list(A.DIMS), "censo_teste": ["QT_X", "QT_X_COPIA", "QT_Y", "QT_VAZIA"]}
RAPIDO = ("Ridge", "Random Forest")


def _dados(anos=range(2007, 2025), n=40, semente=0):
    rng = np.random.default_rng(semente)
    linhas = []
    for etapa in A.ETAPAS:
        for ano in anos:
            for i in range(n):
                linhas.append({"etapa": etapa, "ano": ano, "co_entidade": f"1400{i:04d}", "rede_publica": 1,
                               "localizacao": rng.choice(["Urbana", "Rural"]),
                               "dependencia": rng.choice(["Estadual", "Municipal"]),
                               "abandono_tm1": np.nan if ano == 2007 else float(rng.uniform(0, 20)),
                               "abandono_t": float(rng.uniform(0, 20)),
                               "abandono_t1": SENTINELA if ano == 2024 else float(rng.uniform(0, 20)),
                               "reprovacao_tm1": float(rng.uniform(0, 20)),
                               "variacao_abandono_defasada": float(rng.normal()),
                               **{c: float(rng.uniform()) for c in A.DIMS},
                               "QT_X": float(rng.normal()), "QT_Y": float(rng.normal()),
                               "QT_VAZIA": np.nan if i % 2 else 1.0})
    d = pd.DataFrame(linhas)
    d["QT_X_COPIA"] = d["QT_X"] * 2 + 1
    d["alto_risco_t1"] = 0
    for _, g in d.groupby(["etapa", "ano"]):
        d.loc[g.index, "alto_risco_t1"] = A.CL.rotular(g["abandono_t1"].to_numpy())
    return d


# ------------------------------------------------------------------ 1. trava do 2025
def test_trava_fixa_valores():
    assert A.T_TESTE_LIMPO == 2024 and A.ULTIMO_T_TESTE == 2023


def test_anos_de_teste_param_em_2023_e_tem_treino_antes():
    u = A.universo(_dados(), "AF")
    assert u["ano"].max() == 2023
    anos = A.anos_de_teste(u)
    assert anos[0] == 2010 and anos[-1] == 2023          # 2008 e 2009 são o treino mínimo do primeiro
    assert A.anos_de_teste(u, ano_fim=2030)[-1] == 2023  # nenhuma configuração passa de 2023


def test_conferir_trava_para():
    with pytest.raises(A.TravaViolada):
        A.conferir_trava(pd.DataFrame({"ano": [2023, 2024]}), "teste")
    with pytest.raises(A.TravaViolada):
        A.conferir_trava(pd.DataFrame({"ano": [2019, 2020]}), "treino", t_teste=2020)


def test_desfecho_de_2025_nunca_e_alvo(monkeypatch):
    vistos = []
    orig = A._ajustar
    monkeypatch.setattr(A, "_ajustar", lambda pipe, X, y, t: (vistos.append((X["ano"].max(), t, np.max(y))),
                                                              orig(pipe, X, y, t))[1])
    res = A.ano_a_ano(_dados(), COLS, modelos=RAPIDO)
    assert vistos and all(a < t <= 2023 for a, t, _ in vistos)
    assert max(m for *_, m in vistos) < SENTINELA / 100
    assert res["t"].max() == 2023 and res["MAE"].abs().max() < 1000


# ------------------------------------------------------------------ 2. só anos anteriores no treino
def test_nenhuma_linha_de_teste_no_ajuste(monkeypatch):
    d = _dados(range(2007, 2014))
    d["_id"] = np.arange(len(d))
    vistos = []
    orig = A._ajustar
    monkeypatch.setattr(A, "_ajustar", lambda pipe, X, y, t: (vistos.append((t, set(d.loc[X.index, "_id"]))),
                                                              orig(pipe, X, y, t))[1])
    A.ano_a_ano(d, COLS, modelos=("Ridge",))
    for t, ids in vistos:
        assert not ids & set(d.loc[d["ano"] >= t, "_id"])


def test_imputacao_ajustada_so_no_treino():
    u = A.universo(_dados(), "AF")
    tr = u[u["ano"] < 2015]
    pipe = A._ajustar(A.pipeline("Ridge", ["QT_X"]), tr[["QT_X", *A.CATEGORICAS, "ano"]],
                      tr["abandono_t1"].to_numpy() / 100, 2015)
    imp = pipe.named_steps["pre"].named_transformers_["num"].named_steps["imp"]
    assert imp.statistics_[0] == pytest.approx(tr["QT_X"].median())


# ------------------------------------------------------------------ 3. saúde e redundância no treino
def test_saude_e_redundancia():
    u = A.universo(_dados(), "AF")
    tr = u[u["ano"] < 2015]
    assert "QT_VAZIA" not in A.saudaveis(tr, ["QT_VAZIA", "QT_X"])          # metade vazia
    assert A.redundantes(tr, ["QT_X", "QT_X_COPIA", "QT_Y"]) == ["QT_X", "QT_Y"]
    assert A.redundantes(tr, ["QT_X_COPIA", "QT_X", "QT_Y"]) == ["QT_X_COPIA", "QT_Y"]
    p = A.preditores(tr, COLS)
    assert p[:3] == A.RENDIMENTO and "QT_X_COPIA" not in p and "QT_VAZIA" not in p


def test_redundancia_usa_so_o_treino():
    d = _dados()
    teste = d["ano"] == 2020
    d.loc[teste, "QT_Y"] = d.loc[teste, "QT_X"]          # só no ano de teste QT_Y vira cópia de QT_X
    u = A.universo(d, "AF")
    assert "QT_Y" in A.preditores(u[u["ano"] < 2020], COLS)


# ------------------------------------------------------------------ 4. métricas
def test_metricas_a_mao():
    rot = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    y = np.arange(10, dtype=float)[::-1]
    nota = np.array([9, 1, 8, 0, 0, 0, 0, 0, 0, 0], dtype=float)   # k = 2: aponta as escolas 0 e 2
    m = A.metricas(rot, y, nota)
    assert m["Recall@20%"] == 0.5 and m["Precisão@20%"] == 0.5 and m["F1@20%"] == 0.5
    assert m["MAE"] == pytest.approx(np.mean(np.abs(y - nota)))


def test_resumo_e_grafico():
    import matplotlib
    matplotlib.use("Agg")
    res = A.ano_a_ano(_dados(range(2007, 2013)), COLS, modelos=RAPIDO)
    r = A.resumo(res)
    assert list(r.columns) == list(A.METRICAS) and r.index[0] == ("AF", A.REGUA)
    fig = A.grafico(res, "F1@20%")
    assert len(fig.axes) == 2


# ------------------------------------------------------------------ 5. colunas mais relevantes
def test_importancia_acha_a_coluna_que_move_o_desfecho_e_reporta_todas():
    d = _dados(range(2007, 2014))
    ok = d["ano"] <= 2023
    d.loc[ok, "abandono_t1"] = 10 + 8 * d.loc[ok, "QT_X"]
    imp = A.importancias(d, COLS, modelos=("Ridge",), t=2013, n_repeticoes=3)
    for etapa in A.ETAPAS:
        g = imp[(imp["etapa"] == etapa) & (imp["modelo"] == "Ridge")]
        assert g.iloc[0]["coluna"] == "QT_X"                                  # a mais relevante
        esperadas = set(A.preditores(A.universo(d, etapa).query("ano < 2013"), COLS)) | set(A.CATEGORICAS)
        assert set(g["coluna"]) == esperadas and "ano" not in set(g["coluna"])   # todas, inclusive as nulas
    top = A.top_colunas(imp, n=3)
    assert list(top) == list(A.ETAPAS) and top["AF"].iloc[0, 0].startswith("QT_X")


def test_importancia_nao_usa_o_ano_de_teste_no_treino(monkeypatch):
    vistos = []
    orig = A._ajustar
    monkeypatch.setattr(A, "_ajustar", lambda pipe, X, y, t: (vistos.append((X["ano"].max(), t)),
                                                              orig(pipe, X, y, t))[1])
    A.importancias(_dados(), COLS, modelos=("Ridge",), n_repeticoes=2)
    assert vistos and all(a < t == 2023 for a, t in vistos)
