"""src/estendida/grupos/censo_bruto_v0.py: o grupo do estudo E (v0), contra o contrato e o docs/PROTOCOLO.md, E.2.

  1. o 03_grupos.py carrega o grupo e acrescenta exatamente as COLUNAS (contrato), sem ele estar ligado;
  2. '--' e texto vazio viram ausente, nunca 0 (regra 8); CO_ENTIDADE sem '.0'; 2025 nunca é lido;
  3. o módulo não abre nenhum arquivo de rendimento (regra 7);
  4. a lista, as 22 colunas da infraestrutura e os blocos são os do protocolo, escritos literalmente;
  5. filtro_mecanico() no cache real devolve EXATAMENTE as COLUNAS (pula se o cache não existir).

Nenhum teste lê o desfecho."""
from __future__ import annotations

import builtins
import importlib.util
import pathlib
import re

import numpy as np
import pandas as pd
import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CACHE_REAL = RAIZ / "dados" / "cache" / "censo_completo"


def _carregar(caminho, nome):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ETAPA03 = _carregar(RAIZ / "src" / "estendida" / "03_grupos.py", "etapa03_grupos_e")
G = ETAPA03.carregar("censo_bruto_v0")
PROTOCOLO = (RAIZ / "docs" / "PROTOCOLO.md").read_text(encoding="utf-8")
SEC_E2 = PROTOCOLO.split("\n### E.2")[1].split("\n### E.3")[0]


# ------------------------------------------------------------------ cache sintético
def _cache_sintetico(pasta, anos=(2013, 2014, 2025)):
    """Tabela escola em texto, como o INEP publica: 3 escolas, com '--', vazio e um código com '.0'."""
    pasta.mkdir(parents=True, exist_ok=True)
    for ano in anos:
        t = pd.DataFrame({"CO_ENTIDADE": ["14000001", "14000002.0", " 14000003 "],
                          "TP_SITUACAO_FUNCIONAMENTO": ["1", "1", "2"], "TP_DEPENDENCIA": ["2", "3", "2"]})
        for c in G.COLUNAS:
            t[c] = ["1", "0", "3"] if c.startswith("QT_") else ["1", "0", "1"]
        t["QT_MAT_BAS"] = ["--", "", "12"]          # traço e vazio: ausentes, nunca 0
        if ano == 2014:
            t = t.drop(columns=["QT_DOC_BAS"])      # fora do layout no ano: ausente
        t.to_parquet(pasta / f"{ano}_escola.parquet", index=False)
    return pasta


# ------------------------------------------------------------------ 1. contrato
def test_contrato_do_03_grupos(tmp_path):
    cache = _cache_sintetico(tmp_path / "cache")
    grupo = type("G", (), {"NOME": G.NOME, "COLUNAS": G.COLUNAS,
                           "extrair": staticmethod(lambda rel: G.extrair(rel, cache=cache, anos=(2013, 2014)))})
    base = pd.DataFrame({"ANO": pd.array([2013, 2014, 2014], dtype="Int16"),
                         "CO_ENTIDADE": pd.array(["14000001", "14000002", "14000009"], dtype="string")})
    saida, tab = ETAPA03.acrescentar(base, grupo, tmp_path)
    assert list(tab.columns) == ["ANO", "CO_ENTIDADE", *G.COLUNAS]
    assert list(saida.columns) == ["ANO", "CO_ENTIDADE", *G.COLUNAS] and len(saida) == 3
    assert saida[G.COLUNAS].iloc[2].isna().all()                 # escola fora do cache: tudo ausente
    assert G.NOME == "censo_bruto_v0" and not hasattr(G, "derivar")


def test_nao_esta_ligado():
    assert "censo_bruto_v0" not in ETAPA03.ler_ligados()


