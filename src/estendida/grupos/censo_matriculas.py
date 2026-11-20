# -*- coding: utf-8 -*-
"""
Grupo CENSO_MATRICULAS: as matrículas da educação básica por etapa, modalidade, sexo, cor/raça, faixa de idade e
período integral. As seis faixas de idade (QT_MAT_BAS_0_3 … QT_MAT_BAS_18_MAIS) são parcialmente mecânicas:
acumulam a reprovação e o abandono de anos anteriores (regra 6).

Origem: o bloco "matriculas" da lista fechada do estudo E (censo_bruto_v0.BLOCOS), 37 colunas, brutas
(docs/DECISOES.md, 2026-11-20, "Grupos do Censo ligados"). Segue o contrato de src/estendida/grupos/README.md.
A leitura, a conversão, a regra "coletada" e o tratamento de 2025 estão em _censo_comum.py.
"""
import importlib.util
import sys
from pathlib import Path


def _comum():
    nome = "grupos_censo_comum"
    if nome not in sys.modules:
        spec = importlib.util.spec_from_file_location(nome, Path(__file__).with_name("_censo_comum.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[nome] = mod
        spec.loader.exec_module(mod)
    return sys.modules[nome]


NOME = "censo_matriculas"

COLUNAS = [
    "QT_MAT_BAS", "QT_MAT_BAS_0_3", "QT_MAT_BAS_11_14", "QT_MAT_BAS_15_17", "QT_MAT_BAS_18_MAIS",
    "QT_MAT_BAS_4_5", "QT_MAT_BAS_6_10", "QT_MAT_BAS_AMARELA", "QT_MAT_BAS_BRANCA", "QT_MAT_BAS_D",
    "QT_MAT_BAS_FEM", "QT_MAT_BAS_INDIGENA", "QT_MAT_BAS_MASC", "QT_MAT_BAS_N", "QT_MAT_BAS_ND",
    "QT_MAT_BAS_PARDA", "QT_MAT_BAS_PRETA", "QT_MAT_EJA", "QT_MAT_EJA_FUND", "QT_MAT_EJA_MED", "QT_MAT_ESP",
    "QT_MAT_ESP_CC", "QT_MAT_FUND", "QT_MAT_FUND_AF", "QT_MAT_FUND_AF_INT", "QT_MAT_FUND_AI",
    "QT_MAT_FUND_AI_INT", "QT_MAT_FUND_INT", "QT_MAT_INF", "QT_MAT_INF_CRE", "QT_MAT_INF_CRE_INT",
    "QT_MAT_INF_INT", "QT_MAT_INF_PRE", "QT_MAT_MED", "QT_MAT_MED_INT", "QT_MAT_PROF", "QT_MAT_PROF_TEC",
]


def extrair(relatorios: Path, **kw):
    """["ANO", "CO_ENTIDADE", *COLUNAS], uma linha por escola e ano do cache (2007–2025)."""
    return _comum().extrair_bloco(COLUNAS, relatorios, **kw)
