# -*- coding: utf-8 -*-
"""
03 — Extrai as 18 features de infraestrutura do Censo Escolar (Almeida &
Mussato, 2023) para RR, 2007-2025.

Entrada:  abandono-escolar/dados/{bruto,origem}/censo/
Saída:    gustavo/saida/etapas/03_censo_features.parquet
Cache:    gustavo/cache/censo/{ano}.parquet       (linhas de RR, colunas cruas)
          gustavo/cache/censo/{ano}_nacional.json (estatística nacional por coluna)
Relatórios: gustavo/saida/relatorios/diagnostico_features_censo.txt
            gustavo/saida/relatorios/fontes_features_censo.csv

REGRA DE FONTE (corrigida em 14/10/2026)
----------------------------------------
Cada variável tem uma lista de colunas candidatas: a PRIMEIRA é a do artigo
(Quadro 3); as demais são substitutas para anos em que a do artigo não existia
no questionário. O INEP mantém muitas colunas no layout mesmo quando a pergunta
não foi feita (tudo 0), então "a coluna existe" NÃO significa "foi coletada".
Para cada (variável, ano) usamos a primeira candidata COLETADA naquele ano, onde
coletada = pelo menos uma escola do BRASIL com valor 1 naquela coluna/ano.
Se nenhuma candidata foi coletada, o valor é NA (nunca 0).

Tipagem (regra 6 do CLAUDE.md): CO_ENTIDADE `string`, ANO `Int16`, as 18
variáveis e INFRA_FONTE_ARTIGO `Int8` nullable.

A coluna INFRA_FONTE_ARTIGO vale 1 no ano em que as 18 variáveis vieram das
colunas do próprio artigo; 0 quando alguma usou substituta ou ficou ausente.
A matriz variável × ano com a coluna usada fica em fontes_features_censo.csv.

Uso:  python programas/03_censo_features.py [--force]
"""
import argparse
import io
import json
import re
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------
# Descoberta das pastas
# ------------------------------------------------------------------


RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
BASE_PROJETO = RAIZ  # antes: a pasta abandono-escolar; os dados agora ficam em RAIZ/dados

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
DADOS = BASE_PROJETO / "dados"
CENSO_BRUTO = DADOS / "bruto" / "censo"
CENSO_ORIGEM = DADOS / "origem" / "censo"
SAIDA_ETAPAS = GUSTAVO / "saida" / "etapas"
SAIDA_REL = GUSTAVO / "saida" / "relatorios"
CACHE = GUSTAVO / "dados" / "cache" / "censo"

SAIDA_ETAPAS.mkdir(parents=True, exist_ok=True)
SAIDA_REL.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)

OUT = SAIDA_ETAPAS / "03_censo_features.parquet"
OUT_REL = SAIDA_REL / "diagnostico_features_censo.txt"
OUT_FONTES = SAIDA_REL / "fontes_features_censo.csv"

ANO_MINIMO = 2007
CHUNKSIZE = 500_000

COL_UF_CANDIDATOS = ("SG_UF", "UF", "SG_UF_ESCOLA")
CO_UF_CANDIDATOS = ("CO_UF", "COD_UF", "CODIGO_UF", "CO_UF_ESCOLA")
COL_ID_CANDIDATOS = ("CO_ENTIDADE", "COD_ESCOLA", "CO_ESCOLA")

# 18 variáveis do Almeida & Mussato (Quadro 3). Lista = candidatas em ordem de
# prioridade: [coluna do artigo, substitutas para anos antigos].
VARIAVEIS = {
    "IIB_agua_potavel":     ["IN_AGUA_POTAVEL", "IN_AGUA_FILTRADA"],
    "IIB_energia_rede":     ["IN_ENERGIA_REDE_PUBLICA"],
    "IIB_coleta_lixo":      ["IN_LIXO_SERVICO_COLETA"],
    "IIB_banheiro":         ["IN_BANHEIRO", "IN_BANHEIRO_DENTRO_PREDIO"],
    "IDA_despensa":         ["IN_DESPENSA"],
    "IDA_refeitorio":       ["IN_REFEITORIO"],
    "IDA_sala_diretoria":   ["IN_SALA_DIRETORIA"],
    "IDA_sala_professor":   ["IN_SALA_PROFESSOR"],
    "IDA_secretaria":       ["IN_SECRETARIA"],
    "IDP_biblioteca":       ["IN_BIBLIOTECA", "IN_BIBLIOTECA_SALA_LEITURA"],
    "IDP_lab_informatica":  ["IN_LABORATORIO_INFORMATICA"],
    "IDP_patio_coberto":    ["IN_PATIO_COBERTO"],
    "IDP_patio_descoberto": ["IN_PATIO_DESCOBERTO"],
    "IDP_quadra_esportes":  ["IN_QUADRA_ESPORTES"],
    "IEP_computador":       ["IN_COMPUTADOR"],
    "IEP_impressora":       ["IN_EQUIP_IMPRESSORA"],
    "IEP_projetor":         ["IN_EQUIP_MULTIMIDIA", "IN_EQUIP_RETROPROJETOR"],
    "IEP_internet":         ["IN_INTERNET"],
}


