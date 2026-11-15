# -*- coding: utf-8 -*-
"""O código do estudo de fatores obedece ao docs/PROTOCOLO.md, seção C — conferido SEM o desfecho real.

Tudo aqui roda com dados sintéticos, de efeitos conhecidos, ou contra o texto do protocolo:
  1. a lista fechada de preditores e os valores fixados do código são os do protocolo (falha se divergir);
  2. com efeitos plantados, o código recupera os coeficientes dentro do IC e dá os vereditos planejados
     (um ASSOCIADO, um SEM ASSOCIAÇÃO PRÁTICA, um INCONCLUSIVO);
  3. sem nenhum efeito além do ano, o ΔR² fica perto de zero e o controle negativo passa;
  4. com um vazamento plantado (um preditor que copia o desfecho), o ΔR² denuncia;
  5. a regra dos 30 e a das reamostragens inválidas funcionam com uma categoria rara;
  6. a GroupKFold nunca põe a mesma escola nos dois lados;
  7. as travas da execução única (sem --executar nada roda; saida/ existente recusa; o controle
     negativo reprovado grava só o 07; toda saída começa com o commit e o sha256 do dataset).

Nenhum número do desfecho real é calculado em nenhum teste.
"""
import importlib.util
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "fatores", RAIZ / "experimentos" / "fatores_2013_2018" / "fatores.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

PROTOCOLO = (RAIZ / "docs" / "PROTOCOLO.md").read_text(encoding="utf-8")
SEC_C = PROTOCOLO.split("\n## C. Protocolo do estudo")[1].split("\n## D. ")[0]   # só a seção C, antes da D


def test_secao_c_recortada_sem_a_d():
    assert "### C.14" in SEC_C, "o recorte perdeu o fim da seção C"
    assert "Depois da execução" not in SEC_C and "## Protocolo registrado" not in SEC_C, \
        "o recorte da seção C invadiu a D ou o protocolo preservado"


# ------------------------------------------------------------------ dados sintéticos (nenhum dado real)
def base_sintetica(n_escolas=160, anos=range(2013, 2019), semente=7, ruido=2.0,
                   b_rural=0.0, b_municipal=0.0, b_dim=None, efeito_ano=None,
                   frac_rural=0.4, frac_municipal=0.3, federais=0, anos_federais=1,
                   iep_quase_constante=False, etapas=("AF",)):
    """Painel com o formato do dataset e efeitos conhecidos. Características no nível da escola
    (constantes nos anos), desfecho = 10 + efeito do ano + efeitos plantados + ruído normal."""
    rng = np.random.default_rng(semente)
    b_dim = b_dim or {}
    efeito_ano = efeito_ano or {}
    itens = [i.lower() for i in F.ITENS]
    linhas = []
    for e in range(n_escolas):
        co = f"E{e:04d}"
        federal = e < federais
        municipal = (not federal) and rng.random() < frac_municipal
        rural = rng.random() < frac_rural
        tem = {i: int(rng.random() < 0.7) for i in itens}
        if iep_quase_constante:
            for i in itens:
                if i.startswith("iep_"):
                    tem[i] = 1
            if e >= n_escolas - 2:            # só as 2 últimas escolas diferem
                tem["iep_computador"] = 0
        dims = {dim: float(np.mean([tem[i] for i in itens if i.startswith(dim[4:7])]))
                for dim in F.DIMENSOES}
        anos_escola = list(anos)[:anos_federais] if federal else list(anos)
        for etapa in etapas:
            for ano in anos_escola:
                y = (10.0 + efeito_ano.get(ano, 0.0) + b_rural * rural + b_municipal * municipal
                     + sum(b_dim.get(d, 0.0) * v for d, v in dims.items())
                     + rng.normal(0.0, ruido))
                linhas.append({"co_entidade": co, "ano": ano, "etapa": etapa, "rede_publica": 1,
                               "localizacao": "Rural" if rural else "Urbana",
                               "dependencia": ("Federal" if federal else
                                               "Municipal" if municipal else "Estadual"),
                               F.DESFECHO: y, F.INDICE: float(np.mean(list(dims.values()))),
                               **tem, **dims})
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ 1. o código contra o protocolo
def test_lista_de_preditores_igual_ao_protocolo():
    tabela_c3 = SEC_C.split("### C.3")[1].split("### C.4")[0]
    no_protocolo = set(re.findall(r"\| `([a-z_]+)` \|", tabela_c3))
    no_codigo = set(F.CATEGORICAS) | set(F.DIMENSOES) | {F.CONTROLE}
    assert no_protocolo == no_codigo, f"lista fechada diverge do protocolo: {no_protocolo ^ no_codigo}"
    for var, ref in F.CATEGORICAS.items():
        assert f"referência: **{ref}**" in tabela_c3, f"referência de {var} diverge"
    for dim, n in F.DIMENSOES.items():
        assert f"`{dim}` | proporção 0–1 | {n} itens" in tabela_c3, f"nº de itens de {dim} diverge"
    assert f"`{F.INDICE}`" in SEC_C and F.INDICE not in no_protocolo  # secundário, fora da lista de fatores


