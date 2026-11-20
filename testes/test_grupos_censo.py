"""Os 7 grupos do Censo (src/estendida/grupos/censo_*.py e _censo_comum.py), contra o contrato do grupos/README.md.

  1. a união das COLUNAS dos 7 grupos é exatamente censo_bruto_v0.COLUNAS, sem repetição, um grupo por bloco;
  2. cada grupo respeita o contrato do 03_grupos.py; os 7 estão ligados depois do infraestrutura;
  3. nenhum grupo abre arquivo de rendimento;
  4. '--' e vazio viram ausente, nunca 0 (regra 8);
  5. coluna não coletada no Brasil no ano fica ausente o ano inteiro (regra 4 do README);
  6. 2025: as tabelas divididas são juntadas 1:1 por CO_ENTIDADE; coluna sem o mesmo nome fica ausente e vai
     para o relatório; o relatório de continuidade marca variação da mediana acima de 50%.

Cache sintético; nenhum teste lê o desfecho."""
from __future__ import annotations

import builtins
import importlib.util
import pathlib
import re

import numpy as np
import pandas as pd
import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
GRUPOS = RAIZ / "src" / "estendida" / "grupos"
NOMES = ["censo_matriculas", "censo_docentes", "censo_turmas_salas", "censo_equipamentos",
         "censo_oferta_turno", "censo_escola_indigena", "censo_predio_servicos"]


def _carregar(caminho, nome):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ETAPA03 = _carregar(RAIZ / "src" / "estendida" / "03_grupos.py", "etapa03_grupos_censo")
V0 = ETAPA03.carregar("censo_bruto_v0")
G = {n: ETAPA03.carregar(n) for n in NOMES}
TODAS = [c for n in NOMES for c in G[n].COLUNAS]

NAO_COLETADA_2023 = "IN_AUDITORIO"          # n_um = 0 no Brasil em 2023
QT_NAO_COLETADA_2023 = "QT_EQUIP_TV"        # n_positivo = 0 no Brasil em 2023
SEM_NOME_2025 = "IN_DIURNO"                 # não existe em nenhuma tabela de 2025


def _origem_2025(c):
    if c.startswith("QT_MAT_"):
        return "matricula"
    if c.startswith("QT_DOC_"):
        return "docente"
    if c.startswith("QT_TUR_"):
        return "turma"
    return "escola"


def _nacional(colunas, sem_um=(), sem_positivo=()):
    return pd.DataFrame({"coluna": colunas, "n_linhas": 100, "n_preenchido": 100, "n_numerico": 100,
                         "n_um": [0 if c in sem_um else 5 for c in colunas],
                         "n_positivo": [0 if c in sem_positivo else 5 for c in colunas]})


def _cache(pasta):
    """2023 e 2024 numa tabela escola; 2025 dividida em escola, docente, matricula e turma, como no cache real.
    3 escolas na escola (uma privada), 2 nas outras tabelas de 2025."""
    pasta.mkdir(parents=True, exist_ok=True)
    co = ["14000001", "14000002.0", " 14000003 "]
    chave = {"CO_ENTIDADE": co, "TP_SITUACAO_FUNCIONAMENTO": ["1", "1", "1"], "TP_DEPENDENCIA": ["2", "3", "4"]}
    for ano in (2023, 2024):
        t = pd.DataFrame(chave)
        for c in TODAS:
            t[c] = ["2", "0", "4"] if c.startswith("QT_") else ["1", "0", "1"]
        t["QT_MAT_BAS"] = ["--", "", "12"]
        t.to_parquet(pasta / f"{ano}_escola.parquet", index=False)
        nac = _nacional(list(t.columns), *(([NAO_COLETADA_2023], [QT_NAO_COLETADA_2023]) if ano == 2023 else ()))
        nac.to_csv(pasta / f"{ano}_escola_nacional.csv", index=False)
    cols25 = [c for c in TODAS if c != SEM_NOME_2025]
    for tab in ("escola", "docente", "matricula", "turma"):
        t = pd.DataFrame(chave) if tab == "escola" else pd.DataFrame({"CO_ENTIDADE": ["14000002", "14000001"]})
        for c in [c for c in cols25 if _origem_2025(c) == tab]:
            if tab == "escola":
                t[c] = ["1", "0", "1"] if c.startswith("IN_") else ["2", "0", "4"]
            else:
                t[c] = ["10", "4"]              # a ordem das linhas difere da escola: a junção é pela chave
        t.to_parquet(pasta / f"2025_{tab}.parquet", index=False)
        _nacional(list(t.columns)).to_csv(pasta / f"2025_{tab}_nacional.csv", index=False)
    return pasta


