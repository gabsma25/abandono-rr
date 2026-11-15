"""O protocolo da Etapa 4, preservado no fim do docs/PROTOCOLO.md, é o original sem nenhuma mudança de texto.

A única mudança permitida são os títulos, rebaixados dois níveis (`#` → `###`) para ficarem abaixo da seção
"Protocolo registrado, não executado, substituído em 2026-11-14". O original é o docs/PROTOCOLO.md do commit
a56482d (o main antes da mudança de escopo, depois do merge do #2).
"""
import re
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PROTOCOLO = RAIZ / "docs" / "PROTOCOLO.md"
MARCO = "## Protocolo registrado, não executado, substituído em 2026-11-14\n"
INICIO_ORIGINAL = "### Protocolo da Etapa 4"
COMMIT_ORIGINAL = "a56482d"


def _preservado():
    texto = PROTOCOLO.read_text(encoding="utf-8")
    assert texto.count(MARCO) == 1, "a seção do protocolo preservado sumiu ou se repetiu"
    corpo = texto.split(MARCO)[1]
    assert corpo.count(INICIO_ORIGINAL) == 1
    return INICIO_ORIGINAL + corpo.split(INICIO_ORIGINAL)[1]


def _promover(texto):
    """Desfaz o rebaixamento: tira dois '#' de cada título fora dos blocos de código."""
    linhas, codigo = [], False
    for linha in texto.split("\n"):
        if linha.startswith("```"):
            codigo = not codigo
        elif not codigo and re.match(r"^#{3,6} ", linha):
            linha = linha[2:]
        linhas.append(linha)
    return "\n".join(linhas)


def test_titulos_preservados_ficam_abaixo_das_secoes():
    codigo = False
    for linha in _preservado().split("\n"):
        if linha.startswith("```"):
            codigo = not codigo
        elif not codigo and linha.startswith("#"):
            assert linha.startswith("###"), f"título do protocolo preservado no nível de A, B, C: {linha!r}"


def test_texto_preservado_igual_ao_original():
    r = subprocess.run(["git", "show", f"{COMMIT_ORIGINAL}:docs/PROTOCOLO.md"], cwd=RAIZ, capture_output=True)
    if r.returncode != 0:
        pytest.skip(f"commit {COMMIT_ORIGINAL} indisponível (clone raso?)")
    original = r.stdout.decode("utf-8")
    assert _promover(_preservado()) == original, "o texto do protocolo preservado mudou em relação ao original"
