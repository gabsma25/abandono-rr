# -*- coding: utf-8 -*-
"""
Baselines do protocolo de avaliação (Etapa 1) — funções puras.

  B0   média       ŷ = média do alvo no TREINO (todas as transições anteriores
                   ao ano avaliado, janela expansiva), por etapa
  B1   persistência ŷ_{i,t+1} = y_{i,t}  (abandono da própria escola em t)
  B1R  ranking     ordena as escolas pelo abandono em t; só Recall@K
                   (não estima valor — é o baseline do uso real: priorizar)

Universo de cada etapa (pré-especificado): REDE_PUBLICA == 1 e escola que
oferece a etapa no ano avaliado (alvo `_T1` não nulo). Escola sem a etapa em
t (sem y_t) continua no universo: o B1 cai no B0 do treino para ela, e a
contagem sai em `n_sem_t`. Assim os três baselines são avaliados exatamente
nas mesmas escolas.

Nenhum parâmetro é ajustado com o ano avaliado: o B0 só vê ANO_ALVO < ano.
"""
import numpy as np
import pandas as pd

import metricas as M

ETAPAS = {"AF": "ABANDONO_FUN_AF", "EM": "ABANDONO_MED"}
FRACOES_K = (0.10, 0.20)


def universo(base, etapa):
    col = ETAPAS[etapa]
    pub = base["REDE_PUBLICA"].astype("Int8") == 1
    tem_alvo = base[f"{col}_T1"].notna()
    u = base.loc[pub & tem_alvo, ["ANO", "ANO_ALVO", "CO_ENTIDADE", "LOCALIZACAO",
                                   "DEPENDENCIA", col, f"{col}_T1"]]
    u = u.rename(columns={col: "y_t", f"{col}_T1": "y_t1"})
    u["y_t"] = u["y_t"].astype("Float64").astype("float64")    # NA -> NaN
    u["y_t1"] = u["y_t1"].astype("Float64").astype("float64")
    return u.reset_index(drop=True)


def b0_media(treino):
    return float(treino["y_t1"].mean())


def b1_persistencia(teste, fallback, col="y_t"):
    return teste[col].fillna(fallback).to_numpy()


def b2_mediana_estrato(treino, teste, estrato=("LOCALIZACAO", "DEPENDENCIA")):
    """B2: mediana do alvo no treino por localização × dependência.

    Célula sem escola no treino recebe a mediana geral do treino.
    """
    estrato = list(estrato)
    med = treino.groupby(estrato, observed=True)["y_t1"].median().rename("b2")
    p = teste[estrato].merge(med, left_on=estrato, right_index=True, how="left")["b2"]
    return p.fillna(float(treino["y_t1"].median())).to_numpy()


def avaliar_ano(u, ano_alvo):
    """Métricas dos três baselines numa transição (ano_alvo-1 -> ano_alvo)."""
    treino = u[u["ANO_ALVO"] < ano_alvo]
    teste = u[u["ANO_ALVO"] == ano_alvo]
    if treino.empty or teste.empty:
        return None
    y = teste["y_t1"].to_numpy()
    n = len(y)
    mu = b0_media(treino)
    p_b0 = np.full(n, mu)
    p_b1 = b1_persistencia(teste, mu)
    pares = teste["y_t"].notna().to_numpy()

    lin = {"ano_alvo": ano_alvo, "n": n, "n_sem_t": int((~pares).sum()),
           "anos_treino": f"{int(treino['ANO_ALVO'].min())}-{int(treino['ANO_ALVO'].max())}",
           "media_treino": mu, "media_real": float(y.mean()),
           "pct_zero_real": float((y == 0).mean() * 100)}
    for nome, p in (("B0", p_b0), ("B1", p_b1)):
        lin[f"{nome}_MAE"] = M.mae(y, p)
        lin[f"{nome}_RMSE"] = M.rmse(y, p)
        lin[f"{nome}_R2"] = M.r2(y, p)
    for f in FRACOES_K:
        k = M.k_de_fracao(n, f)
        tag = f"{int(f * 100)}"
        lin[f"K{tag}"] = k
        lin[f"B0_Rec@{tag}"] = M.recall_at_k(y, p_b0, k)      # = aleatório
        lin[f"B1R_Rec@{tag}"] = M.recall_at_k(y, p_b1, k)
    # conferência com docs/desfechos_persistencia.csv (só pares completos)
    lin["B1_MAE_pares"] = M.mae(y[pares], teste["y_t"].to_numpy()[pares]) if pares.any() else np.nan
    return lin


def avaliar(base, etapa):
    u = universo(base, etapa)
    anos = sorted(u["ANO_ALVO"].unique())
    linhas = [avaliar_ano(u, a) for a in anos]
    df = pd.DataFrame([l for l in linhas if l is not None])
    df.insert(0, "etapa", etapa)
    return df