ANOS = (2023, 2024, 2025)


def _extrair(nome, cache, rel=None):
    return G[nome].extrair(rel, cache=cache, anos=ANOS)


# ------------------------------------------------------------------ 1. a lista
def test_uniao_e_exatamente_a_lista_do_estudo_e_sem_repeticao():
    assert len(TODAS) == len(set(TODAS)) == 124
    assert sorted(TODAS) == sorted(V0.COLUNAS)
    for n in NOMES:
        bloco = n.removeprefix("censo_")
        assert G[n].COLUNAS == sorted(V0.BLOCOS[bloco]), n
    assert {len(G[n].COLUNAS) for n in NOMES} and [len(G[n].COLUNAS) for n in NOMES] == [37, 15, 16, 10, 16, 1, 29]


def test_colunas_literais_no_arquivo():
    for n in NOMES:
        fonte = (GRUPOS / f"{n}.py").read_text(encoding="utf-8")
        bloco = fonte.split("COLUNAS = [")[1].split("]")[0]
        assert re.findall(r'"([A-Z0-9_]+)"', bloco) == G[n].COLUNAS, n


def test_ligados_depois_da_infraestrutura_e_comum_nao_e_grupo():
    lig = ETAPA03.ler_ligados()
    assert lig[lig.index("infraestrutura") + 1:][:7] == NOMES
    assert "_censo_comum" not in lig and "censo_bruto_v0" not in lig


# ------------------------------------------------------------------ 2. contrato
@pytest.mark.parametrize("nome", NOMES)
def test_contrato_do_03_grupos(nome, tmp_path):
    cache = _cache(tmp_path / "cache")
    g = G[nome]
    grupo = type("G", (), {"NOME": g.NOME, "COLUNAS": g.COLUNAS,
                           "extrair": staticmethod(lambda rel: _extrair(nome, cache, rel))})
    base = pd.DataFrame({"ANO": pd.array([2023, 2025, 2025], dtype="Int16"),
                         "CO_ENTIDADE": pd.array(["14000001", "14000002", "14000009"], dtype="string")})
    saida, tab = ETAPA03.acrescentar(base, grupo, tmp_path)
    assert list(tab.columns) == ["ANO", "CO_ENTIDADE", *g.COLUNAS]
    assert list(saida.columns) == ["ANO", "CO_ENTIDADE", *g.COLUNAS] and len(saida) == 3
    assert saida[g.COLUNAS].iloc[2].isna().all()
    assert g.NOME == nome and not hasattr(g, "derivar")
    assert str(tab["ANO"].dtype) == "Int16" and str(tab["CO_ENTIDADE"].dtype) == "string"
    assert all(str(tab[c].dtype) == "Float64" for c in g.COLUNAS)
    assert len(tab) == 9 and not tab.duplicated(["ANO", "CO_ENTIDADE"]).any()


# ------------------------------------------------------------------ 3. rendimento
def test_nenhum_grupo_abre_rendimento(tmp_path, monkeypatch):
    cache = _cache(tmp_path / "c")
    abertos = []
    orig_open, orig_pq, orig_csv = builtins.open, pd.read_parquet, pd.read_csv
    monkeypatch.setattr(builtins, "open", lambda p, *a, **k: (abertos.append(str(p)), orig_open(p, *a, **k))[1])
    monkeypatch.setattr(pd, "read_parquet", lambda p, *a, **k: (abertos.append(str(p)), orig_pq(p, *a, **k))[1])
    monkeypatch.setattr(pd, "read_csv", lambda p, *a, **k: (abertos.append(str(p)), orig_csv(p, *a, **k))[1])
    for n in NOMES:
        _extrair(n, cache)
    lidos = [p for p in abertos if not p.endswith(".py")]
    assert lidos and all(pathlib.Path(p).parent == cache for p in lidos)
    assert not [p for p in lidos if re.search(r"tx_rend|base_atual|rendimento|dataset", p, re.I)]
    for n in ["_censo_comum", *NOMES]:
        fonte = (GRUPOS / f"{n}.py").read_text(encoding="utf-8")
        assert "tx_rend" not in fonte and "base_atual.parquet" not in fonte and "escolas_rr" not in fonte