# ------------------------------------------------------------------ 2. ausentes, tipos e 2025
def test_traco_e_vazio_viram_ausente_nunca_zero(tmp_path):
    tab = G.extrair(None, cache=_cache_sintetico(tmp_path / "c"), anos=(2013, 2014))
    a13 = tab[tab["ANO"] == 2013].set_index("CO_ENTIDADE")
    assert a13["QT_MAT_BAS"].isna().tolist() == [True, True, False]
    assert a13.loc["14000003", "QT_MAT_BAS"] == 12
    assert a13.loc["14000002", "IN_AGUA_CACIMBA"] == 0           # o zero de verdade continua zero
    assert tab.loc[tab["ANO"] == 2014, "QT_DOC_BAS"].isna().all()   # fora do layout: ausente
    assert list(a13.index) == ["14000001", "14000002", "14000003"]  # sem '.0' e sem espaço
    assert str(tab["CO_ENTIDADE"].dtype) == "string" and str(tab["ANO"].dtype) == "Int16"
    assert all(str(tab[c].dtype) == "Float64" for c in G.COLUNAS)
    assert len(tab) == 6                                          # todas as escolas, sem filtrar o universo


def test_extrair_nunca_le_2025(tmp_path, monkeypatch):
    cache = _cache_sintetico(tmp_path / "c")
    lidos = []
    orig = pd.read_parquet
    monkeypatch.setattr(pd, "read_parquet", lambda p, *a, **k: (lidos.append(str(p)), orig(p, *a, **k))[1])
    G.extrair(None, cache=cache, anos=(2013, 2014))
    assert lidos and not any(pathlib.Path(p).name.startswith("2025") for p in lidos)
    assert list(G.ANOS_EXTRAIR) == list(range(2007, 2025))
    with pytest.raises(ValueError):
        G.extrair(None, cache=cache, anos=(2025,))


# ------------------------------------------------------------------ 3. nenhum arquivo de rendimento
def test_modulo_nao_abre_rendimento(tmp_path, monkeypatch):
    cache = _cache_sintetico(tmp_path / "c")
    abertos = []
    orig_open, orig_pq, orig_csv = builtins.open, pd.read_parquet, pd.read_csv
    monkeypatch.setattr(builtins, "open", lambda p, *a, **k: (abertos.append(str(p)), orig_open(p, *a, **k))[1])
    monkeypatch.setattr(pd, "read_parquet", lambda p, *a, **k: (abertos.append(str(p)), orig_pq(p, *a, **k))[1])
    monkeypatch.setattr(pd, "read_csv", lambda p, *a, **k: (abertos.append(str(p)), orig_csv(p, *a, **k))[1])
    G.extrair(None, cache=cache, anos=(2013, 2014))
    G.filtro_mecanico(cache=cache, anos_preench=(2013, 2014), anos_info=(2013,), anos_fonte=(2013, 2014))
    assert abertos and all(pathlib.Path(p).parent == cache for p in abertos)
    assert not [p for p in abertos if re.search(r"tx_rend|base_atual|rendimento|dataset", p, re.I)]
    fonte = (RAIZ / "src" / "estendida" / "grupos" / "censo_bruto_v0.py").read_text(encoding="utf-8")
    assert "tx_rend\"" not in fonte and "base_atual.parquet" not in fonte and "escolas_rr" not in fonte


# ------------------------------------------------------------------ 4. listas literais do protocolo
def test_listas_iguais_as_do_protocolo():
    blocos = {}
    for m in re.finditer(r"- \*\*(\w+)\*\* \((\d+)\): (.+)", SEC_E2):
        cols = re.findall(r"`([A-Z0-9_]+)`", m.group(3))
        assert len(cols) == int(m.group(2)), m.group(1)
        blocos[m.group(1)] = cols
    assert blocos == G.BLOCOS
    assert "**A lista resultante tem 124 colunas.**" in SEC_E2 and len(G.COLUNAS) == 124
    assert G.COLUNAS == sorted(G.COLUNAS) == sorted(c for b in blocos.values() for c in b)
    infra = re.findall(r"`(IN_[A-Z_]+)`", SEC_E2.split("3. **já usada:**")[1].split("4. **preenchimento")[0])
    assert infra == G.USADAS_INFRA and len(infra) == 22
    idade = re.findall(r"`(QT_MAT_BAS_[0-9A-Z_]+)`", SEC_E2.split("**Parcialmente mecânicas")[1].split("\n\n")[0])
    assert set(idade) == set(G.FAIXAS_IDADE) and len(G.FAIXAS_IDADE) == 6


def test_colunas_sem_nenhuma_da_infraestrutura():
    assert not set(G.COLUNAS) & set(G.USADAS_INFRA)
    infra = _carregar(RAIZ / "src" / "estendida" / "grupos" / "infraestrutura.py", "grupo_infra_e")
    assert set(G.USADAS_INFRA) == set(infra.CANDIDATAS)


