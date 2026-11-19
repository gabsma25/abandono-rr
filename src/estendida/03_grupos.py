# -*- coding: utf-8 -*-
"""
03 — Acrescenta à base longitudinal os grupos de colunas ligados.

Entrada:  saida/etapas/02b_tx_rend_longitudinal.parquet
          src/estendida/grupos/ligados.txt          (lista versionada dos grupos, na ordem de entrada)
          src/estendida/grupos/<nome>.py            (contrato em src/estendida/grupos/README.md)
Saída:    saida/etapas/03_grupo_<nome>.parquet       (o que extrair() de cada grupo devolveu)
          saida/etapas/03_base_com_grupos.parquet    (base longitudinal + grupos)
          saida/base_atual.parquet                   (cópia deste)
          saida/relatorios/grupos.txt                (colunas e cobertura de cada grupo, por ano)

Para cada grupo: extrai a tabela (ANO, CO_ENTIDADE, colunas), junta com how="left" a partir da base e
validate="1:1" (regra 9), e acrescenta as derivadas, se o grupo tiver. Para com erro se um grupo quebrar o
contrato: chave repetida, colunas diferentes das declaradas, nome de coluna repetido, linha a mais ou a menos.

Substitui o 03_censo_features.py, o 04_merge_features.py e o 05_indices_infra.py, que viraram o grupo
infraestrutura (docs/DECISOES.md, 2026-11-19).

Uso:  python src/estendida/03_grupos.py
"""
import importlib.util
import shutil
import sys
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
GRUPOS = PASTA / "grupos"
LIGADOS = GRUPOS / "ligados.txt"
SAIDA_ETAPAS = RAIZ / "saida" / "etapas"
SAIDA_REL = RAIZ / "saida" / "relatorios"
IN_LONG = SAIDA_ETAPAS / "02b_tx_rend_longitudinal.parquet"
OUT = SAIDA_ETAPAS / "03_base_com_grupos.parquet"
SAIDA_BASE = RAIZ / "saida" / "base_atual.parquet"
OUT_REL = SAIDA_REL / "grupos.txt"

CHAVE = ["ANO", "CO_ENTIDADE"]


class ErroGrupo(Exception):
    pass


def ler_ligados(caminho=LIGADOS):
    nomes = [lin.strip() for lin in caminho.read_text(encoding="utf-8").splitlines()]
    nomes = [n for n in nomes if n and not n.startswith("#")]
    if len(nomes) != len(set(nomes)):
        raise ErroGrupo(f"grupo repetido em {caminho.name}: {nomes}")
    return nomes