# ------------------------------------------------------------------
# Descoberta de arquivos (com deduplicação por ano)
# ------------------------------------------------------------------
def extrair_ano(nome):
    m = re.findall(r"20\d{2}|19\d{2}", nome)
    return int(m[0]) if m else None


def listar_arquivos():
    candidatos = []
    if CENSO_BRUTO.exists():
        for f in sorted(CENSO_BRUTO.iterdir()):
            if f.is_file() and f.suffix.lower() == ".csv":
                ano = extrair_ano(f.name)
                if ano and ano >= ANO_MINIMO:
                    candidatos.append((ano, f, "ext", "escola" in f.name.lower()))
    if CENSO_ORIGEM.exists():
        for f in sorted(CENSO_ORIGEM.glob("*.zip")):
            ano = extrair_ano(f.name)
            if ano and ano >= ANO_MINIMO:
                candidatos.append((ano, f, "zip", "escola" in f.name.lower()))

    por_ano = {}
    for ano, path, tipo, tem_escola in candidatos:
        por_ano.setdefault(ano, []).append((tipo, path, tem_escola))

    resultado = []
    for ano in sorted(por_ano):
        lista = por_ano[ano]
        com_escola = [x for x in lista if x[2]]
        if com_escola:
            lista = com_escola
        exts = [x for x in lista if x[0] == "ext"]
        if exts:
            lista = exts
        escolhido = max(lista, key=lambda x: x[1].stat().st_size)
        resultado.append((ano, escolhido[1], escolhido[0]))
    return resultado


def abrir_fonte(arquivo, tipo):
    if tipo == "zip":
        try:
            zf = zipfile.ZipFile(arquivo)
        except Exception:
            return None, None
        csvs = [i for i in zf.infolist()
                if i.filename.lower().endswith(".csv")]
        if not csvs:
            zf.close()
            return None, None
        maior = max(csvs, key=lambda i: i.file_size)
        conteudo = zf.read(maior.filename)
        zf.close()
        return io.BytesIO(conteudo), maior.filename
    return arquivo, arquivo.name


def ler_cabecalho(fonte):
    for sep in (";", ",", "|"):
        try:
            if hasattr(fonte, "seek"):
                fonte.seek(0)
            cols = list(pd.read_csv(fonte, sep=sep, encoding="latin1",
                                    nrows=0).columns)
            if len(cols) >= 5:
                return cols, sep
        except Exception:
            continue
    return [], None


def detectar_coluna_uf(cols):
    for c in cols:
        if c.upper() in [x.upper() for x in COL_UF_CANDIDATOS]:
            return c, "sigla"
    for c in cols:
        if c.upper() in [x.upper() for x in CO_UF_CANDIDATOS]:
            return c, "codigo"
    return None, None


def detectar_coluna_id(cols):
    for c in cols:
        if c.upper() in [x.upper() for x in COL_ID_CANDIDATOS]:
            return c
    return None


# ------------------------------------------------------------------
# Processar 1 ano  -> cache cru (RR) + estatística nacional por coluna
# ------------------------------------------------------------------
CANDIDATAS = sorted({c for lista in VARIAVEIS.values() for c in lista})


