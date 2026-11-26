"""Gerador sintético de `pares.csv` e `importancias.csv`, no formato do `CONTRATO.md` (issue #15, R0a).

Serve para desenvolver e testar o resto do esqueleto (recortes, modelos, importâncias, redes, rankings) antes do
`pares.csv` real (issue #17). **Nenhum dado real é lido.** As colunas têm os nomes do dataset v0.2.0 para que o
mesmo código rode depois nos pares reais, mas os valores são inventados e os efeitos são os que estão em
`PLANTADAS`; nada que saia daqui diz alguma coisa sobre as escolas de Roraima.

O desfecho é gerado assim, por escola e etapa, ano a ano:

    abandono(t+1) = base_etapa + 0,5 · abandono(t) + 3 · [Rural] − 6 · dim_iib_prop(t) + ruído N(0, 2)

truncado em [0, 100] e com uma casa decimal, como o INEP publica. As outras colunas (`RUIDO`) são sorteadas sem
nenhuma relação com o desfecho. Algumas têm vazios, para exercitar a imputação.

Uso:
    python -m experimentos.previsao_t1.sintetico                   # grava em experimentos/previsao_t1/saida/sintetico/
    python -m experimentos.previsao_t1.sintetico --semente 3 --saida PASTA
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from experimentos.previsao_t1 import contrato as C

# As variáveis "verdadeiras" e o efeito plantado de cada uma no abandono de t+1 (pontos percentuais por unidade).
PLANTADAS = {"abandono_t": 0.5, "localizacao": 3.0, "dim_iib_prop": -6.0}   # localizacao: efeito de Rural
RUIDO = ("reprovacao_t", "dim_idp_prop", "idp_biblioteca", "iep_internet")
BASE_ETAPA = {"AF": 6.0, "EM": 9.0}
DP_RUIDO = 2.0

PASTA = Path(__file__).resolve().parent
SAIDA_PADRAO = PASTA / "saida" / "sintetico"


def gerar_pares(semente: int = 0, n_escolas: int = 120, anos=range(2009, 2024),
                etapas=C.ETAPAS, frac_em: float = 0.5, frac_vazios: float = 0.05) -> pd.DataFrame:
    """Uma linha por escola × ano t × etapa, com o desfecho de t+1 gerado pela fórmula do módulo."""
    rng = np.random.default_rng(semente)
    anos = list(anos)
    codigos = [f"99{i:06d}" for i in range(1, n_escolas + 1)]   # UF 99 não existe: nunca é código real
    rural = rng.random(n_escolas) < 0.4
    oferece_em = rng.random(n_escolas) < frac_em
    infra0 = np.clip(rng.normal(0.75 - 0.25 * rural, 0.15), 0, 1)           # mais baixa nas rurais
    linhas = []
    for e, cod in enumerate(codigos):
        for etapa in etapas:
            if etapa == "EM" and not oferece_em[e]:
                continue
            y = max(0.0, rng.normal(6.0, 3.0))                               # abandono do ano anterior ao 1º
            for t in anos:
                iib = round(float(np.clip(infra0[e] + rng.normal(0, 0.05), 0, 1)) * 4) / 4   # 4 itens
                y_t1 = (BASE_ETAPA[etapa] + PLANTADAS["abandono_t"] * y + PLANTADAS["localizacao"] * rural[e]
                        + PLANTADAS["dim_iib_prop"] * iib + rng.normal(0, DP_RUIDO))
                y_t1 = round(float(np.clip(y_t1, 0, 100)), 1)
                linhas.append({
                    "co_entidade": cod, "ano": t, "ano_alvo": t + 1, "etapa": etapa,
                    C.ALVO: y_t1,
                    "abandono_t": round(y, 1),
                    "localizacao": "Rural" if rural[e] else "Urbana",
                    "dim_iib_prop": iib,
                    "reprovacao_t": round(float(np.clip(rng.normal(10, 5), 0, 100)), 1),
                    "dim_idp_prop": rng.integers(0, 6) / 5,                  # 5 itens
                    "idp_biblioteca": float(rng.random() < 0.5),
                    "iep_internet": float(rng.random() < 0.6),
                })
                y = y_t1
    pares = pd.DataFrame(linhas)
    pares["co_entidade"] = pares["co_entidade"].astype("string")
    pares["etapa"] = pares["etapa"].astype("string")
    pares["localizacao"] = pares["localizacao"].astype("string")
    for c in ("reprovacao_t", "iep_internet"):                               # vazios só em ruído
        pares.loc[rng.random(len(pares)) < frac_vazios, c] = np.nan
    C.validar_pares(pares)
    return pares


def gerar_importancias(preditores: list[str], semente: int = 0, etapas=C.ETAPAS,
                       anos_validacao=range(2015, 2019), algoritmos=("ridge", "random_forest"),
                       sementes=range(5)) -> pd.DataFrame:
    """Importâncias FALSAS, só para quem lê o arquivo (redes, rankings): as plantadas têm ΔMAE claramente maior.

    Não vêm de modelo nenhum. Cada algoritmo tem a sua escala, para exercitar a normalização dentro de
    algoritmo × recorte (issue #20); as de ruído ficam perto de zero e podem ser negativas.
    """
    rng = np.random.default_rng(semente)
    escala = {a: 1.0 + i for i, a in enumerate(algoritmos)}
    linhas = []
    for algoritmo in algoritmos:
        for historico in (1, 0):
            vars_modelo = [v for v in preditores if historico or v not in C.HISTORICO]
            for t_v in anos_validacao:
                for etapa in etapas:
                    supera = int(historico == 1 or rng.random() < 0.5)
                    for s in sementes:
                        for v in vars_modelo:
                            media = 1.5 if v in PLANTADAS else 0.0
                            dp = 0.2 if v in PLANTADAS else 0.05
                            linhas.append({
                                "algoritmo": algoritmo, "historico": historico, "recorte": f"expansiva_{t_v}",
                                "ano_validacao": t_v, "etapa": etapa, "semente": s, "variavel": v,
                                "importancia": round(escala[algoritmo] * rng.normal(media, dp), 6),
                                "supera_persistencia": supera,
                            })
    imp = pd.DataFrame(linhas, columns=C.COLUNAS_IMPORTANCIAS)
    for c in ("algoritmo", "recorte", "etapa", "variavel"):
        imp[c] = imp[c].astype("string")
    C.validar_importancias(imp, preditores)
    return imp


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--semente", type=int, default=0)
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    a = ap.parse_args(argv)
    pares = gerar_pares(a.semente)
    imp = gerar_importancias(C.preditores(pares), a.semente)
    for nome, df in (("pares.csv", pares), ("importancias.csv", imp)):
        print(f">>> {C.gravar(df, a.saida / nome)}  ({len(df)} linhas × {df.shape[1]} colunas)")


if __name__ == "__main__":
    main()
