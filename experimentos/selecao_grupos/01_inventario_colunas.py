# -*- coding: utf-8 -*-
"""
01 — Inventário das colunas do Censo Escolar de Roraima, ano a ano (2007–2025), para escolher os grupos.

Cruza duas fontes, sem olhar o desfecho (regra 7: não lê o rendimento, o dataset nem a base):

  1. o cache completo do Censo (dados/cache/censo_completo/): em que ano e tabela cada coluna existe, se o INEP
     de fato a coletou (contagens do Brasil inteiro) e quanto ela está preenchida nas escolas de Roraima;
  2. os dicionários de dados do INEP, que vêm dentro dos zips (dados/origem/censo/, "ANEXO I - Dicionário de
     Dados"): descrição, tipo, categorias, a marca "coletada no ano" (s/n) do próprio INEP e as notas sobre
     mudanças entre anos. Há 5 versões distintas (2007–2021, 2022, 2023, 2024, 2025); cada coluna recebe a
     descrição da versão mais nova que a cita.

As saídas foram feitas para outra pessoa ou outra IA ler e propor os grupos de colunas: CSV simples, UTF-8, LF,
uma linha por registro, e um LEIA_ME.md que explica cada campo, gerado por este script (os números dele vêm do
código, regra 3).

Saídas (saida/):
  colunas.csv              uma linha por coluna: descrição, tipo, tabelas, anos no layout, anos coletados,
                           presença em todos os anos, cobertura em RR, tipo de valor
  presenca_por_ano.csv     matriz coluna × ano, com um código por célula (C, L, ausente; legenda no LEIA_ME.md)
  por_ano.csv              uma linha por (ano, tabela, coluna): as contagens que geram as duas acima
  dicionario_inep.csv      o dicionário do INEP unificado: uma linha por (versão, tabela, coluna)
  LEIA_ME.md               o que é cada arquivo e cada campo, as contagens e os cuidados para escolher

Precisa dos zips em dados/origem/censo/ só para o dicionário (python -m src.aquisicao --origem-local PASTA).

Uso:  python experimentos/selecao_grupos/01_inventario_colunas.py
"""
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
CACHE = RAIZ / "dados" / "cache" / "censo_completo"
ORIGEM = RAIZ / "dados" / "origem" / "censo"
SAIDA = PASTA / "saida"
ANOS = list(range(2007, 2026))
JANELA = list(range(2013, 2019))          # janela segura dos estudos (docs/PROTOCOLO.md)
NOME_VALIDO = re.compile(r"^[A-Z][A-Z0-9_]+$")


# ------------------------------------------------------------------
# 1. Cache: presença, coleta no Brasil, preenchimento em RR
# ------------------------------------------------------------------
def tipo_valor(serie: pd.Series) -> str:
    """Classifica os valores de RR (texto) sem olhar desfecho: vazio, binario, contagem, codigo, decimal, texto."""
    v = serie[serie.str.strip() != ""]
    if v.empty:
        return "vazio"
    num = pd.to_numeric(v, errors="coerce")
    if num.notna().mean() < 0.95:
        return "texto"
    num = num.dropna()
    if set(num.unique()) <= {0, 1}:
        return "binario"
    if (num % 1 != 0).any():
        return "decimal"
    return "contagem_ou_codigo"


def escolas_ativas(ano):
    """CO_ENTIDADE das escolas de RR em atividade no ano (TP_SITUACAO_FUNCIONAMENTO == 1, tabela de escolas).
    De 2022 em diante o INEP deixa em branco as escolas paralisadas ou extintas; o preenchimento que importa é o
    das escolas em atividade, que são as que têm rendimento."""
    esc = pd.read_parquet(CACHE / f"{ano}_escola.parquet", columns=["CO_ENTIDADE", "TP_SITUACAO_FUNCIONAMENTO"])
    return set(esc.loc[esc["TP_SITUACAO_FUNCIONAMENTO"].str.strip() == "1", "CO_ENTIDADE"].str.strip())


