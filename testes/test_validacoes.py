"""
Roda os scripts de validação herdados do projeto anterior e exige 0 falhas em cada um.

  01  base: rendimento 2007–2025, lags, desfecho de t+1, conjunto de escolas
  02  índices de infraestrutura (IIE e dimensões), contra o 05 do pipeline
  03  Censo pós-04; com --completo, confere 2019–2025 célula a célula contra os zips originais
      em dados/origem/ (2007–2018 não têm original no projeto: ressalva em docs/DECISOES.md)
  04  instrumento de avaliação: métricas, réguas, universo, bootstrap por escola e Holm
  08  classificação de alto risco: painel, rótulo, sem vazamento, réguas e funil

Cada script grava o relatório completo em saida/relatorios/validacao_*.txt.
"""
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = ["01_validar_base.py", "02_validar_indices.py", "03_validar_censo_pos04.py --completo",
           "04_validar_avaliacao.py", "08_validar_classificacao.py"]


@pytest.mark.parametrize("script", SCRIPTS)
def test_validacao(script):
    nome, *args = script.split()
    r = subprocess.run([sys.executable, str(RAIZ / "testes" / nome), *args], cwd=RAIZ, capture_output=True, check=False,
                       text=True, encoding="utf-8", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    resumo = "\n".join(r.stdout.splitlines()[-15:])
    assert r.returncode == 0, f"{script} falhou (código {r.returncode}):\n{resumo}\n{r.stderr[-2000:]}"
