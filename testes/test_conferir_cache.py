"""src/estendida/conferir_cache.py: refaz o cache a partir de um zip sintético do Censo, numa pasta
temporária, e compara com o cache "versionado" (também sintético). Nunca toca em dados/cache/."""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib

import pandas as pd
import pytest

from testes.conftest import criar_zip

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome.replace(".py", "").replace("-", "_"),
                                                  RAIZ / "src" / "estendida" / nome)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CONF = _carregar("conferir_cache.py")


def _hash_cache():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((RAIZ / "dados" / "cache").rglob("*")) if p.is_file()}


def _csv_censo(valor_rr: int) -> bytes:
    linhas = ["NU_ANO_CENSO;SG_UF;CO_ENTIDADE;IN_AGUA_FILTRADA;IN_ENERGIA_REDE_PUBLICA;IN_BIBLIOTECA"]
    linhas += [f"2010;RR;1400000{i};{valor_rr};1;0" for i in range(3)]
    linhas += [f"2010;SP;3500000{i};1;1;1" for i in range(5)]
    return ("\n".join(linhas) + "\n").encode("latin1")


@pytest.fixture
def cenario(tmp_path):
    etapa01, etapa03 = _carregar("01_tx_rend_bruto.py"), _carregar("03_censo_features.py")
    etapa01.INDICADORES = tmp_path / "sem_indicadores"            # sem zip de rendimento
    etapa03.CENSO_BRUTO = tmp_path / "sem_bruto"
    etapa03.CENSO_ORIGEM = tmp_path / "origem" / "censo"
    criar_zip(etapa03.CENSO_ORIGEM / "microdados_censo_escolar_2010.zip",
              {"microdados/dados/microdados_ed_basica_2010.csv": _csv_censo(1)})
    # o cache "versionado" sai das mesmas funções, gravado noutra pasta
    versionado = tmp_path / "versionado"
    versionado.mkdir()
    etapa03.CACHE = versionado
    arquivo = etapa03.CENSO_ORIGEM / "microdados_censo_escolar_2010.zip"
    etapa03.processar_ano(2010, arquivo, "zip", force=True)
    return {"etapa01": etapa01, "etapa03": etapa03, "versionado": versionado, "tmp": tmp_path}


def _rodar(c):
    return CONF.conferir({2010}, c["etapa01"], c["etapa03"], cache_tx=c["tmp"], cache_censo=c["versionado"])


def test_cache_igual_ao_zip_e_identico_e_dados_cache_nao_muda(cenario):
    antes = _hash_cache()
    r = _rodar(cenario).set_index("etapa")
    assert r.loc["03_censo", "status"] == "identico", r.loc["03_censo", "detalhe"]
    assert r.loc["01_tx_rend", "status"] == "sem_zip"
    assert _hash_cache() == antes


def test_celula_alterada_no_cache_diverge(cenario):
    p = cenario["versionado"] / "2010.parquet"
    df = pd.read_parquet(p)
    df.loc[0, "IN_AGUA_FILTRADA"] = 0
    df.to_parquet(p, index=False)
    r = _rodar(cenario).set_index("etapa")
    assert r.loc["03_censo", "status"] == "diverge"
    assert "IN_AGUA_FILTRADA (1)" in r.loc["03_censo", "detalhe"]


def test_estatistica_nacional_alterada_diverge(cenario):
    p = cenario["versionado"] / "2010_nacional.json"
    p.write_text(p.read_text(encoding="utf-8").replace('"_n_brasil": 8', '"_n_brasil": 9'), encoding="utf-8")
    r = _rodar(cenario).set_index("etapa")
    assert r.loc["03_censo", "status"] == "diverge"
    assert "estatística nacional" in r.loc["03_censo", "detalhe"]


def test_diferencas_aponta_colunas_e_tipos():
    a = pd.DataFrame({"x": [1, 2], "y": [1.0, None]})
    assert CONF.diferencas(a, a.copy()) == ""
    assert "tipos" in CONF.diferencas(a, a.astype({"x": "float64"}))
    assert "colunas" in CONF.diferencas(a, a.rename(columns={"y": "z"}))
    assert "x (1)" in CONF.diferencas(a, a.assign(x=[1, 3]))
