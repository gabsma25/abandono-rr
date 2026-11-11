# -*- coding: utf-8 -*-
"""
Métricas do protocolo de avaliação (funções puras, só numpy).

Regressão: MAE, RMSE, R² (R² = 1 - SSE/SST, SST em torno da média do
próprio conjunto avaliado; pode ser negativo).

Ordenação: Recall@K conforme docs/metodologia_variaveis.md §7.7 do projeto
oficial:  Recall@K = |TopK(ŷ) ∩ TopK(y)| / K.  Os dois conjuntos têm K
elementos, então Precision@K = Recall@K por construção.

Empates. O alvo tem muitos zeros e a persistência repete valores, então o
K-ésimo lugar costuma cair num grupo empatado. Em vez de desempatar por uma
ordem arbitrária (que mudaria o resultado), usa-se o VALOR ESPERADO sob
desempate aleatório uniforme e independente nos dois lados:

    E|TopK(ŷ) ∩ TopK(y)| = Σ_i  P(i ∈ TopK(ŷ)) · P(i ∈ TopK(y))

com P = 1 acima do grupo de fronteira, P = vagas/tamanho dentro dele e
P = 0 abaixo. Consequência útil: uma previsão constante (B0) recebe
exatamente K/n, que é o Recall@K de uma escolha aleatória.
"""
import math

import numpy as np


def _arr(x):
    return np.asarray(x, dtype="float64")


def mae(y, yhat):
    y, yhat = _arr(y), _arr(yhat)
    return float(np.mean(np.abs(y - yhat)))


def rmse(y, yhat):
    y, yhat = _arr(y), _arr(yhat)
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def r2(y, yhat):
    y, yhat = _arr(y), _arr(yhat)
    sst = float(np.sum((y - y.mean()) ** 2))
    if sst == 0:
        return float("nan")
    return 1.0 - float(np.sum((y - yhat) ** 2)) / sst


def k_de_fracao(n, fracao):
    """K = round(fracao · n), no mínimo 1 (arredondamento half-up)."""
    return max(1, int(math.floor(fracao * n + 0.5)))


def prob_topk(v, k):
    """P(i ∈ TopK(v)) sob desempate aleatório uniforme (maiores primeiro)."""
    v = _arr(v)
    n = len(v)
    if not 1 <= k <= n:
        raise ValueError(f"k={k} fora de [1, {n}]")
    limiar = np.sort(v)[::-1][k - 1]          # valor do K-ésimo colocado
    acima = v > limiar
    empatados = v == limiar
    vagas = k - int(acima.sum())
    p = acima.astype("float64")
    p[empatados] = vagas / int(empatados.sum())
    return p


def recall_at_k(y, yhat, k):
    """E|TopK(ŷ) ∩ TopK(y)| / K  (= Precision@K)."""
    y, yhat = _arr(y), _arr(yhat)
    if np.isnan(y).any() or np.isnan(yhat).any():
        raise ValueError("recall_at_k não aceita NaN")
    return float(np.sum(prob_topk(yhat, k) * prob_topk(y, k)) / k)
