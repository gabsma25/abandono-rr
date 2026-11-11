# -*- coding: utf-8 -*-
"""
ANÁLISE 05 — Descritivos por ano para os notebooks (o notebook só exibe).

  A. desfecho_por_ano.csv [FATO] — distribuição do abandono por ano e etapa,
     2007–2025. Universo: públicas com taxa da etapa no ano (o mesmo do
     abandono-escolar/docs/desfechos_distribuicao.csv, que cobre só
     2019–2025). Mesmas estatísticas, sem arredondar: n, média, mediana,
     p75, p90, máx, % de zeros. Descreve o desfecho em si, inclusive 2025;
     nenhum modelo está envolvido.

  B. cobertura_painel.csv [FATO] — % das escolas-ano do painel da Etapa 2
     (painel.montar: universo da avaliação, ANO 2019–2024) com cada grupo de
     preditores não nulo, por ano e etapa. Um grupo de várias colunas conta
     só quando todas são não nulas. O HAD não entra no painel (P019) e fica
     com n_com vazio. Não usa o desfecho.

Saída: gustavo/saida/relatorios/desfecho_por_ano.csv
         (ano, etapa, n, media, mediana, p75, p90, max, pct_zero)
       gustavo/saida/relatorios/cobertura_painel.csv
         (ano, etapa, n_painel, indicador, colunas, n_com, pct_com, observacao)
Uso:   python analises/05_descritivo_por_ano.py
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
sys.path.insert(0, str(GUSTAVO / "src" / "avaliacao"))
import baselines as B  # noqa: E402
import painel as P  # noqa: E402

REL = GUSTAVO / "saida" / "relatorios"


def desfecho_por_ano(atual):
    pub = atual[atual["REDE_PUBLICA"].astype("Int8") == 1]
    partes = []
    for etapa, col in B.ETAPAS.items():
        s = pub[["ANO", col]].dropna()
        g = s[col].astype("float64").groupby(s["ANO"])
        d = pd.DataFrame({"n": g.count(), "media": g.mean(), "mediana": g.median(),
                          "p75": g.quantile(0.75), "p90": g.quantile(0.9), "max": g.max(),
                          "pct_zero": g.apply(lambda s: (s == 0).mean() * 100)})
        partes.append(d.reset_index().rename(columns={"ANO": "ano"}).assign(etapa=etapa))
    out = pd.concat(partes, ignore_index=True)
    return out[["ano", "etapa", "n", "media", "mediana", "p75", "p90", "max", "pct_zero"]]


def grupos(etapa):
    s, st, si = P.SUF[etapa], P.SUF_TDI_ATU[etapa], P.SUF_IED[etapa]
    return {"abandono em t": [f"ABANDONO_{s}_T0"],
            "abandono em t−1": [f"ABANDONO_{s}_L1"],
            "abandono em t−2": [f"ABANDONO_{s}_L2"],
            "TDI": [f"TDI_{st}"],
            "ATU": [f"ATU_{st}"],
            "IED (N1 a N5)": [f"IED_{si}_N{i}" for i in range(1, 6)],
            "infraestrutura (IIE e dimensões)": list(P.INFRA)}


def cobertura_painel(atual):
    linhas = []
    for etapa in B.ETAPAS:
        pn = P.montar(etapa, atual)
        for ano, g in pn.groupby("ANO"):
            for nome, cols in grupos(etapa).items():
                n_com = int(g[cols].notna().all(axis=1).sum())
                linhas.append({"ano": int(ano), "etapa": etapa, "n_painel": len(g), "indicador": nome,
                               "colunas": " ".join(cols), "n_com": n_com,
                               "pct_com": 100 * n_com / len(g), "observacao": ""})
            linhas.append({"ano": int(ano), "etapa": etapa, "n_painel": len(g), "indicador": "HAD",
                           "colunas": "", "n_com": pd.NA, "pct_com": pd.NA,
                           "observacao": "não entra no painel (P019)"})
    out = pd.DataFrame(linhas)
    out["n_com"] = out["n_com"].astype("Int64")
    out["pct_com"] = out["pct_com"].astype("Float64")
    return out


def main():
    atual = pd.read_parquet(P.P_ATUAL)
    REL.mkdir(parents=True, exist_ok=True)
    d = desfecho_por_ano(atual)
    d.to_csv(REL / "desfecho_por_ano.csv", index=False, encoding="utf-8")
    # abandono-rr: a cobertura do painel da Etapa 2 (cobertura_painel.csv) dependia da base oficial com
    # TDI/ATU/IED e fica fora até a meta M5; grupos() e cobertura_painel() ficam para essa volta.
    print(d.round(2).to_string(index=False))
    print(f">>> {REL / 'desfecho_por_ano.csv'}")


if __name__ == "__main__":
    main()
