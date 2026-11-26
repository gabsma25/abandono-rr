# -*- coding: utf-8 -*-
"""
Levantamento das colunas do Censo Escolar, 2007–2025 (início das metas M1/M6).

Só lê CABEÇALHOS: para cada zip de dados/origem/censo/, abre cada CSV do zip e lê só a primeira linha (sem
descompactar o arquivo inteiro). Não lê nenhum valor, não lê o rendimento nem o dataset, então não olha o
desfecho (regra 7). Não escreve fora de experimentos/levantamento_colunas_censo/saida/.

A tabela "principal" de cada ano é o MAIOR CSV do zip, a mesma regra do src/estendida/03_censo_features.py
(abrir_fonte). Em 2007–2024 o zip tem um único CSV (microdados_ed_basica_AAAA.csv); em 2025 há várias tabelas
(Escola, Matrícula, Turma, Docente...), e as outras também são listadas.

Saídas (saida/):
  arquivos.csv            ano, zip, csv dentro do zip, tamanho, nº de colunas, separador, se é a principal
  colunas_por_ano.csv     coluna × ano da tabela principal (1 = existe no cabeçalho, vazio = não existe)
  colunas_outras_2025.csv colunas das tabelas de 2025 que não são a principal (tabela, coluna)
  candidatas.csv          colunas da tabela principal cujo nome casa com os padrões de pertinência abaixo,
                          com os anos em que existem
  resumo.txt              contagens geradas por este script

Todas as saídas são gravadas em UTF-8 com quebra de linha LF, como o .gitattributes as guarda no git; assim
regerar não deixa a pasta versionada aparecendo como modificada.

"Existe no cabeçalho" não é "foi coletada": o INEP mantém colunas no layout mesmo sem a pergunta (03, regra de
fonte). A conferência de "coletada" (alguma escola do Brasil com valor 1) é um segundo passo, só para as
candidatas que o grupo escolher.

Uso:  python experimentos/levantamento_colunas_censo/levantar.py
"""
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
ORIGEM = RAIZ / "dados" / "origem" / "censo"
SAIDA = PASTA / "saida"

# Padrões de NOME escolhidos por pertinência (docs/notas/CONTEXTO_2026-11-18.md, tarefa 1), antes de ver
# qualquer cabeçalho. Servem só para achar as colunas no meio de centenas; a lista final é do grupo.
PADROES = {
    "indigena / quilombola / diferenciada": r"INDIGENA|QUILOMBO|DIFERENCIADA|ASSENTAMENTO|TERRA_IND",
    "localizacao": r"LOCALIZACAO|TP_LOCAL",
    "matriculas": r"^QT_MAT",
    "turmas": r"^QT_TUR",
    "docentes": r"^QT_DOC|DOCENTE|PROFISSIONAL",
    "noturno": r"NOTURN|_NOT$|_NOT_",
    "tempo integral": r"INTEGRAL|_INT$|_INT_",
    "transporte escolar": r"TRANSP",
    "eja / educacao especial": r"EJA|ESPECIAL",
}


def ano_do_nome(nome):
    m = re.search(r"(20\d{2})", nome)
    return int(m.group(1)) if m else None


def cabecalho(zf, info):
    """Lê só a primeira linha do CSV dentro do zip. Devolve (colunas, separador)."""
    with zf.open(info) as f:
        linha = io.TextIOWrapper(f, encoding="latin1", newline="").readline()
    linha = linha.rstrip("\r\n").lstrip("﻿\xef\xbb\xbf")
    for sep in (";", ",", "|"):
        cols = [c.strip().strip('"') for c in linha.split(sep)]
        if len(cols) >= 5:
            return cols, sep
    return [], None


def main():
    zips = sorted(ORIGEM.glob("*.zip"))
    if not zips:
        print(f"Nenhum zip em {ORIGEM}. Obtenha-os com python -m src.aquisicao --origem-local PASTA.")
        return 1
    SAIDA.mkdir(parents=True, exist_ok=True)

    arquivos, principal, outras_2025 = [], {}, []
    for z in zips:
        ano = ano_do_nome(z.name)
        with zipfile.ZipFile(z) as zf:
            csvs = [i for i in zf.infolist() if i.filename.lower().endswith(".csv")]
            maior = max(csvs, key=lambda i: i.file_size)
            for info in csvs:
                cols, sep = cabecalho(zf, info)
                e_principal = info is maior
                arquivos.append([ano, z.name, info.filename, info.file_size, len(cols), sep, int(e_principal)])
                if e_principal:
                    principal[ano] = cols
                else:
                    outras_2025 += [[ano, Path(info.filename).name, c] for c in cols]
        print(f"{ano}: {len(principal[ano])} colunas na tabela principal, {len(csvs)} CSV no zip", flush=True)

    anos = sorted(principal)
    todas = sorted({c for cols in principal.values() for c in cols})

    with open(SAIDA / "arquivos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ano", "zip", "csv", "bytes", "n_colunas", "separador", "principal"])
        w.writerows(arquivos)

    with open(SAIDA / "colunas_por_ano.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["coluna", "n_anos", "primeiro", "ultimo", *anos])
        for c in todas:
            tem = [a for a in anos if c in principal[a]]
            w.writerow([c, len(tem), tem[0], tem[-1], *["1" if a in tem else "" for a in anos]])

    with open(SAIDA / "colunas_outras_2025.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ano", "tabela", "coluna", "tambem_na_principal"])
        outras_2025 = [[a, t, c, int(c in principal[a])] for a, t, c in outras_2025]
        w.writerows(outras_2025)

    with open(SAIDA / "candidatas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["grupo", "coluna", "n_anos", "primeiro", "ultimo", "anos_faltando"])
        for grupo, rx in PADROES.items():
            for c in todas:
                if re.search(rx, c):
                    tem = [a for a in anos if c in principal[a]]
                    falta = [a for a in range(tem[0], tem[-1] + 1) if a not in tem]
                    w.writerow([grupo, c, len(tem), tem[0], tem[-1], " ".join(map(str, falta))])

    em_todos = [c for c in todas if all(c in principal[a] for a in anos)]
    linhas = [
        f"Levantamento das colunas do Censo Escolar ({anos[0]}–{anos[-1]}), só cabeçalhos.",
        f"Zips lidos: {len(zips)}. Anos: {len(anos)}.",
        f"Colunas distintas na tabela principal, somando os anos: {len(todas)}.",
        f"Colunas presentes em todos os {len(anos)} anos: {len(em_todos)}.",
        "Colunas por ano (tabela principal): " + ", ".join(f"{a}={len(principal[a])}" for a in anos) + ".",
    ]
    for a, b in zip(anos, anos[1:]):
        novas = set(principal[b]) - set(principal[a])
        saem = set(principal[a]) - set(principal[b])
        if novas or saem:
            linhas.append(f"{a} -> {b}: +{len(novas)} colunas, -{len(saem)} colunas.")
    (SAIDA / "resumo.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(linhas))
    print(f"\nSaídas em {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
