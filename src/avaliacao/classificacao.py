# -*- coding: utf-8 -*-
"""
Ferramenta de classificação de alto risco na janela 2013–2018 — funções.

Protocolo: abandono-escolar/docs/DECISOES.md, entrada de 2026-11-10
("Protocolo da ferramenta de classificação de alto risco"), registrada antes
deste código. Resumo:

  janela    transições com t de 2013 a 2018 (alvo de 2014 a 2019); as duas
            primeiras só treinam; teste = alvos de 2016 a 2019
  universo  escolas públicas com taxa da etapa em t−1, t e t+1
  alvo      ALTO_RISCO = abandono de t+1 entre os 20% maiores da etapa no ano
            e maior que zero (sensibilidade: abandono ≥ 10)
  variáveis Cenário B. bloco 1 = abandono e reprovação de t−1 + variação
            defasada; bloco 2 = + localização e dependência (one-hot);
            bloco 3 = + 4 dimensões zano e IIE (painel.INFRA)
  modelos   regressão logística, Random Forest, HistGradientBoosting, com
            hiperparâmetros fixos; imputação, padronização e one-hot dentro
            do Pipeline, ajustados só no treino
  réguas    B1R_lag (abandono de t−1), B2 (mediana do treino por
            localização × dependência), acaso

Métricas sobre o rótulo: PR-AUC (precisão média), ROC-AUC, Recall@K e
Precision@K (empate de nota na fronteira: valor esperado, metricas.prob_topk),
precisão, recall e F1 no limiar 0,5 da probabilidade.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import baselines as B
import metricas as M
import painel as P

ANOS_T = tuple(range(2013, 2019))          # ANO (t) das transições da janela
ANOS_TESTE = (2016, 2017, 2018, 2019)      # ANO_ALVO das transições de teste
FRACAO_ALTO = 0.20
LIMIAR_ABS = 10.0                          # sensibilidade: abandono ≥ 10
ALVOS = ("top20", "abs10")
CATEGORICAS = ["LOCALIZACAO", "DEPENDENCIA"]
MODELOS = ("logistica", "floresta", "hgb")
NOME_MODELO = {"logistica": "Regressão logística", "floresta": "Random Forest",
               "hgb": "HistGradientBoosting", "B1R_lag": "B1R_lag", "B2": "B2"}
REGUAS = ("B1R_lag", "B2")
N_BLOCOS = 3
KS_ESCOLAS = (20, 30, 50)


# ------------------------------------------------------------------ painel
def rotular(y, fracao=FRACAO_ALTO):
    """1 se y está entre os round(fracao·n) maiores do vetor (empates no limiar entram) e y > 0."""
    y = np.asarray(y, dtype="float64")
    k = M.k_de_fracao(len(y), fracao)
    limiar = np.sort(y)[::-1][k - 1]
    return ((y >= limiar) & (y > 0)).astype(int)


def montar(etapa, atual=None):
    """Painel da janela: uma linha por escola-ano (t), com as variáveis dos 3 blocos e os rótulos."""
    atual = pd.read_parquet(P.P_ATUAL) if atual is None else atual
    s = P.SUF[etapa]
    u = B.universo(atual, etapa)
    u = u[u["ANO"].isin(ANOS_T)].copy()
    rend = atual[P.CHAVE + [f"ABANDONO_{s}", f"REPROVACAO_{s}"]]
    for lag, tag in ((1, "L1"), (2, "L2")):
        r = rend.copy()
        r["ANO"] = r["ANO"] + lag
        r = r.rename(columns={f"ABANDONO_{s}": f"ABANDONO_{s}_{tag}", f"REPROVACAO_{s}": f"REPROVACAO_{s}_{tag}"})
        u = u.merge(r, on=P.CHAVE, how="left", validate="1:1")
    for c in [c for c in u.columns if c.startswith(("ABANDONO_", "REPROVACAO_"))]:
        u[c] = P._f(u[c])
    u[f"ABANDONO_{s}_DLAG"] = u[f"ABANDONO_{s}_L1"] - u[f"ABANDONO_{s}_L2"]
    u = u.merge(atual[P.CHAVE + P.INFRA], on=P.CHAVE, how="left", validate="1:1")
    for c in P.INFRA:
        u[c] = P._f(u[c])
    for c in CATEGORICAS:
        u[c] = u[c].astype(object)
    # universo: taxa da etapa em t−1, t e t+1 (t+1 já vem de baselines.universo)
    u = u[u["y_t"].notna() & u[f"ABANDONO_{s}_L1"].notna()].reset_index(drop=True)
    u["alto_top20"] = u.groupby("ANO_ALVO")["y_t1"].transform(lambda v: rotular(v.to_numpy()))
    u["alto_abs10"] = (u["y_t1"] >= LIMIAR_ABS).astype(int)
    return u


def blocos(etapa):
    s = P.SUF[etapa]
    return {"rendimento": [f"ABANDONO_{s}_L1", f"REPROVACAO_{s}_L1", f"ABANDONO_{s}_DLAG"],
            "territorio_rede": list(CATEGORICAS),
            "infraestrutura": list(P.INFRA)}


ORDEM_BLOCOS = ["rendimento", "territorio_rede", "infraestrutura"]


def colunas_bloco(etapa, k):
    b = blocos(etapa)
    return [c for nome in ORDEM_BLOCOS[:k] for c in b[nome]]


# ------------------------------------------------------------------ modelos
def modelo(nome, colunas):
    num = [c for c in colunas if c not in CATEGORICAS]
    cat = [c for c in colunas if c in CATEGORICAS]
    partes = [("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                                ("pad", StandardScaler())]), num)]
    if cat:
        partes.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat))
    pre = ColumnTransformer(partes, remainder="drop")
    if nome == "logistica":
        est = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000)
    elif nome == "floresta":
        est = RandomForestClassifier(n_estimators=500, min_samples_leaf=20,
                                     class_weight="balanced_subsample", random_state=1)
    elif nome == "hgb":
        est = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200,
                                             class_weight="balanced", random_state=1)
    else:
        raise ValueError(nome)
    return Pipeline([("pre", pre), ("m", est)])


def rodar_etapa(painel, etapa, alvo="top20", anos=ANOS_TESTE):
    """Walk-forward. Devolve uma célula por ano de teste:
    {"etapa", "ano_alvo", "ano", "co", "y" (rótulo), "y_t1" (taxa), "n_treino",
     "p": {(modelo, bloco): nota}}  — réguas com bloco 0; modelos com probabilidade."""
    s = P.SUF[etapa]
    col_alvo = f"alto_{alvo}"
    celulas = []
    for ano in anos:
        tr = painel[painel["ANO_ALVO"] < ano]
        te = painel[painel["ANO_ALVO"] == ano]
        p = {("B1R_lag", 0): te[f"ABANDONO_{s}_L1"].to_numpy(),
             ("B2", 0): B.b2_mediana_estrato(tr, te)}
        for k in range(1, N_BLOCOS + 1):
            cols = colunas_bloco(etapa, k)
            for nome in MODELOS:
                pipe = modelo(nome, cols).fit(tr[cols], tr[col_alvo].to_numpy())
                p[(nome, k)] = pipe.predict_proba(te[cols])[:, 1]
        celulas.append({"etapa": etapa, "ano_alvo": ano, "ano": ano - 1, "n_treino": len(tr),
                        "co": te["CO_ENTIDADE"].astype(str).to_numpy(),
                        "y": te[col_alvo].to_numpy(), "y_t1": te["y_t1"].to_numpy(), "p": p})
    return celulas


# ------------------------------------------------------------------ métricas
def pr_auc(rot, nota):
    """Precisão média (PR-AUC do scikit-learn)."""
    return float(average_precision_score(rot, nota))


def pr_auc_rapida(rot, nota):
    """A mesma precisão média, em numpy (para o bootstrap). Empates de nota formam um só ponto da curva."""
    o = np.argsort(-nota, kind="stable")
    r, sn = rot[o], nota[o]
    tp = np.cumsum(r)
    fim = np.r_[sn[1:] != sn[:-1], True]            # última posição de cada grupo empatado
    tpf = tp[fim]
    prec = tpf / (np.flatnonzero(fim) + 1)
    rec = tpf / tp[-1]
    return float(np.sum(np.diff(np.r_[0.0, rec]) * prec))


def roc_auc(rot, nota):
    return float(roc_auc_score(rot, nota))


def acertos_topk(rot, nota, k):
    """Número esperado de escolas de alto risco entre as k primeiras (desempate aleatório na fronteira)."""
    return float(np.sum(M.prob_topk(nota, k) * rot))


def recall_k(rot, nota, k):
    return acertos_topk(rot, nota, k) / float(np.sum(rot))


def precisao_k(rot, nota, k):
    return acertos_topk(rot, nota, k) / k


def confusao(rot, prob, limiar=0.5):
    """VP, FP, FN, VN classificando como alto risco quem tem probabilidade ≥ limiar."""
    prev = prob >= limiar
    vp = int(np.sum(prev & (rot == 1)))
    fp = int(np.sum(prev & (rot == 0)))
    fn = int(np.sum(~prev & (rot == 1)))
    vn = int(np.sum(~prev & (rot == 0)))
    return vp, fp, fn, vn


def prf(vp, fp, fn):
    """Precisão, recall e F1; indefinido (NaN) quando o denominador é zero."""
    prec = vp / (vp + fp) if vp + fp else float("nan")
    rec = vp / (vp + fn) if vp + fn else float("nan")
    f1 = 2 * vp / (2 * vp + fp + fn) if 2 * vp + fp + fn else float("nan")
    return prec, rec, f1


def metricas_ano(rot, nota, e_probabilidade):
    """Todas as métricas de um ano para uma nota (probabilidade de modelo ou nota de régua)."""
    n, pos = len(rot), int(np.sum(rot))
    k20 = M.k_de_fracao(n, FRACAO_ALTO)
    out = {"n": n, "n_alto": pos, "prevalencia": pos / n, "K20pct": k20,
           "PR_AUC": pr_auc(rot, nota), "ROC_AUC": roc_auc(rot, nota),
           "Rec@20pct": recall_k(rot, nota, k20), "Prec@20pct": precisao_k(rot, nota, k20)}
    for k in KS_ESCOLAS:                       # lista maior que o ano = o ano inteiro
        out[f"Rec@{k}"] = recall_k(rot, nota, min(k, n))
        out[f"Prec@{k}"] = precisao_k(rot, nota, min(k, n))
    if e_probabilidade:
        vp, fp, fn, vn = confusao(rot, nota)
        prec, rec, f1 = prf(vp, fp, fn)
        out.update({"VP": vp, "FP": fp, "FN": fn, "VN": vn,
                    "precisao_05": prec, "recall_05": rec, "F1_05": f1})
    return out


def leitura(metrica, dif, lo, hi, p_holm, alfa=0.05, margem=0.10):
    """Leitura de uma comparação da F6 (item 10 do protocolo)."""
    if dif > 0 and p_holm <= alfa:
        return "GANHO"
    if metrica == "Rec@20pct" and hi < margem:
        return "SEM GANHO PRÁTICO"
    return "INCONCLUSIVO"
