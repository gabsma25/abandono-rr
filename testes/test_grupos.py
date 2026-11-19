"""src/estendida/03_grupos.py e src/estendida/grupos/: o contrato dos grupos e a equivalência da reorganização.

A reorganização de 2026-11-19 (03, 04 e 05 viraram a etapa 03_grupos + o grupo infraestrutura, lendo o cache
completo do Censo) não pode mudar a base: o test_equivalencia.py confere a base_atual célula a célula com o
projeto anterior, e o test_dataset.py confere o dataset versionado byte a byte. Aqui, a parte que mudou de
fonte: o grupo infraestrutura, lendo dados/cache/censo_completo/, dá exatamente o que o 03 antigo dava lendo o
cache de 22 colunas (dados/cache/censo/)."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import types

import pandas as pd
import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ANTIGO = RAIZ / "dados" / "cache" / "censo"


def _carregar(caminho, nome):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _carregar(RAIZ / "src" / "estendida" / "03_grupos.py", "etapa03_grupos")
INFRA = _carregar(RAIZ / "src" / "estendida" / "grupos" / "infraestrutura.py", "grupo_infraestrutura_teste")


# --- equivalência: cache completo × cache de 22 colunas ------------------------------------------------

def _montar_pelo_cache_antigo(ano):
    """O que o 03_censo_features.py fazia: cache de 22 colunas + estatística nacional em JSON."""
    cru = pd.read_parquet(ANTIGO / f"{ano}.parquet")
    stats = json.loads((ANTIGO / f"{ano}_nacional.json").read_text(encoding="utf-8"))
    return INFRA.montar_ano(ano, cru, stats)


@pytest.mark.parametrize("ano", range(2007, 2026))
def test_infraestrutura_pelo_cache_completo_igual_ao_cache_antigo(ano):
    antigo, fontes_antigas = _montar_pelo_cache_antigo(ano)
    cru, stats = INFRA.ler_ano(ano)
    novo, fontes_novas = INFRA.montar_ano(ano, cru, stats)
    pd.testing.assert_frame_equal(novo, antigo)
    assert fontes_novas == fontes_antigas


def test_extrair_cobre_os_19_anos_com_as_colunas_declaradas(tmp_path):
    tab = INFRA.extrair(tmp_path)
    assert list(tab.columns) == ["ANO", "CO_ENTIDADE", *INFRA.COLUNAS]
    assert sorted(tab["ANO"].unique()) == list(range(2007, 2026))
    assert not tab.duplicated(["ANO", "CO_ENTIDADE"]).any()
    assert (tmp_path / "fontes_features_censo.csv").exists()


def test_ligados_tem_so_a_infraestrutura():
    """Ligar um grupo muda a versão do dataset: entra por pull request, com decisão registrada."""
    assert G.ler_ligados() == ["infraestrutura"]


# --- contrato, com grupos sintéticos ------------------------------------------------------------------

@pytest.fixture
def base():
    return pd.DataFrame({"ANO": pd.array([2010, 2010, 2011], dtype="Int16"),
                         "CO_ENTIDADE": pd.array(["1", "2", "1"], dtype="string"),
                         "TAXA": [1.0, 2.0, 3.0]})


def _grupo(tab, colunas=("X",), derivadas=None, derivar=None, nome="teste"):
    g = types.SimpleNamespace(NOME=nome, COLUNAS=list(colunas), extrair=lambda rel: tab.copy())
    if derivadas is not None:
        g.DERIVADAS, g.derivar = list(derivadas), derivar
    return g


def _tab(chaves, valores):
    return pd.DataFrame({"ANO": pd.array([a for a, _ in chaves], dtype="Int16"),
                         "CO_ENTIDADE": [e for _, e in chaves], "X": valores})


def test_acrescenta_sem_mudar_a_base(base, tmp_path):
    g = _grupo(_tab([(2010, "1"), (2011, "1"), (2012, "9")], [10, 30, 99]),
               derivadas=["X2"], derivar=lambda t, rel: pd.DataFrame({"X2": t["X"] * 2}, index=t.index))
    saida, tab = G.acrescentar(base, g, tmp_path)
    assert list(saida.columns) == ["ANO", "CO_ENTIDADE", "TAXA", "X", "X2"]
    pd.testing.assert_frame_equal(saida[base.columns], base)          # linhas e colunas da base intactas
    assert saida["X"].tolist()[0] == 10 and pd.isna(saida["X"].iloc[1]) and saida["X"].tolist()[2] == 30
    assert len(tab) == 3                                               # escola sem rendimento não entra


def test_recusa_chave_repetida(base, tmp_path):
    with pytest.raises(G.ErroGrupo, match="repetida"):
        G.acrescentar(base, _grupo(_tab([(2010, "1"), (2010, "1 ")], [1, 2])), tmp_path)


def test_recusa_coluna_que_ja_existe(base, tmp_path):
    tab = _tab([(2010, "1")], [1]).rename(columns={"X": "TAXA"})
    with pytest.raises(G.ErroGrupo, match="repetido"):
        G.acrescentar(base, _grupo(tab, colunas=["TAXA"]), tmp_path)


def test_recusa_colunas_diferentes_das_declaradas(base, tmp_path):
    tab = _tab([(2010, "1")], [1]).assign(Y=0)
    with pytest.raises(G.ErroGrupo, match="extrair"):
        G.acrescentar(base, _grupo(tab), tmp_path)


def test_recusa_derivar_fora_do_contrato(base, tmp_path):
    g = _grupo(_tab([(2010, "1")], [1]), derivadas=["X2"],
               derivar=lambda t, rel: pd.DataFrame({"OUTRA": t["X"]}, index=t.index))
    with pytest.raises(G.ErroGrupo, match="derivar"):
        G.acrescentar(base, g, tmp_path)


def test_derivar_recebe_so_ano_e_as_colunas_do_grupo(base, tmp_path):
    recebido = {}

    def derivar(t, rel):
        recebido["colunas"] = list(t.columns)
        return pd.DataFrame({"X2": t["X"]}, index=t.index)

    G.acrescentar(base, _grupo(_tab([(2010, "1")], [1]), derivadas=["X2"], derivar=derivar), tmp_path)
    assert recebido["colunas"] == ["ANO", "X"]                         # sem TAXA: não vê o rendimento


def test_ligados_ignora_comentarios_e_recusa_repetido(tmp_path):
    p = tmp_path / "ligados.txt"
    p.write_text("# comentário\ninfraestrutura\n\noutro\n", encoding="utf-8")
    assert G.ler_ligados(p) == ["infraestrutura", "outro"]
    p.write_text("a\na\n", encoding="utf-8")
    with pytest.raises(G.ErroGrupo, match="repetido"):
        G.ler_ligados(p)


def test_grupo_inexistente_e_erro(tmp_path):
    with pytest.raises(G.ErroGrupo, match="não existe"):
        G.carregar("nao_existe", tmp_path)


def test_infraestrutura_cumpre_o_contrato():
    g = G.carregar("infraestrutura")
    assert g.COLUNAS == list(INFRA.VARIAVEIS) + ["INFRA_FONTE_ARTIGO"]
    assert g.DERIVADAS == ["DIM_IIB_zano", "DIM_IDA_zano", "DIM_IDP_zano", "DIM_IEP_zano", "IIE_zano",
                           "INFRA_ITENS_COMPLETOS"]
