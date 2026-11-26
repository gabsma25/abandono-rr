# -*- coding: utf-8 -*-
"""
Conferência do cache versionado contra os zips originais do INEP.

Para cada ano com zip em dados/origem/, refaz numa pasta temporária, com as mesmas funções que o gravaram,
o cache do rendimento por escola (etapa 01, dados/cache/tx_rend/) e o cache completo do Censo
(src/estendida/extrair_censo.py, dados/cache/censo_completo/: todas as tabelas do ano e as contagens
nacionais), e compara com dados/cache/ célula a célula. Nunca escreve em dados/cache/ (regra 1).

O cache antigo de 22 colunas (dados/cache/censo/) não é mais lido pelo pipeline; ele é conferido contra o
completo por testes/test_cache_censo_completo.py (docs/DECISOES.md, 2026-11-19).

É a conferência que faltava para 2007–2018 (dataset/DICIONARIO.md, "Ressalva sobre a procedência"):
o teste 03 (--completo) confere a base pós-04 contra o Censo, mas não o rendimento.

Saída: saida/relatorios/conferencia_cache.csv (ano, etapa, status, detalhe).
Status: identico | diverge | sem_zip | erro. Sai com código 1 se algum ano diverge ou dá erro.

Uso:  python src/estendida/conferir_cache.py [--anos 2007-2018]
"""
import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
CACHE_TX = RAIZ / "dados" / "cache" / "tx_rend"
CACHE_CENSO = RAIZ / "dados" / "cache" / "censo_completo"
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


def conferir(anos, etapa01=None, extrator=None, zips_censo=None, cache_tx=CACHE_TX, cache_censo=CACHE_CENSO):
    """Tabela (ano, etapa, status, detalhe). Os módulos, os zips do Censo e as pastas do cache versionado
    podem ser trocados nos testes; o cache refeito vai sempre para uma pasta temporária."""
    etapa01 = etapa01 or carregar("01_tx_rend_bruto.py")
    extrator = extrator or carregar("extrair_censo.py")
    zips_tx = etapa01.mapear_zips_escola()
    if zips_censo is None:
        zips_censo = {a: z for a, z, _ in extrator.zips_do_manifesto() if z.exists()}
    linhas = []
    with tempfile.TemporaryDirectory() as tmp:
        etapa01.CACHE = Path(tmp) / "tx_rend"
        etapa01.CACHE.mkdir()
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
            # Censo completo — todas as tabelas do ano e as contagens nacionais
            if ano not in zips_censo:
                linhas.append((ano, "censo_completo", "sem_zip", ""))
            else:
                try:
                    pasta = Path(tmp) / f"censo_{ano}"
                    pasta.mkdir()
                    gravados = extrator.extrair_ano(ano, zips_censo[ano], pasta)
                    nomes = sorted(p.name for p in gravados)
                    versionados = sorted(p.name for p in cache_censo.glob(f"{ano}_*"))
                    if nomes != versionados:
                        d = f"arquivos diferentes: zip {nomes}, cache {versionados}"
                    else:
                        difs = []
                        for nome in nomes:
                            if nome.endswith(".parquet"):
                                x = diferencas(pd.read_parquet(pasta / nome), pd.read_parquet(cache_censo / nome))
                            else:
                                x = "" if (pasta / nome).read_bytes() == (cache_censo / nome).read_bytes()                                     else "contagens nacionais diferentes"
                            if x:
                                difs.append(f"{nome}: {x}")
                        d = "; ".join(difs)
                    linhas.append((ano, "censo_completo", "diverge" if d else "identico",
                                   d or f"{len(nomes) // 2} tabela(s), zip {zips_censo[ano].name}"))
                except Exception as e:  # noqa: BLE001
                    linhas.append((ano, "censo_completo", "erro", repr(e)))
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