def ler_cache():
    linhas, ativas = [], {}
    for p in sorted(CACHE.glob("*.parquet")):
        m = re.fullmatch(r"(\d{4})_(.+)", p.stem)
        ano, tabela = int(m.group(1)), m.group(2)
        rr = pd.read_parquet(p)
        if ano not in ativas:
            ativas[ano] = escolas_ativas(ano)
        em_ativ = rr["CO_ENTIDADE"].str.strip().isin(ativas[ano]).to_numpy()
        nac = pd.read_csv(CACHE / f"{p.stem}_nacional.csv").set_index("coluna")
        for c in rr.columns:
            s = rr[c].astype("string").fillna("")
            preench = s.str.strip() != ""
            n = nac.loc[c]
            linhas.append({
                "ano": ano, "tabela": tabela, "coluna": c,
                "n_brasil": int(n["n_linhas"]), "n_preenchido_br": int(n["n_preenchido"]),
                "n_numerico_br": int(n["n_numerico"]), "n_um_br": int(n["n_um"]),
                "n_positivo_br": int(n["n_positivo"]),
                "n_rr": len(s), "n_preenchido_rr": int(preench.sum()),
                "pct_preenchido_rr": round(100 * preench.mean(), 1) if len(s) else 0.0,
                "n_rr_ativas": int(em_ativ.sum()),
                "pct_preenchido_rr_ativas": round(100 * preench[em_ativ].mean(), 1) if em_ativ.any() else 0.0,
                "n_distintos_rr": int(s[preench].nunique()),
                "tipo_valor_rr": tipo_valor(s),
            })
    df = pd.DataFrame(linhas)
    # Coletada no ano (pelo Brasil): numérica com algum valor > 0, ou texto preenchido. Uma coluna só de zeros ou
    # vazia no Brasil inteiro está no layout, mas a pergunta não foi feita (regra de fonte do grupo infraestrutura).
    numerica = df["n_numerico_br"] >= 0.95 * df["n_preenchido_br"]
    df["coletada_br"] = ((numerica & (df["n_positivo_br"] > 0)) |
                         (~numerica & (df["n_preenchido_br"] > 0))).astype(int)
    return df


# ------------------------------------------------------------------
# 2. Dicionários do INEP
# ------------------------------------------------------------------
def nome_tabela_dic(aba: str) -> str:
    a = aba.lower().strip()
    for chave, nome in (("matr", "matricula"), ("docente", "docente"), ("turma", "turma"),
                        ("gestor", "gestor_escolar"), ("curso", "curso_tecnico"), ("suplemento", "curso_tecnico")):
        if chave in a:
            return nome
    return "escola"


def ler_aba(df: pd.DataFrame):
    """Linhas do dicionário de uma aba: (coluna, descrição, tipo, categoria, {ano: s/n}, notas)."""
    def limpa(lin):
        return lin.map(lambda x: "" if pd.isna(x) else str(x).strip())

    cab = next(i for i in range(min(20, len(df))) if limpa(df.iloc[i]).eq("Nome da Variável").any())
    hdr = limpa(df.iloc[cab])
    col_nome = int(hdr[hdr == "Nome da Variável"].index[0])
    col_desc = int(hdr[hdr == "Descrição da Variável"].index[0])
    col_tipo = int(hdr[hdr == "Tipo"].index[0])
    col_cat = int(hdr[hdr == "Categoria"].index[0])
    col_notas = next((int(i) for i, v in hdr.items() if v.startswith("Notas")), None)
    anos = {}
    for j, t in limpa(df.iloc[cab + 1]).items():
        if re.fullmatch(r"\d{2}", t):
            anos[int(j)] = 2000 + int(t)
    saida = []
    for _, lin in df.iloc[cab + 2:].iterrows():
        nome = str(lin[col_nome]).strip()
        if not NOME_VALIDO.match(nome):
            continue
        coleta = {a: str(lin[j]).strip().lower() for j, a in anos.items() if str(lin[j]).strip() not in ("", "nan")}
        txt = lambda x: "" if pd.isna(x) else " ".join(str(x).split())   # noqa: E731
        saida.append({"coluna": nome, "descricao": txt(lin[col_desc]), "tipo_inep": txt(lin[col_tipo]),
                      "categorias": txt(lin[col_cat]).replace(" - ", "="),
                      "coleta_inep": coleta,
                      "notas_inep": txt(lin[col_notas]) if col_notas is not None else ""})
    return saida


