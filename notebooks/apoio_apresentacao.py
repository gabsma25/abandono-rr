# -*- coding: utf-8 -*-
"""
Apoio do notebook notebooks/05_apresentacao_censo.ipynb (apresentação ao professor). EXPLORATÓRIO: anos de teste
já vistos, sem protocolo de execução única; nada aqui decide nada (docs/DECISOES.md, 2026-11-20, "Notebook de
apresentação (exploratório)"). As contas ficam neste módulo, com testes (testes/test_apoio_apresentacao.py); as
células do notebook só chamam e exibem.

TRAVA FIXA (nenhuma configuração do notebook desliga):
  - o desfecho de 2025 (t = 2024) nunca entra em treino nem em teste: é o teste limpo;
  - t = 2024 e 2025 aparecem só na coleta e na descrição (contagens de escolas e o filtro de saúde, que só olha
    preditores);
  - a avaliação usa no máximo t = 2023 (desfecho 2024): teste t = 2022–2023, treino até t = 2021.

O que faz:
  coleta()        dataset v0.2.0 (desfechos por etapa) + as colunas dos grupos do Censo de saida/base_atual.parquet,
                  juntados por (ano, co_entidade) com validate="m:1";
  saude()         o filtro mecânico de 6 regras do estudo E (censo_bruto_v0.filtro_mecanico), com os anos da
                  configuração: preenchimento nos anos escolhidos até 2024, informação nos anos de treino;
  explorar()      universo da Parte 2 do estudo E, divisão temporal fixa, réguas B1R_lag e B2, Ridge e o MLP do
                  professor nos conjuntos A, A+, B e B+ (como na E.5), redundância |r| > 0,90 só no treino,
                  Recall@20% e MAE com IC pelo bootstrap agrupado por escola;
  comparar()      duas janelas de treino com o mesmo teste e as mesmas reamostragens (diferença pareada).
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


E = _modulo(RAIZ / "experimentos" / "censo_bruto_v0" / "estudo_e.py", "apoio_estudo_e")   # pipelines da E.5
ETAPA03 = _modulo(RAIZ / "src" / "estendida" / "03_grupos.py", "apoio_etapa03")
V0 = E.G                                                                                  # censo_bruto_v0
B, BL, CL, M = E.B, E.BL, E.CL, E.M      # src/avaliacao: bootstrap, baselines, classificacao, metricas

DATASET = RAIZ / "dataset" / "escolas_rr_v0.2.0.csv"
BASE = RAIZ / "saida" / "base_atual.parquet"
SAIDA_E = RAIZ / "experimentos" / "censo_bruto_v0" / "saida"
CACHE = RAIZ / "dados" / "cache" / "censo_completo"

# ------------------------------------------------------------------ trava fixa (não é configuração)
T_TESTE_LIMPO = 2024                 # desfecho 2025: fechado
ULTIMO_T_AVALIACAO = 2023            # desfecho 2024
TESTE = (2022, 2023)                 # os dois últimos t elegíveis
ULTIMO_T_TREINO = 2021
ULTIMO_ANO_PREDITOR_SAUDE = 2024     # o preenchimento é medido até 2024 (só preditores)

ETAPAS = ("AF", "EM")
CONJUNTOS = ("A", "A+", "B", "B+")
MODELOS = ("ridge", "mlp")
CHAVE = ["ano", "co_entidade"]
LIMIAR_REDUNDANCIA = 0.90
N_BOOT = 1000
SEMENTE = 20261120
FRACAO_TOPO = 0.20
DESFECHO = "abandono_t1"
ROTULO = "alto_risco_t1"
CATEGORICAS = list(E.CATEGORICAS)    # localizacao, dependencia
DIMS = list(E.DIMS)                  # as quatro dim_*_prop (o grupo infraestrutura entra por elas, como na E)
RENDIMENTO_A = list(E.RENDIMENTO_A)  # abandono_tm1, reprovacao_tm1, variacao_abandono_defasada


class TravaViolada(AssertionError):
    pass


def conferir_trava(tab, papel):
    """Nenhuma linha com t > 2023 (desfecho 2025 incluído) em treino ou teste; treino só até t = 2021."""
    anos = pd.Series(tab["ano"]).astype(int)
    if (anos > ULTIMO_T_AVALIACAO).any():
        raise TravaViolada(f"{papel}: linha com t > {ULTIMO_T_AVALIACAO} (o desfecho de 2025 fica fechado)")
    if papel == "treino" and (anos > ULTIMO_T_TREINO).any():
        raise TravaViolada(f"treino com t > {ULTIMO_T_TREINO}")
    if papel == "teste" and not anos.isin(range(TESTE[0], TESTE[1] + 1)).all():
        raise TravaViolada(f"teste fora de t = {TESTE[0]}–{TESTE[1]}")


# ------------------------------------------------------------------ coleta
def colunas_dos_grupos(grupos):
    """{grupo: colunas que entram}: os grupos do Censo pelas COLUNAS do arquivo; infraestrutura pelas 4 dimensões."""
    out = {}
    for g in grupos:
        if g == "infraestrutura":
            out[g] = list(DIMS)
        else:
            out[g] = sorted(ETAPA03.carregar(g).COLUNAS)
    return out


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


# ------------------------------------------------------------------ janela de treino
def primeiro_t_treino(d, ano_inicio):
    """ANO_INICIO, ou o primeiro t com abandono_tm1 (a variável do universo), se for depois."""
    com_lag = d.loc[d["abandono_tm1"].notna(), "ano"]
    return max(int(ano_inicio), int(com_lag.min()))


def anos_treino(d, ano_inicio):
    a0 = primeiro_t_treino(d, ano_inicio)
    if a0 > ULTIMO_T_TREINO:
        raise TravaViolada(f"ANO_INICIO = {ano_inicio}: não sobra ano de treino até t = {ULTIMO_T_TREINO}")
    return range(a0, ULTIMO_T_TREINO + 1)


# ------------------------------------------------------------------ saúde (só preditores)
def saude(cols, ano_inicio, anos_info, cache=CACHE, filtro=None):
    """O filtro mecânico do estudo E, com os anos da configuração. Devolve (coluna × grupo × motivo, resumo)."""
    anos_preench = range(ano_inicio, ULTIMO_ANO_PREDITOR_SAUDE + 1)
    filtro = filtro or V0.filtro_mecanico
    f = filtro(cache=cache, anos_preench=anos_preench, anos_info=anos_info, anos_fonte=anos_preench)
    f = f.set_index("coluna")
    linhas = []
    for g, cs in cols.items():
        for c in cs:
            if g == "infraestrutura":
                motivo = "PASSA (dimensão do artigo)"
            else:
                motivo = f.loc[c, "motivo"] if c in f.index else "fora_do_cache"
            linhas.append({"grupo": g, "coluna": c, "motivo": motivo})
    tab = pd.DataFrame(linhas)
    resumo = tab.pivot_table(index="grupo", columns="motivo", values="coluna", aggfunc="count", fill_value=0)
    resumo = resumo.reindex(list(cols))
    return tab, resumo


def passam(tab_saude):
    """{grupo: colunas que passaram}, na ordem dos grupos e em ordem alfabética."""
    ok = tab_saude[tab_saude["motivo"].str.startswith("PASSA")]
    return {g: sorted(ok.loc[ok["grupo"] == g, "coluna"]) for g in dict.fromkeys(tab_saude["grupo"])}


# ------------------------------------------------------------------ universo, divisão, redundância
def universo(d, etapa, ano_inicio):
    """Parte 2 do estudo E: públicas com abandono_tm1, abandono_t e abandono_t1; t de ANO_INICIO a 2023."""
    u = d[(d["etapa"] == etapa) & (d["rede_publica"] == 1) & d["abandono_tm1"].notna()
          & d["abandono_t"].notna() & d[DESFECHO].notna()
          & d["ano"].between(ano_inicio, ULTIMO_T_AVALIACAO)].copy()
    if u[ROTULO].isna().any():
        raise AssertionError("alto_risco_t1 vazio dentro do universo")
    return u


def dividir(u, ano_inicio):
    """Treino t = primeiro ano elegível..2021; teste t = 2022–2023, em ordem de ano. Sem sorteio de linhas."""
    a0 = primeiro_t_treino(u, ano_inicio)
    tr = u[u["ano"].between(a0, ULTIMO_T_TREINO)]
    te = pd.concat([u[u["ano"] == a] for a in range(TESTE[0], TESTE[1] + 1)])
    conferir_trava(tr, "treino")
    conferir_trava(te, "teste")
    return tr, te


def redundantes(tr, ordem, limiar=LIMIAR_REDUNDANCIA):
    """|r| > limiar entre preditores, calculado SÓ nas linhas de treino, na ordem fixa: a coluna sai se tiver
    |r| > limiar com alguma que ficou antes dela. Devolve (ficam, DataFrame das retiradas)."""
    ficam, retiradas = [], []
    x = tr[list(ordem)].astype("float64")
    for c in ordem:
        par = None
        for k in ficam:
            with np.errstate(all="ignore"), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = x[c].corr(x[k])            # coluna constante no treino: r indefinido, não é redundância
            if pd.notna(r) and abs(r) > limiar:
                par = (k, float(r))
                break
        if par:
            retiradas.append({"coluna": c, "redundante_com": par[0], "r_treino": round(par[1], 4)})
        else:
            ficam.append(c)
    return ficam, pd.DataFrame(retiradas, columns=["coluna", "redundante_com", "r_treino"])


def numericas(conjunto, novas, dims):
    base = (RENDIMENTO_A if conjunto.startswith("A") else []) + list(dims)
    return base + list(novas) if conjunto.endswith("+") else base


def _ajustar(pipe, X, y):
    """Todo ajuste passa por aqui: só linhas de treino (os testes conferem)."""
    conferir_trava(X, "treino")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pipe.fit(X, y)


def _pipeline(modelo, num, semente):
    if not num:      # sem numéricas (ex.: B sem infraestrutura): só as categóricas
        from sklearn.compose import ColumnTransformer
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.pipeline import Pipeline
        pipe = E.pipeline_p2(modelo, [], semente)
        pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS)], remainder="drop")
        return Pipeline([("pre", pre), ("m", pipe.named_steps["m"])])
    return E.pipeline_p2(modelo, num, semente)


def prever(tr, te, novas, dims, sementes):
    """{(conjunto, modelo): [nota por semente]} no teste, mais as réguas B1R_lag e B2. Notas em pp."""
    y_tr = tr[DESFECHO].astype("float64").to_numpy() / 100.0
    out = {("régua", "B1R_lag"): [te["abandono_tm1"].astype("float64").to_numpy()],
           ("régua", "B2"): [BL.b2_mediana_estrato(tr.assign(y_t1=tr[DESFECHO]), te, estrato=tuple(CATEGORICAS))]}
    for conjunto in CONJUNTOS:
        num = numericas(conjunto, novas, dims)
        ent = num + CATEGORICAS + ["ano"]                # ano só para a trava; não é preditor
        for modelo in MODELOS:
            lista = sementes if modelo == "mlp" else (None,)
            notas = []
            for s in lista:
                pipe = _ajustar(_pipeline(modelo, num, s), tr[ent], y_tr)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    notas.append(pipe.predict(te[ent]) * 100.0)
            out[(conjunto, modelo)] = notas
    return out


# ------------------------------------------------------------------ métricas com IC
def _recall(rot, notas, por_ano):
    vals = []
    for nota in notas:
        vals.append([CL.recall_k(rot[s], nota[s], M.k_de_fracao(len(s), FRACAO_TOPO)) if rot[s].sum() > 0
                     else np.nan for s in por_ano])
    return float(np.nanmean(np.asarray(vals, dtype="float64").mean(axis=0)))


def _mae(y, notas, idx=None):
    return float(np.mean([M.mae(y if idx is None else y[idx], n if idx is None else n[idx]) for n in notas]))


def sorteios_do_teste(te, n_boot=N_BOOT, semente=SEMENTE):
    anos = list(range(TESTE[0], TESTE[1] + 1))
    cel = [{"ano_alvo": a + 1, "y": te.loc[te["ano"] == a, ROTULO].astype(int).to_numpy(),
            "co": te.loc[te["ano"] == a, "co_entidade"].astype(str).to_numpy()} for a in anos]
    ag = B.Agrupado(cel)
    return ag, ag.sorteios(np.random.default_rng(semente), n_boot)


def metricas(te, prev, ag, sorteios):
    """Recall@20% (média dos dois anos de teste) e MAE, com IC 95% percentil; devolve (tabela, distribuições)."""
    rot = te[ROTULO].astype(int).to_numpy()
    y = te[DESFECHO].astype("float64").to_numpy()
    sel = [np.flatnonzero(te["ano"].to_numpy() == a) for a in range(TESTE[0], TESTE[1] + 1)]
    linhas, dists = [], {}
    for chave, notas in prev.items():
        mets = {"Recall@20%": (_recall(rot, notas, sel),
                               np.array([_recall(rot, notas, list(ag.por_ano(i).values())) for i in sorteios]))}
        if chave[1] != "B1R_lag":
            mets["MAE"] = (_mae(y, notas), np.array([_mae(y, notas, i) for i in sorteios]))
        for met, (ponto, dist) in mets.items():
            dists[(chave, met)] = dist
            lo, hi = np.nanpercentile(dist, [2.5, 97.5])
            linhas.append({"conjunto": chave[0], "modelo": chave[1], "n_sementes": len(notas), "metrica": met,
                           "valor": ponto, "ic_lo": float(lo), "ic_hi": float(hi)})
    return pd.DataFrame(linhas), dists


# ------------------------------------------------------------------ a exploração (célula 6)
def explorar(d, cols_ok, ano_inicio, remover_redundantes=True, n_sementes_mlp=5, n_boot=N_BOOT, semente=SEMENTE):
    """Uma janela de treino. `cols_ok`: {grupo: colunas que passaram na saúde}. Devolve um dicionário com, por
    etapa: tabela de métricas, distribuições, retiradas por redundância, tamanhos e o teste usado."""
    sementes = tuple(range(1, int(n_sementes_mlp) + 1))
    dims = list(cols_ok.get("infraestrutura", []))
    ordem = dims + [c for g, cs in cols_ok.items() if g != "infraestrutura" for c in sorted(cs)]
    censo = [c for c in ordem if c not in dims]
    res = {}
    for etapa in ETAPAS:
        u = universo(d, etapa, ano_inicio)
        tr, te = dividir(u, ano_inicio)
        if remover_redundantes:
            ficam, retiradas = redundantes(tr, ordem)
        else:
            ficam, retiradas = list(ordem), pd.DataFrame(columns=["coluna", "redundante_com", "r_treino"])
        dims_e = [c for c in dims if c in ficam]
        novas = [c for c in censo if c in ficam]
        prev = prever(tr, te, novas, dims_e, sementes)
        ag, sort = sorteios_do_teste(te, n_boot, semente)
        tab, dists = metricas(te, prev, ag, sort)
        tab.insert(0, "etapa", etapa)
        res[etapa] = {"metricas": tab, "dists": dists, "retiradas": retiradas, "n_novas": len(novas),
                      "n_treino": len(tr), "n_teste": len(te),
                      "anos_treino": (int(tr["ano"].min()), int(tr["ano"].max())),
                      "teste_chave": te[CHAVE].astype(str).agg("|".join, axis=1).tolist()}
    return res


def tabela(res):
    """As métricas das duas etapas numa tabela só, com o IC em texto."""
    t = pd.concat([r["metricas"] for r in res.values()], ignore_index=True)
    t["IC 95%"] = t.apply(lambda r: f"[{r.ic_lo:.3f}; {r.ic_hi:.3f}]", axis=1)
    return t.pivot_table(index=["etapa", "conjunto", "modelo"], columns="metrica", values=["valor", "IC 95%"],
                         aggfunc="first", sort=False)


# ------------------------------------------------------------------ comparação de janelas (célula 7)
def comparar(res_a, res_b, rotulo_a, rotulo_b):
    """Lado a lado e a diferença b − a, com IC pareado (as mesmas reamostragens do mesmo teste)."""
    linhas = []
    for etapa in ETAPAS:
        if res_a[etapa]["teste_chave"] != res_b[etapa]["teste_chave"]:
            raise AssertionError(f"{etapa}: o teste das duas janelas não é o mesmo")
        ta = res_a[etapa]["metricas"].set_index(["conjunto", "modelo", "metrica"])
        tb = res_b[etapa]["metricas"].set_index(["conjunto", "modelo", "metrica"])
        for chave in ta.index:
            da = res_a[etapa]["dists"][((chave[0], chave[1]), chave[2])]
            db = res_b[etapa]["dists"][((chave[0], chave[1]), chave[2])]
            dif = db - da
            lo, hi = np.nanpercentile(dif, [2.5, 97.5])
            linhas.append({"etapa": etapa, "conjunto": chave[0], "modelo": chave[1], "metrica": chave[2],
                           rotulo_a: ta.loc[chave, "valor"],
                           f"IC {rotulo_a}": f"[{ta.loc[chave, 'ic_lo']:.3f}; {ta.loc[chave, 'ic_hi']:.3f}]",
                           rotulo_b: tb.loc[chave, "valor"],
                           f"IC {rotulo_b}": f"[{tb.loc[chave, 'ic_lo']:.3f}; {tb.loc[chave, 'ic_hi']:.3f}]",
                           f"{rotulo_b} − {rotulo_a}": tb.loc[chave, "valor"] - ta.loc[chave, "valor"],
                           "IC da diferença (pareado)": f"[{lo:.3f}; {hi:.3f}]"})
    return pd.DataFrame(linhas)


def contra_regua(janelas):
    """Descritivo, sem veredito: Recall@20% de cada modelo − a régua B1R_lag, no mesmo teste, com IC pareado
    (as mesmas reamostragens). `janelas`: {rótulo: resultado de explorar()}."""
    linhas = []
    for rotulo, res in janelas.items():
        for etapa in ETAPAS:
            dists = res[etapa]["dists"]
            t = res[etapa]["metricas"].set_index(["conjunto", "modelo", "metrica"])
            regua = (("régua", "B1R_lag"), "Recall@20%")
            v_regua = t.loc[("régua", "B1R_lag", "Recall@20%"), "valor"]
            for conjunto in CONJUNTOS:
                for modelo in MODELOS:
                    dif = dists[((conjunto, modelo), "Recall@20%")] - dists[regua]
                    lo, hi = np.nanpercentile(dif, [2.5, 97.5])
                    linhas.append({"janela": rotulo, "etapa": etapa, "conjunto": conjunto, "modelo": modelo,
                                   "modelo − B1R_lag": t.loc[(conjunto, modelo, "Recall@20%"), "valor"] - v_regua,
                                   "IC pareado": f"[{lo:.3f}; {hi:.3f}]"})
    return pd.DataFrame(linhas)


def janela(d, cols, ano_inicio, remover_redundantes, n_sementes_mlp, saude_fn=saude, **kw):
    """A célula 6 inteira para um ANO_INICIO: saúde com os anos da janela, depois explorar()."""
    tab_s, _ = saude_fn(cols, ano_inicio, anos_treino(d, ano_inicio))
    return explorar(d, passam(tab_s), ano_inicio, remover_redundantes, n_sementes_mlp, **kw)


# ------------------------------------------------------------------ resultado oficial do estudo E (célula 5)
def _ler_e(nome, pasta=SAIDA_E):
    return pd.read_csv(pasta / nome, skiprows=1)


def resultado_e(pasta=SAIDA_E):
    """E1 (F8, Ridge), E2 (F9 e F10) e o Recall@20% do teste, lidos das saídas da execução única."""
    f8 = _ler_e("05_f8.csv", pasta)
    e1 = f8[f8["familia"] == "F8"][["etapa", "modelo", "diferenca", "ic_lo", "ic_hi", "p_holm", "veredito"]]
    t = _ler_e("08_previsao_testes.csv", pasta)
    e2 = t[t["familia"].isin(["F9", "F10"])][["familia", "etapa", "comparacao", "diferenca", "ic_lo", "ic_hi",
                                              "p_holm", "veredito"]]
    m = _ler_e("07_previsao_metricas.csv", pasta)
    rec = m[m["metrica"] == "Rec@20pct"][["etapa", "conjunto", "modelo", "valor", "ic_lo", "ic_hi"]]
    return e1.reset_index(drop=True), e2.reset_index(drop=True), rec.reset_index(drop=True)


# ------------------------------------------------------------------ gráfico
def barras_recall(rec, titulo):
    """Barras do Recall@20% por etapa, com o IC como traço. `rec`: etapa, conjunto, modelo, valor, ic_lo, ic_hi."""
    import matplotlib.pyplot as plt
    etapas = list(dict.fromkeys(rec["etapa"]))
    fig, eixos = plt.subplots(1, len(etapas), figsize=(6 * len(etapas), 4), sharey=True)
    eixos = np.atleast_1d(eixos)
    for ax, etapa in zip(eixos, etapas):
        r = rec[rec["etapa"] == etapa].reset_index(drop=True)
        rot = [f"{c}\n{m}" for c, m in zip(r["conjunto"], r["modelo"])]
        cores = ["#8c8c8c" if c == "régua" else "#3b6ea5" for c in r["conjunto"]]
        ax.bar(range(len(r)), r["valor"], color=cores)
        ax.errorbar(range(len(r)), r["valor"], yerr=[r["valor"] - r["ic_lo"], r["ic_hi"] - r["valor"]],
                    fmt="none", ecolor="black", capsize=3, lw=1)
        ax.set_xticks(range(len(r)))
        ax.set_xticklabels(rot, fontsize=8)
        ax.set_title(etapa)
        ax.set_ylim(0, 1)
    eixos[0].set_ylabel("Recall@20%")
    fig.suptitle(titulo)
    fig.tight_layout()
    return fig


def recall_de(res):
    t = pd.concat([r["metricas"] for r in res.values()], ignore_index=True)
    return t[t["metrica"] == "Recall@20%"]
