# -*- coding: utf-8 -*-
"""
01 — Etapa 1 do protocolo de avaliação: baselines B0, B1 e B1R.

Entrada: gustavo/saida/base_atual.parquet
Saída:   gustavo/saida/avaliacao/01_baselines.csv  (uma linha por etapa × ano)
         gustavo/saida/avaliacao/01_baselines.md   (tabelas Markdown)
Uso:     python avaliacao/01_baselines.py

Reporta por ano e por etapa, nunca só o agregado. Definições em baselines.py
e metricas.py.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baselines as B  # noqa: E402

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
P_BASE = GUSTAVO / "saida" / "base_atual.parquet"
SAIDA = GUSTAVO / "saida" / "avaliacao"


COLS = ["ano_alvo", "n", "n_sem_t", "media_treino", "media_real", "pct_zero_real",
        "B0_MAE", "B1_MAE", "B0_RMSE", "B1_RMSE", "B0_R2", "B1_R2",
        "K10", "B0_Rec@10", "B1R_Rec@10", "K20", "B0_Rec@20", "B1R_Rec@20"]


def tabela_md(df, cols=COLS):
    """Tabela Markdown (pipes), legível em qualquer visualizador."""
    def fmt(c, v):
        if isinstance(v, float):
            return f"{v:.0f}" if c == "pct_zero_real" else f"{v:.2f}"
        return str(v)
    linhas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df[cols].iterrows():
        linhas.append("| " + " | ".join(fmt(c, r[c]) for c in cols) + " |")
    return "\n".join(linhas)


def main():
    base = pd.read_parquet(P_BASE)
    SAIDA.mkdir(parents=True, exist_ok=True)
    res = pd.concat([B.avaliar(base, e) for e in B.ETAPAS], ignore_index=True)
    # Diferenças contra o B0, prontas para as figuras (o notebook não calcula).
    # Sinal: Recall, B1R − B0 (> 0 = acima do aleatório); MAE, B1 − B0 (< 0 = B1 erra menos).
    for k in ("10", "20"):
        res[f"B1R-B0_Rec@{k}"] = res[f"B1R_Rec@{k}"] - res[f"B0_Rec@{k}"]
    res["B1-B0_MAE"] = res["B1_MAE"] - res["B0_MAE"]
    res.to_csv(SAIDA / "01_baselines.csv", index=False, encoding="utf-8")

    txt = ["# Etapa 1 — Baselines", "",
           "Base: `base_atual.parquet`. Universo: pública + oferece a etapa em t+1.",
           "B0 = média do treino (janela expansiva) · B1 = persistência · B1R = ranking por y_t.",
           "Recall@K = Precision@K (|TopK(ŷ)∩TopK(y)|/K, empates por valor esperado); B0_Rec = aleatório.", ""]
    for e in B.ETAPAS:
        txt += [f"## {e}", "", tabela_md(res[res["etapa"] == e]), ""]
    s = "\n".join(txt)
    print(s)
    (SAIDA / "01_baselines.md").write_text(s, encoding="utf-8")
    (SAIDA / "01_baselines.txt").unlink(missing_ok=True)   # substituído pelo .md
    print(f">>> {SAIDA / '01_baselines.csv'}")


if __name__ == "__main__":
    main()
