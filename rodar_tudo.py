"""
Regera tudo do abandono-rr, na ordem, e roda os testes.

  1. pipeline estendido 2007–2025 (src/estendida/99_pipeline.py) → saida/base_atual.parquet
  2. funil e desfecho por ano (src/relatorios/)                     → saida/relatorios/
  3. régua da Etapa 1 e réguas da janela segura (src/avaliacao/)    → saida/avaliacao/
  4. dataset e dicionário (src/dataset.py)                          → dataset/
  5. testes (pytest)

Uso: python rodar_tudo.py            (tudo, com testes)
     python rodar_tudo.py --sem-testes
Pré-requisito: dados/cache/ (versionado). Para o teste 03 conferir 2019–2025 com os originais, os zips
do MANIFEST em dados/origem/ (python -m src.aquisicao --origem-local PASTA ou --baixar).
"""
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PASSOS = [
    ("pipeline estendido", ["src/estendida/99_pipeline.py"]),
    ("funil", ["src/relatorios/04_funil_recorte.py"]),
    ("desfecho por ano", ["src/relatorios/05_descritivo_por_ano.py"]),
    ("régua da Etapa 1", ["src/avaliacao/01_baselines.py"]),
    ("réguas da janela segura", ["src/avaliacao/reguas.py"]),
    ("dataset", ["-m", "src.dataset"]),
]


def main():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    passos = PASSOS + ([] if "--sem-testes" in sys.argv else [("testes", ["-m", "pytest", "-q"])])
    t0 = time.time()
    for nome, args in passos:
        print(f"\n=== {nome} ===", flush=True)
        r = subprocess.run([sys.executable, *args], cwd=RAIZ, env=env, check=False)
        if r.returncode != 0:
            print(f"\n[!] {nome} falhou (código {r.returncode}). Parei aqui.")
            return r.returncode
    print(f"\nTudo regerado em {time.time() - t0:.0f} s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