# ------------------------------------------------------------------ 4. '--' e vazio
def test_traco_e_vazio_viram_nan_nunca_zero(tmp_path):
    tab = _extrair("censo_matriculas", _cache(tmp_path / "c"))
    a = tab[tab["ANO"] == 2024].set_index("CO_ENTIDADE")
    assert a["QT_MAT_BAS"].isna().tolist() == [True, True, False]
    assert a.loc["14000003", "QT_MAT_BAS"] == 12
    assert a.loc["14000002", "QT_MAT_FUND"] == 0                 # o zero de verdade continua zero
    assert list(a.index) == ["14000001", "14000002", "14000003"]


# ------------------------------------------------------------------ 5. coletada
def test_coluna_nao_coletada_fica_nan_no_ano(tmp_path):
    cache = _cache(tmp_path / "c")
    pred = _extrair("censo_predio_servicos", cache)
    eq = _extrair("censo_equipamentos", cache)
    assert pred.loc[pred["ANO"] == 2023, NAO_COLETADA_2023].isna().all()
    assert pred.loc[pred["ANO"] == 2024, NAO_COLETADA_2023].notna().all()     # coletada no ano seguinte
    assert eq.loc[eq["ANO"] == 2023, QT_NAO_COLETADA_2023].isna().all()
    assert eq.loc[eq["ANO"] == 2023, "QT_EQUIP_SOM"].notna().all()


def test_regra_coletada_por_prefixo():
    C = G[NOMES[0]]._comum()
    nac = _nacional(["IN_X", "QT_Y", "IN_Z"], sem_um=["IN_Z"], sem_positivo=["QT_Y"]).set_index("coluna")
    assert C.coletada("IN_X", nac) and not C.coletada("QT_Y", nac) and not C.coletada("IN_Z", nac)
    assert not C.coletada("IN_FORA", nac)


# ------------------------------------------------------------------ 6. 2025 e relatórios
def test_2025_juntado_pela_chave_e_coluna_sem_nome_ausente(tmp_path):
    cache, rel = _cache(tmp_path / "c"), tmp_path / "rel"
    mat = _extrair("censo_matriculas", cache, rel).set_index(["ANO", "CO_ENTIDADE"])
    assert mat.loc[(2025, "14000001"), "QT_MAT_FUND"] == 4             # veio da tabela matricula, pela chave
    assert mat.loc[(2025, "14000002"), "QT_MAT_FUND"] == 10
    assert pd.isna(mat.loc[(2025, "14000003"), "QT_MAT_FUND"])         # escola fora da matricula: ausente
    of = _extrair("censo_oferta_turno", cache).set_index(["ANO", "CO_ENTIDADE"])
    assert of.xs(2025)[SEM_NOME_2025].isna().all() and of.xs(2024)[SEM_NOME_2025].notna().all()
    txt = (rel / "grupos_censo_2025.txt").read_text(encoding="utf-8")
    assert f"  - {SEM_NOME_2025}" in txt and "Colunas SEM o mesmo nome em nenhuma tabela de 2025" in txt
    col = pd.read_csv(rel / "grupos_censo_coleta.csv")
    assert col.query("ano == 2025 and coluna == @SEM_NOME_2025")["status"].item() == "fora_do_layout"
    assert col.query("ano == 2025 and coluna == 'QT_MAT_FUND'")["tabela"].item() == "matricula"


def test_relatorio_de_continuidade_marca_variacao(tmp_path):
    cache, rel = _cache(tmp_path / "c"), tmp_path / "rel"
    _extrair("censo_matriculas", cache, rel)
    c = pd.read_csv(rel / "grupos_censo_continuidade.csv", keep_default_na=False).set_index("coluna")
    assert len(c) == 124
    # universo: as duas públicas (a 3ª é privada); 2024: (2, 0) → mediana 1; 2025, da matricula: (4, 10) → 7
    assert float(c.loc["QT_MAT_FUND", "mediana_2024"]) == 1 and float(c.loc["QT_MAT_FUND", "mediana_2025"]) == 7
    assert c.loc["QT_MAT_FUND", "marca_2024_2025"] == "VARIOU>50%"
    assert c.loc["QT_DOC_BAS", "marca_2024_2025"] == "VARIOU>50%"
    assert c.loc["QT_SALAS_UTILIZADAS", "marca_2024_2025"] == ""        # escola: (2, 0) nos dois anos
    assert c.loc[SEM_NOME_2025, "marca_2024_2025"] == "SEM_DADO"
    assert float(c.loc["QT_MAT_BAS", "pct_preenchido_2024"]) == 0.0


def test_censo_bruto_v0_nao_mudou():
    """O grupo do estudo E continua lendo 2007–2024, sem a regra de coletada, e fora do ligados.txt."""
    assert list(V0.ANOS_EXTRAIR) == list(range(2007, 2025)) and not hasattr(V0, "coletada")