def processar_ano(ano, arquivo, tipo, force=False):
    cache_path = CACHE / f"{ano}.parquet"
    stats_path = CACHE / f"{ano}_nacional.json"
    if not force and cache_path.exists() and stats_path.exists():
        try:
            cru = pd.read_parquet(cache_path)
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
            return ano, cru, stats, f"[cache] {ano}"
        except Exception:
            pass

    fonte, _ = abrir_fonte(arquivo, tipo)
    cols, sep = ler_cabecalho(fonte)
    if not cols:
        return ano, None, None, f"{ano}: cabeçalho ilegível"
    col_uf, modo_uf = detectar_coluna_uf(cols)
    col_id = detectar_coluna_id(cols)
    if col_uf is None or col_id is None:
        return ano, None, None, f"{ano}: sem coluna UF/ID"

    cols_up = {c.upper().strip(): c for c in cols}
    presentes = {c: cols_up[c] for c in CANDIDATAS if c in cols_up}
    if not presentes:
        return ano, None, None, f"{ano}: nenhuma candidata presente"

    usecols = sorted(set(presentes.values()) | {col_uf, col_id})
    fonte, _ = abrir_fonte(arquivo, tipo)
    stats = {"_n_brasil": 0}
    for c in presentes:
        stats[c] = {"nao_nulo": 0, "uns": 0}
    partes = []
    try:
        for chunk in pd.read_csv(fonte, sep=sep, encoding="latin1",
                                 usecols=usecols, chunksize=300_000,
                                 low_memory=False):
            stats["_n_brasil"] += len(chunk)
            for c, real in presentes.items():
                s = pd.to_numeric(chunk[real], errors="coerce")
                stats[c]["nao_nulo"] += int(s.notna().sum())
                stats[c]["uns"] += int((s == 1).sum())
            if modo_uf == "sigla":
                mask = chunk[col_uf].astype(str).str.upper().str.strip() == "RR"
            else:
                mask = pd.to_numeric(chunk[col_uf], errors="coerce") == 14
            if mask.any():
                partes.append(chunk[mask])
    except Exception as e:
        return ano, None, None, f"{ano}: falha lendo dados ({e})"

    if not partes:
        return ano, None, None, f"{ano}: nenhuma linha RR"

    df = pd.concat(partes, ignore_index=True)
    cru = pd.DataFrame({"ANO": ano,
                        "CO_ENTIDADE": df[col_id].astype(str).str.strip()})
    for c, real in presentes.items():
        cru[c] = pd.to_numeric(df[real], errors="coerce")
    cru.to_parquet(cache_path, index=False)
    stats_path.write_text(json.dumps(stats), encoding="utf-8")
    return ano, cru, stats, f"{ano}: n_RR={len(cru)} n_BR={stats['_n_brasil']}"


def escolher_fonte(candidatas, stats):
    """Primeira candidata coletada no ano (>=1 escola do Brasil com valor 1)."""
    for cand in candidatas:
        st = stats.get(cand)
        if st and st["uns"] > 0:
            return cand
    return None


