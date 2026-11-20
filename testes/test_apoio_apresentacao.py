"""notebooks/apoio_apresentacao.py: o apoio do notebook de apresentação (exploratório), com dados sintéticos.

  1. a trava do 2025: nenhuma linha com t > 2023 em treino ou teste, treino só até t = 2021, e nenhuma
     configuração muda o teste (t = 2022–2023);
  2. a redundância |r| > 0,90 usa só as linhas de treino, na ordem fixa;
  3. as duas janelas usam o mesmo teste, e a diferença usa as mesmas reamostragens (pareada);
  4. nenhuma linha de teste entra num ajuste.

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

NOVAS = ["QT_X", "QT_X_COPIA", "QT_Y"]
SENTINELA = 9.87e6      # desfecho de t = 2024: se entrar em qualquer conta, os números explodem


def _dados(anos=range(2007, 2025), n=40, semente=0):
    rng = np.random.default_rng(semente)
    linhas = []
    for etapa in A.ETAPAS:
        for ano in anos:
            for i in range(n):
                tm1 = np.nan if ano == 2007 else float(rng.uniform(0, 20))
                linhas.append({"etapa": etapa, "ano": ano, "co_entidade": f"1400{i:04d}", "rede_publica": 1,
                               "localizacao": rng.choice(["Urbana", "Rural"]),
                               "dependencia": rng.choice(["Estadual", "Municipal"]),
                               "abandono_tm1": tm1, "abandono_t": float(rng.uniform(0, 20)),
                               "abandono_t1": SENTINELA if ano == 2024 else float(rng.uniform(0, 20)),
                               "reprovacao_tm1": float(rng.uniform(0, 20)),
                               "variacao_abandono_defasada": float(rng.normal()),
                               **{c: float(rng.uniform()) for c in A.DIMS},
                               "QT_X": float(rng.normal()), "QT_Y": float(rng.normal())})
    d = pd.DataFrame(linhas)
    d["QT_X_COPIA"] = d["QT_X"] * 2 + 1           # redundante em todas as linhas
    d["alto_risco_t1"] = 0
    for (_, _), g in d.groupby(["etapa", "ano"]):
        d.loc[g.index, "alto_risco_t1"] = A.CL.rotular(g["abandono_t1"].to_numpy())
    return d


COLS = {"infraestrutura": list(A.DIMS), "censo_teste": NOVAS}


def _explorar(d, ano_inicio, **kw):
    kw = {"remover_redundantes": True, "n_sementes_mlp": 1, "n_boot": 20, **kw}
    return A.explorar(d, COLS, ano_inicio, **kw)


# ------------------------------------------------------------------ 1. trava do 2025
def test_trava_fixa_valores():
    assert A.T_TESTE_LIMPO == 2024 and A.ULTIMO_T_AVALIACAO == 2023
    assert A.TESTE == (2022, 2023) and A.ULTIMO_T_TREINO == 2021


def test_nenhuma_linha_de_t2024_em_treino_ou_teste(monkeypatch):
    d = _dados()
    vistos = []
    orig = A._ajustar
    monkeypatch.setattr(A, "_ajustar", lambda pipe, X, y: (vistos.append((X["ano"].max(), np.max(y))),
                                                           orig(pipe, X, y))[1])
    res = _explorar(d, 2007)
    assert vistos and max(a for a, _ in vistos) <= A.ULTIMO_T_TREINO
    assert max(m for _, m in vistos) < SENTINELA / 100         # o desfecho de 2025 nunca é alvo
    for etapa in A.ETAPAS:
        assert all(int(k.split("|")[0]) in (2022, 2023) for k in res[etapa]["teste_chave"])
        assert res[etapa]["metricas"]["valor"].abs().max() < 1000   # a sentinela não chegou a nenhuma métrica


def test_conferir_trava_para():
    with pytest.raises(A.TravaViolada):
        A.conferir_trava(pd.DataFrame({"ano": [2023, 2024]}), "teste")
    with pytest.raises(A.TravaViolada):
        A.conferir_trava(pd.DataFrame({"ano": [2020, 2022]}), "treino")
    with pytest.raises(A.TravaViolada):
        A.conferir_trava(pd.DataFrame({"ano": [2021]}), "teste")
    with pytest.raises(A.TravaViolada):
        A.anos_treino(_dados(), 2022)                             # não sobra treino: para, não muda o teste


def test_universo_nunca_passa_de_2023():
    d = _dados()
    for etapa in A.ETAPAS:
        assert A.universo(d, etapa, 2007)["ano"].max() == 2023


# ------------------------------------------------------------------ 2. redundância só no treino
def test_redundancia_na_ordem_fixa():
    tr = _dados(range(2015, 2018))
    ficam, ret = A.redundantes(tr, ["QT_X", "QT_X_COPIA", "QT_Y"])
    assert ficam == ["QT_X", "QT_Y"] and ret["coluna"].tolist() == ["QT_X_COPIA"]
    ficam, _ = A.redundantes(tr, ["QT_X_COPIA", "QT_X", "QT_Y"])
    assert ficam == ["QT_X_COPIA", "QT_Y"]                          # a ordem decide quem fica


def test_redundancia_usa_so_linhas_de_treino(monkeypatch):
    d = _dados()
    # no teste (t = 2022–2023), QT_Y vira cópia de QT_X: se o teste entrasse na conta, QT_Y sairia
    teste = d["ano"].isin([2022, 2023])
    d.loc[teste, "QT_Y"] = d.loc[teste, "QT_X"]
    linhas = []
    orig = A.redundantes
    monkeypatch.setattr(A, "redundantes", lambda tr, ordem, **k: (linhas.append(tr["ano"].max()),
                                                                   orig(tr, ordem, **k))[1])
    res = _explorar(d, 2007)
    assert linhas and max(linhas) <= A.ULTIMO_T_TREINO
    for etapa in A.ETAPAS:
        assert res[etapa]["retiradas"]["coluna"].tolist() == ["QT_X_COPIA"]


def test_sem_remover_redundantes_ficam_todas():
    res = _explorar(_dados(), 2007, remover_redundantes=False)
    assert all(res[e]["retiradas"].empty and res[e]["n_novas"] == 3 for e in A.ETAPAS)


# ------------------------------------------------------------------ 3. mesmo teste nas duas janelas
def test_mesmo_teste_e_diferenca_pareada():
    d = _dados()
    r07, r19 = _explorar(d, 2007), _explorar(d, 2019)
    for etapa in A.ETAPAS:
        assert r07[etapa]["teste_chave"] == r19[etapa]["teste_chave"]
        assert r07[etapa]["anos_treino"] == (2008, 2021) and r19[etapa]["anos_treino"] == (2019, 2021)
        # réguas que não dependem da janela (B1R_lag): diferença exatamente 0 em toda reamostragem = pareado
        k = (("régua", "B1R_lag"), "Recall@20%")
        assert np.array_equal(r07[etapa]["dists"][k], r19[etapa]["dists"][k])
    comp = A.comparar(r07, r19, "2007+", "2019+")
    lag = comp[(comp["modelo"] == "B1R_lag")]
    assert (lag["2019+ − 2007+"] == 0).all() and (lag["IC da diferença (pareado)"] == "[0.000; 0.000]").all()


def test_comparar_recusa_testes_diferentes():
    d = _dados()
    r07 = _explorar(d, 2007)
    r19 = _explorar(d, 2019)
    r19["AF"]["teste_chave"] = r19["AF"]["teste_chave"][1:]
    with pytest.raises(AssertionError):
        A.comparar(r07, r19, "a", "b")


# ------------------------------------------------------------------ 4. nada de linha de teste no ajuste
def test_nenhuma_linha_de_teste_no_ajuste(monkeypatch):
    d = _dados()
    d["_id"] = np.arange(len(d))
    teste_ids = set(d.loc[d["ano"].isin([2022, 2023]), "_id"])
    usados = []
    orig_prever = A.prever

    def espiao(tr, te, *a, **k):
        usados.append((set(tr["_id"]), set(te["_id"])))
        return orig_prever(tr, te, *a, **k)
    monkeypatch.setattr(A, "prever", espiao)
    _explorar(d, 2007)
    for tr_ids, te_ids in usados:
        assert not tr_ids & teste_ids and te_ids <= teste_ids and not tr_ids & te_ids


def test_imputacao_ajustada_so_no_treino():
    d = _dados()
    tr, te = A.dividir(A.universo(d, "AF", 2007), 2007)
    pipe = A._ajustar(A._pipeline("ridge", ["QT_X"], None), tr[["QT_X", *A.CATEGORICAS, "ano"]],
                      tr["abandono_t1"].to_numpy() / 100)
    imp = pipe.named_steps["pre"].named_transformers_["num"].named_steps["imp"]
    assert imp.statistics_[0] == pytest.approx(tr["QT_X"].median())


# ------------------------------------------------------------------ saúde e resultado do E
def test_saude_usa_anos_da_configuracao_e_so_preditores():
    chamadas = {}

    def filtro(cache, anos_preench, anos_info, anos_fonte):
        chamadas.update(preench=list(anos_preench), info=list(anos_info), fonte=list(anos_fonte))
        return pd.DataFrame({"coluna": ["QT_X", "QT_X_COPIA", "QT_Y"], "motivo": ["PASSA", "PASSA", "informacao"],
                             "preench_min": 100.0, "valor_dominante_pct": 50.0})
    d = _dados()
    tab, resumo = A.saude(COLS, 2019, A.anos_treino(d, 2019), filtro=filtro)
    assert chamadas["preench"] == list(range(2019, 2025)) and chamadas["info"] == [2019, 2020, 2021]
    assert A.passam(tab) == {"infraestrutura": sorted(A.DIMS), "censo_teste": ["QT_X", "QT_X_COPIA"]}


def test_resultado_oficial_do_e_le_as_saidas():
    if not (A.SAIDA_E / "05_f8.csv").exists():
        pytest.skip("saídas do estudo E ausentes")
    e1, e2, rec = A.resultado_e()
    assert set(e1["etapa"]) == {"AF", "EM"} and set(e2["familia"]) == {"F9", "F10"}
    assert (rec["valor"].between(0, 1)).all()


def test_contra_regua_pareado():
    d = _dados()
    r07 = _explorar(d, 2007)
    t = A.contra_regua({"2007+": r07})
    assert len(t) == len(A.ETAPAS) * len(A.CONJUNTOS) * len(A.MODELOS)
    m = r07["AF"]["metricas"].set_index(["conjunto", "modelo", "metrica"])["valor"]
    lin = t[(t["etapa"] == "AF") & (t["conjunto"] == "A") & (t["modelo"] == "ridge")].iloc[0]
    assert lin["modelo − B1R_lag"] == pytest.approx(m[("A", "ridge", "Recall@20%")] - m[("régua", "B1R_lag", "Recall@20%")])
    # pareado: as mesmas reamostragens; a régua contra ela mesma daria exatamente 0
    k = (("régua", "B1R_lag"), "Recall@20%")
    assert np.array_equal(r07["AF"]["dists"][k] - r07["AF"]["dists"][k], np.zeros(len(r07["AF"]["dists"][k])))
