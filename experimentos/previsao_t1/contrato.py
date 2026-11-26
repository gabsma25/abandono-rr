"""Contrato dos arquivos `pares.csv` e `importancias.csv` (issue #15, R0a).

O texto está em `CONTRATO.md`, na mesma pasta; este módulo é a versão que o código confere. Quem gera um dos
dois arquivos chama `validar_pares` ou `validar_importancias` antes de gravar; quem lê usa `ler_pares` ou
`ler_importancias`, que fixam os tipos (o `co_entidade` como texto, regra 9 do CLAUDE.md) e já validam.

As funções de validação não corrigem nada: juntam todos os problemas encontrados e levantam um único
`ContratoInvalido` com a lista.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ETAPAS = ("AF", "EM")

# ------------------------------------------------------------------------------------------- pares.csv
# Nomes das colunas iguais aos do dataset/DICIONARIO.md (regra 11).
CHAVE_PARES = ["co_entidade", "ano", "etapa"]
IDENTIFICACAO_PARES = ["co_entidade", "ano", "ano_alvo", "etapa"]
ALVO = "abandono_t1"
PERSISTENCIA = "abandono_t"          # o "último abandono conhecido" da régua de persistência (issue #18)
OBRIGATORIAS_PARES = IDENTIFICACAO_PARES + [ALVO, PERSISTENCIA]

# O histórico de abandono: sai dos modelos "sem histórico" (issue #18).
HISTORICO = ("abandono_t", "abandono_tm1", "abandono_tm2", "variacao_abandono_defasada")

# As três taxas de rendimento do mesmo ano nunca entram juntas: somam 100 (regra 6).
TAXAS_T = ("aprovacao_t", "reprovacao_t", "abandono_t")
TAXAS_TM1 = ("aprovacao_tm1", "reprovacao_tm1", "abandono_tm1")

# Colunas do dataset que não podem ser preditoras: alvos e identificação.
NAO_PREDITORAS = ("alto_risco_t1", "co_municipio", "no_municipio", "janela_segura")

# ------------------------------------------------------------------------------------- importancias.csv
CHAVE_IMPORTANCIAS = ["algoritmo", "historico", "recorte", "etapa", "semente", "variavel"]
GRUPO_MODELO = ["algoritmo", "historico", "recorte", "etapa"]       # um modelo ajustado num recorte
COLUNAS_IMPORTANCIAS = ["algoritmo", "historico", "recorte", "ano_validacao", "etapa", "semente",
                        "variavel", "importancia", "supera_persistencia"]


class ContratoInvalido(ValueError):
    """O arquivo não segue o contrato; a mensagem lista todos os problemas."""

    def __init__(self, arquivo: str, problemas: list[str]):
        self.problemas = problemas
        super().__init__(f"{arquivo} fora do contrato:\n  - " + "\n  - ".join(problemas))


def _inteiro(s: pd.Series) -> bool:
    return pd.api.types.is_integer_dtype(s) and not s.isna().any()


def _zero_um(s: pd.Series) -> bool:
    return _inteiro(s) and s.isin([0, 1]).all()


def _texto(s: pd.Series) -> bool:
    return pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s)


def preditores(pares: pd.DataFrame) -> list[str]:
    """Todas as colunas que não são identificação nem alvo, na ordem do arquivo."""
    return [c for c in pares.columns if c not in IDENTIFICACAO_PARES and c != ALVO]


# ------------------------------------------------------------------------------------------- validação
def validar_pares(pares: pd.DataFrame) -> None:
    p: list[str] = []
    faltam = [c for c in OBRIGATORIAS_PARES if c not in pares.columns]
    if faltam:
        raise ContratoInvalido("pares.csv", [f"faltam as colunas obrigatórias {faltam}"])
    if pares.columns.duplicated().any():
        p.append(f"colunas repetidas: {sorted(set(pares.columns[pares.columns.duplicated()]))}")
    if pares.empty:
        p.append("nenhuma linha")

    co = pares["co_entidade"]
    if not _texto(co):
        p.append(f"co_entidade tem de ser texto (regra 9), veio {co.dtype}")
    elif co.isna().any() or not co.astype(str).str.fullmatch(r"\d{8}").all():
        p.append("co_entidade tem de ter 8 dígitos e nunca ficar vazio")
    for c in ("ano", "ano_alvo"):
        if not _inteiro(pares[c]):
            p.append(f"{c} tem de ser inteiro e sem vazios, veio {pares[c].dtype}")
    if _inteiro(pares["ano"]) and _inteiro(pares["ano_alvo"]) and (pares["ano_alvo"] != pares["ano"] + 1).any():
        p.append("ano_alvo tem de ser ano + 1 em todas as linhas")
    if not pares["etapa"].isin(ETAPAS).all():
        p.append(f"etapa só pode ser {ETAPAS}; veio {sorted(set(pares['etapa'].dropna()) - set(ETAPAS))}")
    if pares.duplicated(CHAVE_PARES).any():
        p.append(f"{int(pares.duplicated(CHAVE_PARES).sum())} linhas repetem a chave {CHAVE_PARES}")

    for c, pode_vazio in ((ALVO, False), (PERSISTENCIA, True)):
        s = pares[c]
        if not pd.api.types.is_float_dtype(s):
            p.append(f"{c} tem de ser número decimal, veio {s.dtype}")
            continue
        if not pode_vazio and s.isna().any():
            p.append(f"{c} vazio em {int(s.isna().sum())} linhas: par sem desfecho não entra")
        if ((s < 0) | (s > 100)).any():
            p.append(f"{c} fora de [0, 100]")

    cols = preditores(pares)
    proibidas = [c for c in cols if c.endswith("_t1") or "_zano" in c or c in NAO_PREDITORAS]
    if proibidas:
        p.append(f"colunas que não podem ser preditoras (alvo de t+1, _zano ou identificação): {proibidas}")
    for trio in (TAXAS_T, TAXAS_TM1):
        if all(c in cols for c in trio):
            p.append(f"as três taxas {trio} juntas somam 100 (regra 6): tire uma")
    for c in cols:
        s = pares[c]
        if not (pd.api.types.is_numeric_dtype(s) or _texto(s)) or pd.api.types.is_bool_dtype(s):
            p.append(f"preditor {c} tem de ser número ou categoria em texto, veio {s.dtype}")
        elif s.isna().all():
            p.append(f"preditor {c} está vazio em todas as linhas")

    if p:
        raise ContratoInvalido("pares.csv", p)


def validar_importancias(imp: pd.DataFrame, preditores_pares: list[str] | None = None) -> None:
    p: list[str] = []
    faltam = [c for c in COLUNAS_IMPORTANCIAS if c not in imp.columns]
    if faltam:
        raise ContratoInvalido("importancias.csv", [f"faltam as colunas {faltam}"])
    sobram = [c for c in imp.columns if c not in COLUNAS_IMPORTANCIAS]
    if sobram:
        p.append(f"colunas fora do contrato: {sobram}")
    if imp.empty:
        p.append("nenhuma linha")

    for c in ("algoritmo", "recorte", "variavel"):
        if not _texto(imp[c]) or imp[c].isna().any() or (imp[c].astype(str).str.strip() == "").any():
            p.append(f"{c} tem de ser texto e nunca ficar vazio")
    for c in ("ano_validacao", "semente"):
        if not _inteiro(imp[c]):
            p.append(f"{c} tem de ser inteiro e sem vazios, veio {imp[c].dtype}")
    for c in ("historico", "supera_persistencia"):
        if not _zero_um(imp[c]):
            p.append(f"{c} tem de ser 0 ou 1")
    if not imp["etapa"].isin(ETAPAS).all():
        p.append(f"etapa só pode ser {ETAPAS}")
    s = imp["importancia"]
    if not pd.api.types.is_float_dtype(s) or not np.isfinite(s.to_numpy(dtype=float, na_value=np.nan)).all():
        p.append("importancia tem de ser número decimal finito, sem vazios")
    if p:   # o resto depende dos tipos
        raise ContratoInvalido("importancias.csv", p)

    if imp.duplicated(CHAVE_IMPORTANCIAS).any():
        p.append(f"{int(imp.duplicated(CHAVE_IMPORTANCIAS).sum())} linhas repetem a chave {CHAVE_IMPORTANCIAS}")
    if (imp.groupby("recorte")["ano_validacao"].nunique() > 1).any():
        p.append("cada recorte tem um único ano_validacao")
    varia = imp.groupby(GRUPO_MODELO)["supera_persistencia"].nunique()
    if (varia > 1).any():
        p.append(f"supera_persistencia muda entre sementes do mesmo modelo: {list(varia[varia > 1].index)[:3]}")
    sem_hist = imp[(imp["historico"] == 0) & imp["variavel"].isin(HISTORICO)]
    if not sem_hist.empty:
        p.append(f"modelo sem histórico com variável do histórico: {sorted(sem_hist['variavel'].unique())}")
    for chave, g in imp.groupby(GRUPO_MODELO):
        conjuntos = g.groupby("semente")["variavel"].agg(frozenset)
        if conjuntos.nunique() > 1:
            p.append(f"as sementes de {chave} não têm as mesmas variáveis")
    if preditores_pares is not None:
        fora = sorted(set(imp["variavel"]) - set(preditores_pares))
        if fora:
            p.append(f"variáveis que não são preditoras do pares.csv: {fora}")

    if p:
        raise ContratoInvalido("importancias.csv", p)


# ------------------------------------------------------------------------------------------- leitura
def ler_pares(caminho: str | Path) -> pd.DataFrame:
    """Lê com os tipos do contrato: co_entidade e etapa como texto, anos inteiros, o resto como o pandas inferir."""
    pares = pd.read_csv(caminho, dtype={"co_entidade": "string", "etapa": "string"}, encoding="utf-8")
    for c in ("ano", "ano_alvo"):
        if c in pares.columns and not pares[c].isna().any():
            pares[c] = pares[c].astype("int64")
    for c in (ALVO, PERSISTENCIA):
        if c in pares.columns and pd.api.types.is_integer_dtype(pares[c]):
            pares[c] = pares[c].astype("float64")
    validar_pares(pares)
    return pares


def ler_importancias(caminho: str | Path, preditores_pares: list[str] | None = None) -> pd.DataFrame:
    imp = pd.read_csv(caminho, dtype={"algoritmo": "string", "recorte": "string", "etapa": "string",
                                      "variavel": "string"}, encoding="utf-8")
    if "importancia" in imp.columns and pd.api.types.is_integer_dtype(imp["importancia"]):
        imp["importancia"] = imp["importancia"].astype("float64")
    validar_importancias(imp, preditores_pares)
    return imp


def gravar(df: pd.DataFrame, caminho: str | Path) -> Path:
    """Grava no formato dos dois arquivos: UTF-8, vírgula, ponto decimal, vazio = ausente, fim de linha LF."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8", lineterminator="\n")
    return caminho