def test_valores_fixados_iguais_aos_do_protocolo():
    assert f"semente {F.SEMENTE}" in SEC_C
    assert "5.000 reamostragens" in SEC_C and F.N_BOOT == 5000
    assert "abaixo de 0,02" in SEC_C and F.LIMIAR_CONTROLE == 0.02
    assert "1,0 pp" in SEC_C and F.MARGEM == 1.0
    assert "passo de **0,25**" in SEC_C and F.PASSO_IIE == 0.25
    assert f"`GroupKFold(n_splits={F.N_DOBRAS})`" in SEC_C
    assert "10 sementes" in SEC_C and F.SEMENTES_MLP == tuple(range(1, 11))
    assert f"menos de {F.MIN_CATEGORIA} escolas-ano" in SEC_C
    assert "mais de 10%" in SEC_C and F.MAX_INVALIDAS == 0.10
    assert f"n_repeats = {F.N_REPETICOES_PERM}" in SEC_C
    assert "t = 2013–2018" in SEC_C and F.JANELA == (2013, 2018)
    assert "t = 2012–2019" in SEC_C and F.JANELA_ROBUSTEZ == (2012, 2019)
    assert F.MODELOS_Q1 == ("linear", "ridge", "mlp")


# ------------------------------------------------------------------ 2. efeitos conhecidos → vereditos planejados
def test_recupera_efeitos_e_da_os_vereditos_planejados():
    # plantado de propósito: Rural +4 pp → ASSOCIADO; dim_iib efeito 0 → SEM ASSOCIAÇÃO PRÁTICA;
    # dim_iep quase constante → INCONCLUSIVO (IC enorme e/ou reamostragens inválidas demais).
    # A semente é fixa: um IC de 95% deixa a verdade de fora 5% das vezes, então a cobertura dos 4
    # fatores vale em ~0,95^4 ≈ 81% dos paineis sintéticos (conferido: 19 de 24 sementes; os vereditos
    # valem em 24 de 24). A semente 1 é um painel em que a cobertura vale.
    d = base_sintetica(b_rural=4.0, iep_quase_constante=True, semente=1)
    u, _ = F.universo_pronto(d, "AF")
    tab = F.c6_inferencia(u, n_boot=400, semente=1).set_index("fator")
    assert tab.loc["localizacao=Rural", "veredito"] == "ASSOCIADO"
    assert tab.loc["dim_iib_prop", "veredito"] == "SEM ASSOCIAÇÃO PRÁTICA"
    assert tab.loc["dim_iep_prop", "veredito"] == "INCONCLUSIVO"
    # recuperação: o efeito verdadeiro cai dentro do IC 95% (na escala do efeito em pp)
    verdades = {"localizacao=Rural": 4.0, "dim_iib_prop": 0.0, "dim_ida_prop": 0.0, "dim_idp_prop": 0.0}
    for fator, verdade in verdades.items():
        lo, hi = tab.loc[fator, ["ic_lo_pp", "ic_hi_pp"]]
        assert lo <= verdade <= hi, f"{fator}: IC [{lo:.2f}, {hi:.2f}] não contém {verdade}"
    # a família F7 junta o modelo principal e o iie_prop do secundário; o ano fica fora
    assert "iie_prop" in tab.index and not any(f.startswith("ano=") for f in tab.index)


