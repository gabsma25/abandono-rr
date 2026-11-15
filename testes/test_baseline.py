"""docs/BASELINE.md está em dia, e as cópias congeladas que ele cita são as do projeto anterior.

1. o docs/BASELINE.md é exatamente o que src/relatorios/baseline.py gera com os CSVs atuais;
2. cada cópia em docs/projeto_anterior/ tem o sha256 registrado no README daquela pasta.
"""
import hashlib
import importlib.util
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("baseline", RAIZ / "src" / "relatorios" / "baseline.py")
BL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BL)

ANTERIOR = RAIZ / "docs" / "projeto_anterior"
LINHA = re.compile(r"^\| `([^`]+)` \|.*\| `([0-9a-f]{64})` \|$")
HASHES = dict(m.groups() for m in map(LINHA.match, (ANTERIOR / "README.md").read_text(encoding="utf-8").splitlines()) if m)


def test_baseline_em_dia():
    assert BL.DESTINO.read_text(encoding="utf-8") == BL.texto(), \
        "docs/BASELINE.md desatualizado: rode python src/relatorios/baseline.py e versione"


def test_readme_lista_todas_as_copias():
    no_disco = {p.relative_to(ANTERIOR).as_posix() for p in ANTERIOR.rglob("*") if p.is_file() and p.name != "README.md"}
    assert no_disco == set(HASHES), f"README de docs/projeto_anterior/ e disco divergem: {no_disco ^ set(HASHES)}"


@pytest.mark.parametrize("arquivo", sorted(HASHES))
def test_copia_congelada_intacta(arquivo):
    atual = hashlib.sha256((ANTERIOR / arquivo).read_bytes()).hexdigest()
    assert atual == HASHES[arquivo], f"{arquivo} mudou desde a cópia do projeto anterior"