def carregar(nome, pasta=GRUPOS):
    caminho = pasta / f"{nome}.py"
    if not caminho.exists():
        raise ErroGrupo(f"{nome!r} está em ligados.txt, mas não existe {caminho}")
    spec = importlib.util.spec_from_file_location(f"grupo_{nome}", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if getattr(mod, "NOME", None) != nome:
        raise ErroGrupo(f"{caminho.name}: NOME deve ser {nome!r}")
    for attr in ("COLUNAS", "extrair"):
        if not hasattr(mod, attr):
            raise ErroGrupo(f"{caminho.name}: falta {attr}")
    if hasattr(mod, "derivar") != hasattr(mod, "DERIVADAS"):
        raise ErroGrupo(f"{caminho.name}: derivar e DERIVADAS vêm juntos")
    return mod


def normalizar_chave(df):
    """A mesma normalização do antigo 04: CO_ENTIDADE como texto sem espaços, tipo string."""
    df = df.copy()
    df["CO_ENTIDADE"] = df["CO_ENTIDADE"].astype(str).str.strip().astype("string")
    return df


def acrescentar(base, grupo, relatorios):
    """Base + colunas do grupo (+ derivadas). Confere o contrato; nunca muda o que a base já tinha."""
    nome, colunas = grupo.NOME, list(grupo.COLUNAS)
    derivadas = list(getattr(grupo, "DERIVADAS", []))
    novas_nomes = colunas + derivadas
    repetidas = sorted(set(novas_nomes) & set(base.columns)) + sorted(
        c for c in set(novas_nomes) if novas_nomes.count(c) > 1)
    if repetidas or set(CHAVE) & set(novas_nomes):
        raise ErroGrupo(f"{nome}: nome de coluna repetido {repetidas or sorted(set(CHAVE) & set(novas_nomes))}")

    tab = grupo.extrair(relatorios)
    if list(tab.columns) != CHAVE + colunas:
        raise ErroGrupo(f"{nome}: extrair() devolveu {list(tab.columns)}, esperado {CHAVE + colunas}")
    tab = normalizar_chave(tab)
    if tab.duplicated(CHAVE).any():
        raise ErroGrupo(f"{nome}: chave (ANO, CO_ENTIDADE) repetida em {int(tab.duplicated(CHAVE).sum())} linhas")

    n = len(base)
    saida = base.merge(tab, on=CHAVE, how="left", validate="1:1")
    if len(saida) != n:
        raise ErroGrupo(f"{nome}: a junção mudou o número de linhas ({n} → {len(saida)})")

    if derivadas:
        novas = grupo.derivar(saida[["ANO"] + colunas].copy(), relatorios)
        if list(novas.columns) != derivadas or not novas.index.equals(saida.index):
            raise ErroGrupo(f"{nome}: derivar() devolveu {list(novas.columns)}, esperado {derivadas} no índice da base")
        saida = pd.concat([saida, novas], axis=1)
    return saida, tab


def main():
    print("=" * 78)
    print("03 — GRUPOS DE COLUNAS")
    print("=" * 78)
    if not IN_LONG.exists():
        print(f"[ERRO] não achei {IN_LONG} — rode o 02 antes")
        return 1
    SAIDA_REL.mkdir(parents=True, exist_ok=True)
    nomes = ler_ligados()
    print(f"Grupos ligados ({LIGADOS.relative_to(RAIZ).as_posix()}): {', '.join(nomes) or '(nenhum)'}")

    base = normalizar_chave(pd.read_parquet(IN_LONG))
    print(f"longitudinal: {base.shape[0]} × {base.shape[1]}")
    linhas = ["GRUPOS DE COLUNAS — 03", "=" * 70, f"longitudinal: {base.shape[0]} × {base.shape[1]}",
              f"grupos ligados: {', '.join(nomes) or '(nenhum)'}"]
    for nome in nomes:
        print(f"\n--- grupo {nome}")
        grupo = carregar(nome)
        antes = base.shape[1]
        base, tab = acrescentar(base, grupo, SAIDA_REL)
        tab.to_parquet(SAIDA_ETAPAS / f"03_grupo_{nome}.parquet", index=False)
        cols = list(base.columns[antes:])
        print(f"  +{len(cols)} colunas → base {base.shape[0]} × {base.shape[1]}")
        linhas += ["", f"Grupo {nome}: +{len(cols)} colunas ({len(grupo.COLUNAS)} extraídas, "
                       f"{len(cols) - len(grupo.COLUNAS)} derivadas); extrair() devolveu {len(tab)} linhas",
                   f"{'ano':>5}{'n':>7}{'cobertura_media%':>18}"]
        for ano in sorted(base["ANO"].unique()):
            sub = base[base["ANO"] == ano]
            linhas.append(f"{ano:>5}{len(sub):>7}{round(sub[cols].notna().mean().mean() * 100, 1):>18}")

    base.to_parquet(OUT, index=False)
    shutil.copy2(OUT, SAIDA_BASE)
    OUT_REL.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\n>>> {OUT}  ({base.shape[0]} × {base.shape[1]})")
    print(f">>> {SAIDA_BASE} (cópia)")
    print(f">>> {OUT_REL}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ErroGrupo as e:
        print(f"[ERRO] {e}")
        sys.exit(1)
