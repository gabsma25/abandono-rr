"""Modelos da previsão do abandono de t+1, com e sem histórico, e as métricas por recorte (issue #18, M3a).

Para cada recorte de `recortes.py` (#16), cada etapa (AF e EM, ajustadas separadamente) e cada algoritmo, o modelo é
ajustado no treino do recorte e avaliado na validação dele. Sai uma tabela (`metricas.csv`) com MAE, RMSE e R², em
pontos percentuais, e com a comparação contra a persistência.

**Algoritmos** (hiperparâmetros fixos, sem ajuste; o ajuste na validação temporal fica para a versão completa):
- `persistencia`: repete o abandono de t−1 (`abandono_tm1`) como previsão de t+1. É a régua B1R_lag
  (`docs/BASELINE.md`, seção 1): o último abandono publicado na hora da previsão. Não é ajustada.
- `ridge`: `Ridge(alpha=1.0)`, como no notebook 05.
- `random_forest`: 300 árvores, `min_samples_leaf=5`, como no notebook 05.
- `mlp_professor`: a MLP do exemplo do professor (50 neurônios, logistic, adam, parada antecipada), como no estudo E.
- `mlp_64_32`: a MLP compacta da proposta do professor (64 e 32 neurônios, relu, `alpha=1e-3`, parada antecipada).

**Com e sem histórico.** Com histórico, entram todos os preditores. Sem histórico, saem as colunas de `HISTORICO` (o
abandono de anos anteriores e a variação dele), para medir o que as outras variáveis acrescentam.

**Nada do futuro entra em X.** Saem sempre a identificação, o alvo e as taxas de rendimento do próprio ano t
(`aprovacao_t`, `reprovacao_t`, `abandono_t`), que ainda não estão publicadas no começo de t+1
(`docs/PROTOCOLO.md`, 4.1). Toda transformação (imputação, padronização, codificação das categorias) fica dentro do
`Pipeline` e é ajustada só no treino de cada recorte (regra 5). Ausente continua ausente até a imputação, que usa a
mediana do treino e acrescenta um indicador de ausência (nada vira 0 antes disso; regra 8).

**Mesmas linhas para todos.** As métricas de todos os algoritmos de um recorte × etapa são calculadas nas mesmas
linhas da validação: as que têm `abandono_tm1` (sem ele a persistência não existe). `supera_persistencia` = 1 quando o
MAE do modelo é menor que o da persistência nessas linhas.

**Limitação registrada.** A parada antecipada das duas MLPs separa 10% do treino por sorteio, misturando os anos do
treino. Não toca a validação nem o teste final, mas não é uma separação temporal.

O módulo lê só o `pares.csv` que recebe; nunca o dataset, o cache ou o teste final (`recortes.py` o tranca).

Uso:
    python -m experimentos.previsao_t1.modelos --pares CAMINHO/pares.csv [--saida PASTA] [--semente 0]
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from experimentos.previsao_t1 import recortes as R

IDENTIFICACAO = ("co_entidade", "ano", "ano_alvo", "etapa")
ALVO = "abandono_t1"
PERSISTENCIA = "abandono_tm1"
# Dado do próprio ano t: ainda não publicado no começo de t+1 (PROTOCOLO 4.1). Nunca entra em X.
TAXAS_DE_T = ("aprovacao_t", "reprovacao_t", "abandono_t")
# Histórico de abandono: sai dos modelos "sem histórico".
HISTORICO = ("abandono_tm1", "abandono_tm2", "variacao_abandono_defasada")
# Colunas do dataset que nunca são preditoras (o contrato do #15 as recusa; aqui também saem por segurança).
NUNCA_EM_X = IDENTIFICACAO + (ALVO,) + TAXAS_DE_T + ("alto_risco_t1", "co_municipio", "no_municipio",
                                                       "janela_segura")

ALGORITMOS = ("ridge", "random_forest", "mlp_professor", "mlp_64_32")
COLUNAS_METRICAS = ["algoritmo", "historico", "recorte", "ano_validacao", "etapa", "semente", "n_treino",
                    "n_validacao", "n_preditores", "mae", "rmse", "r2", "mae_persistencia", "supera_persistencia"]
SAIDA_PADRAO = Path(__file__).resolve().parent / "saida"


# ------------------------------------------------------------------ preditores e pipeline
def preditores(pares: pd.DataFrame, historico: bool) -> list[str]:
    """As colunas de X, na ordem do arquivo: tudo que não é identificação, alvo nem dado de t."""
    cols = [c for c in pares.columns if c not in NUNCA_EM_X and not c.endswith("_t1") and "_zano" not in c]
    if not historico:
        cols = [c for c in cols if c not in HISTORICO]
    return cols


def _categoricas(X: pd.DataFrame) -> list[str]:
    return [c for c in X.columns if not pd.api.types.is_numeric_dtype(X[c])]


def estimador(algoritmo: str, semente: int = 0):
    if algoritmo == "ridge":
        return Ridge(alpha=1.0)
    if algoritmo == "random_forest":
        return RandomForestRegressor(n_estimators=300, min_samples_leaf=5, n_jobs=-1, random_state=semente)
    if algoritmo == "mlp_professor":
        return MLPRegressor(hidden_layer_sizes=(50,), activation="logistic", solver="adam", max_iter=5000,
                            tol=1e-7, momentum=0.8, early_stopping=True, epsilon=1e-08, n_iter_no_change=10,
                            random_state=semente)
    if algoritmo == "mlp_64_32":
        return MLPRegressor(hidden_layer_sizes=(64, 32), activation="relu", solver="adam", alpha=1e-3,
                            max_iter=2000, early_stopping=True, validation_fraction=0.1, n_iter_no_change=20,
                            random_state=semente)
    raise ValueError(f"algoritmo desconhecido: {algoritmo}")


def pipeline(algoritmo: str, X: pd.DataFrame, semente: int = 0) -> Pipeline:
    """Imputação + padronização (numéricas) e codificação (categóricas), tudo ajustado só no treino."""
    cat = _categoricas(X)
    num = [c for c in X.columns if c not in cat]
    partes = [("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                                ("pad", StandardScaler())]), num)]
    if cat:
        partes.append(("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                                        ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat))
    return Pipeline([("pre", ColumnTransformer(partes, remainder="drop")), ("m", estimador(algoritmo, semente))])


def _X(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    X = df[cols].copy()
    for c in _categoricas(X):
        X[c] = X[c].astype(object).where(X[c].notna(), np.nan)    # pd.NA -> nan, que o sklearn entende
    return X


def ajustar(treino: pd.DataFrame, algoritmo: str, historico: bool, semente: int = 0):
    """Ajusta o pipeline só no treino. Devolve (pipeline ajustado, colunas de X)."""
    cols = preditores(treino, historico)
    if not cols:
        raise ValueError("nenhum preditor")
    X = _X(treino, cols)
    pipe = pipeline(algoritmo, X, semente)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pipe.fit(X, treino[ALVO].to_numpy(dtype=float))
    return pipe, cols


# ------------------------------------------------------------------ métricas
def mae(y, p) -> float:
    return float(np.mean(np.abs(np.asarray(y, float) - np.asarray(p, float))))


def rmse(y, p) -> float:
    return float(np.sqrt(np.mean((np.asarray(y, float) - np.asarray(p, float)) ** 2)))


def r2(y, p) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    ss = np.sum((y - y.mean()) ** 2)
    return float(1 - np.sum((y - p) ** 2) / ss) if ss > 0 else float("nan")


def linhas_comuns(validacao: pd.DataFrame) -> pd.DataFrame:
    """As linhas da validação em que todos os algoritmos, inclusive a persistência, são comparados."""
    return validacao[validacao[PERSISTENCIA].notna()]


# ------------------------------------------------------------------ laço principal
def iterar(pares: pd.DataFrame, recortes: list, algoritmos=ALGORITMOS, etapas=None, semente: int = 0):
    """Ajusta cada algoritmo × histórico × recorte × etapa e devolve um dict por modelo, com o modelo ajustado e a
    validação comum (X e y). A M5a (#19) usa o mesmo laço para as importâncias."""
    etapas = sorted(pares["etapa"].dropna().unique()) if etapas is None else etapas
    for recorte in recortes:
        for etapa in etapas:
            treino, validacao = R.dividir(pares, recorte, etapa=etapa)
            comum = linhas_comuns(validacao)
            if treino.empty or comum.empty:
                continue
            for algoritmo in algoritmos:
                for historico in (1, 0):
                    modelo, cols = ajustar(treino, algoritmo, bool(historico), semente)
                    yield {"algoritmo": algoritmo, "historico": historico, "recorte": recorte.id,
                           "ano_validacao": recorte.ano_validacao, "etapa": etapa, "semente": semente,
                           "modelo": modelo, "colunas": cols, "n_treino": len(treino),
                           "X_validacao": _X(comum, cols), "y_validacao": comum[ALVO].to_numpy(dtype=float),
                           "persistencia_validacao": comum[PERSISTENCIA].to_numpy(dtype=float)}


def avaliar(pares: pd.DataFrame, recortes: list, algoritmos=ALGORITMOS, etapas=None, semente: int = 0) -> pd.DataFrame:
    """A tabela do metricas.csv: uma linha por algoritmo × histórico × recorte × etapa, mais a persistência."""
    linhas, vistos = [], set()
    for m in iterar(pares, recortes, algoritmos, etapas, semente):
        y, pers = m["y_validacao"], m["persistencia_validacao"]
        mae_p = mae(y, pers)
        chave = (m["recorte"], m["etapa"])
        if chave not in vistos:                 # uma linha da persistência por recorte × etapa
            vistos.add(chave)
            linhas.append({**{k: m[k] for k in ("recorte", "ano_validacao", "etapa", "n_treino")},
                           "algoritmo": "persistencia", "historico": 1, "semente": semente,
                           "n_validacao": len(y), "n_preditores": 1, "mae": mae_p, "rmse": rmse(y, pers),
                           "r2": r2(y, pers), "mae_persistencia": mae_p, "supera_persistencia": 0})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = m["modelo"].predict(m["X_validacao"])
        linhas.append({**{k: m[k] for k in ("algoritmo", "historico", "recorte", "ano_validacao", "etapa",
                                             "semente", "n_treino")},
                       "n_validacao": len(y), "n_preditores": len(m["colunas"]), "mae": mae(y, p),
                       "rmse": rmse(y, p), "r2": r2(y, p), "mae_persistencia": mae_p,
                       "supera_persistencia": int(mae(y, p) < mae_p)})
    return pd.DataFrame(linhas, columns=COLUNAS_METRICAS)


def gravar(df: pd.DataFrame, caminho: Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8", lineterminator="\n")
    return caminho


def ler_pares(caminho) -> pd.DataFrame:
    pares = pd.read_csv(caminho, dtype={"co_entidade": "string", "etapa": "string"}, encoding="utf-8")
    for c in ("ano", "ano_alvo"):
        pares[c] = pares[c].astype("int64")
    return pares


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pares", type=Path, required=True)
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    ap.add_argument("--semente", type=int, default=0)
    a = ap.parse_args(argv)
    pares = ler_pares(a.pares)
    met = avaliar(pares, R.gerar_recortes(pares["ano"].unique()), semente=a.semente)
    print(f">>> {gravar(met, a.saida / 'metricas.csv')}  ({len(met)} linhas)")


if __name__ == "__main__":
    main()
