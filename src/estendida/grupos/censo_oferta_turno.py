# -*- coding: utf-8 -*-
"""
Grupo CENSO_OFERTA_TURNO: as etapas e modalidades oferecidas e os turnos (diurno, noturno).

Origem: o bloco "oferta_turno" da lista fechada do estudo E (censo_bruto_v0.BLOCOS), 16 colunas, brutas
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


NOME = "censo_oferta_turno"

COLUNAS = [
    "IN_DIURNO", "IN_EJA", "IN_EJA_FUND", "IN_EJA_MED", "IN_ESP", "IN_ESP_CC", "IN_FUND", "IN_FUND_AF",
    "IN_FUND_AI", "IN_INF", "IN_INF_CRE", "IN_INF_PRE", "IN_MED", "IN_NOTURNO", "IN_PROF", "IN_PROF_TEC",
]


def extrair(relatorios: Path, **kw):
    """["ANO", "CO_ENTIDADE", *COLUNAS], uma linha por escola e ano do cache (2007–2025)."""
    return _comum().extrair_bloco(COLUNAS, relatorios, **kw)
