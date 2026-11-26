# -*- coding: utf-8 -*-
"""
Apoio do notebook notebooks/05_apresentacao_censo.ipynb (apresentação ao professor). EXPLORATÓRIO: anos de teste
já vistos, sem protocolo de execução única; nada aqui decide nada (docs/DECISOES.md, 2026-11-20, "Notebook de
apresentação (exploratório)" e "Notebook de apresentação simplificado"). As contas ficam neste módulo, com testes
(testes/test_apoio_apresentacao.py); as células só chamam e exibem.

PREVISÃO ANO A ANO (janela que cresce)
  Para cada ano t de teste, o modelo é treinado com todos os anos anteriores (de ANO_INICIO até t − 1) e prevê o
  abandono de t + 1 das escolas do ano t. Os anos de treino só têm desfechos até t, que já são conhecidos quando se
  faz a previsão de t + 1. Tudo o que é ajustado (filtro de saúde, redundância, imputação, padronização, modelo)
  usa só as linhas de treino daquele ano.

TRAVA FIXA (nenhuma configuração do notebook desliga):
  - o desfecho de 2025 (t = 2024) nunca entra em treino nem em teste: é o teste limpo;
  - o último ano de teste é t = 2023 (desfecho 2024).
"""
from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]


def _modulo(caminho, nome):
    if nome in sys.modules:
        return sys.modules[nome]
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


E = _modulo(RAIZ / "experimentos" / "censo_bruto_v0" / "estudo_e.py", "apoio_estudo_e")   # MLP do professor
ETAPA03 = _modulo(RAIZ / "src" / "estendida" / "03_grupos.py", "apoio_etapa03")
CL, M = E.CL, E.M                        # src/avaliacao: classificacao, metricas

from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.linear_model import Ridge  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402

DATASET = RAIZ / "dataset" / "escolas_rr_v0.2.0.csv"
BASE = RAIZ / "saida" / "base_atual.parquet"

# ------------------------------------------------------------------ trava fixa (não é configuração)
T_TESTE_LIMPO = 2024                 # desfecho 2025: fechado
ULTIMO_T_TESTE = 2023                # desfecho 2024
MIN_ANOS_TREINO = 2                  # o primeiro ano de teste tem pelo menos 2 anos de treino antes

ETAPAS = ("AF", "EM")
CHAVE = ["ano", "co_entidade"]
DESFECHO = "abandono_t1"
ROTULO = "alto_risco_t1"             # os 20% de maior abandono em t + 1 (dataset)
FRACAO_TOPO = 0.20
CATEGORICAS = list(E.CATEGORICAS)    # localizacao, dependencia
DIMS = list(E.DIMS)                  # as quatro dim_*_prop (o grupo infraestrutura entra por elas)
RENDIMENTO = list(E.RENDIMENTO_A)    # abandono_tm1, reprovacao_tm1, variacao_abandono_defasada
MIN_PREENCH = 0.95                   # saúde, no treino: coluna com menos de 95% preenchida sai
MAX_DOMINANTE = 0.99                 # saúde, no treino: coluna com mais de 99% num valor sai
LIMIAR_REDUNDANCIA = 0.90            # |r| > 0,90 com uma coluna anterior: sai

REGUA = "Régua (abandono de t−1)"
MODELOS = ("Ridge", "Random Forest", "Gradient Boosting", "MLP (professor)")
METRICAS = ("Recall@20%", "Precisão@20%", "F1@20%", "R²", "MAE")


class TravaViolada(AssertionError):
    pass


def conferir_trava(tab, papel, t_teste=None):
    anos = pd.Series(tab["ano"]).astype(int)
    if (anos > ULTIMO_T_TESTE).any():
        raise TravaViolada(f"{papel}: linha com t > {ULTIMO_T_TESTE} (o desfecho de 2025 fica fechado)")
    if papel == "treino" and t_teste is not None and (anos >= t_teste).any():
        raise TravaViolada(f"treino com t >= {t_teste}, o ano de teste")


