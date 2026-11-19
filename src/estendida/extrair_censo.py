# -*- coding: utf-8 -*-
"""
Extração única do Censo Escolar de Roraima, 2007–2025: TODAS as colunas de TODAS as tabelas de cada zip.

Fica fora do fluxo normal (rodar_tudo.py não chama): precisa dos zips de dados/origem/censo/ e escreve em
dados/cache/, que é somente leitura (regra 1). Roda uma vez, quando o grupo aprova, e o que ela grava entra
no dados/MANIFEST.csv com sha256. Depois disso, o pipeline só LÊ este cache; quem precisar de uma coluna nova
do Censo não volta aos zips (docs/DECISOES.md, 2026-11-19).

O cache antigo de 22 colunas (dados/cache/censo/, do 03_censo_features.py) continua onde está e não muda:
os resultados já publicados dependem dele. testes/test_cache_censo_completo.py confere que este cache tem
exatamente os mesmos valores nas 22 colunas.

O que grava, em dados/cache/censo_completo/ (nome-base único por arquivo, como o manifesto exige):
  {ano}_{tabela}.parquet          as linhas de RR (SG_UF == "RR") com todas as colunas, como TEXTO,
                                  exatamente como estão no CSV do INEP (sem converter, sem trocar '' ou
                                  '--' por ausente, sem renomear). Converter é papel de quem usa.
  {ano}_{tabela}_nacional.csv     por coluna, contagens no BRASIL inteiro, para a regra de "coletada"
                                  (o INEP mantém colunas no layout mesmo sem a pergunta):
                                  n_linhas, n_preenchido (texto não vazio), n_numerico (vira número),
                                  n_um (== 1), n_positivo (> 0)

{tabela}: "escola" é a tabela principal (o maior CSV do zip, a mesma regra do 03); as outras recebem o nome
do arquivo sem prefixo, ano e versão (2023–2024: suplemento_cursos_tecnicos; 2025: matricula, turma, docente,
gestor_escolar, curso_tecnico).

Cada zip é conferido contra o sha256 do dados/MANIFEST.csv antes de ser lido; divergência é erro (regra 1).
Recusa gravar numa pasta que já existe: para refazer e comparar, use --destino com uma pasta nova.

Uso:  python src/estendida/extrair_censo.py                         (grava dados/cache/censo_completo/
                                                                     e acrescenta as linhas ao manifesto)
      python src/estendida/extrair_censo.py --destino PASTA_NOVA    (só grava em PASTA_NOVA)
      python src/estendida/extrair_censo.py --anos 2013-2018 --destino PASTA_NOVA
"""
import argparse
import csv
import datetime as dt
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from src.aquisicao import linhas_manifesto, parse_anos  # noqa: E402
from src.integridade import sha256_arquivo  # noqa: E402

DADOS = RAIZ / "dados"
MANIFEST = DADOS / "MANIFEST.csv"
DESTINO_PADRAO = DADOS / "cache" / "censo_completo"
CHUNK = 200_000
ESTATISTICAS = ["n_linhas", "n_preenchido", "n_numerico", "n_um", "n_positivo"]


def nome_tabela(nome_csv: str, principal: bool) -> str:
    """'Tabela_Matricula_2025_V2.csv' -> 'matricula'; a principal é sempre 'escola'."""
    if principal:
        return "escola"
    base = Path(nome_csv).stem.lower()
    base = re.sub(r"^tabela_", "", base)
    base = re.sub(r"_(19|20)\d{2}(_v\d+)?$", "", base)
    return base


def zips_do_manifesto(anos=None):
    """[(ano, caminho, sha256 esperado)] dos microdados do Censo registrados no manifesto."""
    out = []
    for lin in linhas_manifesto(MANIFEST):
        if lin["estagio"] == "origem" and lin["tabela"] == "microdados":
            ano = int(lin["ano"])
            if anos is None or ano in anos:
                out.append((ano, DADOS / lin["arquivo"], lin["sha256"]))
    return sorted(out)


def separador(zf, info):
    with zf.open(info) as f:
        linha = io.TextIOWrapper(f, encoding="latin1", newline="").readline()
    for sep in (";", ",", "|"):
        if len(linha.split(sep)) >= 5:
            return sep
    raise ValueError(f"{info.filename}: separador não reconhecido")


