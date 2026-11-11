# -*- coding: utf-8 -*-
"""
Monta, EM MEMÓRIA, o painel de avaliação da Etapa 2 (nada é gravado na base).

Espinha: universo da Etapa 1 (base_atual: pública + oferece a etapa em t+1),
restrito a ANO 2019–2024 (o TDI/ATU/IED só existe a partir de 2019).
Fontes, todas por (ANO, CO_ENTIDADE), merge LEFT com validate="1:1":
  - base_atual.parquet .......... rendimento de t, t−1, t−2 (série 2007–2025)
                                   e infraestrutura (DIM_*_zano, IIE_zano)
  - base oficial 2019–2025 ...... TDI, ATU, IED

Regras pré-especificadas (DECISOES.md, 2026-11-02):
  * Nunca as três taxas de rendimento da mesma etapa: usa ABANDONO + REPROVACAO
    (APROVACAO = 100 − as outras duas; P026).
  * IED: N1..N5 (N6 = 100 − Σ N1..N5; ALTO = N4+N5+N6 — ambos redundantes).
  * Cenário B (principal): nada de rendimento de t. A variação é a DEFASADA,
    ABANDONO(t−1) − ABANDONO(t−2); o DELTA1 da base (t − (t−1)) somado ao
    lag reconstruiria ABANDONO(t).
  * Cenário A (teto otimista): rendimento de t e DELTA1 = ABANDONO(t) − ABANDONO(t−1).
  * Cada etapa só vê as variáveis da sua etapa (D15).
"""
from pathlib import Path

import pandas as pd

import baselines as B

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
P_ATUAL = GUSTAVO / "saida" / "base_atual.parquet"
P_OFICIAL = (GUSTAVO.parent / "abandono-escolar" / "dados" / "processado"
             / "base_longitudinal_rr_2019_2025.parquet")
ANOS_FEATURES = range(2019, 2025)          # ANO (t); ANO_ALVO 2020–2025
CHAVE = ["ANO", "CO_ENTIDADE"]

SUF = {"AF": "FUN_AF", "EM": "MED"}                 # rendimento
SUF_TDI_ATU = {"AF": "FUN_AF", "EM": "MED_TOTAL"}   # TDI / ATU
SUF_IED = {"AF": "FUN", "EM": "MED"}                # IED só existe FUN e MED
INFRA = ["DIM_IIB_zano", "DIM_IDA_zano", "DIM_IDP_zano", "DIM_IEP_zano", "IIE_zano"]
CENARIOS = ("B", "A")


def blocos(etapa, cenario):
    """Colunas de cada bloco conceitual (para modelos e permutação)."""
    s, st, si = SUF[etapa], SUF_TDI_ATU[etapa], SUF_IED[etapa]
    if cenario == "B":
        rend = [f"ABANDONO_{s}_L1", f"REPROVACAO_{s}_L1", f"ABANDONO_{s}_DLAG"]
    else:
        rend = [f"ABANDONO_{s}_T0", f"REPROVACAO_{s}_T0", f"ABANDONO_{s}_D1"]
    return {
        "rendimento": rend,
        "TDI_ATU": [f"TDI_{st}", f"ATU_{st}"],
        "IED": [f"IED_{si}_N{i}" for i in range(1, 6)],
        "infraestrutura": INFRA,
    }


# Blocos cumulativos pré-especificados: 1 = rend; 2 = +TDI/ATU; 3 = +IED; 4 = +infra
ORDEM_BLOCOS = ["rendimento", "TDI_ATU", "IED", "infraestrutura"]

# Grupos de PERMUTAÇÃO com TDI e ATU separados (2026-11-02). Só a medida de
# importância muda: o modelo continua o do bloco 4, com as mesmas colunas.
GRUPOS_IMPORTANCIA = ["rendimento", "TDI", "ATU", "IED", "infraestrutura"]


def blocos_importancia(etapa, cenario):
    b = blocos(etapa, cenario)
    tdi, atu = b["TDI_ATU"]
    return {"rendimento": b["rendimento"], "TDI": [tdi], "ATU": [atu],
            "IED": b["IED"], "infraestrutura": b["infraestrutura"]}


def colunas_bloco(etapa, cenario, k):
    b = blocos(etapa, cenario)
    return [c for nome in ORDEM_BLOCOS[:k] for c in b[nome]]


def _f(s):
    return s.astype("Float64").astype("float64")


def montar(etapa, atual=None, oficial=None):
    """Painel com as colunas dos dois cenários (o cenário escolhe as colunas)."""
    atual = pd.read_parquet(P_ATUAL) if atual is None else atual
    oficial = pd.read_parquet(P_OFICIAL) if oficial is None else oficial
    s, st, si = SUF[etapa], SUF_TDI_ATU[etapa], SUF_IED[etapa]

    u = B.universo(atual, etapa)
    u = u[u["ANO"].isin(ANOS_FEATURES)].copy()

    # rendimento de t, t−1, t−2 (a série longa da base_atual dá t−2 de 2019 = 2017)
    rend = atual[CHAVE + [f"ABANDONO_{s}", f"REPROVACAO_{s}"]].copy()
    for lag, tag in ((0, "T0"), (1, "L1"), (2, "L2")):
        r = rend.copy()
        r["ANO"] = r["ANO"] + lag
        r = r.rename(columns={f"ABANDONO_{s}": f"ABANDONO_{s}_{tag}",
                              f"REPROVACAO_{s}": f"REPROVACAO_{s}_{tag}"})
        u = u.merge(r, on=CHAVE, how="left", validate="1:1")
    for c in [c for c in u.columns if c.startswith(("ABANDONO_", "REPROVACAO_"))]:
        u[c] = _f(u[c])
    u[f"ABANDONO_{s}_DLAG"] = u[f"ABANDONO_{s}_L1"] - u[f"ABANDONO_{s}_L2"]
    u[f"ABANDONO_{s}_D1"] = u[f"ABANDONO_{s}_T0"] - u[f"ABANDONO_{s}_L1"]

    of = oficial[CHAVE + [f"TDI_{st}", f"ATU_{st}"] + [f"IED_{si}_N{i}" for i in range(1, 6)]]
    u = u.merge(of, on=CHAVE, how="left", validate="1:1")
    u = u.merge(atual[CHAVE + INFRA], on=CHAVE, how="left", validate="1:1")
    for c in of.columns.drop(CHAVE).tolist() + INFRA:
        u[c] = _f(u[c])
    return u.reset_index(drop=True)