def test_vereditos_na_ordem_do_protocolo():
    casos = [
        ((0.01, 2.0, 1.0, 3.0, 0.0), "ASSOCIADO"),
        ((0.50, 0.1, -0.3, 0.5, 0.0), "SEM ASSOCIAÇÃO PRÁTICA"),
        ((0.01, 0.5, 0.2, 0.8, 0.0), "SEM ASSOCIAÇÃO PRÁTICA"),   # p pequeno, efeito < margem
        ((0.20, 1.5, -0.2, 3.0, 0.0), "INCONCLUSIVO"),
        ((0.50, 0.5, -0.5, 1.0, 0.0), "INCONCLUSIVO"),            # IC encosta na margem: não é "dentro"
        ((0.001, 5.0, 4.0, 6.0, 0.2), "INCONCLUSIVO"),            # inválidas demais vencem tudo
    ]
    for args, esperado in casos:
        assert F.c6_veredito(*args) == esperado, args


# ------------------------------------------------------------------ 3. só o ano → ΔR² perto de zero e controle passa
def test_sem_efeito_alem_do_ano():
    d = base_sintetica(efeito_ano={2013: 0, 2014: 2, 2015: 4, 2016: 1, 2017: 6, 2018: 3}, semente=5)
    u, _ = F.universo_pronto(d, "AF")
    q1 = F.c7_q1(u, modelos=("linear",)).set_index(["modelo", "variaveis"])
    assert q1.loc[("linear", "so_ano"), "r2_cv"] > 0.2          # o ano explica de verdade
    assert q1.loc[("linear", "completo"), "delta_r2_cv"] < F.LIMIAR_CONTROLE
    _, passou = F.c9_controle_negativo(u, modelos=("linear",), sementes=(1,))
    assert passou


# ------------------------------------------------------------------ 4. vazamento plantado → o ΔR² denuncia
def test_vazamento_plantado_e_denunciado():
    d = base_sintetica(efeito_ano={2014: 2, 2016: 3}, semente=9)
    u, _ = F.universo_pronto(d, "AF")
    u["dim_iib_prop"] = (u[F.DESFECHO] / u[F.DESFECHO].max()).clip(0, 1)   # copia o desfecho
    q1 = F.c7_q1(u, modelos=("linear",)).set_index(["modelo", "variaveis"])
    assert q1.loc[("linear", "completo"), "delta_r2_cv"] > 0.5, \
        "um preditor que copia o desfecho tem de estourar o ΔR²"


# ------------------------------------------------------------------ 5. regra dos 30 e reamostragens inválidas
def test_regra_dos_30_exclui_categoria_rara_com_contagem():
    d = base_sintetica(federais=4, anos_federais=1, semente=3)    # 4 escolas-ano federais < 30
    u, registro = F.universo_pronto(d, "AF")
    assert "Federal" not in set(u["dependencia"])
    assert registro["categorias_excluidas"] == {"Federal": 4}
    tabela0, _ = F.c13_tabela0(d)
    t_af = tabela0[tabela0["etapa"] == "AF"].set_index("chave")["valor"]
    assert t_af["excluida_regra_30:dependencia=Federal"] == 4


def test_reamostragem_sem_a_categoria_da_coeficiente_na():
    d = base_sintetica(n_escolas=40, frac_municipal=0.0, semente=2)
    d.loc[d["co_entidade"].isin(["E0000", "E0001"]), "dependencia"] = "Municipal"
    u, _ = F.c2_universo(d, "AF")                                  # sem a regra dos 30, de propósito
    X, y = F.matriz_x(u, "principal")
    sem_municipais = np.flatnonzero(~u["co_entidade"].isin(["E0000", "E0001"]).to_numpy())
    coef = F._coef_reamostra(X, y, sem_municipais)
    assert np.isnan(coef["dependencia=Municipal"])
    assert np.isfinite(coef["localizacao=Rural"])


# ------------------------------------------------------------------ 6. GroupKFold nunca mistura escolas
def test_groupkfold_nao_poe_a_mesma_escola_dos_dois_lados():
    u, _ = F.universo_pronto(base_sintetica(n_escolas=40, semente=4), "AF")
    co = u["co_entidade"].to_numpy()
    dobras = F.dobras_por_escola(u)
    assert len(dobras) == F.N_DOBRAS
    for treino, validacao in dobras:
        assert not set(co[treino]) & set(co[validacao])