# ------------------------------------------------------------------ coleta
def colunas_dos_grupos(grupos):
    """{grupo: colunas}: os grupos do Censo pelas COLUNAS do arquivo; infraestrutura pelas 4 dimensões."""
    return {g: (list(DIMS) if g == "infraestrutura" else sorted(ETAPA03.carregar(g).COLUNAS)) for g in grupos}


def coleta(grupos, ano_inicio, ano_fim, dataset=DATASET, base=BASE):
    """(dataset + colunas do Censo, de ano_inicio a ano_fim; {grupo: colunas}). Junção how="left", validate="m:1"."""
    cols = colunas_dos_grupos(grupos)
    censo = [c for g, cs in cols.items() if g != "infraestrutura" for c in cs]
    d = pd.read_csv(dataset, dtype={"co_entidade": str, "co_municipio": str})
    b = pd.read_parquet(base, columns=["ANO", "CO_ENTIDADE", *censo]).rename(
        columns={"ANO": "ano", "CO_ENTIDADE": "co_entidade"})
    b["ano"] = b["ano"].astype("int64")
    b["co_entidade"] = b["co_entidade"].astype(str)
    for c in censo:
        b[c] = b[c].astype("Float64").astype("float64")           # <NA> → NaN (ausente, nunca 0)
    n = len(d)
    d = d.merge(b, on=CHAVE, how="left", validate="m:1")
    if len(d) != n:
        raise AssertionError("a junção com a base mudou o número de linhas")
    d = d[d["ano"].between(ano_inicio, ano_fim)].reset_index(drop=True)
    return d, cols


def resumo_coleta(d, cols):
    """Escolas-ano por ano e etapa (só contagem) e nº de colunas por grupo."""
    por_ano = d.pivot_table(index="ano", columns="etapa", values="co_entidade", aggfunc="count", fill_value=0)
    por_grupo = pd.DataFrame({"grupo": list(cols), "colunas": [len(c) for c in cols.values()]})
    return por_ano, por_grupo


# ------------------------------------------------------------------ universo e anos de teste
def universo(d, etapa):
    """Escolas públicas com abandono_tm1, abandono_t e abandono_t1; t até 2023."""
    u = d[(d["etapa"] == etapa) & (d["rede_publica"] == 1) & d["abandono_tm1"].notna()
          & d["abandono_t"].notna() & d[DESFECHO].notna() & (d["ano"] <= ULTIMO_T_TESTE)].copy()
    if u[ROTULO].isna().any():
        raise AssertionError("alto_risco_t1 vazio dentro do universo")
    return u


def anos_de_teste(u, ano_fim=ULTIMO_T_TESTE):
    """Cada t com pelo menos MIN_ANOS_TREINO anos anteriores no universo, até t = 2023."""
    anos = sorted(int(a) for a in u["ano"].unique())
    return [a for a in anos if a <= min(ano_fim, ULTIMO_T_TESTE) and sum(x < a for x in anos) >= MIN_ANOS_TREINO]


# ------------------------------------------------------------------ preditores, ajustados só no treino
def saudaveis(tr, colunas):
    """Saúde no treino: ≥ 95% preenchida e nenhum valor com mais de 99% dos não ausentes."""
    ok = []
    for c in colunas:
        x = tr[c]
        if x.notna().mean() < MIN_PREENCH:
            continue
        v = x.dropna()
        if not len(v) or v.value_counts(normalize=True).iloc[0] > MAX_DOMINANTE:
            continue
        ok.append(c)
    return ok


def redundantes(tr, ordem, limiar=LIMIAR_REDUNDANCIA):
    """|r| > limiar no treino, na ordem dada: a coluna sai se tiver |r| > limiar com alguma que ficou antes."""
    if not ordem:
        return []
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = tr[list(ordem)].astype("float64").corr().abs().to_numpy()
    ficam = []
    for i in range(len(ordem)):
        if not any(r[i, j] > limiar for j in ficam if np.isfinite(r[i, j])):
            ficam.append(i)
    return [ordem[i] for i in ficam]


def preditores(tr, cols):
    """Rendimento de t e t−1 (sempre) + dimensões da infraestrutura + colunas do Censo que passam na saúde e na
    redundância, medidas só no treino. Ordem fixa: infraestrutura, grupos na ordem da lista, colunas em ordem
    alfabética."""
    ordem = [c for g, cs in cols.items() for c in (cs if g == "infraestrutura" else sorted(cs))]
    return RENDIMENTO + redundantes(tr, saudaveis(tr, ordem))


