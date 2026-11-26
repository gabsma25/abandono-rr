# -*- coding: utf-8 -*-
"""
Grupo CENSO_DOCENTES: os docentes por etapa e modalidade.

Origem: o bloco "docentes" da lista fechada do estudo E (censo_bruto_v0.BLOCOS), 15 colunas, brutas
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


NOME = "censo_docentes"

COLUNAS = [
    "QT_DOC_BAS", "QT_DOC_EJA", "QT_DOC_EJA_FUND", "QT_DOC_EJA_MED", "QT_DOC_ESP", "QT_DOC_ESP_CC",
    "QT_DOC_FUND", "QT_DOC_FUND_AF", "QT_DOC_FUND_AI", "QT_DOC_INF", "QT_DOC_INF_CRE", "QT_DOC_INF_PRE",
    "QT_DOC_MED", "QT_DOC_PROF", "QT_DOC_PROF_TEC",
]


def extrair(relatorios: Path, **kw):
    """["ANO", "CO_ENTIDADE", *COLUNAS], uma linha por escola e ano do cache (2007–2025)."""
    return _comum().extrair_bloco(COLUNAS, relatorios, **kw)