# ------------------------------------------------------------------ 7. travas da execução única
def test_sem_executar_nada_roda(capsys, monkeypatch):
    def nao_pode(*a, **k):
        raise AssertionError("leu o dataset sem --executar")
    monkeypatch.setattr(F, "ler_dataset", nao_pode)
    assert F.main([]) == 0
    assert "--executar" in capsys.readouterr().out
    assert not F.SAIDA.exists()


def test_executar_recusa_saida_existente(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "SAIDA", tmp_path / "saida")
    (tmp_path / "saida").mkdir()
    chamadas = []
    monkeypatch.setattr(F, "ler_dataset", lambda *a, **k: chamadas.append(1))
    with pytest.raises(SystemExit) as erro:
        F.main(["--executar"])
    assert "única" in str(erro.value)
    assert not chamadas, "com saida/ existente, o dataset nem pode ser lido"


@pytest.fixture
def git_limpo(monkeypatch):
    """Os testes de executar() não dependem do estado do repositório de quem roda os testes."""
    estado = {"commit": "c" * 40, "branch": "branch-de-teste", "limpa": True}
    monkeypatch.setattr(F, "estado_git", lambda: dict(estado))
    return estado


def test_executar_recusa_arvore_suja(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "estado_git", lambda: {"commit": "c" * 40, "branch": "x", "limpa": False})
    def nao_pode(*a, **k):
        raise AssertionError("calculou alguma coisa com a árvore suja")
    monkeypatch.setattr(F, "c13_tabela0", nao_pode)
    pasta = tmp_path / "saida"
    with pytest.raises(SystemExit) as erro:
        F.executar(base_sintetica(n_escolas=10), pasta, caminho_dataset=tmp_path / "nao_lido.csv")
    assert "limpa" in str(erro.value)
    assert not pasta.exists()


def test_estado_git_le_o_repositorio():
    estado = F.estado_git()
    assert re.fullmatch(r"[0-9a-f]{40}", estado["commit"]) and estado["branch"]
    assert isinstance(estado["limpa"], bool)


def _csv_sintetico(tmp_path, d):
    caminho = tmp_path / "sintetico.csv"
    d.to_csv(caminho, index=False)
    return caminho


def test_executar_ordem_cabecalho_e_saidas(tmp_path, git_limpo):
    d = base_sintetica(n_escolas=40, b_rural=3.0, semente=6, etapas=("AF", "EM"))
    arquivo = _csv_sintetico(tmp_path, d)
    pasta = tmp_path / "saida"
    resultado = F.executar(d, pasta, caminho_dataset=arquivo, n_boot=60,
                           modelos=("linear",), sementes=(1,))
    assert resultado.startswith("OK")
    esperados = ["00_universo.csv", "01_itens.csv", "02_correlacao.csv", "03_vif.csv",
                 "04_fatores.csv", "05_r2.csv", "07_controle_negativo.csv", "08_robustez.csv",
                 "fig_forest.png"]
    assert sorted(p.name for p in pasta.iterdir()) == sorted(esperados)   # sem 06: rodou sem o MLP
    import hashlib
    sha = hashlib.sha256(arquivo.read_bytes()).hexdigest()
    for nome in esperados:
        if nome.endswith(".csv"):
            primeira = (pasta / nome).read_text(encoding="utf-8").splitlines()[0]
            assert primeira.startswith(f"# commit={git_limpo['commit']} branch={git_limpo['branch']} ")
            assert f"dataset_sha256={sha}" in primeira
    fatores = pd.read_csv(pasta / "04_fatores.csv", comment="#")
    assert set(fatores["etapa"]) == {"AF", "EM"} and "veredito" in fatores.columns
    robustez = pd.read_csv(pasta / "08_robustez.csv", comment="#")
    assert {"media_por_escola", "janela_2012_2019"} == set(robustez["analise"])
    assert robustez.loc[robustez["analise"] == "janela_2012_2019", "linhas_preditor_vazio"].notna().all()


