"""dados/cache/censo_completo/ (src/estendida/extrair_censo.py).

Os testes com o cache de verdade não precisam dos zips: comparam o cache completo com o cache antigo de
22 colunas (dados/cache/censo/), que é o que os resultados publicados usam, e com o dados/MANIFEST.csv.
Os testes do extrator usam zips sintéticos numa pasta temporária e nunca tocam em dados/cache/."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import pathlib

import pandas as pd
import pytest

from testes.conftest import criar_zip

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ANTIGO = RAIZ / "dados" / "cache" / "censo"
COMPLETO = RAIZ / "dados" / "cache" / "censo_completo"
ANOS = range(2007, 2026)


def _carregar():
    spec = importlib.util.spec_from_file_location("extrair_censo", RAIZ / "src" / "estendida" / "extrair_censo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EXT = _carregar()


# --- o cache de verdade -------------------------------------------------------------------------------

@pytest.mark.parametrize("ano", ANOS)
def test_completo_tem_os_mesmos_valores_do_cache_de_22_colunas(ano):
    antigo = pd.read_parquet(ANTIGO / f"{ano}.parquet")
    novo = pd.read_parquet(COMPLETO / f"{ano}_escola.parquet")
    assert len(novo) == len(antigo)
    assert novo["CO_ENTIDADE"].str.strip().tolist() == antigo["CO_ENTIDADE"].tolist()
    assert (novo["NU_ANO_CENSO"].astype(int) == ano).all()
    for c in antigo.columns.drop(["ANO", "CO_ENTIDADE"]):
        a = pd.to_numeric(novo[c], errors="coerce").astype("float64")
        b = antigo[c].astype("float64")
        assert ((a == b) | (a.isna() & b.isna())).all(), c


@pytest.mark.parametrize("ano", ANOS)
def test_completo_tem_a_mesma_estatistica_nacional(ano):
    antigo = json.loads((ANTIGO / f"{ano}_nacional.json").read_text(encoding="utf-8"))
    novo = pd.read_csv(COMPLETO / f"{ano}_escola_nacional.csv").set_index("coluna")
    assert (novo["n_linhas"] == antigo["_n_brasil"]).all()
    for c, st in antigo.items():
        if c != "_n_brasil":
            assert novo.loc[c, "n_numerico"] == st["nao_nulo"], c
            assert novo.loc[c, "n_um"] == st["uns"], c


def test_so_linhas_de_roraima_e_tudo_texto():
    for p in sorted(COMPLETO.glob("*.parquet")):
        df = pd.read_parquet(p)
        assert len(df) > 0, p.name
        assert (df["SG_UF"].str.strip() == "RR").all(), p.name
        assert all(str(t) == "string" for t in df.dtypes), p.name


def test_todo_arquivo_do_cache_completo_esta_no_manifesto_com_o_sha256():
    with open(RAIZ / "dados" / "MANIFEST.csv", encoding="utf-8") as f:
        linhas = {r["arquivo"]: r["sha256"] for r in csv.DictReader(f) if r["tabela"] == "cache_censo_completo"}
    no_disco = {f"cache/censo_completo/{p.name}": p for p in COMPLETO.iterdir()}
    assert set(linhas) == set(no_disco)
    for nome, p in no_disco.items():
        assert hashlib.sha256(p.read_bytes()).hexdigest() == linhas[nome], nome


# --- o extrator, com zips sintéticos ------------------------------------------------------------------

def _csv(linhas):
    return ("\n".join(linhas) + "\n").encode("latin1")


@pytest.fixture
def zip_2025(tmp_path):
    escola = _csv(["NU_ANO_CENSO;SG_UF;CO_ENTIDADE;IN_AGUA;QT_X;TX_NOME",
                   "2025;RR;14000001;1;3;São José",
                   "2025;RR;14000002;--;0;",
                   "2025;SP;35000001;1;5;outra",
                   "2025;SP;35000002;0;;outra"])
    turma = _csv(["NU_ANO_CENSO;SG_UF;CO_ENTIDADE;QT_TUR;IN_Y",
                  "2025;RR;14000001;2;1"])
    return criar_zip(tmp_path / "microdados_censo_escolar_2025_.zip", {
        "m/dados/Tabela_Escola_2025_V2.csv": escola,   # a principal é o maior CSV
        "m/dados/Tabela_Turma_2025_V2.csv": turma,
    })


def test_nome_tabela():
    assert EXT.nome_tabela("x/Tabela_Matricula_2025_V2.csv", False) == "matricula"
    assert EXT.nome_tabela("x/Tabela_Gestor_Escolar_2025_v2.csv", False) == "gestor_escolar"
    assert EXT.nome_tabela("x/suplemento_cursos_tecnicos_2024.csv", False) == "suplemento_cursos_tecnicos"
    assert EXT.nome_tabela("x/microdados_ed_basica_2013.csv", True) == "escola"


def test_extrai_rr_como_texto_e_conta_o_brasil(zip_2025, tmp_path):
    destino = tmp_path / "destino"
    destino.mkdir()
    gravados = EXT.extrair_ano(2025, zip_2025, destino)
    assert sorted(p.name for p in gravados) == ["2025_escola.parquet", "2025_escola_nacional.csv",
                                                 "2025_turma.parquet", "2025_turma_nacional.csv"]
    esc = pd.read_parquet(destino / "2025_escola.parquet")
    assert esc["CO_ENTIDADE"].tolist() == ["14000001", "14000002"]
    assert esc["IN_AGUA"].tolist() == ["1", "--"]          # '--' fica como está: converter é de quem usa
    assert esc["TX_NOME"].tolist() == ["São José", ""]
    st = pd.read_csv(destino / "2025_escola_nacional.csv").set_index("coluna")
    assert st.loc["IN_AGUA"].tolist() == [4, 4, 3, 2, 2]   # n_linhas, preenchido, numérico, ==1, >0
    assert st.loc["QT_X"].tolist() == [4, 3, 3, 0, 2]
    assert len(pd.read_parquet(destino / "2025_turma.parquet")) == 1


def test_recusa_destino_que_ja_existe(tmp_path):
    assert EXT.main(["--anos", "2025", "--destino", str(tmp_path)]) == 1