def ler_dicionarios():
    """DataFrame (versao, tabela, coluna, ...) de todas as versões distintas do dicionário."""
    vistos, linhas = {}, []
    for z in sorted(ORIGEM.glob("*.zip")):
        ano = int(re.search(r"(20\d{2})", z.name).group(1))
        with zipfile.ZipFile(z) as zf:
            infos = [i for i in zf.infolist() if i.filename.lower().endswith(".xlsx")
                     and "dicion" in i.filename.lower() and "~$" not in i.filename]
            if not infos:
                continue
            conteudo = zf.read(infos[0])
        chave = (len(conteudo), hash(conteudo))
        if chave in vistos:                       # mesma versão já lida (2007–2021 repetem o mesmo arquivo)
            vistos[chave][1] = ano
            continue
        vistos[chave] = [ano, ano]
        xl = pd.ExcelFile(io.BytesIO(conteudo))
        for aba in xl.sheet_names:
            for r in ler_aba(pd.read_excel(xl, aba, header=None, dtype=object)):
                linhas.append({"chave_versao": chave, "tabela": nome_tabela_dic(aba), **r})
    if not linhas:
        return pd.DataFrame()
    dic = pd.DataFrame(linhas)
    dic["versao"] = dic["chave_versao"].map(lambda k: f"{vistos[k][0]}-{vistos[k][1]}" if vistos[k][0] != vistos[k][1]
                                            else str(vistos[k][0]))
    dic["versao_fim"] = dic["chave_versao"].map(lambda k: vistos[k][1])
    dic["anos_coleta_inep"] = dic["coleta_inep"].map(lambda d: " ".join(str(a) for a, v in sorted(d.items())
                                                                        if v == "s"))
    return dic.drop(columns=["chave_versao", "coleta_inep"])


# ------------------------------------------------------------------
# 3. Junta e grava
# ------------------------------------------------------------------
def faixa(anos):
    """[2007, 2008, 2009, 2012] -> '2007-2009 2012'."""
    anos = sorted(anos)
    if not anos:
        return ""
    partes, ini, ant = [], anos[0], anos[0]
    for a in anos[1:] + [None]:
        if a is not None and a == ant + 1:
            ant = a
            continue
        partes.append(str(ini) if ini == ant else f"{ini}-{ant}")
        if a is not None:
            ini = ant = a
    return " ".join(partes)