def test_controle_negativo_reprovado_grava_so_o_07(tmp_path, monkeypatch, git_limpo):
    d = base_sintetica(n_escolas=30, semente=8, etapas=("AF", "EM"))
    arquivo = _csv_sintetico(tmp_path, d)
    reprovado = pd.DataFrame({"modelo": ["linear"], "delta_r2_cv_embaralhado": [0.5],
                              "limiar": [F.LIMIAR_CONTROLE], "passou": [False]})
    monkeypatch.setattr(F, "c9_controle_negativo", lambda *a, **k: (reprovado.copy(), False))
    pasta = tmp_path / "saida"
    resultado = F.executar(d, pasta, caminho_dataset=arquivo, n_boot=50, modelos=("linear",),
                           sementes=(1,))
    assert resultado.startswith("PAROU")
    assert [p.name for p in pasta.iterdir()] == ["07_controle_negativo.csv"]


# ------------------------------------------------------------------ robustez (C.10)
def test_robustez_usa_as_categorias_da_tabela_0():
    """4 escolas federais: 24 escolas-ano em 2013–2018 (saem pela regra dos 30) e 32 em 2012–2019.
    A robustez não reaplica a regra: a Federal continua fora, e as linhas retiradas são relatadas."""
    d = base_sintetica(n_escolas=50, anos=range(2012, 2020), federais=4, anos_federais=8, semente=14)
    d.loc[(d["co_entidade"] == "E0040") & (d["ano"] == 2012), "dim_iib_prop"] = np.nan   # um preditor vazio
    principal, registro = F.universo_pronto(d, "AF")
    assert registro["categorias_excluidas"] == {"Federal": 24}
    tab = F.c10_janela_2012_2019(d, "AF", principal["dependencia"].unique(), n_boot=30)
    assert "dependencia=Federal" not in set(tab["fator"])
    fatores_principal = set(F.c6_inferencia(principal, n_boot=30)["fator"])
    assert set(tab["fator"]) == fatores_principal, "a robustez tem de ter os mesmos fatores do principal"
    assert (tab["linhas_categoria_fora_da_tabela_0"] == 32).all()
    assert (tab["linhas_preditor_vazio"] == 1).all()
    assert "veredito" not in tab.columns and "p_holm" not in tab.columns


# ------------------------------------------------------------------ a figura principal (C.5)
def test_forest_cada_painel_com_os_seus_fatores(tmp_path):
    """AF e EM excluem categorias diferentes pela regra dos 30: cada painel mostra os SEUS fatores."""
    af = base_sintetica(n_escolas=60, semente=12, etapas=("AF",), frac_municipal=0.4)            # sem Federal
    em = base_sintetica(n_escolas=60, semente=13, etapas=("EM",), frac_municipal=0.0, federais=10,
                        anos_federais=6)                                                         # sem Municipal
    d = pd.concat([af, em], ignore_index=True)
    partes = []
    for etapa in F.ETAPAS:
        u, _ = F.universo_pronto(d, etapa)
        partes.append(F.c6_inferencia(u, n_boot=30).assign(etapa=etapa))
    fatores = pd.concat(partes, ignore_index=True)
    esperado = {e: list(fatores.loc[fatores["etapa"] == e, "fator"]) for e in F.ETAPAS}
    assert "dependencia=Municipal" in esperado["AF"] and "dependencia=Federal" not in esperado["AF"]
    assert "dependencia=Federal" in esperado["EM"] and "dependencia=Municipal" not in esperado["EM"]
    rotulos = F.fig_forest(fatores, tmp_path / "forest.png")
    assert rotulos == esperado, "os rótulos de um painel foram parar no outro"


# ------------------------------------------------------------------ fumaça do MLP e da permutação (C.7, C.8)
def test_c7_e_c8_rodam_com_o_mlp_em_miniatura():
    u, _ = F.universo_pronto(base_sintetica(n_escolas=25, semente=10), "AF")
    q1 = F.c7_q1(u, modelos=("mlp",), sementes=(1,))
    assert set(q1["variaveis"]) == {"completo", "so_ano"}
    assert np.isfinite(q1.set_index("variaveis").loc["completo", "delta_r2_cv"])
    perm = F.c8_permutacao(u, sementes=(1,), n_repeticoes=2)
    assert {"grupo:territorio", "grupo:rede", "grupo:infraestrutura", "grupo:ano"} <= set(perm["alvo"])
    assert set(F.CATEGORICAS) | set(F.DIMENSOES) <= set(perm["alvo"])
    assert np.isfinite(perm["queda_r2"]).all() and (perm["ic_lo"] <= perm["ic_hi"]).all()
