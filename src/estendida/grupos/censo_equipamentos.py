# -*- coding: utf-8 -*-
"""
Grupo CENSO_EQUIPAMENTOS: os equipamentos (indicadores e quantidades).

Origem: o bloco "equipamentos" da lista fechada do estudo E (censo_bruto_v0.BLOCOS), 10 colunas, brutas
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


NOME = "censo_equipamentos"

COLUNAS = [
    "IN_EQUIP_COPIADORA", "IN_EQUIP_DVD", "IN_EQUIP_IMPRESSORA_MULT", "IN_EQUIP_PARABOLICA", "IN_EQUIP_SOM",
    "IN_EQUIP_TV", "QT_EQUIP_DVD", "QT_EQUIP_MULTIMIDIA", "QT_EQUIP_SOM", "QT_EQUIP_TV",
]


def extrair(relatorios: Path, **kw):
    """["ANO", "CO_ENTIDADE", *COLUNAS], uma linha por escola e ano do cache (2007–2025)."""
    return _comum().extrair_bloco(COLUNAS, relatorios, **kw)
