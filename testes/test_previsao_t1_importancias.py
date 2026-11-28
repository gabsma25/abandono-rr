"""experimentos/previsao_t1/importancias.py (issue #19, M5a): permutação (ΔMAE) na validação → importancias.csv.

  1. o formato é o do contrato (#15): colunas, tipos, chave sem repetição, completo por modelo, sem histórico
     no modelo "sem histórico", supera_persistencia igual em todas as sementes e igual ao do metricas.csv;
  2. a conta é ΔMAE na validação, com o modelo já ajustado (conferida à mão para uma variável);
  3. nos dados sintéticos, as variáveis plantadas ficam no topo e o ruído perto de zero;
  4. com o desfecho embaralhado dentro do ano, nenhuma variável tem importância clara;
  5. o metricas.csv da passada única é igual ao do modelos.py; o resultado é determinístico.

Só dados sintéticos (os mesmos de test_previsao_t1_modelos.py). Nenhum dado real é lido."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from experimentos.previsao_t1 import importancias as I
from experimentos.previsao_t1 import modelos as M
from experimentos.previsao_t1 import recortes as R
from testes.test_previsao_t1_modelos import _pares

PARES = _pares()
RECORTES = R.gerar_recortes(PARES["ano"].unique())[:3]
ALGS = ("ridge", "random_forest")


@pytest.fixture(scope="module")
def resultado():
    return I.rodar(PARES, RECORTES, algoritmos=ALGS)


# ------------------------------------------------------------------ 1. formato do contrato
def test_formato_do_contrato(resultado):
    met, imp = resultado
    assert imp.columns.tolist() == I.COLUNAS_IMPORTANCIAS
    assert not imp.duplicated(["algoritmo", "historico", "recorte", "etapa", "semente", "variavel"]).any()
    assert imp["importancia"].notna().all() and np.isfinite(imp["importancia"]).all()
    assert set(imp["historico"]) == {0, 1} and set(imp["supera_persistencia"]) <= {0, 1}
    assert set(imp["semente"]) == set(I.SEMENTES_PERMUTACAO)
    assert (imp.groupby("recorte")["ano_validacao"].nunique() == 1).all()
    assert "persistencia" not in set(imp["algoritmo"])
    grupo = ["algoritmo", "historico", "recorte", "etapa"]
    for _, g in imp.groupby(grupo):
        conjuntos = g.groupby("semente")["variavel"].agg(frozenset)
        assert conjuntos.nunique() == 1                         # completo por modelo
        assert g["supera_persistencia"].nunique() == 1
    sem = imp[imp["historico"] == 0]
    assert not sem["variavel"].isin(M.HISTORICO).any()
    # supera_persistencia é o mesmo do metricas.csv
    junto = imp.drop_duplicates(grupo).merge(met, on=grupo, suffixes=("", "_met"))
    assert len(junto) == len(imp.drop_duplicates(grupo))
    assert (junto["supera_persistencia"] == junto["supera_persistencia_met"]).all()


# ------------------------------------------------------------------ 2. a conta, à mão
def test_delta_mae_a_mao():
    r = RECORTES[0]
    treino, val = R.dividir(PARES, r, etapa="AF")
    modelo, cols = M.ajustar(treino, "ridge", True)
    comum = M.linhas_comuns(val)
    X, y = M._X(comum, cols), comum[M.ALVO].to_numpy(float)
    imp = I.permutacao(modelo, X, y, sementes=(7,))
    Xp = X.copy()
    j = cols.index("dim_iib_prop")
    Xp["dim_iib_prop"] = X["dim_iib_prop"].to_numpy()[np.random.default_rng((7, j)).permutation(len(X))]
    esperado = M.mae(y, modelo.predict(Xp)) - M.mae(y, modelo.predict(X))
    assert imp.set_index("variavel").loc["dim_iib_prop", "importancia"] == pytest.approx(esperado)
    pd.testing.assert_frame_equal(X, M._X(comum, cols))       # X original não foi alterado


# ------------------------------------------------------------------ 3. plantadas no topo
def test_plantadas_no_topo(resultado):
    _, imp = resultado
    media = imp.groupby(["algoritmo", "historico", "variavel"])["importancia"].mean()
    for alg in ALGS:
        com = media.loc[(alg, 1)].sort_values(ascending=False)
        assert com.index[0] == "abandono_tm1"
        sem = media.loc[(alg, 0)].sort_values(ascending=False)
        assert set(sem.index[:2]) == {"localizacao", "dim_iib_prop"}
        assert abs(sem["ruido"]) < 0.1 * sem.iloc[0]


# ------------------------------------------------------------------ 4. desfecho embaralhado
def test_desfecho_embaralhado_nao_tem_importancia_clara():
    rng = np.random.default_rng(1)
    base = _pares(n_escolas=150)
    emb = base.copy()
    emb["abandono_t1"] = emb.groupby(["ano", "etapa"])["abandono_t1"].transform(
        lambda s: s.to_numpy()[rng.permutation(len(s))])
    _, imp = I.rodar(emb, RECORTES, algoritmos=("ridge",))
    _, real = I.rodar(base, RECORTES, algoritmos=("ridge",))
    topo_emb = imp.groupby("variavel")["importancia"].mean().max()
    topo_real = real.groupby("variavel")["importancia"].mean().max()
    assert topo_emb < 0.1 * topo_real


# ------------------------------------------------------------------ 5. igual ao modelos.py e determinístico
def test_metricas_iguais_as_do_modelos(resultado):
    met, _ = resultado
    so_modelos = M.avaliar(PARES, RECORTES, algoritmos=ALGS)
    pd.testing.assert_frame_equal(met, so_modelos, check_exact=False, rtol=1e-9)


def test_deterministico(resultado):
    _, a = resultado
    _, b = I.rodar(PARES, RECORTES, algoritmos=ALGS)
    pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-9)


def test_grava(tmp_path, resultado):
    _, imp = resultado
    out = M.gravar(imp, tmp_path / "importancias.csv")
    assert pd.read_csv(out).shape == imp.shape
