"""
Confere dataset/escolas_rr_v<versão>.csv e dataset/DICIONARIO.md (gerados por python -m src.dataset).

  - regerar o dataset a partir de saida/base_atual.parquet dá exatamente o arquivo versionado

  - chave co_entidade + ano + etapa única; anos t de 2007 a 2025; só AF e EM
  - alvos separados: abandono_t1 = ABANDONO_*_T1 da base; nenhuma explicativa é o alvo nem é de t+1
  - na janela segura, alto_risco_t1 é idêntico ao rótulo da classificação (classificacao.montar)
  - janela_segura marca exatamente t de 2013 a 2018
  - o dicionário tem uma linha por coluna, na mesma ordem, com papel alvo ou explicativa
  - o nome da escola não está no dataset
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src" / "avaliacao"))
import classificacao as C

sys.path.insert(0, str(RAIZ))
from src import dataset as DS

P_DATASET = DS.DESTINO
P_DIC = RAIZ / "dataset" / "DICIONARIO.md"
P_BASE = RAIZ / "saida" / "base_atual.parquet"
SUF = {"AF": "FUN_AF", "EM": "MED"}


@pytest.fixture(scope="module")
def d():
    if not P_DATASET.exists():
        pytest.fail(f"falta {P_DATASET.relative_to(RAIZ)}: rode python -m src.dataset")
    return pd.read_csv(P_DATASET, dtype={"co_entidade": str, "co_municipio": str})


@pytest.fixture(scope="module")
def base():
    return pd.read_parquet(P_BASE)


def test_chave_e_cobertura(d):
    assert not d.duplicated(["co_entidade", "ano", "etapa"]).any()
    assert set(d["etapa"]) == {"AF", "EM"}
    assert d["ano"].min() == 2007 and d["ano"].max() == 2025
    assert "no_entidade" not in d.columns


def test_alvo_igual_a_base(d, base):
    for etapa, s in SUF.items():
        e = d[d["etapa"] == etapa][["co_entidade", "ano", "abandono_t1"]]
        b = base[["CO_ENTIDADE", "ANO", f"ABANDONO_{s}_T1"]].rename(columns={"CO_ENTIDADE": "co_entidade", "ANO": "ano"})
        b["ano"] = b["ano"].astype(int)
        m = e.merge(b, on=["co_entidade", "ano"], how="left", validate="1:1")
        x, y = m["abandono_t1"].to_numpy(float), m[f"ABANDONO_{s}_T1"].astype("float64").to_numpy()
        assert np.array_equal(x, y, equal_nan=True), f"{etapa}: abandono_t1 difere da base"


def test_explicativas_sem_alvo(d):
    dic = _dicionario()
    explic = [c for c, papel in dic if papel == "explicativa"]
    alvos = [c for c, papel in dic if papel == "alvo"]
    assert alvos == ["abandono_t1", "alto_risco_t1"]
    assert not [c for c in explic if c.endswith("_t1") or c in alvos]


def test_alto_risco_igual_a_classificacao(d, base):
    for etapa in SUF:
        pn = C.montar(etapa, base)[["CO_ENTIDADE", "ANO", "alto_top20"]]
        pn = pn.rename(columns={"CO_ENTIDADE": "co_entidade", "ANO": "ano"}).astype({"ano": int, "co_entidade": str})
        j = d[(d["etapa"] == etapa) & (d["janela_segura"] == 1) & d["alto_risco_t1"].notna()]
        assert len(j) == len(pn), f"{etapa}: {len(j)} rótulos na janela × {len(pn)} no painel da classificação"
        m = j.merge(pn, on=["co_entidade", "ano"], how="outer", validate="1:1", indicator=True)
        assert (m["_merge"] == "both").all(), f"{etapa}: escolas-ano diferentes das do painel"
        assert (m["alto_risco_t1"].astype(int) == m["alto_top20"]).all(), f"{etapa}: rótulo difere"


def test_janela(d):
    assert set(d.loc[d["janela_segura"] == 1, "ano"]) == set(range(2013, 2019))
    assert not d.loc[d["janela_segura"] == 0, "ano"].between(2013, 2018).any()


def _dicionario():
    linhas = [l for l in P_DIC.read_text(encoding="utf-8").splitlines() if l.startswith("| `")]
    return [(re.match(r"\| `([^`]+)` \| ([^|]+) \|", l).group(1), re.match(r"\| `[^`]+` \| ([^|]+) \|", l).group(1).strip())
            for l in linhas]


def test_dicionario_uma_linha_por_coluna(d):
    dic = _dicionario()
    assert [c for c, _ in dic] == list(d.columns)
    assert {p for _, p in dic} == {"identificação", "alvo", "explicativa"}


def test_regerar_da_o_arquivo_versionado(base):
    """O dataset versionado é exatamente o que o código gera hoje, byte a byte."""
    regerado = DS.para_csv(DS.montar(base)).encode("utf-8")
    versionado = P_DATASET.read_bytes()
    assert regerado == versionado, (f"{P_DATASET.name} difere do que src/dataset.py gera "
                                    f"({len(regerado)} × {len(versionado)} bytes): regere e versione de novo")
