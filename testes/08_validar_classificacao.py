# -*- coding: utf-8 -*-
"""
08 — Valida a ferramenta de classificação de alto risco (avaliacao/classificacao.py
e o bootstrap de avaliacao/03_classificacao.py), antes da execução única.

Este teste NÃO calcula nenhuma métrica dos modelos nos dados reais: nos dados
reais ele só confere o painel, as contagens e a igualdade de previsões entre
execuções (vazamento). As métricas são conferidas em exemplos pequenos.

  A. Métricas à mão num exemplo de 10 escolas: matriz de confusão, precisão,
     recall, F1, Recall@K, Precision@K, PR-AUC, ROC-AUC; PR-AUC em numpy igual
     à do scikit-learn (com empates); nota constante = acaso
  B. Rótulo: 20% maiores do ano, empates no limiar, zero nunca é alto risco
  C. Painel: universo (pública; taxa em t−1, t e t+1), defasagens conferidas
     linha a linha, nenhuma variável de t ou de t+1 entre os preditores,
     nunca as três taxas juntas
  D. Contagens por ano contra o funil (saida/relatorios/funil_recorte.csv)
  E. Sem vazamento: perturbar os anos futuros (alvo e variáveis) não muda as
     previsões do ano; perturbar o alvo do próprio ano de teste também não;
     imputação e padronização ajustadas só com o treino
  F. Bootstrap e leitura: nota constante = acaso em toda reamostragem; F6 com
     36 testes; regra de leitura (GANHO, SEM GANHO PRÁTICO, INCONCLUSIVO)

Saída: gustavo/saida/relatorios/validacao_classificacao.txt
Uso:   python testes/08_validar_classificacao.py
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, f1_score, precision_score, recall_score,
                             roc_auc_score)

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
sys.path.insert(0, str(GUSTAVO / "src" / "avaliacao"))
import baselines as B  # noqa: E402
import classificacao as C  # noqa: E402
import painel as P  # noqa: E402

spec = importlib.util.spec_from_file_location("exec03", GUSTAVO / "experimentos" / "classificacao_2013_2018" / "03_classificacao.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

REPORT = GUSTAVO / "saida" / "relatorios" / "validacao_classificacao.txt"
P_FUNIL = GUSTAVO / "saida" / "relatorios" / "funil_recorte.csv"
TOL = 1e-12

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
log, cont = [], {"ok": 0, "fail": 0}


def secao(t):
    log.extend(["", t])


def check(cond, m):
    cont["ok" if cond else "fail"] += 1
    log.append(f"  {'✅' if cond else '❌'} {m}")


def perto(a, b, tol=TOL):
    return abs(a - b) <= tol


rng = np.random.default_rng(8)
base = pd.read_parquet(P.P_ATUAL)

# ------------------------------------------------------------------ A
secao("A. Métricas à mão (10 escolas)")
rot = np.array([1, 1, 0, 1, 0, 0, 0, 0, 0, 0])
prob = np.array([.9, .8, .7, .4, .6, .3, .2, .2, .1, .05])
vp, fp, fn, vn = C.confusao(rot, prob)
check((vp, fp, fn, vn) == (2, 2, 1, 5), f"matriz de confusão no limiar 0,5: VP 2, FP 2, FN 1, VN 5 (obtido {vp}, {fp}, {fn}, {vn})")
prec, rec, f1 = C.prf(vp, fp, fn)
check(perto(prec, 2 / 4) and perto(rec, 2 / 3) and perto(f1, 2 * 2 / (2 * 2 + 2 + 1)),
      "precisão 2/4, recall 2/3, F1 4/7")
prev = (prob >= .5).astype(int)
check(perto(prec, precision_score(rot, prev)) and perto(rec, recall_score(rot, prev)) and perto(f1, f1_score(rot, prev)),
      "precisão, recall e F1 iguais aos do scikit-learn")
check(np.isnan(C.prf(0, 0, 3)[0]) and C.prf(0, 0, 3)[1] == 0, "sem nenhuma escola classificada: precisão indefinida (NaN), recall 0")
check(perto(C.recall_k(rot, prob, 3), 2 / 3) and perto(C.precisao_k(rot, prob, 3), 2 / 3),
      "lista de 3 escolas com 3 de alto risco: Recall@3 = Precision@3 = 2/3")
check(perto(C.recall_k(rot, prob, 5), 1.0) and perto(C.precisao_k(rot, prob, 5), 3 / 5), "Recall@5 = 3/3, Precision@5 = 3/5")
# empate na fronteira: posições 7 e 8 têm nota 0,2; uma delas é de alto risco
rot_e = np.array([1, 0, 0, 0, 0, 0, 1, 0, 0, 0])
check(perto(C.acertos_topk(rot_e, prob, 7), 1 + 0.5), "empate de nota na fronteira da lista: acerto esperado = 1 + 1/2")
# PR-AUC à mão: positivos nas posições 1, 2 e 5 da lista -> (1/1 + 2/2 + 3/5) / 3
check(perto(C.pr_auc(rot, prob), (1 + 1 + 3 / 5) / 3), "PR-AUC (precisão média) = (1 + 1 + 3/5) / 3")
# ROC-AUC à mão: pares (alto, não alto) bem ordenados = 7 + 7 + 5 de 21
check(perto(C.roc_auc(rot, prob), 19 / 21), "ROC-AUC = 19 de 21 pares bem ordenados")
pior = 0.0
for _ in range(200):
    n = int(rng.integers(8, 60))
    r = (rng.random(n) < .25).astype(int)
    r[0] = 1
    v = rng.integers(0, 6, n) / 5.0 if rng.random() < .5 else rng.random(n)
    pior = max(pior, abs(C.pr_auc_rapida(r, v) - average_precision_score(r, v)))
check(pior <= TOL, f"PR-AUC em numpy igual à do scikit-learn em 200 sorteios, com empates (maior diferença {pior:.1e})")
const = np.full(10, .3)
check(perto(C.pr_auc(rot, const), .3) and perto(C.recall_k(rot, const, 2), 2 / 10) and perto(roc_auc_score(rot, const), .5),
      "nota constante: PR-AUC = prevalência, Recall@K = K/n, ROC-AUC = 0,5 (o acaso)")
m = C.metricas_ano(rot, prob, True)
check(m["n"] == 10 and m["n_alto"] == 3 and m["K20pct"] == 2 and perto(m["Rec@20pct"], 2 / 3) and perto(m["Prec@20pct"], 1.0),
      "metricas_ano: n, alto risco, K de 20% e Recall/Precision@20% do exemplo")
check("precisao_05" not in C.metricas_ano(rot, prob, False), "régua (nota que não é probabilidade): sem precisão, recall e F1 no limiar 0,5")

# ------------------------------------------------------------------ B
secao("B. Rótulo de alto risco")
y = np.array([30., 20., 10., 5., 5., 0., 0., 0., 0., 0.])
check(C.rotular(y).tolist() == [1, 1, 0, 0, 0, 0, 0, 0, 0, 0], "10 escolas: as 2 maiores (20%) são de alto risco")
y2 = np.array([30., 20., 20., 5., 5., 0., 0., 0., 0., 0.])
check(C.rotular(y2).sum() == 3, "empate no limiar: as escolas empatadas entram todas")
y3 = np.array([4., 0., 0., 0., 0., 0., 0., 0., 0., 0.])
check(C.rotular(y3).tolist() == [1] + [0] * 9, "abandono zero nunca é alto risco, mesmo dentro dos 20%")

# ------------------------------------------------------------------ C
secao("C. Painel")
paineis = {e: C.montar(e, base) for e in ("AF", "EM")}
for etapa, pn in paineis.items():
    s = P.SUF[etapa]
    col = B.ETAPAS[etapa]
    check(sorted(pn["ANO"].unique()) == list(C.ANOS_T) and sorted(pn["ANO_ALVO"].unique()) == [a + 1 for a in C.ANOS_T],
          f"{etapa}: t de {C.ANOS_T[0]} a {C.ANOS_T[-1]}, alvo de {C.ANOS_T[0] + 1} a {C.ANOS_T[-1] + 1}")
    check(not pn.duplicated(P.CHAVE).any(), f"{etapa}: chave (ANO, CO_ENTIDADE) única ({len(pn)} linhas)")
    orig = pn[P.CHAVE].merge(base, on=P.CHAVE, how="left", validate="1:1")
    check((orig["REDE_PUBLICA"].astype("Int8") == 1).all(), f"{etapa}: só escolas públicas")
    check(pn["y_t"].notna().all() and pn["y_t1"].notna().all() and pn[f"ABANDONO_{s}_L1"].notna().all(),
          f"{etapa}: todas com taxa da etapa em t−1, t e t+1")
    # defasagens conferidas contra a linha do ano anterior na base
    ant = base[P.CHAVE + [col, f"REPROVACAO_{s}"]].copy()
    dif = 0.0
    for lag, tag in ((1, "L1"), (2, "L2")):
        a = ant.assign(ANO=ant["ANO"] + lag)
        mm = pn.merge(a, on=P.CHAVE, how="left", validate="1:1")
        for origem, destino in ((col, f"ABANDONO_{s}_{tag}"), (f"REPROVACAO_{s}", f"REPROVACAO_{s}_{tag}")):
            x, z = mm[origem].astype("Float64").astype("float64"), mm[destino]
            check(bool((x.isna() == z.isna()).all()), f"{etapa}: {destino} ausente exatamente onde a base não tem t−{lag}")
            dif = max(dif, float((x - z).abs().max()))
    check(dif == 0.0, f"{etapa}: abandono e reprovação de t−1 e t−2 iguais aos da base, linha a linha")
    d = pn[f"ABANDONO_{s}_L1"] - pn[f"ABANDONO_{s}_L2"]
    check(bool(((d - pn[f"ABANDONO_{s}_DLAG"]).abs().fillna(0) == 0).all()), f"{etapa}: variação defasada = (t−1) − (t−2)")
    cols3 = C.colunas_bloco(etapa, 3)
    proibidas = {"y_t", "y_t1", "alto_top20", "alto_abs10", col, f"{col}_T1", f"REPROVACAO_{s}", f"APROVACAO_{s}"}
    check(not proibidas & set(cols3) and all(c.endswith(("_L1", "_DLAG")) or c in C.CATEGORICAS or c in P.INFRA for c in cols3),
          f"{etapa}: preditores só de t−1, t−2, território, rede e infraestrutura; nenhum de rendimento de t nem de t+1 ({len(cols3)} colunas)")
    check(not any("APROVACAO" in c for c in cols3), f"{etapa}: nunca as três taxas juntas (sem aprovação; P026)")
    check(len(C.colunas_bloco(etapa, 1)) == 3 and len(C.colunas_bloco(etapa, 2)) == 5 and len(cols3) == 10,
          f"{etapa}: blocos cumulativos com 3, 5 e 10 colunas")
    rot_ref = pn.groupby("ANO_ALVO")["y_t1"].transform(lambda v: C.rotular(v.to_numpy()))
    check(bool((rot_ref == pn["alto_top20"]).all()) and bool(((pn["y_t1"] >= 10).astype(int) == pn["alto_abs10"]).all()),
          f"{etapa}: rótulos conferidos (20% maiores do ano; sensibilidade ≥ 10)")
    prevs = pn.groupby("ANO_ALVO")["alto_top20"].mean()
    check(bool(prevs.between(.10, .25).all()), f"{etapa}: prevalência anual do alto risco entre {prevs.min():.3f} e {prevs.max():.3f}")

# ------------------------------------------------------------------ D
secao("D. Contagens por ano contra o funil")
funil = pd.read_csv(P_FUNIL)
for etapa, pn in paineis.items():
    s, col = P.SUF[etapa], B.ETAPAS[etapa]
    f = funil[(funil["etapa"] == etapa) & funil["ano"].isin(C.ANOS_T)]
    com_t_t1 = f[f["ordem"] == 5].set_index("ano")["n"].astype(int)
    # sem t−1, contado de forma independente na base
    b = base[base["REDE_PUBLICA"].astype("Int8") == 1]
    tem = b[b[col].notna() & b[f"{col}_T1"].notna() & b["ANO"].isin(C.ANOS_T)][P.CHAVE]
    ant = b[P.CHAVE + [col]].assign(ANO=b["ANO"] + 1).rename(columns={col: "ant"})
    sem_ant = tem.merge(ant, on=P.CHAVE, how="left")
    sem_ant = sem_ant[sem_ant["ant"].isna()].groupby("ANO").size().reindex(C.ANOS_T, fill_value=0)
    anos_ = list(C.ANOS_T)
    n = pn.groupby("ANO").size().reindex(anos_)
    com_t_t1, sem_ant = com_t_t1.reindex(anos_), sem_ant.reindex(anos_)
    check((n.to_numpy() == com_t_t1.to_numpy() - sem_ant.to_numpy()).all(),
          f"{etapa}: escolas por ano = degrau 5 do funil (etapa em t e alvo em t+1) menos as sem taxa em t−1: "
          f"{n.tolist()} = {com_t_t1.tolist()} − {sem_ant.tolist()}")

# ------------------------------------------------------------------ E
secao("E. Sem vazamento")
etapa, ano = "EM", 2017
pn = paineis[etapa]
cols = C.colunas_bloco(etapa, 3)
num = [c for c in cols if c not in C.CATEGORICAS]
ref = C.rodar_etapa(pn, etapa, "top20", anos=(ano,))[0]
pert = pn.copy()
fut = (pert["ANO_ALVO"] > ano).to_numpy()
pert.loc[fut, "y_t1"] = rng.uniform(0, 100, fut.sum())
pert.loc[fut, "alto_top20"] = rng.integers(0, 2, fut.sum())
pert.loc[fut, num] = rng.normal(0, 50, (fut.sum(), len(num)))
pert.loc[fut, "LOCALIZACAO"] = "Outra"
p2 = C.rodar_etapa(pert, etapa, "top20", anos=(ano,))[0]
maior = max(float(np.abs(ref["p"][k] - p2["p"][k]).max()) for k in ref["p"])
check(maior == 0.0, f"perturbar alvo e variáveis dos anos após {ano} não muda nenhuma das {len(ref['p'])} notas de {ano} (maior diferença {maior:.1e})")
pert2 = pn.copy()
hoje = (pert2["ANO_ALVO"] == ano).to_numpy()
pert2.loc[hoje, "y_t1"] = rng.uniform(0, 100, hoje.sum())
pert2.loc[hoje, "alto_top20"] = rng.integers(0, 2, hoje.sum())
p3 = C.rodar_etapa(pert2, etapa, "top20", anos=(ano,))[0]
maior = max(float(np.abs(ref["p"][k] - p3["p"][k]).max()) for k in ref["p"])
check(maior == 0.0, f"perturbar o alvo do próprio ano de teste ({ano}) não muda as notas (o alvo de teste não entra no ajuste)")
check(ref["n_treino"] == int((pn["ANO_ALVO"] < ano).sum()), f"treino de {ano} = só transições com alvo antes de {ano} ({ref['n_treino']} linhas)")
tr = pn[pn["ANO_ALVO"] < ano]
pipe = C.modelo("logistica", cols).fit(tr[cols], tr["alto_top20"])
passos = pipe.named_steps["pre"].named_transformers_["num"].named_steps
check(np.allclose(passos["imp"].statistics_, tr[num].median().to_numpy(), atol=TOL, rtol=0),
      "imputação: medianas iguais às do treino")
imputado = passos["imp"].transform(tr[num])
check(np.allclose(passos["pad"].mean_, imputado.mean(axis=0), atol=1e-9, rtol=0), "padronização: médias iguais às do treino imputado")
check(sorted(ref["p"]) == sorted([("B1R_lag", 0), ("B2", 0)] + [(m_, k) for m_ in C.MODELOS for k in (1, 2, 3)]),
      "cada ano tem 2 réguas e 3 modelos × 3 blocos")
s = P.SUF[etapa]
te = pn[pn["ANO_ALVO"] == ano]
check(bool((ref["p"][("B1R_lag", 0)] == te[f"ABANDONO_{s}_L1"].to_numpy()).all()), "régua B1R_lag = abandono de t−1")
check(all(((v >= 0) & (v <= 1)).all() for k, v in ref["p"].items() if k[0] in C.MODELOS), "notas dos modelos são probabilidades (0 a 1)")

# ------------------------------------------------------------------ F
secao("F. Bootstrap e leitura")
cel = []
for a in (2016, 2017):
    n = 40
    yb = (rng.random(n) < .3).astype(int)
    yb[:2] = 1
    cel.append({"etapa": "X", "ano_alvo": a, "ano": a - 1, "n_treino": 0, "co": np.array([f"e{i}" for i in range(n)]),
                "y": yb, "y_t1": yb * 10.0,
                "p": {("B1R_lag", 0): np.full(n, 1.0), ("logistica", 1): yb + rng.random(n) * .1}})
dist = E.bootstrap(cel, np.random.default_rng(1), 200)
check(all(np.abs(dist[(("B1R_lag", 0), m_)] - dist[(("acaso", 0), m_)]).max() <= 1e-12 for m_ in E.PRIMARIAS),
      "nota constante = acaso em todas as reamostragens (PR-AUC e Recall@20%)")
check(bool((dist[(("logistica", 1), "PR_AUC")] == 1).all()), "nota perfeita: PR-AUC = 1 em todas as reamostragens")
tab = E.tabela_metricas(cel, "top20")
agr = tab[(tab["modelo"] == "logistica") & (tab["periodo"] == E.PERIODO)].iloc[0]
anos_ = tab[(tab["modelo"] == "logistica") & (tab["periodo"] != E.PERIODO)]
check(perto(agr["PR_AUC"], anos_["PR_AUC"].mean()) and agr["n"] == anos_["n"].sum() and agr["VP"] == anos_["VP"].sum(),
      "linha agrupada = média simples das métricas dos anos; contagens somadas")
check(len(C.MODELOS) * C.N_BLOCOS * len(E.PRIMARIAS) * 2 == 36, "F6: 3 modelos × 3 blocos × 2 métricas × 2 etapas = 36 testes")
check(C.leitura("Rec@20pct", .15, .02, .30, .01) == "GANHO", "leitura: diferença positiva com p de Holm ≤ 0,05 = GANHO")
check(C.leitura("Rec@20pct", .02, -.05, .09, 1.0) == "SEM GANHO PRÁTICO", "leitura: limite superior abaixo de +0,10 no Recall@20% = SEM GANHO PRÁTICO")
check(C.leitura("Rec@20pct", .05, -.05, .15, 1.0) == "INCONCLUSIVO", "leitura: nenhum dos dois = INCONCLUSIVO")
check(C.leitura("PR_AUC", .02, -.05, .09, 1.0) == "INCONCLUSIVO", "leitura: a margem de +0,10 não se aplica à PR-AUC")
check(C.leitura("Rec@20pct", -.15, -.30, -.02, .01) != "GANHO", "leitura: diferença negativa nunca é GANHO")

log.extend(["", f"RESUMO: {cont['ok']} OK, {cont['fail']} falhas"])
txt = "\n".join(log).lstrip("\n")
print(txt)
REPORT.write_text(txt, encoding="utf-8")
sys.exit(1 if cont["fail"] else 0)
