"""
Confere dataset/escolas_rr_v<versão>.csv e dataset/DICIONARIO.md (gerados por python -m src.dataset).

  - regerar o dataset a partir de saida/base_atual.parquet dá exatamente o arquivo versionado

  - chave co_entidade + ano + etapa única; anos t de 2007 a 2025; só AF e EM
  - alvos separados: abandono_t1 = ABANDONO_*_T1 da base; nenhuma explicativa é o alvo nem é de t+1
  - na janela segura, alto_risco_t1 é idêntico ao rótulo da classificação (classificacao.montar)
  - janela_segura marca exatamente t de 2013 a 2018
  - o dicionário tem uma linha por coluna, na mesma ordem, com papel alvo ou explicativa
  - o nome da escola não está no dataset
  - dim_*_prop e iie_prop (v0.2.0): proporção dos itens da própria linha, vazia se faltar item; não mudam quando
    outras escolas saem da base; iguais às de 05_indices_infra --com-prop onde o ano tem todos os itens
"""
import importlib.util
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


PROP = [f"dim_{d.lower()}_prop" for d in DS.DIM_ITENS] + ["iie_prop"]


def test_zano_longe_das_fronteiras_de_arredondamento(base):
    """O arquivo é o mesmo em qualquer máquina: cada valor *_zano, antes de arredondar, fica a pelo menos
    FOLGA_MINIMA (10× a maior diferença medida entre Windows e Linux) da fronteira de arredondamento de
    CASAS_ZANO casas. Se um dado novo cair perto de uma fronteira, este teste avisa antes do arquivo divergir."""
    bruto = DS.montar(base)
    passo = 10.0 ** -DS.CASAS_ZANO
    for c in DS.colunas_zano(bruto):
        v = bruto[c].dropna().to_numpy(dtype=float)
        escalado = v / passo
        folga = np.abs(escalado - np.floor(escalado) - 0.5) * passo
        assert folga.min() > DS.FOLGA_MINIMA, (
            f"{c}: um valor está a {folga.min():.1e} de uma fronteira de arredondamento "
            f"(mínimo {DS.FOLGA_MINIMA:.0e}); reveja CASAS_ZANO em src/dataset.py")
    # as outras colunas de ponto flutuante não são arredondadas
    nao_zano = [c for c in bruto.columns if str(bruto[c].dtype) == "Float64" and c not in DS.colunas_zano(bruto)]
    arred = DS.arredondar(bruto)
    for c in nao_zano:
        assert _iguais(arred[c], bruto[c]), c


def _iguais(a, b):
    return np.allclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float), equal_nan=True, rtol=0, atol=1e-12)


def test_prop_linha_a_linha(d):
    """Cada dim_*_prop é a média dos itens da própria linha; vazia se algum item estiver vazio."""
    dims = []
    for dim, cols in DS.DIM_ITENS.items():
        x = d[cols].to_numpy(dtype=float)
        esperado = np.where(np.isnan(x).any(axis=1), np.nan, x.mean(axis=1))
        assert _iguais(d[f"dim_{dim.lower()}_prop"], esperado), f"dim_{dim.lower()}_prop"
        dims.append(esperado)
    m = np.column_stack(dims)
    assert _iguais(d["iie_prop"], np.where(np.isnan(m).any(axis=1), np.nan, m.mean(axis=1)))
    v = d[PROP].to_numpy(dtype=float)
    assert np.nanmin(v) >= 0 and np.nanmax(v) <= 1
    assert d.loc[d["janela_segura"] == 1, PROP].notna().all().all(), "proporção vazia na janela segura"


def test_prop_nao_depende_de_outras_escolas(base):
    """Tirar metade das escolas da base não muda a proporção de nenhuma das que ficam."""
    escolas = sorted(base["CO_ENTIDADE"].astype(str).unique())
    metade = base[base["CO_ENTIDADE"].astype(str).isin(escolas[::2])]
    chave = ["co_entidade", "ano", "etapa"]
    cheio, parcial = DS.montar(base), DS.montar(metade)
    assert all(str(parcial[c].dtype) == "Float64" for c in PROP)
    m = parcial[chave + PROP].merge(cheio[chave + PROP], on=chave, how="left", validate="1:1", suffixes=("", "_cheio"))
    for c in PROP:
        assert _iguais(m[c], m[f"{c}_cheio"]), f"{c} muda quando outras escolas saem"


def test_prop_igual_ao_05_onde_o_ano_tem_todos_os_itens(base):
    """Confere contra a implementação independente de src/estendida/05_indices_infra.py (--com-prop).

    Lá, o denominador são os itens disponíveis no ano (perguntados a alguma escola); aqui, todos os itens da
    dimensão. Nos anos com todos os itens, as duas coincidem; nos outros, a proporção daqui é vazia.
    """
    spec = importlib.util.spec_from_file_location("indices", RAIZ / "src" / "estendida" / "05_indices_infra.py")
    I = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(I)
    novas, params = I.calcular(base, com_prop=True)
    ref = pd.concat([base[["CO_ENTIDADE", "ANO"]], novas], axis=1)
    ref = ref.rename(columns={"CO_ENTIDADE": "co_entidade", "ANO": "ano"}).astype({"co_entidade": str, "ano": int})
    meu = DS.montar(base).drop_duplicates(["co_entidade", "ano"])
    m = meu.merge(ref, on=["co_entidade", "ano"], how="left", validate="1:1")
    for dim in DS.DIM_ITENS:
        completo = m["ano"].astype(str).map(lambda a: len(params["itens_por_ano"][a][dim]) == len(DS.DIM_ITENS[dim]))
        assert _iguais(m.loc[completo, f"dim_{dim.lower()}_prop"], m.loc[completo, f"DIM_{dim}_prop"]), dim
        assert m.loc[~completo, f"dim_{dim.lower()}_prop"].isna().all(), f"{dim}: ano com item faltando deveria ser vazio"
    todos = m["ano"].astype(str).map(lambda a: all(len(params["itens_por_ano"][a][x]) == len(DS.DIM_ITENS[x]) for x in DS.DIM_ITENS))
    assert _iguais(m.loc[todos, "iie_prop"], m.loc[todos, "IIE_prop"])
