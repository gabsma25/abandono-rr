# -*- coding: utf-8 -*-
"""
04 — Junta o LONGITUDINAL (02b) com as FEATURES do CENSO (03).

Entrada:  gustavo/saida/etapas/02b_tx_rend_longitudinal.parquet  (30 col)
          gustavo/saida/etapas/03_censo_features.parquet         (21 col: 18 variáveis
                                                                  + INFRA_FONTE_ARTIGO + chaves)
Saída:    gustavo/saida/etapas/04_base_com_censo.parquet         (12.597 × 49)
Relatório: gustavo/saida/relatorios/merge_features.txt

O base_atual.parquet NÃO é mais escrito aqui: a última etapa do pipeline (05,
índices de infraestrutura) é quem o atualiza.

Merge: LEFT a partir do longitudinal (todas as escolas com tx_rend mantidas,
NaN onde o Censo não cobriu). Chave: (ANO, CO_ENTIDADE).

Uso:  python programas/04_merge_features.py
"""
import sys
from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------
# Descoberta das pastas
# ------------------------------------------------------------------


RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
BASE_PROJETO = RAIZ  # antes: a pasta abandono-escolar; os dados agora ficam em RAIZ/dados

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
SAIDA_ETAPAS = GUSTAVO / "saida" / "etapas"
SAIDA_REL = GUSTAVO / "saida" / "relatorios"

IN_LONG = SAIDA_ETAPAS / "02b_tx_rend_longitudinal.parquet"
IN_CENSO = SAIDA_ETAPAS / "03_censo_features.parquet"
OUT = SAIDA_ETAPAS / "04_base_com_censo.parquet"
OUT_REL = SAIDA_REL / "merge_features.txt"

CHAVE = ["ANO", "CO_ENTIDADE"]


def main():
    print("=" * 78)
    print("04 — MERGE longitudinal + censo")
    print(f"BASE_PROJETO: {BASE_PROJETO}")
    print("=" * 78)

    if not IN_LONG.exists():
        print(f"[ERRO] não achei {IN_LONG} — rode 02 antes")
        sys.exit(1)
    if not IN_CENSO.exists():
        print(f"[ERRO] não achei {IN_CENSO} — rode 03 antes")
        sys.exit(1)

    lon = pd.read_parquet(IN_LONG)
    censo = pd.read_parquet(IN_CENSO)
    print(f"\nlongitudinal: {lon.shape[0]} × {lon.shape[1]}")
    print(f"censo:        {censo.shape[0]} × {censo.shape[1]}")

    # Normaliza chaves para string
    for df in (lon, censo):
        df["CO_ENTIDADE"] = df["CO_ENTIDADE"].astype(str).str.strip().astype("string")

    # Merge
    antes = len(lon)
    base = lon.merge(censo, on=CHAVE, how="left", validate="1:1")
    print(f"\nMerge: {antes} → {len(base)} linhas (LEFT, sem perda)")
    print(f"Base:  {base.shape[0]} × {base.shape[1]} colunas")

    # Cobertura das features do Censo
    vars_mussato = [c for c in base.columns
                    if c.startswith(("IIB_", "IDA_", "IDP_", "IEP_"))]
    assert len(vars_mussato) == 18, f"esperava 18 variáveis, achei {len(vars_mussato)}"
    print(f"\nCobertura das {len(vars_mussato)} features do Censo:")
    linhas = [
        "MERGE — 02b + 03",
        "=" * 60,
        f"longitudinal: {lon.shape[0]} × {lon.shape[1]}",
        f"censo:        {censo.shape[0]} × {censo.shape[1]}",
        f"base final:   {base.shape[0]} × {base.shape[1]}",
        "",
        f"Cobertura das {len(vars_mussato)} features do Censo (por ano):",
        f"{'ano':>5}{'n':>7}{'cobertura_media':>20}",
    ]
    for ano in sorted(base["ANO"].unique()):
        sub = base[base["ANO"] == ano]
        cob = round(sub[vars_mussato].notna().mean().mean() * 100, 1)
        print(f"  {ano}: n={len(sub)}, cobertura={cob}%")
        linhas.append(f"{ano:>5}{len(sub):>7}{cob:>20}")

    # Salva
    base.to_parquet(OUT, index=False)
    print(f"\n>>> {OUT}")

    OUT_REL.write_text("\n".join(linhas), encoding="utf-8")
    print(f">>> Relatório: {OUT_REL}")


if __name__ == "__main__":
    main()