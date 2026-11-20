# -*- coding: utf-8 -*-
"""
Grupo CENSO_PREDIO_SERVICOS: água, esgoto, lixo, energia, local de funcionamento e dependências do prédio.

Origem: o bloco "predio_servicos" da lista fechada do estudo E (censo_bruto_v0.BLOCOS), 29 colunas, brutas
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


NOME = "censo_predio_servicos"

COLUNAS = [
    "IN_AGUA_CACIMBA", "IN_AGUA_FONTE_RIO", "IN_AGUA_INEXISTENTE", "IN_AGUA_POCO_ARTESIANO",
    "IN_AGUA_REDE_PUBLICA", "IN_ALMOXARIFADO", "IN_AREA_VERDE", "IN_AUDITORIO", "IN_BANHEIRO_CHUVEIRO",
    "IN_BANHEIRO_EI", "IN_BANHEIRO_PNE", "IN_COZINHA", "IN_DEPENDENCIAS_OUTRAS", "IN_ENERGIA_INEXISTENTE",
    "IN_ESGOTO_FOSSA", "IN_ESGOTO_INEXISTENTE", "IN_ESGOTO_REDE_PUBLICA", "IN_LABORATORIO_CIENCIAS",
    "IN_LIXO_ENTERRA", "IN_LIXO_QUEIMA", "IN_LOCAL_FUNC_GALPAO", "IN_LOCAL_FUNC_OUTROS",
    "IN_LOCAL_FUNC_PREDIO_ESCOLAR", "IN_LOCAL_FUNC_SALAS_OUTRA_ESC", "IN_PARQUE_INFANTIL",
    "IN_QUADRA_ESPORTES_COBERTA", "IN_QUADRA_ESPORTES_DESCOBERTA", "IN_SALA_ATENDIMENTO_ESPECIAL",
    "IN_SALA_LEITURA",
]


def extrair(relatorios: Path, **kw):
    """["ANO", "CO_ENTIDADE", *COLUNAS], uma linha por escola e ano do cache (2007–2025)."""
    return _comum().extrair_bloco(COLUNAS, relatorios, **kw)
