# -*- coding: utf-8 -*-
"""
Conferência do cache versionado contra os zips originais do INEP.

Para cada ano com zip em dados/origem/, refaz o cache das etapas 01 (tx_rend por escola) e 03 (Censo:
colunas cruas de RR e estatística nacional) numa pasta temporária, com as mesmas funções do pipeline,
e compara com dados/cache/ célula a célula. Nunca escreve em dados/cache/ (regra 1).

É a conferência que faltava para 2007–2018 (dataset/DICIONARIO.md, "Ressalva sobre a procedência"):
o teste 03 (--completo) confere a base pós-04 contra o Censo, mas não o rendimento.

Saída: saida/relatorios/conferencia_cache.csv (ano, etapa, status, detalhe).
Status: identico | diverge | sem_zip | erro. Sai com código 1 se algum ano diverge ou dá erro.

Uso:  python src/estendida/conferir_cache.py [--anos 2007-2018]
"""
import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
CACHE_TX = RAIZ / "dados" / "cache" / "tx_rend"
CACHE_CENSO = RAIZ / "dados" / "cache" / "censo"
SAIDA = RAIZ / "saida" / "relatorios" / "conferencia_cache.csv"


def carregar(nome_arquivo):
    """Importa um script do pipeline pelo caminho (o nome começa com dígito)."""
    spec = importlib.util.spec_from_file_location(Path(nome_arquivo).stem.replace("-", "_"), PASTA / nome_arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def diferencas(novo: pd.DataFrame, versionado: pd.DataFrame) -> str:
    """'' se idênticos (valores, tipos, ordem); senão um resumo do que difere."""
    if list(novo.columns) != list(versionado.columns):
        so_novo = sorted(set(novo.columns) - set(versionado.columns))
        so_vers = sorted(set(versionado.columns) - set(novo.columns))
        return f"colunas diferentes: só no zip {so_novo[:5]}, só no cache {so_vers[:5]}"
    if novo.shape != versionado.shape:
        return f"forma {novo.shape} no zip × {versionado.shape} no cache"
    tipos = [c for c in novo.columns if novo[c].dtype != versionado[c].dtype]
    if tipos:
        return f"tipos diferentes em {tipos[:5]}"
    cols = []
    for c in novo.columns:
        a, b = novo[c], versionado[c]
        iguais = (a == b) | (a.isna() & b.isna())
        if not bool(iguais.fillna(False).all()):
            cols.append(f"{c} ({int((~iguais.fillna(False)).sum())})")
    return f"células diferentes em {cols[:8]}" if cols else ""


def conferir(anos, etapa01=None, etapa03=None, cache_tx=CACHE_TX, cache_censo=CACHE_CENSO):
    """Tabela (ano, etapa, status, detalhe). Os módulos e as pastas do cache versionado podem ser
    trocados nos testes; o cache refeito vai sempre para uma pasta temporária."""
    etapa01 = etapa01 or carregar("01_tx_rend_bruto.py")
    etapa03 = etapa03 or carregar("03_censo_features.py")
    zips_tx = etapa01.mapear_zips_escola()
    fontes_censo = {a: (f, t) for a, f, t in etapa03.listar_arquivos()}
    linhas = []
    with tempfile.TemporaryDirectory() as tmp:
        etapa01.CACHE = Path(tmp) / "tx_rend"
        etapa03.CACHE = Path(tmp) / "censo"
        etapa01.CACHE.mkdir()
        etapa03.CACHE.mkdir()
        for ano in sorted(anos):
            # 01 — rendimento por escola
            if ano not in zips_tx:
                linhas.append((ano, "01_tx_rend", "sem_zip", ""))
            else:
                try:
                    _, df, msg, erro = etapa01.processar_ano(ano, zips_tx[ano], force=True)
                    if df is None or erro:
                        linhas.append((ano, "01_tx_rend", "erro", msg))
                    else:
                        novo = pd.read_parquet(etapa01.CACHE / f"{ano}.parquet")
                        d = diferencas(novo, pd.read_parquet(cache_tx / f"{ano}.parquet"))
                        linhas.append((ano, "01_tx_rend", "diverge" if d else "identico",
                                       d or f"{len(novo)} linhas, zip {zips_tx[ano].name}"))
                except Exception as e:  # noqa: BLE001 — o relatório registra e segue para o próximo ano
                    linhas.append((ano, "01_tx_rend", "erro", repr(e)))
            # 03 — Censo (colunas cruas de RR + estatística nacional)
            if ano not in fontes_censo:
                linhas.append((ano, "03_censo", "sem_zip", ""))
            else:
                arquivo, tipo = fontes_censo[ano]
                try:
                    _, cru, stats, msg = etapa03.processar_ano(ano, arquivo, tipo, force=True)
                    if cru is None:
                        linhas.append((ano, "03_censo", "erro", msg))
                    else:
                        novo = pd.read_parquet(etapa03.CACHE / f"{ano}.parquet")
                        d = diferencas(novo, pd.read_parquet(cache_censo / f"{ano}.parquet"))
                        vers = json.loads((cache_censo / f"{ano}_nacional.json").read_text(encoding="utf-8"))
                        if stats != vers:
                            d = (d + "; " if d else "") + "estatística nacional diferente"
                        linhas.append((ano, "03_censo", "diverge" if d else "identico",
                                       d or f"{len(novo)} linhas RR, {stats['_n_brasil']} no Brasil, {arquivo.name}"))
                except Exception as e:  # noqa: BLE001
                    linhas.append((ano, "03_censo", "erro", repr(e)))
            print(f"  {ano}: " + " | ".join(f"{e} {s}" for a, e, s, _ in linhas if a == ano), flush=True)
    return pd.DataFrame(linhas, columns=["ano", "etapa", "status", "detalhe"])


def main(argv=None):
    sys.path.insert(0, str(RAIZ))
    from src.aquisicao import parse_anos

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--anos", default="2007-2025", help="ex.: 2007-2018 (padrão: 2007-2025)")
    args = ap.parse_args(argv)
    print("=" * 78)
    print("CONFERÊNCIA DO CACHE CONTRA OS ZIPS DO INEP")
    print("=" * 78)
    r = conferir(parse_anos(args.anos))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    r.to_csv(SAIDA, index=False)
    print()
    print(r.groupby(["etapa", "status"]).size().unstack(fill_value=0).to_string())
    print(f"\n>>> {SAIDA}")
    ruins = r[r["status"].isin(["diverge", "erro"])]
    if not ruins.empty:
        print("\n[!] divergências ou erros:\n" + ruins.to_string(index=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
