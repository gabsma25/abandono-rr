"""experimentos/previsao_t1/modelos.py (issue #18, M3a): pipeline só no treino, com e sem histórico, métricas.

  1. preditores: nunca identificação, alvo, taxas de t, abandono_tm2 (redundante), _t1 nem _zano; "sem histórico"
     tira o histórico;
  2. alterar a validação (e os anos depois dela) não muda os parâmetros ajustados;
  3. a imputação usa a mediana do treino, e o ausente não vira 0 antes dela;
  4. todos os algoritmos de um recorte × etapa são medidos nas mesmas linhas (as que têm abandono_tm1);
  5. as métricas batem com as do sklearn e a persistência é o abandono de t−1;
  6. nos dados sintéticos com efeito plantado, o modelo com histórico supera a persistência e o sem histórico usa as
     outras variáveis;
  7. as duas MLPs rodam; o teste final nunca aparece; o resultado é determinístico.

Só dados sintéticos montados aqui (códigos de escola começando por 99). Nenhum dado real é lido."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from experimentos.previsao_t1 import modelos as M
from experimentos.previsao_t1 import recortes as R


def _pares(semente=0, n_escolas=60, anos=range(2008, 2025), vazios=0.05):
    """abandono(t+1) = 4 + 0,6·abandono(t−1) + 3·[Rural] − 4·dim_iib_prop + ruído; o resto é ruído."""
    rng = np.random.default_rng(semente)
    rural = rng.random(n_escolas) < 0.4
    linhas = []
    for e in range(n_escolas):
        for etapa in ("AF", "EM"):
            hist = [max(0.0, rng.normal(6, 3)) for _ in range(3)]          # abandono de anos anteriores
            for t in anos:
                iib = float(np.clip(rng.normal(0.75 - 0.25 * rural[e], 0.15), 0, 1))
                tm1, tm2 = hist[-2], hist[-3]
                y = float(np.clip(4 + 0.6 * tm1 + 3 * rural[e] - 4 * iib + rng.normal(0, 1), 0, 100))
                linhas.append({"co_entidade": f"99{e:06d}", "ano": t, "ano_alvo": t + 1, "etapa": etapa,
                               "abandono_t1": round(y, 1), "abandono_tm1": round(tm1, 1),
                               "abandono_tm2": round(tm2, 1),
                               "variacao_abandono_defasada": round(tm1 - tm2, 1),
                               "abandono_t": round(hist[-1], 1),                     # dado de t: nunca em X
                               "localizacao": "Rural" if rural[e] else "Urbana",
                               "dim_iib_prop": iib, "ruido": rng.normal()})
                hist.append(y)
    p = pd.DataFrame(linhas)
    p["co_entidade"] = p["co_entidade"].astype("string")
    p["localizacao"] = p["localizacao"].astype("string")
    p.loc[rng.random(len(p)) < vazios, "dim_iib_prop"] = np.nan
    p.loc[rng.random(len(p)) < vazios, "abandono_tm1"] = np.nan
    return p


PARES = _pares()
RECORTES = R.gerar_recortes(PARES["ano"].unique())


# ------------------------------------------------------------------ 1. preditores
def test_preditores():
    extra = PARES.assign(aprovacao_t=1.0, reprovacao_t=1.0, dim_iib_zano=0.0, alto_risco_t1=1,
                         co_municipio="1400100")
    com = M.preditores(extra, historico=True)
    sem = M.preditores(extra, historico=False)
    assert com == ["abandono_tm1", "variacao_abandono_defasada", "localizacao", "dim_iib_prop", "ruido"]
    assert sem == ["localizacao", "dim_iib_prop", "ruido"]
    for c in ("abandono_t", "abandono_tm2", "aprovacao_t", "reprovacao_t", "abandono_t1", "dim_iib_zano", "alto_risco_t1",
              "co_municipio", "co_entidade", "ano", "ano_alvo", "etapa"):
        assert c not in com


# ------------------------------------------------------------------ 2. a validação não mexe no ajuste
@pytest.mark.parametrize("algoritmo", ["ridge", "random_forest"])
def test_alterar_a_validacao_nao_muda_o_ajuste(algoritmo):
    r = RECORTES[3]
    treino, _ = R.dividir(PARES, r, etapa="AF")
    sonda = M._X(treino.head(50), M.preditores(treino, True))
    m1, _ = M.ajustar(treino, algoritmo, True)

    estragado = PARES.copy()
    depois = estragado["ano"] >= r.ano_validacao                     # a validação e tudo o que vem depois
    estragado.loc[depois, "abandono_t1"] = 99.0
    estragado.loc[depois, "dim_iib_prop"] = -50.0
    estragado.loc[depois, "abandono_tm1"] = np.nan
    treino2, _ = R.dividir(estragado, r, etapa="AF")
    m2, _ = M.ajustar(treino2, algoritmo, True)
    # igual até o arredondamento da soma em paralelo do random forest (n_jobs=-1)
    np.testing.assert_allclose(m1.predict(sonda), m2.predict(sonda), rtol=1e-12, atol=1e-12)


# ------------------------------------------------------------------ 3. imputação ajustada só no treino
def test_imputacao_pela_mediana_do_treino():
    r = RECORTES[0]
    treino, _ = R.dividir(PARES, r, etapa="AF")
    m, cols = M.ajustar(treino, "ridge", True)
    imp = m.named_steps["pre"].named_transformers_["num"].named_steps["imp"]
    num = [c for c in cols if c != "localizacao"]
    np.testing.assert_allclose(imp.statistics_, treino[num].median().to_numpy())
    assert imp.indicator_ is not None                                # o ausente ganha um indicador
    assert treino["dim_iib_prop"].isna().any()                       # e continua ausente na entrada (não vira 0)


# ------------------------------------------------------------------ 4 e 5. mesmas linhas e métricas
@pytest.fixture(scope="module")
def metricas():
    return M.avaliar(PARES, RECORTES[:4], algoritmos=("ridge", "random_forest"))


def test_mesmas_linhas_para_todos(metricas):
    assert set(metricas["algoritmo"]) == {"persistencia", "ridge", "random_forest"}
    for (rec, etapa), g in metricas.groupby(["recorte", "etapa"]):
        assert g["n_validacao"].nunique() == 1
        assert g["mae_persistencia"].nunique() == 1
        r = next(x for x in RECORTES if x.id == rec)
        _, val = R.dividir(PARES, r, etapa=etapa)
        assert g["n_validacao"].iloc[0] == val["abandono_tm1"].notna().sum() < len(val)


def test_metricas_batem_com_o_sklearn(metricas):
    r = RECORTES[2]
    _, val = R.dividir(PARES, r, etapa="EM")
    v = val[val["abandono_tm1"].notna()]
    y, p = v["abandono_t1"], v["abandono_tm1"]
    linha = metricas[(metricas["algoritmo"] == "persistencia") & (metricas["recorte"] == r.id)
                     & (metricas["etapa"] == "EM")].iloc[0]
    assert linha["mae"] == pytest.approx(mean_absolute_error(y, p))
    assert linha["rmse"] == pytest.approx(np.sqrt(mean_squared_error(y, p)))
    assert linha["r2"] == pytest.approx(r2_score(y, p))
    assert metricas.columns.tolist() == M.COLUNAS_METRICAS
    assert metricas[["mae", "rmse", "r2"]].notna().all().all()
    ok = metricas["algoritmo"] != "persistencia"
    assert ((metricas.loc[ok, "mae"] < metricas.loc[ok, "mae_persistencia"]).astype(int)
            == metricas.loc[ok, "supera_persistencia"]).all()


# ------------------------------------------------------------------ 6. o efeito plantado aparece
def test_efeito_plantado(metricas):
    ridge = metricas[metricas["algoritmo"] == "ridge"]
    assert ridge[ridge["historico"] == 1]["supera_persistencia"].all()
    # sem histórico, o modelo ainda usa rural e infraestrutura: R² acima de zero
    assert (ridge[ridge["historico"] == 0]["r2"] > 0).all()
    assert (ridge[ridge["historico"] == 0]["n_preditores"] == 3).all()


# ------------------------------------------------------------------ 7. MLPs, teste final, determinismo
def test_as_duas_mlps_rodam():
    pequeno = _pares(n_escolas=15, anos=range(2008, 2014))
    rs = R.gerar_recortes(pequeno["ano"].unique())
    met = M.avaliar(pequeno, rs, algoritmos=("mlp_professor", "mlp_64_32"), etapas=["AF"])
    assert set(met["algoritmo"]) == {"persistencia", "mlp_professor", "mlp_64_32"}
    assert np.isfinite(met["mae"]).all()


def test_teste_final_nunca_aparece(metricas):
    todas = M.avaliar(PARES, RECORTES[-1:], algoritmos=("ridge",))
    assert todas["ano_validacao"].max() == 2023
    assert (metricas["ano_validacao"] < 2024).all()


def test_deterministico():
    a = M.avaliar(PARES, RECORTES[:2], algoritmos=("ridge", "random_forest"), semente=3)
    b = M.avaliar(PARES, RECORTES[:2], algoritmos=("ridge", "random_forest"), semente=3)
    pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-9)


def test_algoritmo_desconhecido():
    with pytest.raises(ValueError):
        M.estimador("xgboost")


def test_grava_e_le(tmp_path):
    caminho = tmp_path / "pares.csv"
    PARES.to_csv(caminho, index=False)
    lido = M.ler_pares(caminho)
    assert lido["co_entidade"].dtype == "string" and lido["ano"].dtype == "int64"
    met = M.avaliar(lido, RECORTES[:1], algoritmos=("ridge",))
    out = M.gravar(met, tmp_path / "saida" / "metricas.csv")
    assert pd.read_csv(out).shape == met.shape
