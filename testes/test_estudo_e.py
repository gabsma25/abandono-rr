# -*- coding: utf-8 -*-
"""experimentos/censo_bruto_v0/estudo_e.py obedece ao docs/PROTOCOLO.md, seção E — conferido SEM o desfecho real.

Tudo roda com dados sintéticos ou contra o texto do protocolo:
  1. os valores fixados no código são os do protocolo;
  2. a diferença S2 − S1 é pareada no bootstrap (mesmas reamostragens), sem reajuste;
  3. o veredito da F8 e as famílias F9/F10, com Holm, na ordem do protocolo;
  4. a permutação em bloco usa o mesmo sorteio de linhas para todas as colunas, e o ausente vai junto;
  5. o universo é idêntico em S0, S1, S2 e S2r (ausente imputado, linha não sai);
  6. o imputador é ajustado só no treino; as previsões de teste da Parte 2 não usam linhas de teste;
  7. nenhuma linha com t fora de 2013–2018 entra em cálculo (o dataset sintético tem t = 2024, com sentinela);
  8. S0 e S1 reproduzem o código do estudo C (equivalência) e o embaralhamento é o da C.9;
  9. as paradas (filtro, controle negativo, equivalência) gravam só o arquivo que levou à parada; a execução
     completa grava 00–08 e o RELATORIO.md, com o cabeçalho e as ressalvas.

Nenhum número do desfecho real é calculado em nenhum teste."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("estudo_e", RAIZ / "experimentos" / "censo_bruto_v0" / "estudo_e.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
F, B, CL = E.F, E.B, E.CL

PROTOCOLO = (RAIZ / "docs" / "PROTOCOLO.md").read_text(encoding="utf-8")
SEC_E = PROTOCOLO.split("\n## E. Estudo exploratório E (v0)")[1].split("\n## Protocolo registrado")[0]

COLS = ["IN_C", "QT_A", "QT_B", "QT_CONST", "QT_IDADE"]          # as "colunas do Censo" sintéticas
BLOCOS = {"bloco_x": ["QT_A", "QT_B"], "bloco_y": ["IN_C", "QT_CONST"], "matriculas": ["QT_IDADE"]}
SENTINELA = 9.87e6


# ------------------------------------------------------------------ dados sintéticos
def base_e(n_escolas=60, semente=3, efeito_a=0.0):
    """Dataset no formato do v0.2.0 (AF e EM, t = 2013–2018, mais t = 2024 com sentinela) e o Censo sintético."""
    rng = np.random.default_rng(semente)
    linhas, censo = [], []
    for e in range(n_escolas):
        co = f"1400{e:04d}"
        rural = rng.random() < 0.4
        municipal = rng.random() < 0.3
        dims = {d: float(rng.integers(0, 5) / 4) for d in F.DIMENSOES}
        qt_a = rng.normal(50, 15, 20)
        serie = {etapa: 10 + rng.normal(0, 3, 20) + efeito_a * (qt_a - 50) / 15 for etapa in ("AF", "EM")}
        for i, ano in enumerate(range(2011, 2026)):
            if 2013 <= ano <= 2018 or ano == 2024:
                censo.append({"ANO": ano, "CO_ENTIDADE": co, "IN_C": float(rng.random() < 0.5),
                              "QT_A": float(round(qt_a[i])), "QT_B": np.nan if rng.random() < 0.1 else float(e % 7),
                              "QT_CONST": 3.0, "QT_IDADE": float(rng.integers(0, 40))})
            if not (2013 <= ano <= 2018 or ano == 2024):
                continue
            for etapa in ("AF", "EM"):
                s = serie[etapa]
                sent = ano == 2024
                linhas.append({"co_entidade": co, "ano": ano, "etapa": etapa, "rede_publica": 1,
                               "localizacao": "Rural" if rural else "Urbana",
                               "dependencia": "Municipal" if municipal else "Estadual",
                               **dims, "iie_prop": float(np.mean(list(dims.values()))),
                               "abandono_t": SENTINELA if sent else max(s[i], 0.0),
                               "abandono_tm1": SENTINELA if sent else max(s[i - 1], 0.0),
                               "reprovacao_tm1": float(rng.uniform(0, 20)),
                               "variacao_abandono_defasada": float(s[i - 1] - s[i - 2]),
                               "abandono_t1": SENTINELA if sent else max(s[i + 1], 0.0)})
    d = pd.DataFrame(linhas)
    d["alto_risco_t1"] = d.groupby(["etapa", "ano"])["abandono_t1"].transform(lambda v: CL.rotular(v.to_numpy()))
    c = pd.DataFrame(censo)
    c["ANO"] = c["ANO"].astype("Int16")
    c["CO_ENTIDADE"] = c["CO_ENTIDADE"].astype("string")
    for col in COLS:
        c[col] = c[col].astype("Float64")
    return d, c


def filtro_ok(colunas=COLS):
    return pd.DataFrame({"coluna": ["CO_ENTIDADE"] + list(colunas),
                         "motivo": ["tipo"] + ["PASSA"] * len(colunas),
                         "preench_min": [np.nan] + [100.0] * len(colunas),
                         "valor_dominante_pct": [np.nan] + [50.0] * len(colunas)})


ESTADO = {"commit": "c" * 40, "branch": "branch-de-teste", "limpa": True}


def ref_do_c(d, caminho, modelos=("linear", "ridge"), sementes=(1,)):
    """Um 05_r2.csv calculado pelo código do estudo C nos universos sintéticos (para a equivalência passar)."""
    partes = []
    for etapa in F.ETAPAS:
        u, _ = F.universo_pronto(E.na_janela(d), etapa)
        partes.append(F.c7_q1(u, modelos, sementes).assign(etapa=etapa))
    ref = pd.concat(partes, ignore_index=True)
    F.gravar(ref[["etapa"] + [c for c in ref.columns if c != "etapa"]], caminho, "# cabecalho")
    return caminho


# ------------------------------------------------------------------ 1. valores fixados
def test_valores_fixados_iguais_aos_do_protocolo():
    assert f"semente **{E.SEMENTE_E}**" in SEC_E and E.SEMENTE_E == 20261120
    assert "5.000\n  reamostragens" in SEC_E or "5.000 reamostragens" in SEC_E
    assert E.N_BOOT == 5000
    assert "**Margem prática: 0,02 de R².**" in SEC_E and E.MARGEM_R2 == 0.02
    assert "margem +0,10 no\nRecall@20%" in SEC_E and E.MARGEM_RECALL == 0.10
    assert "treino t = 2013–2016" in SEC_E and E.TREINO == (2013, 2016)
    assert "teste t = 2017–2018" in SEC_E and E.TESTE == (2017, 2018)
    assert "`n_repeats = 20`" in SEC_E and E.N_REPETICOES_PERM == 20
    assert "semente 20261115 da C.9" in SEC_E and E.SEMENTE_CONTROLE == 20261115
    assert "diferença menor que 1e-6" in SEC_E and E.TOL_EQUIVALENCIA == 1e-6
    assert "critério continua ΔR² < 0,02" in SEC_E and E.LIMIAR_CONTROLE == 0.02
    assert E.JANELA == (2013, 2018) and E.SEMENTES_MLP == tuple(range(1, 11))
    assert E.CONJUNTOS_P1 == ("S0", "S1", "S2", "S2r") and E.CONJUNTOS_P2 == ("A", "A+", "B", "B+")
    for c in E.RENDIMENTO_A:
        assert f"`{c}`" in SEC_E.split("| **A** |")[1].split("\n")[0]


# ------------------------------------------------------------------ 2. S2 − S1 pareada
def test_diferenca_s2_menos_s1_pareada_no_bootstrap():
    rng = np.random.default_rng(0)
    n = 200
    u = pd.DataFrame({"co_entidade": [f"E{i // 4}" for i in range(n)]})
    y = rng.normal(10, 3, n)
    p1, p2 = y + rng.normal(0, 3, n), y + rng.normal(0, 2, n)
    sorteios = F._sorteios_escolas(u, 30, np.random.default_rng(1))
    ponto, dist = E.dif_r2_bootstrap(y, [p1], [p2], sorteios)
    assert ponto == pytest.approx(E._r2(y, p2) - E._r2(y, p1))
    for idx, v in zip(sorteios, dist):                     # mesma reamostragem para S1 e S2, sem reajuste
        assert v == pytest.approx(E._r2(y[idx], p2[idx]) - E._r2(y[idx], p1[idx]))
    _, zero = E.dif_r2_bootstrap(y, [p1], [p1.copy()], sorteios)
    assert np.all(zero == 0)                               # pareada: previsões iguais → diferença zero exata
    # MLP: o R² de cada semente e depois a média
    ponto_m, _ = E.dif_r2_bootstrap(y, [p1, p1 + 1], [p2, p2 - 1], sorteios[:2])
    assert ponto_m == pytest.approx(np.mean([E._r2(y, p2), E._r2(y, p2 - 1)])
                                    - np.mean([E._r2(y, p1), E._r2(y, p1 + 1)]))


# ------------------------------------------------------------------ 3. vereditos e famílias
def test_veredito_f8_na_ordem_do_protocolo():
    assert E.veredito_f8(0.03, 0.01, 0.05) == "ACRESCENTA"
    assert E.veredito_f8(0.02, 0.05, 0.04) == "ACRESCENTA"            # nos limites, inclusive
    assert E.veredito_f8(0.01, 0.001, 0.019) == "NÃO ACRESCENTA"      # p pequeno, abaixo da margem
    assert E.veredito_f8(-0.05, 0.001, -0.01) == "NÃO ACRESCENTA"     # negativa é resultado, não defeito
    assert E.veredito_f8(0.01, 0.01, 0.02) == "INCONCLUSIVO"          # IC encosta na margem
    assert E.veredito_f8(0.03, 0.20, 0.08) == "INCONCLUSIVO"
    assert E.veredito_f8(np.nan, 0.01, 0.05) == "INCONCLUSIVO"


def test_f8_holm_so_na_ridge_af_em():
    res = {e: {m: {"diferenca": d, "ic_lo": d - .01, "ic_hi": d + .01, "p": p, "n_reamostragens_validas": 10}
               for m, d, p in (("linear", 0.05, 0.001), ("ridge", 0.05, p_r), ("mlp", 0.0, 0.9))}
           for e, p_r in (("AF", 0.01), ("EM", 0.04))}
    tab = E.f8(res).set_index(["etapa", "modelo"])
    assert tab.loc[("AF", "ridge"), "p_holm"] == pytest.approx(0.02)
    assert tab.loc[("EM", "ridge"), "p_holm"] == pytest.approx(0.04)
    assert tab.loc[("AF", "ridge"), "veredito"] == "ACRESCENTA" and tab.loc[("AF", "ridge"), "n_familia"] == 2
    assert tab.loc[("AF", "linear"), "familia"] == "descritiva" and tab.loc[("AF", "linear"), "veredito"] == ""
    assert np.isnan(tab.loc[("AF", "mlp"), "p_holm"])


def test_familias_f9_f10_com_holm_e_leitura():
    rng = np.random.default_rng(4)
    valores, dists = {}, {}
    for etapa, ganho in (("AF", 0.15), ("EM", 0.0)):
        base = rng.normal(0.4, 0.02, 400)
        v = {("régua", "B1R_lag"): 0.4, ("régua", "B2"): 0.3}
        d = {("régua", "B1R_lag"): base, ("régua", "B2"): base - 0.1}
        for conj in E.CONJUNTOS_P2:
            for m in E.MODELOS_P2:
                v[(conj, m)] = 0.4 + ganho
                d[(conj, m)] = base + ganho + rng.normal(0, 0.01, 400)
        valores[etapa], dists[etapa] = v, d
    tab = E.testes_p2(valores, dists)
    for fam in ("F9", "F10"):
        t = tab[tab["familia"] == fam]
        assert len(t) == 4 and (t["n_familia"] == 4).all()                 # 2 modelos × 2 etapas
        assert np.allclose(t["p_holm"], B.holm(t["p"].to_numpy()))
        for r in t.itertuples():
            assert r.veredito == CL.leitura("Rec@20pct", r.diferenca, r.ic_lo, r.ic_hi, r.p_holm, margem=0.10)
    f9 = tab[tab["familia"] == "F9"].set_index(["etapa", "modelo"])
    assert f9.loc[("AF", "ridge"), "veredito"] == "GANHO"
    assert f9.loc[("EM", "ridge"), "veredito"] == "SEM GANHO PRÁTICO"
    desc = tab[tab["familia"] == "descritiva"]
    assert (desc["veredito"] == "").all() and desc["p_holm"].isna().all()
    assert set(desc["comparacao"]) >= {"ridge A+ − ridge A", "mlp B+ − mlp B", "ridge A − mlp A"}


# ------------------------------------------------------------------ 4. permutação em bloco
def test_permutacao_em_bloco_mesmo_sorteio_e_ausente_acompanha():
    ent = pd.DataFrame({"QT_A": [1.0, 2.0, np.nan, 4.0], "QT_B": [10.0, np.nan, 30.0, 40.0], "QT_C": [7.0] * 4})
    ordem = np.array([2, 0, 3, 1])
    emb = E.permutar(ent, ["QT_A", "QT_B"], ordem)
    assert emb["QT_A"].tolist()[1:] == [1.0, 4.0, 2.0] and np.isnan(emb["QT_A"].iloc[0])
    assert emb["QT_B"].tolist()[0] == 30.0 and np.isnan(emb["QT_B"].iloc[3])
    for i, j in enumerate(ordem):                          # a linha i recebe a linha j inteira do bloco
        assert emb.iloc[i][["QT_A", "QT_B"]].equals(ent.iloc[j][["QT_A", "QT_B"]])
    assert emb["QT_C"].equals(ent["QT_C"]) and ent["QT_A"].iloc[0] == 1.0   # fora do bloco e original intactos
    alvos = E.alvos_permutacao(["QT_A", "QT_B"], BLOCOS)
    assert alvos["bloco:bloco_x"] == ("bloco", "bloco_x", ["QT_A", "QT_B"])
    assert "bloco:bloco_y" not in alvos                    # bloco sem coluna no modelo da etapa não aparece
    assert alvos["bloco:infraestrutura"][2] == list(F.DIMENSOES) and "bloco:ano" in alvos


# ------------------------------------------------------------------ 5. universo idêntico; 6. imputador no treino
def _universo_p1(d, c, etapa="AF"):
    dd = E.juntar_censo(E.na_janela(d), c, COLS)
    u, _ = F.universo_pronto(dd, etapa)
    return u


def test_universo_identico_em_s0_s1_s2_e_s2r():
    d, c = base_e(n_escolas=40)
    u = _universo_p1(d, c)
    assert u["QT_B"].isna().any()                          # há ausente nas colunas novas...
    dobras = F.dobras_por_escola(u)
    novas = [x for x in COLS if x not in E.constantes(u, COLS)]
    prev = E.prever_p1(u, E.CONJUNTOS_P1, {"S2": novas, "S2r": [x for x in novas if x != "QT_IDADE"]},
                       ("linear", "ridge"), (1,), dobras)
    for (conj, modelo), rs in prev.items():
        dentro, fora = rs[0]
        assert len(fora) == len(dentro) == len(u) and np.isfinite(fora).all(), (conj, modelo)   # ...e nenhuma linha sai
    assert "QT_CONST" in E.constantes(u, COLS)


def test_imputador_ajustado_so_no_treino():
    d, c = base_e(n_escolas=40)
    u = _universo_p1(d, c)
    u.loc[u.index[: len(u) // 2], "QT_A"] += 1000            # o treino e o resto têm medianas bem diferentes
    novas = ["QT_A", "QT_B"]
    tr = np.arange(len(u) // 2)
    ent = u[E.entradas_p1("S2", novas)]
    pipe = E._ajustar(E.pipeline_p1("ridge", "S2", novas), ent.iloc[tr], u[E.DESFECHO].to_numpy()[tr] / 100)
    imp = pipe.named_steps["pre"].named_transformers_["novas"].named_steps["imp"]
    assert np.allclose(imp.statistics_, ent.iloc[tr][novas].median().to_numpy())
    assert not np.isclose(imp.statistics_[0], ent["QT_A"].median())
    assert imp.add_indicator


def test_previsoes_de_teste_da_parte2_sem_linhas_de_teste(monkeypatch):
    d, c = base_e(n_escolas=40)
    dd = E.juntar_censo(E.na_janela(d), c, COLS)
    v = E.universo_p2(dd, "AF")
    vistos = []
    orig = E._ajustar
    monkeypatch.setattr(E, "_ajustar", lambda p, X, y: (vistos.append(X["ano"].copy()), orig(p, X, y))[1])
    te, prev = E.prever_p2(v, ["QT_A", "QT_B", "IN_C"], ("ridge", "mlp"), (1,))
    assert len(vistos) == len(E.CONJUNTOS_P2) * 2
    for anos in vistos:
        assert anos.between(*E.TREINO).all() and not anos.between(*E.TESTE).any()
    assert set(te["ano"]) == {2017, 2018} and list(te["ano"]) == sorted(te["ano"])
    assert all(len(n) == len(te) for notas in prev.values() for n in notas)
    assert np.array_equal(prev[("régua", "B1R_lag")][0], te["abandono_tm1"].to_numpy())


def test_numericas_dos_conjuntos_da_parte2():
    assert E.numericas_p2("A", ["X"]) == E.RENDIMENTO_A + E.DIMS
    assert E.numericas_p2("A+", ["X"]) == E.RENDIMENTO_A + E.DIMS + ["X"]
    assert E.numericas_p2("B", ["X"]) == E.DIMS and E.numericas_p2("B+", ["X"]) == E.DIMS + ["X"]
    for conj in E.CONJUNTOS_P2:                            # o abandono_t (e a reprovação de t) nunca entra em X
        assert not {"abandono_t", "reprovacao_t", "aprovacao_t", "abandono_t1"} & set(E.numericas_p2(conj, ["X"]))


# ------------------------------------------------------------------ 7. nenhuma linha fora de 2013–2018
def test_nenhuma_linha_fora_da_janela(tmp_path, monkeypatch):
    d, c = base_e(n_escolas=40)
    assert (d["ano"] == 2024).any() and (d["abandono_t"] == SENTINELA).any()
    vistos = []
    orig = E._ajustar
    monkeypatch.setattr(E, "_ajustar", lambda p, X, y: (vistos.append(X["ano"].copy()), orig(p, X, y))[1])
    ref = ref_do_c(d, tmp_path / "ref.csv")
    res = E.executar(d, c, filtro_ok(), tmp_path / "saida", caminho_dataset=ref, estado=ESTADO, ref_c=ref,
                     colunas=COLS, blocos=BLOCOS, faixas=["QT_IDADE"], n_boot=20, modelos=("linear", "ridge"),
                     sementes=(1,), n_repeticoes=1)
    assert res.startswith("OK"), res
    assert vistos and all(a.between(2013, 2018).all() for a in vistos)
    for f in (tmp_path / "saida").iterdir():
        assert "9870000" not in f.read_text(encoding="utf-8"), f.name
    with pytest.raises(AssertionError):
        E._conferir_janela(d)                              # o próprio código para se uma linha de 2024 chegar


# ------------------------------------------------------------------ 8. equivalência com o código do estudo C
def test_s0_s1_reproduzem_o_codigo_do_estudo_c():
    d, c = base_e(n_escolas=40)
    u = _universo_p1(d, c)
    dobras = F.dobras_por_escola(u)
    prev = E.prever_p1(u, ("S0", "S1"), {}, ("linear", "ridge", "mlp"), (1,), dobras)
    meu = E.tabela_r2(u, prev, {}).set_index(["conjunto", "modelo"])
    c7 = F.c7_q1(u, ("linear", "ridge", "mlp"), (1,)).set_index(["modelo", "variaveis"])
    for m in ("linear", "ridge", "mlp"):
        assert abs(meu.loc[("S0", m), "r2_cv"] - c7.loc[(m, "so_ano"), "r2_cv"]) < 1e-12
        assert abs(meu.loc[("S1", m), "r2_cv"] - c7.loc[(m, "completo"), "r2_cv"]) < 1e-12
        assert abs(meu.loc[("S1", m), "delta_r2_cv"] - c7.loc[(m, "completo"), "delta_r2_cv"]) < 1e-12
        assert abs(meu.loc[("S1", m), "r2_dentro"] - c7.loc[(m, "completo"), "r2_dentro"]) < 1e-12


def test_embaralhamento_igual_ao_da_c9(monkeypatch):
    d, c = base_e(n_escolas=30)
    u = _universo_p1(d, c)
    capturado = {}
    orig_c7 = F.c7_q1

    def falso_c7(emb, *a, **k):
        capturado["emb"] = emb.copy()
        return orig_c7(emb, *a, **k)
    monkeypatch.setattr(F, "c7_q1", falso_c7)
    tab_c, _ = F.c9_controle_negativo(u, modelos=("linear",), sementes=(1,))
    monkeypatch.setattr(F, "c7_q1", orig_c7)
    assert np.array_equal(capturado["emb"][E.DESFECHO].to_numpy(), E.embaralhar(u)[E.DESFECHO].to_numpy())
    meu = E.controle_negativo(u, ["QT_A", "QT_B"], ("linear",), (1,), F.dobras_por_escola(u)).set_index("conjunto")
    assert meu.loc["S1", "delta_r2_cv_embaralhado"] == pytest.approx(tab_c.loc[0, "delta_r2_cv_embaralhado"], abs=1e-12)
    assert set(meu.index) == {"S1", "S2"} and meu["passou"].dtype == bool


def test_equivalencia_para_so_em_linear_e_ridge():
    tab = pd.DataFrame({"conjunto": ["S0", "S1"] * 2, "modelo": ["ridge"] * 2 + ["mlp"] * 2,
                        "r2_cv": [0.1, 0.2, 0.1, 0.2], "delta_r2_cv": [np.nan, 0.1, np.nan, 0.1]})
    ref = pd.DataFrame({"etapa": "AF", "modelo": ["ridge", "ridge", "mlp", "mlp"],
                        "variaveis": ["so_ano", "completo"] * 2, "r2_cv": [0.1, 0.2, 0.1, 0.3],
                        "delta_r2_cv": [np.nan, 0.1, np.nan, 0.2]})
    eq = E.equivalencia(tab, ref, "AF")
    assert eq.loc[eq["decide"], "passou"].all()
    assert eq.loc[~eq["decide"], "passou"].isna().all() and (eq.loc[~eq["decide"], "diferenca_abs"] > 0).any()
    ref.loc[1, "r2_cv"] += 2e-6
    assert not E.equivalencia(tab, ref, "AF").loc[lambda x: x["decide"], "passou"].all()


# ------------------------------------------------------------------ 9. paradas e execução completa
def _rodar(tmp_path, d, c, **kw):
    ref = kw.pop("ref", None) or ref_do_c(d, tmp_path / "ref.csv")
    d.to_csv(tmp_path / "dataset.csv", index=False)
    args = dict(caminho_dataset=tmp_path / "dataset.csv", estado=ESTADO, ref_c=ref, colunas=COLS, blocos=BLOCOS, faixas=["QT_IDADE"],
                n_boot=20, modelos=("linear", "ridge"), sementes=(1,), n_repeticoes=1)
    args.update(kw)
    filtro = args.pop("filtro", filtro_ok())
    return E.executar(d, c, filtro, tmp_path / "saida", **args)


def test_filtro_diferente_da_lista_para(tmp_path):
    d, c = base_e(n_escolas=20)
    filtro = filtro_ok()
    filtro.loc[filtro["coluna"] == "QT_B", "motivo"] = "preenchimento"
    res = _rodar(tmp_path, d, c, filtro=filtro, ref=tmp_path / "nao_lido.csv")
    assert res.startswith("PAROU")
    assert [p.name for p in (tmp_path / "saida").iterdir()] == ["00_filtro.csv"]


def test_controle_negativo_reprovado_grava_so_o_02(tmp_path, monkeypatch):
    d, c = base_e(n_escolas=20)
    reprovado = pd.DataFrame({"conjunto": ["S2"], "modelo": ["linear"], "delta_r2_cv_embaralhado": [0.5],
                              "limiar": [0.02], "passou": [False]})
    monkeypatch.setattr(E, "controle_negativo", lambda *a, **k: reprovado.copy())
    res = _rodar(tmp_path, d, c, ref=tmp_path / "nao_lido.csv")
    assert res.startswith("PAROU")
    assert [p.name for p in (tmp_path / "saida").iterdir()] == ["02_controle_negativo.csv"]


def test_equivalencia_reprovada_grava_so_o_03(tmp_path):
    d, c = base_e(n_escolas=30)
    ref = ref_do_c(d, tmp_path / "ref.csv")
    tab = pd.read_csv(ref, skiprows=1)
    tab.loc[0, "r2_cv"] += 0.01
    F.gravar(tab, ref, "# cabecalho")
    res = _rodar(tmp_path, d, c, ref=ref)
    assert res.startswith("PAROU")
    assert [p.name for p in (tmp_path / "saida").iterdir()] == ["03_equivalencia_c.csv"]


def test_execucao_completa_grava_tudo_com_cabecalho_e_relatorio(tmp_path):
    d, c = base_e(n_escolas=50, efeito_a=3.0)
    res = _rodar(tmp_path, d, c, modelos=("linear", "ridge", "mlp"),
                 ref=ref_do_c(d, tmp_path / "ref.csv", modelos=("linear", "ridge", "mlp")))
    assert res.startswith("OK"), res
    pasta = tmp_path / "saida"
    esperados = ["00_filtro.csv", "01_universo.csv", "02_controle_negativo.csv", "03_equivalencia_c.csv",
                 "04_r2.csv", "05_f8.csv", "06_permutacao.csv", "07_previsao_metricas.csv",
                 "08_previsao_testes.csv", "RELATORIO.md"]
    assert sorted(p.name for p in pasta.iterdir()) == esperados
    for nome in esperados[:-1]:
        primeira = (pasta / nome).read_text(encoding="utf-8").splitlines()[0]
        assert primeira.startswith(f"# commit={'c' * 40} branch=branch-de-teste dataset_sha256=")
    r2 = pd.read_csv(pasta / "04_r2.csv", skiprows=1)
    assert len(r2) == 2 * 4 * 3 and r2.groupby("etapa")["n_escolas_ano"].nunique().eq(1).all()
    assert r2.loc[r2["conjunto"] == "S2r", "n_colunas_novas"].eq(3).all()          # sem a faixa de idade
    univ = pd.read_csv(pasta / "01_universo.csv", skiprows=1)
    assert "constante_retirada:QT_CONST" in set(univ["chave"])
    f8 = pd.read_csv(pasta / "05_f8.csv", skiprows=1)
    assert set(f8.loc[f8["familia"] == "F8", "etapa"]) == {"AF", "EM"} and (f8["familia"] == "F8").sum() == 2
    tes = pd.read_csv(pasta / "08_previsao_testes.csv", skiprows=1)
    assert (tes["familia"] == "F9").sum() == 4 and (tes["familia"] == "F10").sum() == 4
    perm = pd.read_csv(pasta / "06_permutacao.csv", skiprows=1)
    assert set(perm["modelo"]) == {"ridge", "mlp"} and "bloco:bloco_x" in set(perm["alvo"])
    rel = (pasta / "RELATORIO.md").read_text(encoding="utf-8")
    for trecho in ("É exploratório", "Anos já vistos", "Colunas brutas", "Desvio declarado da regra B.6",
                   "Não responde (E.9)", "## Parte 1 — E1: S2 − S1", "F9", "F10", "As 15 colunas"):
        assert trecho in rel, trecho


def test_main_recusa_saida_existente(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "SAIDA", tmp_path / "saida")
    (tmp_path / "saida").mkdir()
    monkeypatch.setattr(E, "ler_dataset", lambda *a, **k: (_ for _ in ()).throw(AssertionError("leu o dataset")))
    with pytest.raises(SystemExit) as erro:
        E.main([])
    assert "única" in str(erro.value)


def test_main_recusa_sem_push_ou_com_arvore_suja(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "SAIDA", tmp_path / "saida")
    monkeypatch.setattr(E, "ler_dataset", lambda *a, **k: (_ for _ in ()).throw(AssertionError("leu o dataset")))
    for estado, trecho in (({**ESTADO, "limpa": False, "nao_rastreados_no_codigo": ["x.py"], "publicado": True},
                            "não rastreado"),
                           ({**ESTADO, "limpa": True, "nao_rastreados_no_codigo": [], "publicado": False}, "push")):
        monkeypatch.setattr(E, "estado_git", lambda e=estado: dict(e))
        with pytest.raises(SystemExit) as erro:
            E.main([])
        assert trecho in str(erro.value)
    assert not (tmp_path / "saida").exists()
