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


P_BACKUP = RAIZ / "saida" / "_backup_2026-10-14" / "etapas" / "04_base_com_censo.parquet"


def test_03_comparacao_com_backup_de_outubro():
    """Seção I do teste 03: base do 04 antes × depois da correção de 14/10/2026."""
    if not P_BACKUP.exists():
        pytest.skip("seção I do teste 03 não roda no abandono-rr: o backup de outubro (saida/_backup_2026-10-14) "
                    "ficou no projeto anterior (Dados-do-Projeto 969fc64), onde a comparação foi feita; "
                    "ver docs/DECISOES.md")
    rel = (RAIZ / "saida" / "relatorios" / "validacao_pos04.txt").read_text(encoding="utf-8")
    secao = rel.split("I. ANTES x DEPOIS")[1].split("RESUMO")[0]
    assert "❌" not in secao


def test_03_confere_2019_2025_com_os_zips_originais():
    """Seção F do teste 03: os 7 anos de 2019 a 2025 conferem célula a célula com os zips do INEP."""
    zips = sorted((RAIZ / "dados" / "origem" / "censo").glob("microdados_censo_escolar_*.zip"))
    if len(zips) < 7:
        pytest.skip(f"só {len(zips)} dos 7 zips do Censo 2019–2025 estão em dados/origem/censo: a conferência com o "
                    "original não roda. Obtenha-os com python -m src.aquisicao --origem-local PASTA (ou --baixar)")
    rel = (RAIZ / "saida" / "relatorios" / "validacao_pos04.txt").read_text(encoding="utf-8")
    assert "7 anos conferem célula a célula com o microdado ORIGINAL: 2019–2025" in rel