def resumo_colunas(por_ano, dic):
    linhas = []
    for col, g in por_ano.groupby("coluna", sort=True):
        anos_layout = sorted(g["ano"].unique())
        anos_col = sorted(g.loc[g["coletada_br"] == 1, "ano"].unique())
        g_col = g[g["coletada_br"] == 1]
        tipos = g_col["tipo_valor_rr"].value_counts()
        linhas.append({
            "coluna": col,
            "tabelas": " ".join(sorted(g["tabela"].unique())),
            "n_anos_layout": len(anos_layout), "anos_layout": faixa(anos_layout),
            "n_anos_coletada_br": len(anos_col), "anos_coletada_br": faixa(anos_col),
            "coletada_todos_2007_2024": int(all(a in anos_col for a in range(2007, 2025))),
            "coletada_toda_janela_2013_2018": int(all(a in anos_col for a in JANELA)),
            "coletada_2025": int(2025 in anos_col),
            "pct_preenchido_ativas_medio": round(g_col["pct_preenchido_rr_ativas"].mean(), 1) if len(g_col) else 0.0,
            "pct_preenchido_ativas_min": round(g_col["pct_preenchido_rr_ativas"].min(), 1) if len(g_col) else 0.0,
            "tipo_valor_rr": tipos.index[0] if len(tipos) else "vazio",
            "n_distintos_rr_max": int(g["n_distintos_rr"].max()),
        })
    col = pd.DataFrame(linhas)
    if not dic.empty:
        # descrição da versão mais nova que cita a coluna (na tabela de escola, se houver mais de uma)
        d = dic.assign(_esc=(dic["tabela"] == "escola").astype(int)).sort_values(
            ["versao_fim", "_esc"], ascending=[False, False]).drop_duplicates("coluna")
        col = col.merge(d[["coluna", "descricao", "tipo_inep", "categorias", "anos_coleta_inep", "notas_inep",
                           "versao"]].rename(columns={"versao": "versao_dicionario"}),
                        on="coluna", how="left", validate="1:1")
    col.insert(1, "prefixo", col["coluna"].str.extract(r"^([A-Z]+)_", expand=False).fillna(""))
    return col


def matriz(por_ano):
    """coluna × ano: 'C' coletada (no layout e com dado no Brasil), 'L' só no layout (vazia ou só zeros no
    Brasil), '' fora do layout."""
    m = por_ano.groupby(["coluna", "ano"])["coletada_br"].max().map({1: "C", 0: "L"}).unstack("ano")
    return m.reindex(columns=ANOS).fillna("").reset_index()


def discordancias(por_ano, col):
    """Registros em que a coleta medida no Brasil discorda da marca "s" do dicionário (só colunas com marca)."""
    if "anos_coleta_inep" not in col:
        return 0
    marca = col.set_index("coluna")["anos_coleta_inep"].fillna("").map(lambda s: set(map(int, s.split())))
    p = por_ano[por_ano["coluna"].map(lambda c: bool(marca.get(c)))]
    inep = [a in marca[c] for a, c in zip(p["ano"], p["coluna"])]
    return int((p["coletada_br"].astype(bool).to_numpy() != pd.Series(inep, dtype=bool).to_numpy()).sum())