def ler_tabela(zf, info):
    """(linhas de RR como texto, DataFrame de contagens nacionais por coluna)."""
    sep = separador(zf, info)
    partes, cont, colunas = [], None, None
    with zf.open(info) as f:
        for chunk in pd.read_csv(f, sep=sep, encoding="latin1", dtype=str, keep_default_na=False,
                                 na_filter=False, chunksize=CHUNK):
            if colunas is None:
                colunas = list(chunk.columns)
                cont = {c: [0, 0, 0, 0, 0] for c in colunas}
            for c in colunas:
                s = chunk[c]
                num = pd.to_numeric(s, errors="coerce")
                t = cont[c]
                t[0] += len(s)
                t[1] += int((s.str.strip() != "").sum())
                t[2] += int(num.notna().sum())
                t[3] += int((num == 1).sum())
                t[4] += int((num > 0).sum())
            partes.append(chunk[chunk["SG_UF"].str.strip().str.upper() == "RR"])
    rr = pd.concat(partes, ignore_index=True).astype("string")
    stats = pd.DataFrame([[c, *cont[c]] for c in colunas], columns=["coluna", *ESTATISTICAS])
    return rr, stats


def extrair_ano(ano, zip_path, destino):
    """Grava as tabelas do ano em `destino`. Devolve [(arquivo gravado, n linhas RR, n linhas Brasil)]."""
    gravados = []
    with zipfile.ZipFile(zip_path) as zf:
        csvs = [i for i in zf.infolist() if i.filename.lower().endswith(".csv")]
        maior = max(csvs, key=lambda i: i.file_size)
        for info in sorted(csvs, key=lambda i: i is not maior):  # a principal primeiro
            tabela = nome_tabela(info.filename, info is maior)
            rr, stats = ler_tabela(zf, info)
            p_rr = destino / f"{ano}_{tabela}.parquet"
            p_st = destino / f"{ano}_{tabela}_nacional.csv"
            for p in (p_rr, p_st):
                if p.exists():
                    raise FileExistsError(f"{p} já existe (nome de tabela repetido no zip?)")
            rr.to_parquet(p_rr, index=False)
            stats.to_csv(p_st, index=False, lineterminator="\n", encoding="utf-8")
            n_br = int(stats["n_linhas"].iloc[0]) if len(stats) else 0
            print(f"  {ano} {tabela:<28} {len(rr):>6} linhas RR  {n_br:>9} no Brasil  {rr.shape[1]} colunas",
                  flush=True)
            gravados += [p_rr, p_st]
    return gravados


def acrescentar_ao_manifesto(arquivos):
    hoje = dt.date.today().isoformat()
    with open(MANIFEST, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        for p in arquivos:
            ano = p.name.split("_", 1)[0]
            w.writerow(["cache", "gustavo", ano, "cache_censo_completo",
                        p.relative_to(DADOS).as_posix(), sha256_arquivo(p), hoje])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--anos", default="2007-2025", help="ex.: 2013-2018 (padrão: 2007-2025)")
    ap.add_argument("--destino", type=Path, default=DESTINO_PADRAO,
                    help="pasta nova onde gravar (padrão: dados/cache/censo_completo/, e registra no manifesto)")
    args = ap.parse_args(argv)
    destino = args.destino.resolve()
    no_cache = destino == DESTINO_PADRAO.resolve()

    if destino.exists():
        print(f"[!] {destino} já existe. dados/cache/ é somente leitura (regra 1); para refazer e comparar, "
              f"use --destino com uma pasta nova.")
        return 1
    zips = zips_do_manifesto(parse_anos(args.anos))
    faltam = [z for _, z, _ in zips if not z.exists()]
    if faltam:
        print("[!] Zips do manifesto ausentes em dados/origem/censo/ (python -m src.aquisicao --origem-local "
              "PASTA):\n  " + "\n  ".join(p.name for p in faltam))
        return 1
    for ano, z, esperado in zips:
        if sha256_arquivo(z) != esperado:
            print(f"[!] sha256 de {z.name} diverge do manifesto. Nada foi gravado.")
            return 1

    print(f"Extraindo {len(zips)} ano(s) para {destino}")
    temporaria = destino.with_name(destino.name + ".parcial")
    if temporaria.exists():
        print(f"[!] {temporaria} sobrou de uma execução interrompida; apague-a e rode de novo.")
        return 1
    temporaria.mkdir(parents=True)
    gravados = []
    for ano, z, _ in zips:
        gravados += extrair_ano(ano, z, temporaria)
    temporaria.rename(destino)   # só aparece em dados/cache/ se todos os anos deram certo
    gravados = [destino / p.name for p in gravados]
    print(f"\n{len(gravados)} arquivos em {destino}")
    if no_cache:
        acrescentar_ao_manifesto(gravados)
        print(f"{len(gravados)} linhas acrescentadas a {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