def montar_ano(ano, cru, stats):
    out = pd.DataFrame({
        "ANO": pd.Series(ano, index=cru.index, dtype="Int16"),
        "CO_ENTIDADE": cru["CO_ENTIDADE"].astype("string"),
    })
    fontes, todas_artigo = [], True
    n_br = max(stats["_n_brasil"], 1)
    for var, lista in VARIAVEIS.items():
        usada = escolher_fonte(lista, stats)
        if usada is None:
            out[var] = pd.Series(pd.NA, index=cru.index, dtype="Int8")
            todas_artigo = False
        else:
            out[var] = pd.to_numeric(cru[usada], errors="coerce").astype("Int8").values
            if usada != lista[0]:
                todas_artigo = False
        fontes.append({
            "ano": ano, "variavel": var, "coluna_artigo": lista[0],
            "coluna_usada": usada or "",
            "pct_um_brasil": round(stats[usada]["uns"] / n_br * 100, 2)
                             if usada else np.nan,
        })
    out["INFRA_FONTE_ARTIGO"] = pd.Series(1 if todas_artigo else 0, index=cru.index, dtype="Int8")
    return out, fontes


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    print("=" * 78)
    print("03 — CENSO FEATURES (18 do Almeida & Mussato) — RR 2007-2025")
    print(f"BASE_PROJETO: {BASE_PROJETO}")
    print(f"Cache:        {CACHE}")
    if args.force:
        print("Modo: --force (ignora cache)")
    print("=" * 78)

    arquivos = listar_arquivos()
    print(f"Arquivos: {len(arquivos)}\n")
    # Anos sem arquivo bruto entram pelo cache (se houver); --force não os apaga.
    com_arquivo = {a for a, _, _ in arquivos}
    for p in sorted(CACHE.glob("*.parquet")):
        if (p.stem.isdigit() and int(p.stem) >= ANO_MINIMO
                and int(p.stem) not in com_arquivo
                and (CACHE / f"{p.stem}_nacional.json").exists()):
            arquivos.append((int(p.stem), None, "cache"))
    arquivos.sort(key=lambda x: x[0])

    # Sequencial de propósito: cada ano carrega o CSV nacional em memória
    # (2010 estourava memória com 4 threads).
    partes, fontes = [], []
    for a, f, t in arquivos:
        ano, cru, stats, msg = processar_ano(a, f, t, args.force and f is not None)
        print(f"  {msg}", flush=True)
        if cru is None:
            continue
        df_ano, fnt = montar_ano(ano, cru, stats)
        partes.append(df_ano)
        fontes += fnt

    if not partes:
        print("[!] Nada processado.")
        return

    censo = pd.concat(partes, ignore_index=True)
    print(f"\n>>> Censo features: {censo.shape[0]} linhas × "
          f"{censo.shape[1]} colunas")
    censo.to_parquet(OUT, index=False)
    print(f">>> {OUT}")

    fontes_df = pd.DataFrame(fontes)
    fontes_df.to_csv(OUT_FONTES, index=False, encoding="utf-8")
    print(f">>> {OUT_FONTES}")

    vars18 = list(VARIAVEIS.keys())
    linhas = [
        "FEATURES DO CENSO — RR 2007-2025",
        "=" * 70,
        f"Linhas: {censo.shape[0]}   Colunas: {censo.shape[1]}",
        "",
        "Colunas (18 variáveis + INFRA_FONTE_ARTIGO):",
    ] + [f"  - {v}" for v in vars18] + [
        "  - INFRA_FONTE_ARTIGO (1 = as 18 vieram das colunas do artigo)",
        "",
        "Por ano: n escolas RR | variáveis ausentes (nenhuma candidata coletada) |",
        "variáveis com coluna substituta | cobertura das 18 | fonte = artigo?",
        f"{'ano':>5}{'n':>6}{'ausentes':>10}{'substitutas':>13}"
        f"{'cobertura%':>12}{'artigo':>8}",
    ]
    for ano in sorted(censo["ANO"].unique()):
        sub = censo[censo["ANO"] == ano]
        fa = fontes_df[fontes_df["ano"] == ano]
        aus = int((fa["coluna_usada"] == "").sum())
        subst = int(((fa["coluna_usada"] != "") &
                     (fa["coluna_usada"] != fa["coluna_artigo"])).sum())
        cob = round(sub[vars18].notna().mean().mean() * 100, 1)
        linhas.append(f"{ano:>5}{len(sub):>6}{aus:>10}{subst:>13}"
                      f"{cob:>12}{int(sub['INFRA_FONTE_ARTIGO'].iloc[0]):>8}")
    linhas += [
        "",
        "Variáveis ausentes por ano (nunca coletadas naquele ano no Brasil):",
    ]
    for ano in sorted(censo["ANO"].unique()):
        fa = fontes_df[(fontes_df["ano"] == ano) & (fontes_df["coluna_usada"] == "")]
        if len(fa):
            linhas.append(f"  {ano}: " + ", ".join(fa["variavel"]))
    linhas += [
        "",
        "Variáveis com coluna substituta (não é a coluna do artigo):",
    ]
    for ano in sorted(censo["ANO"].unique()):
        fa = fontes_df[(fontes_df["ano"] == ano) & (fontes_df["coluna_usada"] != "") &
                       (fontes_df["coluna_usada"] != fontes_df["coluna_artigo"])]
        if len(fa):
            linhas.append(f"  {ano}: " + ", ".join(
                f"{r.variavel}<-{r.coluna_usada}" for r in fa.itertuples()))
    OUT_REL.write_text("\n".join(linhas), encoding="utf-8")
    print(f">>> Relatório: {OUT_REL}")


if __name__ == "__main__":
    main()