def leia_me(col, por_ano, dic, m):
    n = len(col)
    def conta(cond):
        return int(cond.sum())
    tabelas_2025 = sorted(por_ano.loc[por_ano["ano"] == 2025, "tabela"].unique())
    por_prefixo = col.groupby("prefixo").size().sort_values(ascending=False)
    L = [
        "# Inventário das colunas do Censo Escolar — Roraima, 2007–2025",
        "",
        "Gerado por `experimentos/selecao_grupos/01_inventario_colunas.py`. Todos os números deste arquivo vêm do "
        "código. Serve para escolher **grupos de colunas** novos (`src/estendida/grupos/README.md`).",
        "",
        "## Regras para quem for escolher (pessoa ou IA)",
        "",
        "- Escolher por **pertinência** (o que a literatura e o problema dizem), **cobertura** (anos coletados, "
        "preenchimento em RR), **estabilidade** (mesmo significado entre anos; veja `notas_inep`) e **redundância** "
        "entre colunas. É **proibido** escolher pela relação com o abandono (`CLAUDE.md`, regra 7); este "
        "inventário não contém o desfecho de propósito.",
        "- **Existir no layout não é ser coletada.** O INEP mantém colunas sem a pergunta (vazias ou só zeros). Use "
        "`anos_coletada_br` e a matriz (`C`), não só `anos_layout`.",
        "- Os estudos usam a **janela 2013–2018** (`coletada_toda_janela_2013_2018`); colunas que só existem a "
        "partir de 2019 não servem para ela.",
        "- Em **2025** o INEP dividiu os microdados em tabelas: " + ", ".join(f"`{t}`" for t in tabelas_2025) +
        ". Contagens por escola (`QT_MAT_*`, `QT_TUR_*`, `QT_DOC_*`) saíram da tabela de escolas e estão nas "
        "outras; a coluna aparece com o mesmo nome, em outra tabela (campo `tabelas`).",
        "- Ausente estrutural nunca vira 0 (regra 8); `'--'` e texto vazio do INEP são ausentes.",
        "- Não invente nomes de coluna (regra 11): todo nome está em `colunas.csv`.",
        "- Colunas de identificação e localização (`CO_*`, `NO_*`, `SG_*`, `NU_ANO_CENSO`) são chaves e "
        "rótulos, não preditores.",
        "",
        "## Os arquivos",
        "",
        "| Arquivo | Uma linha por | Para quê |",
        "|---|---|---|",
        "| `colunas.csv` | coluna | a tabela principal para escolher |",
        "| `presenca_por_ano.csv` | coluna | ver de relance em que anos cada coluna existe e foi coletada |",
        "| `por_ano.csv` | ano × tabela × coluna | o detalhe que gera as duas acima |",
        "| `dicionario_inep.csv` | versão do dicionário × tabela × coluna | o texto do INEP, sem resumo |",
        "",
        "### `colunas.csv`",
        "",
        "| Campo | Significado |",
        "|---|---|",
        "| `coluna` | nome da variável no microdado do INEP |",
        "| `prefixo` | início do nome: `IN` indicador 0/1, `QT` contagem, `TP` código de categoria, `CO` código, "
        "`NO` nome, `NU` número, `DT` data, `TX` texto |",
        "| `tabelas` | tabela(s) do cache em que aparece (`escola` é a principal; 2023–2025 têm outras) |",
        "| `n_anos_layout`, `anos_layout` | anos em que a coluna está no arquivo do INEP (faixas, ex.: `2007-2014 2019`) |",
        "| `n_anos_coletada_br`, `anos_coletada_br` | anos em que alguma escola do Brasil tem valor (> 0 se numérica, "
        "não vazio se texto) |",
        "| `coletada_todos_2007_2024` | 1 se coletada em todos os anos de 2007 a 2024 |",
        "| `coletada_toda_janela_2013_2018` | 1 se coletada em todos os anos da janela dos estudos |",
        "| `coletada_2025` | 1 se coletada em 2025 |",
        "| `pct_preenchido_ativas_medio`, `_min` | % das escolas de RR **em atividade** com valor não vazio, nos anos "
        "coletados (média e mínimo). Escolas paralisadas ou extintas ficam de fora: de 2022 em diante o INEP as "
        "deixa em branco |",
        "| `tipo_valor_rr` | `binario` (0/1), `contagem_ou_codigo` (inteiros), `decimal`, `texto` ou `vazio`, pelos valores de RR |",
        "| `n_distintos_rr_max` | maior número de valores distintos em RR num ano |",
        "| `descricao`, `tipo_inep`, `categorias` | do dicionário do INEP (versão mais nova que cita a coluna); "
        "`categorias` no formato `código=rótulo` |",
        "| `anos_coleta_inep` | anos marcados com \"s\" (coletada) no dicionário do INEP |",
        "| `notas_inep` | notas do INEP sobre mudanças entre anos (quando há) |",
        "| `versao_dicionario` | de que versão do dicionário vieram a descrição e as marcas |",
        "",
        "### `presenca_por_ano.csv`",
        "",
        "Uma coluna por ano, 2007 a 2025. Código de cada célula: **`C`** = no layout e coletada no Brasil; "
        "**`L`** = no layout, mas vazia ou só zeros no Brasil (pergunta não feita); **vazio** = fora do layout.",
        "",
        "### `por_ano.csv`",
        "",
        "`n_brasil` (linhas do Brasil), `n_preenchido_br`, `n_numerico_br`, `n_um_br` (valor 1), "
        "`n_positivo_br` (> 0), `coletada_br` (0/1, a regra acima), `n_rr` (linhas de RR, todas as situações), "
        "`n_preenchido_rr`, `pct_preenchido_rr`, `n_rr_ativas` e `pct_preenchido_rr_ativas` (só escolas em "
        "atividade), `n_distintos_rr`, `tipo_valor_rr`.",
        "",
        "## Contagens",
        "",
        f"- Colunas distintas (todas as tabelas, todos os anos): **{n}**.",
        f"- No layout em todos os {len(ANOS)} anos: **{conta(col['n_anos_layout'] == len(ANOS))}**.",
        f"- Coletadas em todos os anos de 2007 a 2024: **{conta(col['coletada_todos_2007_2024'] == 1)}**.",
        f"- Coletadas em toda a janela 2013–2018: **{conta(col['coletada_toda_janela_2013_2018'] == 1)}**.",
        f"- Coletadas na janela e com pelo menos 90% das escolas de RR em atividade preenchidas (mínimo nos anos): "
        f"**{conta((col['coletada_toda_janela_2013_2018'] == 1) & (col['pct_preenchido_ativas_min'] >= 90))}**.",
        f"- Registros (ano × tabela × coluna) em que `coletada_br` discorda da marca \"s\" do dicionário do INEP: "
        f"**{discordancias(por_ano, col)}** (só colunas que o dicionário marca).",
        f"- Com descrição no dicionário do INEP: **{conta(col['descricao'].fillna('') != '') if 'descricao' in col else 0}**.",
        f"- Versões distintas do dicionário lidas: **{dic['versao'].nunique() if not dic.empty else 0}** "
        f"({', '.join(sorted(dic['versao'].unique())) if not dic.empty else 'nenhuma: faltam os zips'}).",
        "",
        "Colunas por prefixo:",
        "",
        "| prefixo | colunas | coletadas em toda a janela 2013–2018 |",
        "|---|---|---|",
    ]
    jan = col[col["coletada_toda_janela_2013_2018"] == 1].groupby("prefixo").size()
    for p, k in por_prefixo.items():
        L.append(f"| `{p or '(outro)'}` | {k} | {int(jan.get(p, 0))} |")
    L += ["", "Colunas por ano (no layout / coletadas no Brasil):", "", "| ano | no layout | coletadas |", "|---|---|---|"]
    for a in ANOS:
        L.append(f"| {a} | {conta(m[a] != '')} | {conta(m[a] == 'C')} |")
    return "\n".join(L) + "\n"


