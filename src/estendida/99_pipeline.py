# -*- coding: utf-8 -*-
"""
99 — Pipeline completo: 01 → 02 → 03.

  01  rendimento por escola de RR, 2007–2025 (lê o cache dados/cache/tx_rend/; com os zips, confere a ordem)
  02  seleção das taxas e base longitudinal (lags, deltas, ANO_ALVO)
  03  grupos de colunas ligados em src/estendida/grupos/ligados.txt → saida/base_atual.parquet

O cache em dados/cache/ é somente leitura (regra 1): nenhuma etapa o regrava. Para conferir o cache contra
os zips do INEP, use src/estendida/conferir_cache.py; o cache completo do Censo só se refaz com
src/estendida/extrair_censo.py, numa pasta nova.

Uso:
    python src/estendida/99_pipeline.py               # 01 → 02 → 03
    python src/estendida/99_pipeline.py --from 03     # começa do 03
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]

ETAPAS = [
    ("01", "01_tx_rend_bruto.py"),
    ("02", "02_tx_rend_selecionado_longitudinal.py"),
    ("03", "03_grupos.py"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="from_etapa", default=None,
                        help="começa a partir desta etapa (ex: 03)")
    args = parser.parse_args()

    nomes = [e[0] for e in ETAPAS]
    if args.from_etapa and args.from_etapa not in nomes:
        print(f"[ERRO] etapa {args.from_etapa!r} não existe. Opções: {nomes}")
        return 1
    etapas = ETAPAS[nomes.index(args.from_etapa):] if args.from_etapa else ETAPAS

    print("=" * 78)
    print("PIPELINE — " + " → ".join(nomes))
    print(f"Raiz do projeto: {RAIZ}")
    if args.from_etapa:
        print(f"Começando em: {args.from_etapa}")
    print("=" * 78)

    tempo_total = time.time()
    for nome, script in etapas:
        print(f"\n{'=' * 78}\nETAPA {nome}: {script}\n{'=' * 78}")
        t0 = time.time()
        ret = subprocess.run([sys.executable, str(PASTA / script)], cwd=str(RAIZ))
        if ret.returncode != 0:
            print(f"\n[!] Etapa {nome} falhou (código {ret.returncode}). Parei aqui.")
            return ret.returncode
        print(f"\n[ok] Etapa {nome} concluída em {time.time() - t0:.1f}s")

    print(f"\n{'=' * 78}\nPIPELINE COMPLETO em {time.time() - tempo_total:.1f}s\n{'=' * 78}")
    print(f"\nBase final: {RAIZ / 'saida' / 'base_atual.parquet'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
