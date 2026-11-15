"""O exemplo do professor (docs/tese_base/) nunca passa pelo nbstripout; os notebooks do projeto passam.

Lê os atributos efetivos com `git check-attr`, que já considera o .git/info/attributes da máquina. Se alguém
instalou o nbstripout sem `--attributes .gitattributes`, a regra local anula a exceção e este teste acusa.
"""
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLOS = sorted(p.relative_to(RAIZ).as_posix() for p in (RAIZ / "docs" / "tese_base").glob("*.ipynb"))
DO_PROJETO = sorted(p.relative_to(RAIZ).as_posix() for p in (RAIZ / "notebooks").glob("*.ipynb"))


def _attr(caminho, nome):
    saida = subprocess.run(["git", "check-attr", nome, "--", caminho], cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8", check=True).stdout.strip()
    return saida.rsplit(": ", 1)[1]


def test_ha_exemplo_do_professor():
    assert EXEMPLOS, "nenhum .ipynb em docs/tese_base/"


@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_exemplo_fora_do_nbstripout(caminho):
    assert _attr(caminho, "filter") == "unspecified" and _attr(caminho, "diff") == "unspecified", (
        f"{caminho} passaria pelo nbstripout. Provável causa: instalação sem --attributes. Corrija com "
        "`nbstripout --uninstall` e `nbstripout --install --attributes .gitattributes` (CONTRIBUTING, primeiro dia)")


@pytest.mark.parametrize("caminho", DO_PROJETO)
def test_notebook_do_projeto_no_nbstripout(caminho):
    assert _attr(caminho, "filter") == "nbstripout" and _attr(caminho, "diff") == "ipynb"