def main():
    if not CACHE.exists():
        print(f"[ERRO] falta {CACHE}")
        return 1
    SAIDA.mkdir(parents=True, exist_ok=True)
    print("Lendo o cache completo do Censo...", flush=True)
    por_ano = ler_cache()
    print(f"  {len(por_ano)} registros (ano × tabela × coluna)")
    print("Lendo os dicionários do INEP nos zips...", flush=True)
    dic = ler_dicionarios()
    if dic.empty:
        print("  [aviso] nenhum dicionário: faltam os zips em dados/origem/censo/; colunas.csv sai sem descrição")
    else:
        print(f"  {len(dic)} linhas, versões {sorted(dic['versao'].unique())}")
    col = resumo_colunas(por_ano, dic)
    m = matriz(por_ano)

    escrever = dict(index=False, encoding="utf-8", lineterminator="\n")
    col.to_csv(SAIDA / "colunas.csv", **escrever)
    m.to_csv(SAIDA / "presenca_por_ano.csv", **escrever)
    por_ano.sort_values(["coluna", "ano", "tabela"]).to_csv(SAIDA / "por_ano.csv", **escrever)
    if not dic.empty:
        dic.drop(columns=["versao_fim"]).sort_values(["versao", "tabela", "coluna"]).to_csv(
            SAIDA / "dicionario_inep.csv", **escrever)
    (SAIDA / "LEIA_ME.md").write_text(leia_me(col, por_ano, dic, m), encoding="utf-8", newline="\n")
    print(f"\n{len(col)} colunas → {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
