# -*- coding: utf-8 -*-
"""
02 — Valida os índices de infraestrutura (05) em base_atual.parquet.

Recalcula tudo de forma independente (numpy, sem reaproveitar as colunas
gravadas nem as funções de conta do 05) e compara:
  A. presença, tipos e ausência das colunas legadas (zref19, prop fora do padrão)
  B. itens disponíveis por ano (fatos conhecidos do Censo + estrutura 0/100%)
  C. dimensões: soma dos itens disponíveis, NaN só quando falta item, z por ano
  D. SEM VAZAMENTO: perturbar os outros anos não muda o ano t (executa o 05 de verdade)
  E. IIE: PC1 do próprio ano, pesos, autovalores, critérios do artigo (Kaiser, >60%)
  F. cobertura 2007-2025 e marcador INFRA_ITENS_COMPLETOS
  G. sanidade substantiva e limitação de 2007-2011 (persistência na virada 2011->2012)
  H. colunas opcionais --com-prop (só se existirem)

Saída: gustavo/saida/relatorios/validacao_indices.txt
Uso:   python testes/02_validar_indices.py
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
P_ATUAL = GUSTAVO / "saida" / "base_atual.parquet"
P_JSON = GUSTAVO / "saida" / "relatorios" / "indices_infra_parametros.json"
REPORT = GUSTAVO / "saida" / "relatorios" / "validacao_indices.txt"
TOL = 1e-9

# do 05 só as CONSTANTES e a função pura 'calcular' (usada apenas na seção D)
spec = importlib.util.spec_from_file_location(
    "ind05", GUSTAVO / "src" / "estendida" / "05_indices_infra.py")
ind05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind05)
DIMS = ind05.DIMENSOES
ITENS = [i for l in DIMS.values() for i in l]
COL_FLAG = ind05.COL_FLAG
MIN_N = ind05.MIN_ESCOLAS_ANO
ZCOLS = [f"DIM_{d}_zano" for d in DIMS]
# fatos do Censo (relatório 04): itens que NÃO foram coletados em 2007-2011
SO_2012 = ["IDA_despensa", "IDA_refeitorio", "IDA_secretaria",
           "IDP_patio_coberto", "IDP_patio_descoberto"]

log, cont = [], {"ok": 0, "warn": 0, "fail": 0}


def secao(t):
    log.extend(["", "=" * 78, t, "=" * 78])


def ok(m):
    cont["ok"] += 1; log.append(f"  ✅ {m}")


def warn(m):
    cont["warn"] += 1; log.append(f"  ⚠️  {m}")


def fail(m):
    cont["fail"] += 1; log.append(f"  ❌ {m}")


def info(m):
    log.append(f"     {m}")


def check(cond, msg_ok, msg_fail):
    ok(msg_ok) if cond else fail(msg_fail)


for p in (P_ATUAL, P_JSON):
    if not p.exists():
        print(f"[ERRO] falta {p} — rode o pipeline (99_pipeline.py)")
        sys.exit(1)
base = pd.read_parquet(P_ATUAL)
par = json.loads(P_JSON.read_text(encoding="utf-8"))
ANO = base["ANO"].astype(int)
ano_arr = ANO.to_numpy()
anos = sorted(set(ano_arr.tolist()))
com_prop = "IIE_prop" in base.columns
F = base[ITENS].astype("float64")
X_all = F.to_numpy()
col_ix = {c: k for k, c in enumerate(ITENS)}

# ------------------------------------------------------------------
secao("A. COLUNAS, TIPOS E COLUNAS LEGADAS")
# ------------------------------------------------------------------
esperadas = ind05.nomes_colunas(com_prop)
falt = [c for c in esperadas if c not in base.columns]
check(not falt, f"{len(esperadas)} colunas derivadas presentes: {', '.join(esperadas)}",
      f"faltam colunas derivadas: {falt}")
check(all(str(base[i].dtype) == "Int8" for i in ITENS), "18 itens seguem Int8 (regra 6)",
      "algum dos 18 itens não é Int8")
tipo_f = [c for c in esperadas if c != COL_FLAG and str(base[c].dtype) != "Float64"]
check(not tipo_f and str(base[COL_FLAG].dtype) == "Int8",
      f"derivadas Float64 e {COL_FLAG} Int8 (regra 6)",
      f"tipos errados: {tipo_f} / {COL_FLAG}={base[COL_FLAG].dtype}")
leg = [c for c in base.columns if c.endswith("_zref19")]
check(not leg, "nenhuma coluna legada _zref19 na base (método descartado em 14/10)",
      f"colunas legadas presentes: {leg}")
if not com_prop:
    legp = [c for c in base.columns if c.endswith("_prop")]
    check(not legp, "nenhuma coluna _prop (fora do padrão; use 05 --com-prop se quiser)",
          f"colunas _prop presentes sem --com-prop: {legp}")
check(base.duplicated(["CO_ENTIDADE", "ANO"]).sum() == 0, "chave (CO_ENTIDADE, ANO) única",
      "há (CO_ENTIDADE, ANO) duplicado")

# ------------------------------------------------------------------
secao("B. ITENS DISPONÍVEIS POR ANO")
# ------------------------------------------------------------------
disp = {}                       # (ano, dim) -> lista de itens
estrutural = True
for a in anos:
    m = ano_arr == a
    for d, l in DIMS.items():
        av = []
        for i in l:
            cobi = float(np.mean(~np.isnan(X_all[m, col_ix[i]])))
            if cobi > 0:
                av.append(i)
            if 0 < cobi < 1:
                estrutural = False
        disp[(a, d)] = av
check(estrutural, "cada item tem valor em 0% ou 100% das escolas de cada ano (ausência é estrutural)",
      "há item com cobertura parcial dentro de um ano")
json_ok = all(par["itens_por_ano"][str(a)][d] == disp[(a, d)] for a in anos for d in DIMS)
check(json_ok, "itens por ano do JSON = recomputados do parquet",
      "itens por ano do JSON divergem do parquet")
ok_fatos = True
for i in ITENS:
    anos_i = [a for a in anos if i in disp[(a, i.split("_")[0])]]
    esperado = [a for a in anos if a >= 2012] if i in SO_2012 else anos
    ok_fatos &= anos_i == esperado
check(ok_fatos, "13 itens existem em 2007-2025; 5 (despensa, refeitório, secretaria, pátios) só de 2012 em diante",
      "disponibilidade dos itens diverge do fato documentado no relatório 04")
resumo = {a: [len(disp[(a, d)]) for d in DIMS] for a in (2007, 2011, 2012, 2025)}
info("itens usados (IIB IDA IDP IEP): " + "; ".join(f"{a}: {v}" for a, v in resumo.items()))

# ------------------------------------------------------------------
secao("C. DIMENSÕES: soma dos itens disponíveis e z por ano (recomputados)")
# ------------------------------------------------------------------
soma_i, z_i = {}, {}
dif_max, dp_max_desv, media_max = 0.0, 0.0, 0.0
nan_ok, faixa_ok, ddof_ok = True, True, True
for d, l in DIMS.items():
    soma_i[d] = np.full(len(base), np.nan)
    z_i[d] = np.full(len(base), np.nan)
    for a in anos:
        m = ano_arr == a
        av = disp[(a, d)]
        X = X_all[np.ix_(np.flatnonzero(m), [col_ix[i] for i in av])]
        s = np.where(np.isnan(X).any(axis=1), np.nan, X.sum(axis=1))
        soma_i[d][m] = s
        v = s[~np.isnan(s)]
        faixa_ok &= bool(((v >= 0) & (v <= len(av))).all())
        if len(v) >= MIN_N and v.std() > 0:
            z_i[d][m] = (s - v.mean()) / v.std()          # ddof=0
    got = base[f"DIM_{d}_zano"].astype("float64").to_numpy()
    nan_ok &= bool((np.isnan(got) == np.isnan(z_i[d])).all())
    both = ~np.isnan(got) & ~np.isnan(z_i[d])
    dif_max = max(dif_max, float(np.abs(got[both] - z_i[d][both]).max()))
    for a in anos:
        g = got[(ano_arr == a) & ~np.isnan(got)]
        if len(g) >= MIN_N:
            media_max = max(media_max, abs(float(g.mean())))
            dp_max_desv = max(dp_max_desv, abs(float(g.std()) - 1))
check(nan_ok, "NaN das 4 dimensões coincide com o recomputado (só falta item numa escola gera NaN)",
      "padrão de NaN das dimensões diverge do recomputado")
check(dif_max < TOL, f"DIM_*_zano = z da soma dos itens disponíveis do ano (erro máx {dif_max:.1e})",
      f"DIM_*_zano diverge do recomputado (erro máx {dif_max:.2e})")
check(faixa_ok, "soma bruta sempre entre 0 e o nº de itens disponíveis",
      "soma bruta fora de [0, nº de itens]")
check(media_max < 1e-9 and dp_max_desv < 1e-9,
      f"cada dimensão tem média 0 e desvio 1 em todos os anos (desvios máx: {media_max:.1e}, {dp_max_desv:.1e})",
      f"z por ano não tem média 0/desvio 1 (média {media_max:.2e}, dp {dp_max_desv:.2e})")
ez = pd.DataFrame(par["z_por_ano"])
chk = True
for r in ez.itertuples():
    if r.valido:
        s = soma_i[r.dim][ano_arr == r.ano]; s = s[~np.isnan(s)]
        chk &= abs(r.media_soma - s.mean()) < 1e-9 and abs(r.dp_soma - s.std()) < 1e-9 and r.n == len(s)
check(chk, "média/desvio/n por (dimensão, ano) do JSON = recomputados", "parâmetros z do JSON divergem")
inval = ez[~ez["valido"]]
check(len(inval) == 0, f"todo (dimensão, ano) tem n ≥ {MIN_N} e desvio > 0",
      f"(dimensão, ano) sem z: {[(r.dim, r.ano) for r in inval.itertuples()][:6]}")
menor = ez.loc[ez["dp_soma"].idxmin()]
(ok if menor["dp_soma"] >= 0.5 else warn)(
    f"menor desvio da soma bruta: {menor['dp_soma']:.2f} ({menor['dim']}/{int(menor['ano'])}) "
    "— abaixo de 0,5 o z-score amplifica ruído")

# ------------------------------------------------------------------
secao("D. SEM VAZAMENTO TEMPORAL (executa o 05 em dados perturbados)")
# ------------------------------------------------------------------
rng = np.random.default_rng(14102026)
cols_d = ZCOLS + ["IIE_zano"]
orig = base[cols_d].astype("float64").to_numpy()
entrada = base[["ANO"] + ITENS].copy()
entrada[ITENS] = entrada[ITENS].astype("float64")
for a in (2009, 2012, 2019, 2025):
    pert = entrada.copy()
    fora = ano_arr != a
    for i in ITENS:
        pert.loc[fora, i] = rng.integers(0, 2, fora.sum()).astype("float64")
    nov, _ = ind05.calcular(pert)
    nv = nov[cols_d].astype("float64").to_numpy()
    m = ano_arr == a
    mesmo = (np.isnan(nv[m]) == np.isnan(orig[m])).all() and \
        np.nanmax(np.abs(nv[m] - orig[m])) < 1e-12
    check(mesmo, f"{a}: embaralhar todos os OUTROS anos não muda as 5 colunas de {a}",
          f"{a}: o resultado de {a} depende de outros anos (vazamento!)")
# controle negativo: um z com média/desvio de TODOS os anos (método vazado) mudaria o ano 2019
# quando os outros anos são perturbados -> prova que o teste acima é capaz de detectar vazamento
pert = entrada.copy()
fora = ano_arr != 2019
for i in ITENS:
    pert.loc[fora, i] = rng.integers(0, 2, fora.sum()).astype("float64")


def z_global(df):
    s_ = df[DIMS["IIB"]].sum(axis=1, min_count=4)
    return ((s_ - s_.mean()) / s_.std(ddof=0)).to_numpy()


dg = np.abs(z_global(entrada)[ano_arr == 2019] - z_global(pert)[ano_arr == 2019]).max()
check(dg > 1e-3, f"controle negativo: um z com parâmetros de todos os anos MUDARIA 2019 (Δ máx {dg:.2f}) — o teste enxerga vazamento",
      "controle negativo falhou: o teste de vazamento não distingue um método vazado")
alt = entrada.copy()
mm = ano_arr == 2019
for i in ITENS:
    alt.loc[mm, i] = rng.integers(0, 2, mm.sum()).astype("float64")
nov, _ = ind05.calcular(alt)
nv = nov[cols_d].astype("float64").to_numpy()
mesmo = (np.isnan(nv[~mm]) == np.isnan(orig[~mm])).all() and \
    np.nanmax(np.abs(nv[~mm] - orig[~mm])) < 1e-12
check(mesmo, "embaralhar 2019 não altera nenhum outro ano (sem influência do futuro sobre o passado, nem o inverso)",
      "mudar 2019 alterou outros anos")

# ------------------------------------------------------------------
secao("E. IIE: PC1 do próprio ano")
# ------------------------------------------------------------------
Zb = np.column_stack([base[c].astype("float64").to_numpy() for c in ZCOLS])
iie_i = np.full(len(base), np.nan)
w_max_json, kaiser_ok, p60_ok, norma_ok, soma_pos, pesos_faixa, var_ok = 0.0, True, True, True, True, True, True
for a in anos:
    m = ano_arr == a
    M = Zb[m]; okr = ~np.isnan(M).any(axis=1)
    R = np.corrcoef(M[okr].T)
    vals, vecs = np.linalg.eigh(R)
    w = vecs[:, -1]
    if w.sum() < 0:
        w = -w
    tmp = np.full(m.sum(), np.nan); tmp[okr] = M[okr] @ w; iie_i[m] = tmp
    pj = par["pca_por_ano"][str(a)]
    wj = np.array(list(pj["pesos_pc1"].values()))
    w_max_json = max(w_max_json, float(np.abs(w - wj).max()), abs(vals[-1] - pj["autovalores"][0]))
    kaiser_ok &= vals[-1] > 1
    p60_ok &= vals[-1] / vals.sum() > 0.6
    norma_ok &= abs(np.linalg.norm(w) - 1) < 1e-9
    soma_pos &= w.sum() > 0
    pesos_faixa &= bool(((w > 0.35) & (w < 0.65)).all())
    var_ok &= abs(tmp[okr].var() - vals[-1]) < 1e-6
got = base["IIE_zano"].astype("float64").to_numpy()
check((np.isnan(got) == np.isnan(iie_i)).all(), "IIE_zano é NaN exatamente quando falta alguma das 4 dimensões",
      "padrão de NaN do IIE diverge do recomputado")
d_iie = float(np.nanmax(np.abs(got - iie_i)))
check(d_iie < 1e-9, f"IIE_zano = soma(peso·dimensão) com PC1 do ano (erro máx {d_iie:.1e})",
      f"IIE_zano diverge do recomputado (erro máx {d_iie:.2e})")
check(w_max_json < 1e-9, "pesos e autovalores por ano do JSON = recomputados",
      f"pesos/autovalores do JSON divergem ({w_max_json:.2e})")
check(norma_ok and soma_pos, "pesos de norma 1 e soma > 0 em todos os anos", "norma/sinal dos pesos incorretos")
check(var_ok, "variância do IIE em cada ano = autovalor do PC1", "variância do IIE ≠ autovalor")
check(kaiser_ok, "critério de Kaiser (autovalor PC1 > 1) em todos os anos",
      "Kaiser falha em algum ano")
check(p60_ok, "PC1 explica > 60% da variância em todos os anos (critério do artigo)",
      "PC1 ≤ 60% em algum ano")
check(pesos_faixa, "nenhum peso fora de 0,35–0,65 (dimensões contribuem de forma parecida)",
      "algum peso fora de 0,35–0,65")
W = np.array([list(par["pca_por_ano"][str(a)]["pesos_pc1"].values()) for a in anos])
info("pesos PC1 por dimensão (mín–máx entre anos): " + "; ".join(
    f"{d} {W[:, k].min():.3f}–{W[:, k].max():.3f}" for k, d in enumerate(DIMS)))
info("variância explicada pelo PC1: " + f"{min(par['pca_por_ano'][str(a)]['variancia_explicada'][0] for a in anos)*100:.1f}%"
     f"–{max(par['pca_por_ano'][str(a)]['variancia_explicada'][0] for a in anos)*100:.1f}%")

# ------------------------------------------------------------------
secao("F. COBERTURA 2007-2025 E MARCADOR DE ITENS COMPLETOS")
# ------------------------------------------------------------------
cob = base.groupby(ANO)[ZCOLS + ["IIE_zano"]].apply(lambda d: d.notna().mean() * 100)
check((cob.min().min() == 100), "as 4 dimensões e o IIE existem para 100% das escolas em todos os anos (2007-2025)",
      f"cobertura < 100% em algum ano (mínimo {cob.min().min():.1f}%)")
fl = base[COL_FLAG].astype("int64").to_numpy()
comp_i = np.array([int(all(len(disp[(a, d)]) == len(l) for d, l in DIMS.items())) for a in ano_arr])
check((fl == comp_i).all(), f"{COL_FLAG} = 1 exatamente nos anos em que as 4 dimensões usam todos os itens do artigo",
      f"{COL_FLAG} diverge do recomputado")
check(((fl == 1) == (ano_arr >= 2012)).all(), f"{COL_FLAG} = 1 para 2012-2025 e 0 para 2007-2011",
      f"{COL_FLAG} não coincide com 2012+")
check(base[COL_FLAG].notna().all(), f"{COL_FLAG} sem ausentes", f"{COL_FLAG} tem ausentes")
info(f"escolas-ano com itens completos: {int(fl.sum())} de {len(fl)} ({fl.mean()*100:.1f}%)")

# ------------------------------------------------------------------
secao("G. SANIDADE SUBSTANTIVA E LIMITAÇÃO DE 2007-2011")
# ------------------------------------------------------------------
loc = base["LOCALIZACAO"].astype(str).str.lower()
for a in (2012, 2019, 2025):
    t = pd.Series(got[ano_arr == a]).groupby(loc[ano_arr == a].to_numpy()).mean()
    urb = [k for k in t.index if k.startswith("urb")]; rur = [k for k in t.index if k.startswith("rur")]
    if urb and rur:
        check(t[urb[0]] > t[rur[0]], f"{a}: IIE médio urbano ({t[urb[0]]:.2f}) > rural ({t[rur[0]]:.2f})",
              f"{a}: IIE urbano ≤ rural")
eq = np.nanmean(Zb, axis=1)
rs = []
for a in anos:
    m = ano_arr == a
    rs.append(pd.Series(got[m]).rank().corr(pd.Series(eq[m]).rank()))
check(min(rs) > 0.995, f"IIE com PC1 ordena como a média simples das 4 dimensões (Spearman mínimo {min(rs):.4f})",
      f"IIE e média simples divergem (mínimo {min(rs):.4f})")
chave = pd.Series(np.arange(len(base)), index=(base["CO_ENTIDADE"].astype(str) + "_" + ANO.astype(str)).to_numpy())


def persist(v, a):
    cur = np.flatnonzero(ano_arr == a)
    k = base["CO_ENTIDADE"].astype(str).iloc[cur] + "_" + str(a + 1)
    okk = k.isin(chave.index).to_numpy()
    x, y = v[cur[okk]], v[chave.loc[k[okk]].to_numpy()]
    m = ~(np.isnan(x) | np.isnan(y))
    return pd.Series(x[m]).rank().corr(pd.Series(y[m]).rank())


info("persistência da posição da mesma escola (Spearman t→t+1) em volta da virada de itens:")
info(f"  {'transição':>10}{'IDA':>8}{'IDP':>8}{'IIE':>8}")
P = {}
vecs_g = {"IDA": base["DIM_IDA_zano"].astype("float64").to_numpy(),
          "IDP": base["DIM_IDP_zano"].astype("float64").to_numpy(), "IIE": got}
for a in (2009, 2010, 2011, 2012, 2013):
    P[a] = {k: persist(v, a) for k, v in vecs_g.items()}
    info(f"  {a}→{a+1:>4}{P[a]['IDA']:>8.3f}{P[a]['IDP']:>8.3f}{P[a]['IIE']:>8.3f}"
         + ("   <- virada de itens" if a == 2011 else ""))
for k in ("IDA", "IDP", "IIE"):
    viz = np.mean([P[a][k] for a in (2009, 2010, 2012, 2013)])
    queda = viz - P[2011][k]
    (ok if queda < 0.10 else warn)(
        f"{k}: persistência na virada 2011→2012 = {P[2011][k]:.3f} (vizinhos {viz:.3f}; queda {queda:.3f})"
        + ("" if queda < 0.10 else " — queda > 0,10"))
info("Limitação documentada: IDA/IDP de 2007-2011 usam 2 e 3 itens (relatório 05).")

# ------------------------------------------------------------------
secao("H. COLUNAS OPCIONAIS (--com-prop)")
# ------------------------------------------------------------------
if not com_prop:
    info("base gerada sem --com-prop: nada a validar nesta seção")
else:
    errp, rngp, rho = 0.0, True, 1.0
    props = []
    for d in DIMS:
        pv = np.full(len(base), np.nan)
        for a in anos:
            m = ano_arr == a
            pv[m] = soma_i[d][m] / len(disp[(a, d)])
        props.append(pv)
        g = base[f"DIM_{d}_prop"].astype("float64").to_numpy()
        b2 = ~np.isnan(g) & ~np.isnan(pv)
        errp = max(errp, float(np.abs(g[b2] - pv[b2]).max()))
        rngp &= bool(((g[b2] >= 0) & (g[b2] <= 1)).all())
        for a in anos:
            m = (ano_arr == a) & b2
            rho = min(rho, pd.Series(g[m]).rank().corr(pd.Series(base[f"DIM_{d}_zano"].astype("float64").to_numpy()[m]).rank()))
    check(errp < TOL, f"DIM_*_prop = soma/nº de itens disponíveis do ano (erro máx {errp:.1e})",
          f"DIM_*_prop diverge ({errp:.2e})")
    check(rngp, "DIM_*_prop em [0, 1]", "DIM_*_prop fora de [0,1]")
    check(rho > 0.9999, f"dentro do ano, prop e zano ordenam as dimensões de forma idêntica (Spearman mínimo {rho:.4f})",
          f"prop e zano divergem na ordenação ({rho:.4f})")
    ie = np.nanmean(np.column_stack(props), axis=1)
    ie = np.where(np.isnan(np.column_stack(props)).any(axis=1), np.nan, ie)
    g = base["IIE_prop"].astype("float64").to_numpy()
    b2 = ~np.isnan(g) & ~np.isnan(ie)
    check((np.isnan(g) == np.isnan(ie)).all() and float(np.abs(g[b2] - ie[b2]).max()) < TOL,
          "IIE_prop = média simples das 4 dimensões prop", "IIE_prop diverge da média simples")

# ------------------------------------------------------------------
secao("RESUMO")
# ------------------------------------------------------------------
log.append(f"  ✅ OK:      {cont['ok']}")
log.append(f"  ⚠️  Warn:   {cont['warn']}")
log.append(f"  ❌ Falhas:  {cont['fail']}")
log.append("")
log.append("  🎉 ÍNDICES VALIDADOS" if cont["fail"] == 0
           else f"  ❌ {cont['fail']} falhas — revisar")
txt = "\n".join(log)
print(txt)
REPORT.write_text(txt, encoding="utf-8")
print(f"\n>>> Relatório: {REPORT}")
sys.exit(1 if cont["fail"] else 0)
