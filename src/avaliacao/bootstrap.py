# -*- coding: utf-8 -*-
"""
Bootstrap de escolas (metodologia §7.7) — funções puras.

Em cada ano de teste cada escola aparece uma vez, então reamostrar linhas do
ano = reamostrar escolas. As mesmas reamostragens (mesmos índices) são usadas
para todos os modelos e baselines do ano: as diferenças são PAREADAS.
K é fixado pelo n do ano (K = round(f·n)), igual ao da estimativa pontual.

Intervalo: percentil 2,5–97,5 de N_BOOT reamostragens.
Classe de uma diferença (modelo − referência):
  "vence" se o intervalo inteiro > 0; "perde" se inteiro < 0; senão "indeterminado".
"""
import numpy as np

import metricas as M

N_BOOT = 1000
SEMENTE_BOOT = 20261103
FRACOES = {"Rec@10": .10, "Rec@20": .20}


def indices(n, rng, n_boot=N_BOOT):
    return rng.integers(0, n, size=(n_boot, n))


def distribuicao(y, p, idx, fracao):
    k = M.k_de_fracao(len(y), fracao)
    return np.array([M.recall_at_k(y[i], p[i], k) for i in idx])


def intervalo(v):
    lo, hi = np.percentile(v, [2.5, 97.5])
    return float(lo), float(hi)


def classe(lo, hi):
    if lo > 0:
        return "vence"
    if hi < 0:
        return "perde"
    return "indeterminado"


def distribuicoes_ano(cel, rng):
    """{(id, métrica): distribuição} para um ano (cel vem de walkforward.prev)."""
    y = cel["y"]
    idx = indices(len(y), rng)
    return {(pid, met): distribuicao(y, p, idx, f)
            for pid, p in cel["p"].items() for met, f in FRACOES.items()}


# ------------------------------------------------------------------
# Bootstrap agrupado por escola, com pooling dos anos de teste
# ------------------------------------------------------------------
# Junta as transições de teste e sorteia ESCOLAS (CO_ENTIDADE) com reposição,
# mantendo todos os anos de teste de cada escola sorteada (cluster bootstrap).
# O Recall@K continua calculado dentro de cada ano (o ranking é anual) e o
# valor agrupado é a MÉDIA SIMPLES das transições. O mesmo sorteio dá também
# o intervalo de cada ano (a parte do sorteio que cai naquele ano), pareado
# com o agrupado.
FRACOES_3K = {"Rec@10": .10, "Rec@20": .20, "Rec@30": .30}


class Agrupado:
    def __init__(self, celulas):
        self.anos = [c["ano_alvo"] for c in celulas]
        self.y = np.concatenate([c["y"] for c in celulas])
        self.ano = np.concatenate([np.full(len(c["y"]), c["ano_alvo"]) for c in celulas])
        co = np.concatenate([c["co"] for c in celulas])
        self.escolas, self.esc_idx = np.unique(co, return_inverse=True)
        self.linhas_por_escola = [np.flatnonzero(self.esc_idx == e) for e in range(len(self.escolas))]

    def sorteios(self, rng, n_boot=N_BOOT):
        """Lista de vetores de índices de linhas (com repetição), um por reamostragem."""
        ne = len(self.escolas)
        out = []
        for _ in range(n_boot):
            esc = rng.integers(0, ne, ne)
            out.append(np.concatenate([self.linhas_por_escola[e] for e in esc]))
        return out

    def por_ano(self, idx):
        a = self.ano[idx]
        return {ano: idx[a == ano] for ano in self.anos}


def recall_ano(y, p, sel, fracao):
    return M.recall_at_k(y[sel], p[sel], M.k_de_fracao(len(sel), fracao))


# ------------------------------------------------------------------
# Testes múltiplos (regra de 2026-11-02): p-valor bootstrap + Holm por família
# ------------------------------------------------------------------
def p_bootstrap(d):
    """p bilateral da hipótese 'diferença = 0' pela distribuição bootstrap d.

    p = min(1, 2·min(#(d ≤ 0) + 1, #(d ≥ 0) + 1) / (B + 1)). Com B reamostragens
    o menor p possível é 2/(B+1): B precisa ser grande o bastante para a
    família (Holm exige p ≤ α/m no primeiro passo).
    """
    d = np.asarray(d)
    b = len(d)
    return min(1.0, 2 * min((d <= 0).sum() + 1, (d >= 0).sum() + 1) / (b + 1))


def holm(pvals):
    """p-valores ajustados por Holm (step-down), na ordem de entrada."""
    p = np.asarray(pvals, dtype="float64")
    m = len(p)
    ordem = np.argsort(p)
    ajust = np.empty(m)
    corrente = 0.0
    for pos, i in enumerate(ordem):
        corrente = max(corrente, min(1.0, (m - pos) * p[i]))
        ajust[i] = corrente
    return ajust