def test_valores_do_filtro_iguais_aos_do_protocolo():
    assert "menos de 95% de valores não ausentes" in SEC_E2 and G.MIN_PREENCH == 95.0
    assert "mais de 99% dos valores não ausentes de 2013–2018" in SEC_E2 and G.MAX_DOMINANTE == 99.0
    assert "`TP_SITUACAO_FUNCIONAMENTO` = 1 e `TP_DEPENDENCIA` em {1, 2, 3}" in SEC_E2
    assert G.DEPENDENCIAS_PUBLICAS == (1, 2, 3) and G.SITUACAO_EM_FUNCIONAMENTO == 1
    assert "`abandono|aprovacao|reprovacao|alto_risco|variacao|tx_rend|base_atual`" in SEC_E2
    assert G.PROIBIDO.pattern == "abandono|aprovacao|reprovacao|alto_risco|variacao|tx_rend|base_atual"


# ------------------------------------------------------------------ o filtro, em dados sintéticos e no cache real
def test_filtro_na_ordem_das_regras(tmp_path):
    """Cada coluna cai na primeira regra que a pega; universo = públicas em funcionamento."""
    pasta = tmp_path / "f"
    pasta.mkdir()
    n = 200
    for ano in (2013, 2014):
        t = pd.DataFrame({"CO_ENTIDADE": [str(i) for i in range(n)],
                          "TP_SITUACAO_FUNCIONAMENTO": ["1"] * (n - 1) + ["2"],
                          "TP_DEPENDENCIA": ["2"] * (n - 1) + ["4"],
                          "NU_ANO_CENSO": [str(ano)] * n,                                   # tipo
                          "QT_ABANDONO_X": ["1"] * n,                                       # proibida
                          "IN_INTERNET": [str(i % 2) for i in range(n)],                    # já usada
                          "QT_POUCO": [""] * 20 + [str(i) for i in range(n - 20)],          # 90% preenchida
                          "QT_FRACAO": ["1.5"] + [str(i) for i in range(n - 1)],            # escala
                          "IN_DOIS": ["2"] + [str(i % 2) for i in range(n - 1)],            # escala (IN_ fora de 0/1)
                          "IN_QUASE": ["1"] + ["0"] * (n - 1),                              # informação (>99%)
                          "QT_BOA": ["--"] + [str(i % 7) for i in range(n - 1)]})           # passa
        t.to_parquet(pasta / f"{ano}_escola.parquet", index=False)
    f = G.filtro_mecanico(cache=pasta, anos_preench=(2013, 2014), anos_info=(2013,),
                          anos_fonte=(2013, 2014)).set_index("coluna")
    esperado = {"CO_ENTIDADE": "tipo", "TP_SITUACAO_FUNCIONAMENTO": "tipo", "NU_ANO_CENSO": "tipo",
                "QT_ABANDONO_X": "proibida", "IN_INTERNET": "ja_usada", "QT_POUCO": "preenchimento",
                "QT_FRACAO": "escala", "IN_DOIS": "escala", "IN_QUASE": "informacao", "QT_BOA": "PASSA"}
    assert f["motivo"].to_dict() == {**esperado, "TP_DEPENDENCIA": "tipo"}
    assert f.loc["QT_POUCO", "preench_min"] == pytest.approx(100 * 179 / 199)   # a escola paralisada sai
    assert f.loc["QT_BOA", "preench_min"] == pytest.approx(100 * 198 / 199)     # '--' é ausente, não 0
    assert list(f.reset_index().columns) == ["coluna", "motivo", "preench_min", "valor_dominante_pct"]


def test_filtro_no_cache_real_devolve_exatamente_as_colunas():
    if not (CACHE_REAL / "2024_escola.parquet").exists():
        pytest.skip("cache completo do Censo ausente (dados/cache/censo_completo/)")
    f = G.filtro_mecanico()
    assert f.loc[f["motivo"] == "PASSA", "coluna"].tolist() == G.COLUNAS
    assert (f.loc[f["motivo"] == "PASSA", "preench_min"] >= G.MIN_PREENCH).all()
    assert np.all(f.loc[f["motivo"] == "PASSA", "valor_dominante_pct"] <= G.MAX_DOMINANTE)
