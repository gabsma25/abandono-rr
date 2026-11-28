"""Importância de cada variável por permutação (ΔMAE), na validação de cada recorte (issue #19, M5a).

Para cada modelo ajustado por `modelos.py` (#18), algoritmo × histórico × recorte × etapa, e para cada variável que
entrou em X: embaralha a coluna dentro da validação, prevê de novo **com o mesmo modelo** (sem reajustar) e mede
quanto o MAE piora:

    importancia = MAE com a variável embaralhada − MAE original      (pontos percentuais; pode ser negativa)

Cada semente de permutação vira uma linha separada; quem lê agrega (média, desvio). Todas as variáveis de cada
modelo são gravadas, inclusive as de importância nula ou negativa (regra 7). A normalização e o tratamento dos
negativos são do `redes.py` (#20), não deste arquivo.

A permutação é feita só nas linhas da validação comum (as mesmas do `metricas.csv`); o treino não é tocado. A
persistência não tem variáveis e não aparece aqui. `supera_persistencia` é a mesma coluna do `metricas.csv`.

**Importância não é causa.** Ela mede o quanto o modelo usa a variável para prever, nos dados de validação. Variáveis
correlacionadas podem dividir ou esconder importância entre si; a análise por grupos fica para a versão completa.

O formato de saída é o do `importancias.csv` do contrato (#15, `experimentos/previsao_t1/CONTRATO.md`).

Uso:
    python -m experimentos.previsao_t1.importancias --pares CAMINHO/pares.csv [--saida PASTA] [--semente 0]
    (grava metricas.csv e importancias.csv numa só passada: cada modelo é ajustado uma vez)
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from experimentos.previsao_t1 import modelos as M
from experimentos.previsao_t1 import recortes as R

SEMENTES_PERMUTACAO = tuple(range(5))
COLUNAS_IMPORTANCIAS = ["algoritmo", "historico", "recorte", "ano_validacao", "etapa", "semente", "variavel",
                        "importancia", "supera_persistencia"]


def _prever(modelo, X) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return modelo.predict(X)


def permutacao(modelo, X: pd.DataFrame, y: np.ndarray, sementes=SEMENTES_PERMUTACAO) -> pd.DataFrame:
    """ΔMAE de cada coluna de X, uma linha por semente × variável. O modelo não é reajustado."""
    base = M.mae(y, _prever(modelo, X))
    linhas = []
    for s in sementes:
        for j, col in enumerate(X.columns):
            rng = np.random.default_rng((s, j))          # uma permutação por semente × variável
            Xp = X.copy()
            Xp[col] = X[col].to_numpy()[rng.permutation(len(X))]
            linhas.append({"semente": s, "variavel": col, "importancia": M.mae(y, _prever(modelo, Xp)) - base})
    return pd.DataFrame(linhas)


def rodar(pares: pd.DataFrame, recortes: list, algoritmos=M.ALGORITMOS, etapas=None, semente: int = 0,
          sementes_permutacao=SEMENTES_PERMUTACAO) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Uma passada: ajusta cada modelo uma vez e devolve (metricas, importancias)."""
    met_linhas, imp_partes, vistos = [], [], set()
    for m in M.iterar(pares, recortes, algoritmos, etapas, semente):
        y, pers, X = m["y_validacao"], m["persistencia_validacao"], m["X_validacao"]
        p = _prever(m["modelo"], X)
        mae_p, mae_m = M.mae(y, pers), M.mae(y, p)
        chave = (m["recorte"], m["etapa"])
        if chave not in vistos:
            vistos.add(chave)
            met_linhas.append({**{k: m[k] for k in ("recorte", "ano_validacao", "etapa", "n_treino")},
                               "algoritmo": "persistencia", "historico": 1, "semente": semente,
                               "n_validacao": len(y), "n_preditores": 1, "mae": mae_p, "rmse": M.rmse(y, pers),
                               "r2": M.r2(y, pers), "mae_persistencia": mae_p, "supera_persistencia": 0})
        supera = int(mae_m < mae_p)
        met_linhas.append({**{k: m[k] for k in ("algoritmo", "historico", "recorte", "ano_validacao", "etapa",
                                                 "semente", "n_treino")},
                           "n_validacao": len(y), "n_preditores": len(m["colunas"]), "mae": mae_m,
                           "rmse": M.rmse(y, p), "r2": M.r2(y, p), "mae_persistencia": mae_p,
                           "supera_persistencia": supera})
        imp = permutacao(m["modelo"], X, y, sementes_permutacao)
        for k in ("algoritmo", "historico", "recorte", "ano_validacao", "etapa"):
            imp[k] = m[k]
        imp["supera_persistencia"] = supera
        imp_partes.append(imp)
    met = pd.DataFrame(met_linhas, columns=M.COLUNAS_METRICAS)
    imp = (pd.concat(imp_partes, ignore_index=True)[COLUNAS_IMPORTANCIAS] if imp_partes
           else pd.DataFrame(columns=COLUNAS_IMPORTANCIAS))
    for c in ("algoritmo", "recorte", "etapa", "variavel"):
        imp[c] = imp[c].astype("string")
    for c in ("historico", "ano_validacao", "semente", "supera_persistencia"):
        imp[c] = imp[c].astype("int64")
    imp["importancia"] = imp["importancia"].astype("float64")
    return met, imp


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pares", type=Path, required=True)
    ap.add_argument("--saida", type=Path, default=M.SAIDA_PADRAO)
    ap.add_argument("--semente", type=int, default=0)
    a = ap.parse_args(argv)
    pares = M.ler_pares(a.pares)
    met, imp = rodar(pares, R.gerar_recortes(pares["ano"].unique()), semente=a.semente)
    print(f">>> {M.gravar(met, a.saida / 'metricas.csv')}  ({len(met)} linhas)")
    print(f">>> {M.gravar(imp, a.saida / 'importancias.csv')}  ({len(imp)} linhas)")


if __name__ == "__main__":
    main()
