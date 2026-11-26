# -*- coding: utf-8 -*-
"""
Estudo exploratório E (v0) — colunas brutas do Censo, por filtro mecânico. Implementação do docs/PROTOCOLO.md,
seção E (escrita antes de qualquer execução; decisão no docs/DECISOES.md, 2026-11-20).

RODA UMA VEZ: `python experimentos/censo_bruto_v0/estudo_e.py`, depois do commit e do push do protocolo e deste
código. Lê dataset/escolas_rr_v0.2.0.csv, o cache do Censo por meio do grupo src/estendida/grupos/censo_bruto_v0.py
(não ligado), as funções de src/avaliacao/ e as do estudo C (experimentos/fatores_2013_2018/fatores.py, reutilizadas
por importlib). Escreve só em saida/, nesta pasta.

Travas da execução única (E.8 e seção D):
  - recusa rodar se saida/ existir;
  - recusa rodar se algum arquivo rastreado tiver conteúdo diferente do commit, se houver arquivo não rastreado
    no código que roda (src/, esta pasta, o estudo C) ou se o commit não estiver publicado num branch remoto (o push é a data
    pública de que o protocolo veio antes do resultado);
  - toda saída começa com o commit, o branch, o sha256 do dataset e a data;
  - nenhuma linha com t fora de 2013–2018 entra em cálculo (o dataset tem t = 2024, desfecho 2025: fica fechado);
  - ordem (E.8): filtro → controle negativo → equivalência com o estudo C → Parte 1 → Parte 2. Tudo é calculado
    em memória e gravado no fim; se parar, grava só o arquivo que levou à parada.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
RAIZ = next(p for p in PASTA.parents if (p / "src" / "avaliacao").is_dir())


def _modulo(caminho, nome):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


F = _modulo(RAIZ / "experimentos" / "fatores_2013_2018" / "fatores.py", "fatores_c")      # o estudo C (E.3)
G = _modulo(RAIZ / "src" / "estendida" / "grupos" / "censo_bruto_v0.py", "grupo_censo_bruto_v0")  # E.2
import bootstrap as B  # noqa: E402  (o fatores.py põe src/avaliacao no caminho)
import baselines as BL  # noqa: E402
import classificacao as CL  # noqa: E402
import metricas as M  # noqa: E402

from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.linear_model import Ridge  # noqa: E402
from sklearn.neural_network import MLPRegressor  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402

DATASET = F.DATASET
SAIDA = PASTA / "saida"
REF_C = RAIZ / "experimentos" / "fatores_2013_2018" / "saida" / "05_r2.csv"   # E.4: equivalência

# ------------------------------------------------------------------ valores fixados no protocolo (seção E)
SEMENTE_E = 20261120                  # E.4 (bootstrap da F8), E.5 (bootstrap da Parte 2), E.6 (permutação)
SEMENTE_CONTROLE = F.SEMENTE          # E.4: o controle negativo usa a semente 20261115 da C.9
N_BOOT = 5000                         # E.4, E.5
MARGEM_R2 = 0.02                      # E.4: margem prática da F8 (a do controle negativo, C.9)
MARGEM_RECALL = 0.10                  # E.5: margem do Recall@20% (classificacao.leitura)
TREINO = (2013, 2016)                 # E.5: t do treino (desfechos 2014–2017)
TESTE = (2017, 2018)                  # E.5: t do teste (desfechos 2018–2019, já vistos)
JANELA = F.JANELA                     # E.3: t = 2013–2018
ALFA = 0.05                           # E.4, E.5 (Holm)
TOL_EQUIVALENCIA = 1e-6               # E.4: S0 e S1 contra o 05_r2.csv do estudo C
LIMIAR_CONTROLE = F.LIMIAR_CONTROLE   # E.4: ΔR² < 0,02 no desfecho embaralhado (C.9)
FRACAO_TOPO = 0.20                    # E.5: Recall@20%
N_REPETICOES_PERM = 20                # E.6
SEMENTES_MLP = F.SEMENTES_MLP         # E.3: as 10 sementes do MLP do professor
ETAPAS = F.ETAPAS                     # E.3: AF e EM separados
DESFECHO = F.DESFECHO                 # E.3: abandono_t (Parte 1)
DESFECHO_P2 = "abandono_t1"           # E.5
ROTULO_P2 = "alto_risco_t1"           # E.5
MODELOS_P1 = ("linear", "ridge", "mlp")       # E.4
MODELOS_P2 = ("ridge", "mlp")                 # E.5 (mais as réguas B1R_lag e B2)
CONJUNTOS_P1 = ("S0", "S1", "S2", "S2r")      # E.4
CONJUNTOS_P2 = ("A", "A+", "B", "B+")         # E.5
CATEGORICAS = list(F.CATEGORICAS)             # localizacao, dependencia
DIMS = list(F.DIMENSOES)                      # as quatro dim_*_prop
RENDIMENTO_A = ["abandono_tm1", "reprovacao_tm1", "variacao_abandono_defasada"]   # E.5, conjunto A
BLOCOS_C = {"territorio": ["localizacao"], "rede": ["dependencia"], "infraestrutura": DIMS,
            "ano": [F.CONTROLE]}              # E.6: os blocos do estudo C (o ano só relatado)
CHAVE = ["ano", "co_entidade"]


# ------------------------------------------------------------------ dados: o dataset + o grupo (E.2)
def ler_dataset(caminho=DATASET):
    """O dataset versionado, só com t na janela: nenhuma linha fora de 2013–2018 entra em cálculo (E.5)."""
    return na_janela(F.ler_dataset(caminho))


def na_janela(d):
    d = d[d["ano"].between(*JANELA)].copy()
    _conferir_janela(d)
    return d


def _conferir_janela(tab):
    if len(tab) and not tab["ano"].between(*JANELA).all():
        raise AssertionError("linha com t fora de 2013–2018 chegou a um cálculo")


def juntar_censo(d, censo, colunas):
    """E.2: o resultado de extrair() junto ao dataset por (ano, co_entidade), how="left", validate="m:1"
    (regra 9). As colunas da linha são as do Censo do próprio ano t."""
    c = censo.rename(columns={"ANO": "ano", "CO_ENTIDADE": "co_entidade"})[CHAVE + list(colunas)].copy()
    c["ano"] = c["ano"].astype("int64")
    c["co_entidade"] = c["co_entidade"].astype(str)
    c = c[c["ano"].between(*JANELA)]
    for col in colunas:
        c[col] = c[col].astype("Float64").astype("float64")        # <NA> → NaN (ausente, nunca 0)
    d = d.copy()
    d["co_entidade"] = d["co_entidade"].astype(str)
    n = len(d)
    out = d.merge(c, on=CHAVE, how="left", validate="m:1")
    if len(out) != n:
        raise AssertionError("a junção com o Censo mudou o número de linhas")
    _conferir_janela(out)
    return out


def constantes(u, colunas):
    """E.2: coluna com um único valor não ausente (ou nenhum) no universo da etapa sai daquela etapa."""
    return [c for c in colunas if u[c].nunique(dropna=True) <= 1]


# ------------------------------------------------------------------ pipelines e ajustes (E.3, E.4, E.5)
def _novas():
    """E.4/E.5: colunas numéricas novas — imputação pela mediana com indicador, depois padronização."""
    return Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)), ("pad", StandardScaler())])


def _mlp(semente):
    """O MLP do exemplo do professor, como na C.7 (sem ajuste)."""
    return MLPRegressor(hidden_layer_sizes=(50,), activation="logistic", solver="adam",
                        max_iter=5000, tol=1e-7, momentum=0.8, early_stopping=True, epsilon=1e-08,
                        n_iter_no_change=10, random_state=semente)


def pipeline_p1(modelo, conjunto, novas=(), semente=None):
    """E.4: S0 e S1 são exatamente o pipeline da C.7 (F._pipeline_q1); S2 e S2r acrescentam as colunas novas
    com imputação e padronização, ajustadas só no treino de cada dobra (regra 5)."""
    if conjunto in ("S0", "S1"):
        return F._pipeline_q1(modelo, so_ano=(conjunto == "S0"), semente=semente)
    base = F._pipeline_q1(modelo, so_ano=False, semente=semente)
    partes = list(base.named_steps["pre"].transformers) + [("novas", _novas(), list(novas))]
    return Pipeline([("pre", ColumnTransformer(partes, remainder="drop")), ("m", base.named_steps["m"])])


def pipeline_p2(modelo, numericas, semente=None):
    """E.5: numéricas com SimpleImputer(median, add_indicator=True) + StandardScaler; categóricas com
    OneHotEncoder(handle_unknown="ignore"); tudo ajustado só no treino."""
    pre = ColumnTransformer([("num", _novas(), list(numericas)),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS)], remainder="drop")
    if modelo == "ridge":
        est = Ridge(alpha=1.0)
    elif modelo == "mlp":
        est = _mlp(semente)
    else:
        raise ValueError(modelo)
    return Pipeline([("pre", pre), ("m", est)])


def _ajustar(pipe, X, y):
    """Todo ajuste passa por aqui (os testes conferem quais linhas cada ajuste usou). X sempre leva a coluna
    `ano` para a conferência da janela; na Parte 2 ela não é preditor (o ColumnTransformer descarta o resto)."""
    if "ano" not in X:
        raise AssertionError("ajuste sem a coluna ano: não dá para conferir a janela")
    _conferir_janela(X)
    return pipe.fit(X, y)


def _r2(y, p):
    sst = float(((y - y.mean()) ** 2).sum())
    return 1.0 - float(((y - p) ** 2).sum()) / sst if sst > 0 else np.nan


# ------------------------------------------------------------------ Parte 1 (E.4): previsões e métricas
def entradas_p1(conjunto, novas):
    base = CATEGORICAS + DIMS + [F.CONTROLE]
    return base + list(novas) if conjunto in ("S2", "S2r") else base


def rodada_p1(u, modelo, conjunto, novas, semente, dobras):
    """Uma passada: ajuste na amostra inteira (dentro) e fora-da-dobra (previsões agrupadas), em pp; alvo ÷ 100."""
    ent = u[entradas_p1(conjunto, novas)]
    y = u[DESFECHO].astype("float64").to_numpy()
    pipe = _ajustar(pipeline_p1(modelo, conjunto, novas, semente), ent, y / 100.0)
    dentro = pipe.predict(ent) * 100.0
    fora = np.full(len(u), np.nan)
    for tr, va in dobras:
        p = _ajustar(pipeline_p1(modelo, conjunto, novas, semente), ent.iloc[tr], y[tr] / 100.0)
        fora[va] = p.predict(ent.iloc[va]) * 100.0
    return dentro, fora


def prever_p1(u, conjuntos, novas_por_conjunto, modelos, sementes, dobras, aviso=""):
    """{(conjunto, modelo): [(dentro, fora) por semente]} — as mesmas dobras e as mesmas linhas em todos."""
    out = {}
    for conjunto in conjuntos:
        for modelo in modelos:
            lista = sementes if modelo == "mlp" else (None,)
            print(f"  {aviso} {conjunto} {modelo} ({len(lista)} semente(s))", flush=True)
            out[(conjunto, modelo)] = [rodada_p1(u, modelo, conjunto, novas_por_conjunto.get(conjunto, ()), s, dobras)
                                       for s in lista]
    return out


def tabela_r2(u, prev, novas_por_conjunto):
    """04: MAE, RMSE e R², dentro e na validação cruzada, e o ΔR² sobre S0 da mesma classe (média e desvio
    nas sementes, pareados por semente)."""
    y = u[DESFECHO].astype("float64").to_numpy()
    linhas = []
    for (conjunto, modelo), rs in prev.items():
        lin = {"conjunto": conjunto, "modelo": modelo, "n_escolas_ano": len(u),
               "n_colunas_novas": len(novas_por_conjunto.get(conjunto, ())), "n_sementes": len(rs),
               "fora_de_0_100_dentro": float(np.mean([((d < 0) | (d > 100)).sum() for d, _ in rs])),
               "fora_de_0_100_cv": float(np.mean([((f < 0) | (f > 100)).sum() for _, f in rs]))}
        for onde, k in (("dentro", 0), ("cv", 1)):
            for met in ("mae", "rmse", "r2"):
                v = [F._metricas(y, r[k])[met] for r in rs]
                lin[f"{met}_{onde}"] = float(np.mean(v))
                lin[f"{met}_{onde}_dp"] = float(np.std(v, ddof=1)) if len(v) > 1 else np.nan
        if conjunto != "S0" and ("S0", modelo) in prev:
            delta = [F._metricas(y, c[1])["r2"] - F._metricas(y, a[1])["r2"]
                     for c, a in zip(rs, prev[("S0", modelo)])]
            lin["delta_r2_cv"] = float(np.mean(delta))
            lin["delta_r2_cv_dp"] = float(np.std(delta, ddof=1)) if len(delta) > 1 else np.nan
        else:
            lin["delta_r2_cv"], lin["delta_r2_cv_dp"] = np.nan, np.nan
        linhas.append(lin)
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ controle negativo (E.4 = C.9 em S1 e S2)
def embaralhar(u, semente=SEMENTE_CONTROLE):
    """O mesmo embaralhamento da C.9 (F.c9_controle_negativo): abandono_t dentro de cada ano, semente 20261115."""
    rng = np.random.default_rng(semente)
    emb = u.copy()
    for _, g in emb.groupby(F.CONTROLE):
        emb.loc[g.index, DESFECHO] = g[DESFECHO].to_numpy()[rng.permutation(len(g))]
    return emb


def controle_negativo(u, novas, modelos, sementes, dobras):
    """E.4: ΔR² da validação cruzada sobre S0, no desfecho embaralhado, abaixo de 0,02 para cada modelo e para
    S1 e S2 (no MLP, a média das sementes). Se não ficar, a execução PARA."""
    emb = embaralhar(u)
    prev = prever_p1(emb, ("S0", "S1", "S2"), {"S2": novas}, modelos, sementes, dobras, aviso="controle")
    tab = tabela_r2(emb, prev, {"S2": novas})
    tab = tab[tab["conjunto"] != "S0"].rename(columns={"r2_cv": "r2_cv_embaralhado",
                                                       "delta_r2_cv": "delta_r2_cv_embaralhado"})
    tab = tab[["conjunto", "modelo", "n_sementes", "r2_cv_embaralhado", "delta_r2_cv_embaralhado"]].copy()
    tab["limiar"] = LIMIAR_CONTROLE
    tab["passou"] = tab["delta_r2_cv_embaralhado"] < LIMIAR_CONTROLE
    return tab.reset_index(drop=True)


# ------------------------------------------------------------------ equivalência com o estudo C (E.4)
def equivalencia(tab_s0_s1, ref, etapa):
    """S0 e S1 contra o 05_r2.csv do estudo C: linear e Ridge têm de reproduzir r2_cv e delta_r2_cv com
    diferença < 1e-6 (senão PARA); no MLP a diferença é relatada e não para."""
    r = ref[ref["etapa"] == etapa].set_index(["modelo", "variaveis"])
    t = tab_s0_s1.set_index(["conjunto", "modelo"])
    linhas = []
    for modelo in t.index.get_level_values("modelo").unique():
        pares = [("S0", "so_ano", "r2_cv", "r2_cv"), ("S1", "completo", "r2_cv", "r2_cv"),
                 ("S1", "completo", "delta_r2_cv", "delta_r2_cv")]
        for conj, var, met_e, met_c in pares:
            e = float(t.loc[(conj, modelo), met_e])
            c = float(r.loc[(modelo, var), met_c]) if (modelo, var) in r.index else np.nan
            dif = abs(e - c)
            decide = modelo in ("linear", "ridge")
            linhas.append({"etapa": etapa, "modelo": modelo, "conjunto": conj, "metrica": met_e,
                           "estudo_e": e, "estudo_c": c, "diferenca_abs": dif, "tolerancia": TOL_EQUIVALENCIA,
                           "decide": decide,
                           "passou": bool(dif < TOL_EQUIVALENCIA) if decide else np.nan})
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ F8 (E.4): S2 − S1 pareada no bootstrap
def dif_r2_bootstrap(y, prev_s1, prev_s2, sorteios):
    """A diferença de R² (S2 − S1) sobre as previsões fora-da-dobra JÁ calculadas, sem reajuste. Em cada
    reamostragem (as mesmas para S1 e S2), recalculam-se os dois R² e guarda-se a diferença. Com várias sementes
    (MLP), o R² de cada semente e depois a média. Devolve (diferença pontual, distribuição)."""
    def r2_medio(prevs, idx):
        return float(np.mean([_r2(y[idx], p[idx]) for p in prevs]))
    todos = np.arange(len(y))
    ponto = r2_medio(prev_s2, todos) - r2_medio(prev_s1, todos)
    dist = np.array([r2_medio(prev_s2, idx) - r2_medio(prev_s1, idx) for idx in sorteios])
    return ponto, dist


def veredito_f8(dif, p_holm, ic_hi):
    """E.4, na ordem: ACRESCENTA (≥ 0,02 e p Holm ≤ 0,05) → NÃO ACRESCENTA (limite superior do IC 95% sem
    correção abaixo de 0,02) → INCONCLUSIVO."""
    if not np.isfinite([dif, p_holm, ic_hi]).all():
        return "INCONCLUSIVO"
    if dif >= MARGEM_R2 and p_holm <= ALFA:
        return "ACRESCENTA"
    if ic_hi < MARGEM_R2:
        return "NÃO ACRESCENTA"
    return "INCONCLUSIVO"


def resumo_dist(ponto, dist):
    v = dist[np.isfinite(dist)]
    lo, hi = np.percentile(v, [2.5, 97.5]) if len(v) else (np.nan, np.nan)
    return {"diferenca": ponto, "ic_lo": float(lo), "ic_hi": float(hi),
            "p": B.p_bootstrap(v) if len(v) else np.nan, "n_reamostragens_validas": int(len(v))}


def f8(por_etapa):
    """05: F8 = {AF, EM} na Ridge, com Holm; linear e MLP descritivos (sem Holm nem veredito)."""
    linhas = [{"etapa": e, "modelo": m, **r} for e, res in por_etapa.items() for m, r in res.items()]
    tab = pd.DataFrame(linhas)
    tab["familia"] = np.where(tab["modelo"] == "ridge", "F8", "descritiva")
    tab["p_holm"], tab["veredito"] = np.nan, ""
    fam = (tab["familia"] == "F8") & tab["p"].notna()
    if fam.any():
        tab.loc[fam, "p_holm"] = B.holm(tab.loc[fam, "p"].to_numpy())
    for i in tab.index[tab["familia"] == "F8"]:
        tab.loc[i, "veredito"] = veredito_f8(tab.loc[i, "diferenca"], tab.loc[i, "p_holm"], tab.loc[i, "ic_hi"])
    tab["n_familia"] = int(fam.sum())
    return tab


# ------------------------------------------------------------------ E.6: permutação (coluna e bloco)
def permutar(ent, cols, ordem):
    """Permuta as colunas do bloco com o MESMO sorteio de linhas, na coluna bruta (antes do pipeline): o
    ausente vai junto com a linha, então o indicador de ausente acompanha."""
    emb = ent.copy()
    for c in cols:
        emb[c] = ent[c].to_numpy()[ordem]
    return emb


def alvos_permutacao(novas, blocos):
    alvos = {c: ("coluna", _bloco_de(c, blocos), [c]) for c in CATEGORICAS + DIMS + list(novas)}
    for nome, cols in blocos.items():
        presentes = [c for c in cols if c in novas]
        if presentes:
            alvos[f"bloco:{nome}"] = ("bloco", nome, presentes)
    for nome, cols in BLOCOS_C.items():
        alvos[f"bloco:{nome}"] = ("bloco", nome, cols)
    return alvos


def _bloco_de(c, blocos):
    for nome, cols in {**blocos, **BLOCOS_C}.items():
        if c in cols:
            return nome
    return ""


def permutacao(u, novas, blocos, modelos, sementes, dobras, n_repeticoes=N_REPETICOES_PERM, semente=SEMENTE_E):
    """E.6: queda de R² fora da dobra ao permutar cada coluna e cada bloco, em S2, para Ridge e MLP;
    IC pelos percentis das repetições. Descrição: nenhuma coluna entra, sai ou recebe veredito por ela."""
    ent = u[entradas_p1("S2", novas)]
    y = u[DESFECHO].astype("float64").to_numpy()
    alvos = alvos_permutacao(novas, blocos)
    linhas = []
    for modelo in [m for m in ("ridge", "mlp") if m in modelos]:
        print(f"  permutação {modelo}", flush=True)
        rng = np.random.default_rng(semente)
        quedas = {a: [] for a in alvos}
        for s in (sementes if modelo == "mlp" else (None,)):
            for tr, va in dobras:
                pipe = _ajustar(pipeline_p1(modelo, "S2", novas, s), ent.iloc[tr], y[tr] / 100.0)
                ev = ent.iloc[va]
                base = _r2(y[va], pipe.predict(ev) * 100.0)
                for nome, (_, _, cols) in alvos.items():
                    for _ in range(n_repeticoes):
                        ordem = rng.permutation(len(ev))
                        quedas[nome].append(base - _r2(y[va], pipe.predict(permutar(ev, cols, ordem)) * 100.0))
        for nome, (tipo, bloco, cols) in alvos.items():
            v = np.asarray(quedas[nome])
            lo, hi = np.percentile(v, [2.5, 97.5])
            linhas.append({"modelo": modelo, "tipo": tipo, "alvo": nome, "bloco": bloco, "n_colunas": len(cols),
                           "queda_r2": float(v.mean()), "ic_lo": float(lo), "ic_hi": float(hi)})
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ Parte 2 (E.5)
def universo_p2(d, etapa):
    """E.5: escolas públicas com abandono_tm1, abandono_t e abandono_t1 não vazios, t = 2013–2018. O abandono_t
    só delimita o universo e nunca entra em X."""
    u = d[(d["etapa"] == etapa) & (d["rede_publica"] == 1) & d["abandono_tm1"].notna()
          & d[DESFECHO].notna() & d[DESFECHO_P2].notna() & d["ano"].between(*JANELA)].copy()
    _conferir_janela(u)
    if u[ROTULO_P2].isna().any():
        raise AssertionError("alto_risco_t1 vazio dentro do universo da Parte 2 (o dicionário diz que não pode)")
    return u


def dividir_p2(u):
    """E.5: treino t = 2013–2016, teste t = 2017–2018, sem sorteio de linhas; o teste em ordem de ano."""
    tr = u[u["ano"].between(*TREINO)]
    te = pd.concat([u[u["ano"] == a] for a in range(TESTE[0], TESTE[1] + 1)])
    return tr, te


def numericas_p2(conjunto, novas):
    base = (RENDIMENTO_A if conjunto.startswith("A") else []) + DIMS
    return base + list(novas) if conjunto.endswith("+") else base


def prever_p2(u, novas, modelos, sementes):
    """{(conjunto, modelo): [nota por semente]} no teste, mais as réguas: B1R_lag (abandono_tm1) e B2
    (mediana do treino por localização × dependência). Alvo abandono_t1 ÷ 100; notas de volta em pp."""
    tr, te = dividir_p2(u)
    y_tr = tr[DESFECHO_P2].astype("float64").to_numpy() / 100.0
    out = {("régua", "B1R_lag"): [te["abandono_tm1"].astype("float64").to_numpy()],
           ("régua", "B2"): [BL.b2_mediana_estrato(tr.assign(y_t1=tr[DESFECHO_P2]), te, estrato=tuple(CATEGORICAS))]}
    for conjunto in CONJUNTOS_P2:
        num = numericas_p2(conjunto, novas)
        for modelo in [m for m in MODELOS_P2 if m in modelos]:
            lista = sementes if modelo == "mlp" else (None,)
            print(f"  previsão {conjunto} {modelo} ({len(lista)} semente(s))", flush=True)
            ent = num + CATEGORICAS + ["ano"]          # ano só para a conferência da janela; não é preditor
            out[(conjunto, modelo)] = [
                _ajustar(pipeline_p2(modelo, num, s), tr[ent], y_tr).predict(te[ent]) * 100.0 for s in lista]
    return te, out


def _recall_anos(rot, notas, por_ano):
    """Recall@20% de cada ano de teste (empates pelo valor esperado) e a média simples dos anos; com várias
    notas (sementes do MLP), a média das sementes."""
    vals = []
    for nota in notas:
        anos = []
        for sel in por_ano:
            r = rot[sel]
            anos.append(CL.recall_k(r, nota[sel], M.k_de_fracao(len(sel), FRACAO_TOPO)) if r.sum() > 0 else np.nan)
        vals.append(anos)
    v = np.asarray(vals, dtype="float64").mean(axis=0)
    return float(np.mean(v)), v


def metricas_p2(te, prev, n_boot=N_BOOT, semente=SEMENTE_E):
    """07 e as distribuições para o 08: Recall@20% (média dos dois anos de teste; o que decide) e MAE, RMSE, R²
    (descritivos), com IC pelo bootstrap agrupado por escola (src/avaliacao/bootstrap.Agrupado), 5.000
    reamostragens, as mesmas para todos."""
    rot = te[ROTULO_P2].astype(int).to_numpy()
    y = te[DESFECHO_P2].astype("float64").to_numpy()
    anos = list(range(TESTE[0], TESTE[1] + 1))
    celulas = [{"ano_alvo": a + 1, "y": rot[te["ano"].to_numpy() == a],
                "co": te.loc[te["ano"] == a, "co_entidade"].astype(str).to_numpy()} for a in anos]
    ag = B.Agrupado(celulas)
    sorteios = ag.sorteios(np.random.default_rng(semente), n_boot)
    sel_ponto = [np.flatnonzero(te["ano"].to_numpy() == a) for a in anos]
    linhas, dists = [], {}
    for chave, notas in prev.items():
        ponto, por_ano = _recall_anos(rot, notas, sel_ponto)
        dist = np.array([_recall_anos(rot, notas, [s for s in ag.por_ano(idx).values()])[0] for idx in sorteios])
        dists[chave] = dist
        res = resumo_dist(ponto, dist)
        base = {"conjunto": chave[0], "modelo": chave[1], "n_sementes": len(notas), "n_teste": len(te)}
        linhas.append({**base, "metrica": "Rec@20pct", "valor": ponto, "ic_lo": res["ic_lo"], "ic_hi": res["ic_hi"]})
        for a, v in zip(anos, por_ano):
            linhas.append({**base, "metrica": f"Rec@20pct_t={a}", "valor": float(v), "ic_lo": np.nan, "ic_hi": np.nan})
        if chave[1] != "B1R_lag":            # a régua só ordena; não estima valor
            for met, fn in (("mae", M.mae), ("rmse", M.rmse), ("r2", _r2)):
                pv = float(np.mean([fn(y, n) for n in notas]))
                dv = np.array([np.mean([fn(y[idx], n[idx]) for n in notas]) for idx in sorteios])
                r = resumo_dist(pv, dv)
                linhas.append({**base, "metrica": met, "valor": pv, "ic_lo": r["ic_lo"], "ic_hi": r["ic_hi"]})
    return pd.DataFrame(linhas), dists


def testes_p2(valores, dists):
    """08: F9 (A+ − régua) e F10 (B+ − B2), Holm dentro de cada família (α = 0,05), vereditos da
    classificacao.leitura com margem +0,10; A+ − A, B+ − B e Ridge − MLP descritivos (IC e p, sem veredito).
    `valores` e `dists`: {etapa: {(conjunto, modelo): Recall@20%}} e as distribuições pareadas."""
    linhas = []
    for etapa in valores:
        v, d = valores[etapa], dists[etapa]

        def nome(x):
            return x[1] if x[0] == "régua" else f"{x[1]} {x[0]}"

        def comp(familia, a, b):
            if a in v and b in v:
                r = resumo_dist(v[a] - v[b], d[a] - d[b])
                linhas.append({"familia": familia, "etapa": etapa, "comparacao": f"{nome(a)} − {nome(b)}",
                               "modelo": a[1], **r})

        for m in MODELOS_P2:
            comp("F9", ("A+", m), ("régua", "B1R_lag"))
            comp("F10", ("B+", m), ("régua", "B2"))
        for m in MODELOS_P2:
            comp("descritiva", ("A+", m), ("A", m))
            comp("descritiva", ("B+", m), ("B", m))
        for c in CONJUNTOS_P2:
            comp("descritiva", (c, "ridge"), (c, "mlp"))
    tab = pd.DataFrame(linhas)
    tab["_o"] = tab["familia"].map({"F9": 0, "F10": 1, "descritiva": 2})
    tab = tab.sort_values(["_o", "etapa"], kind="stable").drop(columns="_o").reset_index(drop=True)
    tab["p_holm"], tab["veredito"], tab["n_familia"] = np.nan, "", 0
    for fam in ("F9", "F10"):
        sel = (tab["familia"] == fam) & tab["p"].notna()
        if sel.any():
            tab.loc[sel, "p_holm"] = B.holm(tab.loc[sel, "p"].to_numpy())
            tab.loc[tab["familia"] == fam, "n_familia"] = int(sel.sum())
        for i in tab.index[tab["familia"] == fam]:
            r = tab.loc[i]
            tab.loc[i, "veredito"] = CL.leitura("Rec@20pct", r["diferenca"], r["ic_lo"], r["ic_hi"], r["p_holm"],
                                                alfa=ALFA, margem=MARGEM_RECALL) if np.isfinite(r["p_holm"]) \
                else "INCONCLUSIVO"
    return tab


# ------------------------------------------------------------------ git, gravação e relatório
def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=RAIZ)


def estado_git():
    """Commit e branch (F.estado_git) e as travas da E.8: conteúdo rastreado igual ao commit, nada não rastreado
    no código e o commit publicado num branch remoto. 'limpa' olha o conteúdo, não a data dos arquivos (a pasta
    é sincronizada pelo Google Drive, que marca arquivos como modificados sem mudar nada)."""
    e = F.estado_git()
    e["conteudo_igual_ao_commit"] = _git("diff", "--quiet", "HEAD").returncode == 0
    soltos = _git("status", "--porcelain", "--untracked-files=all", "--", "src", "experimentos/censo_bruto_v0",
                  "experimentos/fatores_2013_2018").stdout.splitlines()
    e["nao_rastreados_no_codigo"] = [s[3:] for s in soltos if s.startswith("??")
                                     and "censo_bruto_v0/saida/" not in s and "__pycache__" not in s]
    e["publicado"] = bool(_git("branch", "-r", "--contains", "HEAD").stdout.strip())
    e["limpa"] = e["conteudo_igual_ao_commit"] and not e["nao_rastreados_no_codigo"]
    return e


def _md(df, casas=4):
    def fmt(x):
        if isinstance(x, (float, np.floating)):
            return "" if not np.isfinite(x) else f"{x:.{casas}f}"
        return str(x)
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(fmt(x) for x in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(linhas)


def _ler(pasta, nome):
    return pd.read_csv(pasta / nome, skiprows=1)


RESSALVAS = [
    "**É exploratório** (E, abertura): o estudo foi desenhado depois de conhecidos os resultados do estudo C e da "
    "classificação (seção A).",
    "**Anos já vistos:** os desfechos 2016–2019 já foram olhados como teste, e os outros anos da janela também, no "
    "estudo C. O teste da Parte 2 (desfechos 2018–2019) é de anos já vistos.",
    "**Colunas brutas:** as 124 colunas saíram de um filtro mecânico que só olha preditores (E.2), sem a revisão "
    "coluna a coluna. Problemas conhecidos ficam dentro delas (E.7). Nenhuma coluna nova recebe coeficiente, "
    "veredito de fator nem frase de efeito; a tabela de fatores continua sendo a do estudo C.",
    "**As seis faixas de idade das matrículas são parcialmente mecânicas** (regra 6): acumulam a reprovação e o "
    "abandono de anos anteriores. A robustez S2r mostra o resultado sem elas.",
    "**Desvio declarado da regra B.6:** o protocolo foi para o branch por commit e push antes da execução, sem pull "
    "request revisado antes; a revisão vem no pull request da execução (docs/DECISOES.md, 2026-11-20).",
    "**Responde (E.9):** se as colunas brutas que passam no filtro aumentam o quanto se explica da diferença de "
    "abandono entre escolas (E1) e se melhoram a lista de risco do ano seguinte contra a régua e contra a B2 (E2), "
    "na versão 0, antes da limpeza.",
    "**Não responde (E.9):** o peso de cada coluna; causa; nada sobre 2025 (fechado para o teste limpo); se os dados "
    "limpos dariam outro resultado. A importância por permutação é descrição e roteiro da limpeza: nenhuma coluna "
    "entra, sai ou recebe veredito por ela (regra 7).",
]


def relatorio(pasta):
    """RELATORIO.md gerado por código, só com números lidos dos CSVs gravados (regras 3 e 4)."""
    pasta = Path(pasta)
    cab = (pasta / "00_filtro.csv").read_text(encoding="utf-8").splitlines()[0].lstrip("# ")
    filtro = _ler(pasta, "00_filtro.csv")
    univ = _ler(pasta, "01_universo.csv")
    controle = _ler(pasta, "02_controle_negativo.csv")
    equiv = _ler(pasta, "03_equivalencia_c.csv")
    r2 = _ler(pasta, "04_r2.csv")
    f8_ = _ler(pasta, "05_f8.csv")
    perm = _ler(pasta, "06_permutacao.csv")
    met = _ler(pasta, "07_previsao_metricas.csv")
    tes = _ler(pasta, "08_previsao_testes.csv")
    L = ["# Estudo exploratório E (v0) — colunas brutas do Censo", "",
         f"Gerado por `experimentos/censo_bruto_v0/estudo_e.py` a partir dos CSVs desta pasta ({cab}). "
         "Protocolo: `docs/PROTOCOLO.md`, seção E.", "", "## Ressalvas (E.8 e E.9)", ""]
    L += [f"- {r}" for r in RESSALVAS]
    contagem = filtro["motivo"].value_counts().rename_axis("motivo").reset_index(name="colunas")
    L += ["", "## Filtro mecânico (00)", "", _md(contagem)]
    u = univ[univ["chave"].isin(["escolas", "escolas_ano", "colunas_constantes_retiradas", "colunas_novas_no_modelo",
                                 "treino_escolas_ano", "teste_escolas_ano"])]
    piv = u.pivot_table(index="chave", columns=["parte", "etapa"], values="valor", aggfunc="first")
    piv.columns = [f"{p} {e}" for p, e in piv.columns]
    L += ["", "## Universo (01)", "", _md(piv.reset_index(), casas=0)]
    L += ["", "## Controle negativo (02)", "", _md(controle),
          "", "## Equivalência com o estudo C (03)", "", _md(equiv, casas=8)]
    cols_r2 = ["etapa", "conjunto", "modelo", "n_colunas_novas", "r2_dentro", "r2_cv", "r2_cv_dp", "delta_r2_cv",
               "mae_cv", "rmse_cv"]
    L += ["", "## Parte 1 — E1: quanto se explica (04)", "", _md(r2[cols_r2])]
    L += ["", "## Parte 1 — E1: S2 − S1 (05; a F8 é a Ridge)", "",
          _md(f8_[["etapa", "modelo", "familia", "diferenca", "ic_lo", "ic_hi", "p", "p_holm", "veredito"]])]
    L += ["", "## Parte 2 — E2: métricas no teste (07)", "",
          _md(met[["etapa", "conjunto", "modelo", "metrica", "valor", "ic_lo", "ic_hi"]])]
    L += ["", "## Parte 2 — E2: F9, F10 e diferenças descritivas (08)", "",
          _md(tes[["familia", "etapa", "comparacao", "diferenca", "ic_lo", "ic_hi", "p", "p_holm", "veredito"]])]
    L += ["", "## Importância por permutação (06; descrição, não decide nada)", "", "### Blocos", ""]
    L += [_md(perm[perm["tipo"] == "bloco"].sort_values(["etapa", "modelo", "queda_r2"], ascending=[True, True, False])
              [["etapa", "modelo", "alvo", "n_colunas", "queda_r2", "ic_lo", "ic_hi"]])]
    L += ["", "### As 15 colunas com maior queda de R², por etapa e modelo", ""]
    top = (perm[perm["tipo"] == "coluna"].sort_values("queda_r2", ascending=False)
           .groupby(["etapa", "modelo"], sort=True).head(15).sort_values(["etapa", "modelo", "queda_r2"],
                                                                          ascending=[True, True, False]))
    L += [_md(top[["etapa", "modelo", "alvo", "bloco", "queda_r2", "ic_lo", "ic_hi"]])]
    (pasta / "RELATORIO.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ a execução única (ordem da E.8)
def executar(d, censo, filtro, pasta, caminho_dataset=DATASET, estado=None, ref_c=REF_C, colunas=None,
             blocos=None, faixas=None, n_boot=N_BOOT, modelos=MODELOS_P1, sementes=SEMENTES_MLP,
             n_repeticoes=N_REPETICOES_PERM):
    """E.8: filtro → controle negativo → equivalência → Parte 1 → Parte 2; tudo em memória, gravado no fim.
    Se parar, grava só o arquivo que levou à parada e devolve 'PAROU: …'."""
    colunas = list(G.COLUNAS if colunas is None else colunas)
    blocos = G.BLOCOS if blocos is None else blocos
    faixas = list(G.FAIXAS_IDADE if faixas is None else faixas)
    pasta = Path(pasta)
    estado = estado or estado_git()
    cab = F.cabecalho(caminho_dataset, estado)
    d = na_janela(d)

    # 1. o filtro confere a lista fechada
    filtro = filtro.assign(na_lista_do_protocolo=filtro["coluna"].isin(colunas))
    if filtro.loc[filtro["motivo"] == "PASSA", "coluna"].tolist() != colunas:
        F.gravar(filtro, pasta / "00_filtro.csv", cab)
        return "PAROU: o filtro mecânico não devolveu a lista fechada da E.2 (defeito de código ou de dado)"
    d = juntar_censo(d, censo, colunas)

    universo, p1, p2 = [], {}, {}
    for etapa in ETAPAS:
        u, reg = F.universo_pronto(d, etapa)
        _conferir_janela(u)
        cte = constantes(u, colunas)
        novas = [c for c in colunas if c not in cte]
        p1[etapa] = {"u": u, "novas": novas, "dobras": F.dobras_por_escola(u),
                     "novas_por": {"S2": novas, "S2r": [c for c in novas if c not in faixas]}}
        universo += [("parte1", etapa, "escolas", u["co_entidade"].nunique()), ("parte1", etapa, "escolas_ano", len(u)),
                     ("parte1", etapa, "linhas_preditor_vazio", reg["linhas_preditor_vazio"]),
                     ("parte1", etapa, "colunas_constantes_retiradas", len(cte)),
                     ("parte1", etapa, "colunas_novas_no_modelo", len(novas))]
        universo += [("parte1", etapa, f"escolas_ano:ano={a}", int(n)) for a, n in u["ano"].value_counts().sort_index().items()]
        for cat, cont in reg["categorias_excluidas"].items():
            universo += [("parte1", etapa, f"excluida:dependencia={cat}:escolas_ano", cont["escolas_ano"]),
                         ("parte1", etapa, f"excluida:dependencia={cat}:escolas", cont["escolas"])]
        universo += [("parte1", etapa, f"constante_retirada:{c}", 1) for c in cte]
        v = universo_p2(d, etapa)
        cte2 = constantes(v, colunas)
        p2[etapa] = {"u": v, "novas": [c for c in colunas if c not in cte2]}
        tr, te = dividir_p2(v)
        universo += [("parte2", etapa, "escolas", v["co_entidade"].nunique()), ("parte2", etapa, "escolas_ano", len(v)),
                     ("parte2", etapa, "treino_escolas_ano", len(tr)), ("parte2", etapa, "teste_escolas_ano", len(te)),
                     ("parte2", etapa, "colunas_constantes_retiradas", len(cte2)),
                     ("parte2", etapa, "colunas_novas_no_modelo", len(p2[etapa]["novas"]))]
        universo += [("parte2", etapa, f"escolas_ano:ano={a}", int(n)) for a, n in v["ano"].value_counts().sort_index().items()]
        universo += [("parte2", etapa, f"constante_retirada:{c}", 1) for c in cte2]
    universo = pd.DataFrame(universo, columns=["parte", "etapa", "chave", "valor"])

    # 2. controle negativo (pode parar)
    print("controle negativo", flush=True)
    controle = pd.concat([controle_negativo(p1[e]["u"], p1[e]["novas"], modelos, sementes, p1[e]["dobras"])
                          .assign(etapa=e) for e in ETAPAS], ignore_index=True)
    controle = controle[["etapa"] + [c for c in controle.columns if c != "etapa"]]
    if not controle["passou"].all():
        F.gravar(controle, pasta / "02_controle_negativo.csv", cab)
        return "PAROU: controle negativo reprovou (E.4/C.9); só o 02 foi gravado"

    # 3. equivalência com o estudo C (pode parar)
    print("equivalência com o estudo C", flush=True)
    ref = pd.read_csv(ref_c, skiprows=1)
    prev, equiv = {}, []
    for e in ETAPAS:
        x = p1[e]
        prev[e] = prever_p1(x["u"], ("S0", "S1"), {}, modelos, sementes, x["dobras"], aviso=f"{e}")
        equiv.append(equivalencia(tabela_r2(x["u"], prev[e], {}), ref, e))
    equiv = pd.concat(equiv, ignore_index=True)
    if not equiv.loc[equiv["decide"], "passou"].astype(bool).all():
        F.gravar(equiv, pasta / "03_equivalencia_c.csv", cab)
        return "PAROU: S0/S1 não reproduzem o 05_r2.csv do estudo C (defeito de código); só o 03 foi gravado"

    # 4. Parte 1: S2, S2r, F8 e permutação
    r2s, f8_res, perms = [], {}, []
    for e in ETAPAS:
        x = p1[e]
        prev[e].update(prever_p1(x["u"], ("S2", "S2r"), x["novas_por"], modelos, sementes, x["dobras"], aviso=f"{e}"))
        r2s.append(tabela_r2(x["u"], prev[e], x["novas_por"]).assign(etapa=e))
        y = x["u"][DESFECHO].astype("float64").to_numpy()
        sorteios = F._sorteios_escolas(x["u"], n_boot, np.random.default_rng(SEMENTE_E))
        f8_res[e] = {}
        for m in modelos:
            ponto, dist = dif_r2_bootstrap(y, [f for _, f in prev[e][("S1", m)]], [f for _, f in prev[e][("S2", m)]],
                                           sorteios)
            f8_res[e][m] = resumo_dist(ponto, dist)
        perms.append(permutacao(x["u"], x["novas"], blocos, modelos, sementes, x["dobras"], n_repeticoes).assign(etapa=e))
    r2 = pd.concat(r2s, ignore_index=True)
    r2["_ordem"] = r2["conjunto"].map({c: i for i, c in enumerate(CONJUNTOS_P1)})
    r2 = r2.sort_values(["etapa", "modelo", "_ordem"]).drop(columns="_ordem").reset_index(drop=True)
    r2 = r2[["etapa"] + [c for c in r2.columns if c != "etapa"]]
    tab_f8 = f8(f8_res)
    perm = pd.concat(perms, ignore_index=True)
    perm = perm[["etapa"] + [c for c in perm.columns if c != "etapa"]]

    # 5. Parte 2: previsão de t+1
    mets, valores, dists = [], {}, {}
    for e in ETAPAS:
        te, prev2 = prever_p2(p2[e]["u"], p2[e]["novas"], modelos, sementes)
        tab, ds = metricas_p2(te, prev2, n_boot)
        mets.append(tab.assign(etapa=e))
        rec = tab[tab["metrica"] == "Rec@20pct"].set_index(["conjunto", "modelo"])["valor"]
        valores[e], dists[e] = {k: float(rec.loc[k]) for k in prev2}, ds
    met = pd.concat(mets, ignore_index=True)
    met = met[["etapa"] + [c for c in met.columns if c != "etapa"]]
    tes = testes_p2(valores, dists)

    # gravação no fim
    for nome, tab in (("00_filtro.csv", filtro), ("01_universo.csv", universo), ("02_controle_negativo.csv", controle),
                      ("03_equivalencia_c.csv", equiv), ("04_r2.csv", r2), ("05_f8.csv", tab_f8),
                      ("06_permutacao.csv", perm), ("07_previsao_metricas.csv", met),
                      ("08_previsao_testes.csv", tes)):
        F.gravar(tab, pasta / nome, cab)
    relatorio(pasta)
    return "OK: execução única concluída"


def main(argv=None):
    if SAIDA.exists():
        sys.exit(f"ERRO: {SAIDA} já existe. A execução é única (E.8 e D.1); uma nova execução exige decisão "
                 "registrada no docs/DECISOES.md, nunca a regravação por cima.")
    estado = estado_git()
    if not estado["limpa"]:
        sys.exit("ERRO: há arquivo rastreado com conteúdo diferente do commit ou arquivo não rastreado no código "
                 f"({estado['nao_rastreados_no_codigo']}). O commit gravado nas saídas tem de ser o código que rodou.")
    if not estado["publicado"]:
        sys.exit("ERRO: o commit atual não está em nenhum branch remoto. O protocolo e o código vão por push "
                 "antes da execução (docs/DECISOES.md, 2026-11-20): o push é a data pública.")
    print(f"commit {estado['commit']} ({estado['branch']})", flush=True)
    print("filtro mecânico (E.2)", flush=True)
    filtro = G.filtro_mecanico()
    censo = G.extrair()
    print(executar(ler_dataset(), censo, filtro, SAIDA, estado=estado), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
