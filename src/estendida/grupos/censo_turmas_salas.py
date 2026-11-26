# -*- coding: utf-8 -*-
"""
Grupo CENSO_TURMAS_SALAS: as turmas por etapa e modalidade e as salas utilizadas.

Origem: o bloco "turmas_salas" da lista fechada do estudo E (censo_bruto_v0.BLOCOS), 16 colunas, brutas
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


NOME = "censo_turmas_salas"

COLUNAS = [
    "QT_SALAS_UTILIZADAS", "QT_TUR_BAS", "QT_TUR_EJA", "QT_TUR_EJA_FUND", "QT_TUR_EJA_MED", "QT_TUR_ESP",
    "QT_TUR_ESP_CC", "QT_TUR_FUND", "QT_TUR_FUND_AF", "QT_TUR_FUND_AI", "QT_TUR_INF", "QT_TUR_INF_CRE",
    "QT_TUR_INF_PRE", "QT_TUR_MED", "QT_TUR_PROF", "QT_TUR_PROF_TEC",
]


def extrair(relatorios: Path, **kw):
    """["ANO", "CO_ENTIDADE", *COLUNAS], uma linha por escola e ano do cache (2007–2025)."""
    return _comum().extrair_bloco(COLUNAS, relatorios, **kw)