def _estimador(nome, semente=0):
    if nome == "Ridge":
        return Ridge(alpha=1.0)
    if nome == "Random Forest":
        return RandomForestRegressor(n_estimators=300, min_samples_leaf=5, n_jobs=-1, random_state=semente)
    if nome == "Gradient Boosting":
        return HistGradientBoostingRegressor(random_state=semente)
    if nome == "MLP (professor)":
        return E._mlp(semente)
    raise ValueError(nome)


def pipeline(nome, numericas, semente=0):
    num = Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)), ("pad", StandardScaler())])
    pre = ColumnTransformer([("num", num, list(numericas)),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS)], remainder="drop")
    return Pipeline([("pre", pre), ("m", _estimador(nome, semente))])


def _ajustar(pipe, X, y, t_teste):
    """Todo ajuste passa por aqui: só linhas de anos anteriores ao de teste (os testes conferem)."""
    conferir_trava(X, "treino", t_teste)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pipe.fit(X, y)


# ------------------------------------------------------------------ métricas
def metricas(rot, y, nota, com_regressao=True):
    """As 20% com maior nota são apontadas como de alto risco; compara com alto_risco_t1."""
    k = M.k_de_fracao(len(nota), FRACAO_TOPO)
    acertos = CL.acertos_topk(rot, nota, k)
    rec = acertos / rot.sum() if rot.sum() > 0 else np.nan
    prec = acertos / k
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    out = {"Recall@20%": rec, "Precisão@20%": prec, "F1@20%": f1}
    if com_regressao:
        out["R²"] = M.r2(y, nota)
        out["MAE"] = M.mae(y, nota)
    return out


# ------------------------------------------------------------------ previsão ano a ano
def prever_ano(u, cols, t, modelos=MODELOS, sementes_mlp=3):
    """Treina com t' < t e prevê o desfecho das escolas de t. Devolve linhas de métricas."""
    tr, te = u[u["ano"] < t], u[u["ano"] == t]
    conferir_trava(tr, "treino", t)
    conferir_trava(te, "teste")
    rot = te[ROTULO].astype(int).to_numpy()
    y = te[DESFECHO].astype("float64").to_numpy()
    num = preditores(tr, cols)
    ent = num + CATEGORICAS + ["ano"]                      # ano só para a trava; não é preditor
    y_tr = tr[DESFECHO].astype("float64").to_numpy() / 100.0
    base = {"t": t, "ano_previsto": t + 1, "n_treino": len(tr), "n_teste": len(te), "n_preditores": len(num)}
    linhas = [{**base, "modelo": REGUA, **metricas(rot, y, te["abandono_tm1"].astype("float64").to_numpy())}]
    for nome in modelos:
        sementes = range(1, sementes_mlp + 1) if nome == "MLP (professor)" else (0,)
        notas = []
        for s in sementes:
            pipe = _ajustar(pipeline(nome, num, s), tr[ent], y_tr, t)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                notas.append(pipe.predict(te[ent]) * 100.0)
        linhas.append({**base, "modelo": nome, **metricas(rot, y, np.mean(notas, axis=0))})
    return linhas


def ano_a_ano(d, cols, modelos=MODELOS, sementes_mlp=3, ano_fim=ULTIMO_T_TESTE):
    """Métricas de cada modelo em cada ano de teste, nas duas etapas."""
    linhas = []
    for etapa in ETAPAS:
        u = universo(d, etapa)
        for t in anos_de_teste(u, ano_fim):
            linhas += [{"etapa": etapa, **x} for x in prever_ano(u, cols, t, modelos, sementes_mlp)]
    return pd.DataFrame(linhas)


def resumo(res):
    """Média das métricas nos anos de teste, por etapa e modelo (a régua na primeira linha)."""
    ordem = [REGUA, *[m for m in MODELOS if m in set(res["modelo"])]]
    t = res.groupby(["etapa", "modelo"], sort=False)[list(METRICAS)].mean()
    return t.reindex([(e, m) for e in ETAPAS for m in ordem if (e, m) in t.index])


