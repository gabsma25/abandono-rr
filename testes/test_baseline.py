"""docs/BASELINE.md está em dia: é exatamente o que src/relatorios/baseline.py gera com os CSVs atuais."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("baseline", RAIZ / "src" / "relatorios" / "baseline.py")
BL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BL)


def test_baseline_em_dia():
    assert BL.DESTINO.read_text(encoding="utf-8") == BL.texto(), \
        "docs/BASELINE.md desatualizado: rode python src/relatorios/baseline.py e versione"