# ------------------------------------------------------------------ colunas mais relevantes
def importancias(d, cols, modelos=MODELOS, sementes_mlp=3, t=ULTIMO_T_TESTE, n_repeticoes=5, semente=0):
    """Importância por permutação de cada coluna de entrada, por etapa e modelo: o quanto o MAE (pp) piora no
    ano de teste t quando a coluna é embaralhada. Treino com os anos anteriores a t, como no ano a ano. Devolve
    TODAS as colunas (inclusive as de importância zero ou negativa), ordenadas pela importância. Descritivo."""
    from sklearn.inspection import permutation_importance
    linhas = []
    for etapa in ETAPAS:
        u = universo(d, etapa)
        tr, te = u[u["ano"] < t], u[u["ano"] == t]
        conferir_trava(tr, "treino", t)
        conferir_trava(te, "teste")
        num = preditores(tr, cols)
        entradas = num + CATEGORICAS
        ent = entradas + ["ano"]
        y_tr = tr[DESFECHO].astype("float64").to_numpy() / 100.0
        y_te = te[DESFECHO].astype("float64").to_numpy() / 100.0
        for nome in modelos:
            sementes = range(1, sementes_mlp + 1) if nome == "MLP (professor)" else (0,)
            imp = []
            for s in sementes:
                pipe = _ajustar(pipeline(nome, num, s), tr[ent], y_tr, t)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r = permutation_importance(pipe, te[ent], y_te, scoring="neg_mean_absolute_error",
                                               n_repeats=n_repeticoes, random_state=semente, n_jobs=1)
                imp.append(pd.Series(r.importances_mean * 100.0, index=ent))
            media = pd.concat(imp, axis=1).mean(axis=1).drop("ano")
            for col, v in media.items():
                linhas.append({"etapa": etapa, "modelo": nome, "coluna": col, "aumento_mae_pp": float(v),
                               "t_teste": t, "n_treino": len(tr), "n_teste": len(te)})
    out = pd.DataFrame(linhas)
    out["posicao"] = out.groupby(["etapa", "modelo"])["aumento_mae_pp"].rank(ascending=False, method="first")
    return out.sort_values(["etapa", "modelo", "posicao"]).reset_index(drop=True)


def top_colunas(imp, n=10):
    """As n colunas mais relevantes de cada modelo, lado a lado (coluna e aumento do MAE em pp), por etapa."""
    out = {}
    for etapa, g in imp.groupby("etapa", sort=False):
        tab = {}
        for modelo, h in g.groupby("modelo", sort=False):
            h = h.nsmallest(n, "posicao")
            tab[modelo] = [f"{c} ({v:+.3f})" for c, v in zip(h["coluna"], h["aumento_mae_pp"])]
        out[etapa] = pd.DataFrame(tab, index=pd.RangeIndex(1, n + 1, name="posição"))
    return out


# ------------------------------------------------------------------ gráfico
def grafico(res, metrica="Recall@20%"):
    """Uma linha por modelo: a métrica em cada ano previsto (treino com os anos anteriores). A régua tracejada."""
    import matplotlib.pyplot as plt
    fig, eixos = plt.subplots(1, len(ETAPAS), figsize=(13, 4.5), sharey=True)
    for ax, etapa in zip(np.atleast_1d(eixos), ETAPAS):
        r = res[res["etapa"] == etapa]
        for nome, g in r.groupby("modelo", sort=False):
            regua = nome == REGUA
            ax.plot(g["ano_previsto"], g[metrica], marker="o", lw=2 if regua else 1.5,
                    ls="--" if regua else "-", color="black" if regua else None, label=nome)
        ax.set_title(f"{etapa} — {metrica}")
        ax.set_xlabel("ano previsto (treino com todos os anos anteriores)")
        ax.grid(alpha=0.3)
    np.atleast_1d(eixos)[0].set_ylabel(metrica)
    np.atleast_1d(eixos)[-1].legend(fontsize=8, loc="best")
    fig.tight_layout()
    return fig
