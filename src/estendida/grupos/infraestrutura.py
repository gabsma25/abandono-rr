# -*- coding: utf-8 -*-
"""
Grupo INFRAESTRUTURA: os 18 itens do Almeida & Mussato (2023, Quadro 3) e os índices derivados deles.

Junta o que eram o 03_censo_features.py (os 18 itens) e o 05_indices_infra.py (dimensões e IIE); a regra de
fonte e o método dos índices não mudaram (docs/DECISOES.md, 2026-11-19). Segue o contrato de
src/estendida/grupos/README.md.

EXTRAIR (linha a linha, só do cache completo do Censo, dados/cache/censo_completo/)
-------------------------------------------------------------------------------------
Cada variável tem uma lista de colunas candidatas: a PRIMEIRA é a do artigo (Quadro 3); as demais são
substitutas para anos em que a do artigo não existia no questionário. O INEP mantém muitas colunas no layout
mesmo quando a pergunta não foi feita (tudo 0), então "a coluna existe" NÃO significa "foi coletada". Para cada
(variável, ano) usa-se a primeira candidata COLETADA naquele ano, onde coletada = pelo menos uma escola do
BRASIL com valor 1 naquela coluna/ano (n_um do {ano}_escola_nacional.csv). Se nenhuma candidata foi coletada,
o valor é NA (nunca 0).

INFRA_FONTE_ARTIGO vale 1 no ano em que as 18 variáveis vieram das colunas do próprio artigo; 0 quando alguma
usou substituta ou ficou ausente. A matriz variável × ano com a coluna usada fica em
saida/relatorios/fontes_features_censo.csv.

DERIVAR (método de 14/10/2026, docs/procedencia/relatorio_05; recebe só ANO e as colunas deste grupo)
-----------------------------------------------------------------------------------------------------
Dimensões do artigo (Quadro 3): IIB (4 itens), IDA (5), IDP (5), IEP (4).

1. Itens disponíveis por ano. Um item está disponível num ano se alguma escola tem valor nele (o Censo não
   perguntava despensa, refeitório, secretaria e os dois pátios em 2007-2011). A dimensão de um ano é a SOMA
   dos itens disponíveis naquele ano. Uma escola só recebe a dimensão se tiver TODOS os itens disponíveis do
   ano. IIB e IEP usam sempre todos os itens; IDA usa 2 itens e IDP 3 itens em 2007-2011.
2. z-score DENTRO de cada ano (média e desvio de todas as escolas da base no ano; ddof=0; exige n >= 30 e
   desvio > 0). Usa as outras escolas do ano: é herança declarada; grupo novo calcula linha a linha
   (grupos/README.md, regra 3). Cada ano usa só os dados do próprio ano: não há dado futuro.
3. IIE = PC1 da matriz de correlação das 4 dimensões z, NO PRÓPRIO ANO (pesos de norma 1 e soma > 0).
4. INFRA_ITENS_COMPLETOS = 1 quando as 4 dimensões do ano usam todos os itens do artigo (2012+); 0 em
   2007-2011. Marcador de regime, não feature.

LIMITAÇÃO REGISTRADA: em 2007-2011 IDA/IDP (e portanto o IIE) são aproximações com menos itens; ver
docs/procedencia/relatorio_05_fechamento_18_variaveis_2026-10-14.md.

calcular(..., com_prop=True) acrescenta DIM_<d>_prop e IIE_prop (fora do padrão; usado pelo
testes/test_dataset.py como implementação independente das _prop do dataset).

Tipagem (regra 9): ANO Int16, CO_ENTIDADE string, as 18 variáveis e INFRA_FONTE_ARTIGO Int8 nullable;
derivadas Float64 nullable; INFRA_ITENS_COMPLETOS Int8.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
CACHE = RAIZ / "dados" / "cache" / "censo_completo"
ANO_MINIMO = 2007

NOME = "infraestrutura"

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
CANDIDATAS = sorted({c for lista in VARIAVEIS.values() for c in lista})

DIMENSOES = {
    "IIB": ["IIB_agua_potavel", "IIB_energia_rede", "IIB_coleta_lixo", "IIB_banheiro"],
    "IDA": ["IDA_despensa", "IDA_refeitorio", "IDA_sala_diretoria",
            "IDA_sala_professor", "IDA_secretaria"],
    "IDP": ["IDP_biblioteca", "IDP_lab_informatica", "IDP_patio_coberto",
            "IDP_patio_descoberto", "IDP_quadra_esportes"],
    "IEP": ["IEP_computador", "IEP_impressora", "IEP_projetor", "IEP_internet"],
}
ITENS = [i for lista in DIMENSOES.values() for i in lista]
MIN_ESCOLAS_ANO = 30
MIN_ITENS_DIM = 2
COL_FLAG = "INFRA_ITENS_COMPLETOS"


def nomes_colunas(com_prop=False):
    zano = [f"DIM_{d}_zano" for d in DIMENSOES] + ["IIE_zano"]
    prop = [f"DIM_{d}_prop" for d in DIMENSOES] + ["IIE_prop"] if com_prop else []
    return zano + prop + [COL_FLAG]


COLUNAS = list(VARIAVEIS) + ["INFRA_FONTE_ARTIGO"]   # o que extrair() acrescenta
DERIVADAS = nomes_colunas()                         # o que derivar() acrescenta


# ------------------------------------------------------------------
# EXTRAIR: 18 itens + INFRA_FONTE_ARTIGO, por (ANO, CO_ENTIDADE)
# ------------------------------------------------------------------
def anos_no_cache(cache=CACHE):
    anos = []
    for p in cache.glob("*_escola.parquet"):
        m = re.fullmatch(r"(\d{4})_escola", p.stem)
        if m and int(m.group(1)) >= ANO_MINIMO and (cache / f"{m.group(1)}_escola_nacional.csv").exists():
            anos.append(int(m.group(1)))
    return sorted(anos)


def ler_ano(ano, cache=CACHE):
    """(colunas candidatas de RR convertidas em número, estatística nacional no formato do 03 antigo)."""
    nac = pd.read_csv(cache / f"{ano}_escola_nacional.csv").set_index("coluna")
    presentes = [c for c in CANDIDATAS if c in nac.index]
    tabela = pd.read_parquet(cache / f"{ano}_escola.parquet", columns=["CO_ENTIDADE", *presentes])
    cru = pd.DataFrame({"CO_ENTIDADE": tabela["CO_ENTIDADE"].astype(str).str.strip()})
    for c in presentes:
        cru[c] = pd.to_numeric(tabela[c], errors="coerce")
    stats = {"_n_brasil": int(nac["n_linhas"].iloc[0])}
    for c in presentes:
        stats[c] = {"nao_nulo": int(nac.loc[c, "n_numerico"]), "uns": int(nac.loc[c, "n_um"])}
    return cru, stats


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


def diagnostico(censo, fontes_df):
    vars18 = list(VARIAVEIS.keys())
    linhas = [
        "FEATURES DO CENSO — RR 2007-2025 (grupo infraestrutura)",
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
    linhas += ["", "Variáveis ausentes por ano (nunca coletadas naquele ano no Brasil):"]
    for ano in sorted(censo["ANO"].unique()):
        fa = fontes_df[(fontes_df["ano"] == ano) & (fontes_df["coluna_usada"] == "")]
        if len(fa):
            linhas.append(f"  {ano}: " + ", ".join(fa["variavel"]))
    linhas += ["", "Variáveis com coluna substituta (não é a coluna do artigo):"]
    for ano in sorted(censo["ANO"].unique()):
        fa = fontes_df[(fontes_df["ano"] == ano) & (fontes_df["coluna_usada"] != "") &
                       (fontes_df["coluna_usada"] != fontes_df["coluna_artigo"])]
        if len(fa):
            linhas.append(f"  {ano}: " + ", ".join(
                f"{r.variavel}<-{r.coluna_usada}" for r in fa.itertuples()))
    return linhas


def extrair(relatorios: Path, cache=CACHE) -> pd.DataFrame:
    """Tabela (ANO, CO_ENTIDADE, 18 variáveis, INFRA_FONTE_ARTIGO) de todas as escolas de RR no Censo.
    Grava fontes_features_censo.csv e diagnostico_features_censo.txt em `relatorios`."""
    partes, fontes = [], []
    for ano in anos_no_cache(cache):
        cru, stats = ler_ano(ano, cache)
        df_ano, fnt = montar_ano(ano, cru, stats)
        partes.append(df_ano)
        fontes += fnt
        print(f"  {ano}: n_RR={len(cru)} n_BR={stats['_n_brasil']}", flush=True)
    censo = pd.concat(partes, ignore_index=True)
    fontes_df = pd.DataFrame(fontes)
    fontes_df.to_csv(relatorios / "fontes_features_censo.csv", index=False, encoding="utf-8")
    (relatorios / "diagnostico_features_censo.txt").write_text("\n".join(diagnostico(censo, fontes_df)),
                                                              encoding="utf-8")
    return censo


# ------------------------------------------------------------------
# DERIVAR: dimensões z por ano, IIE e marcador de regime
# ------------------------------------------------------------------
def pc1(R):
    """Pesos do 1º componente (matriz de correlação): norma 1, soma > 0.
    Devolve (pesos, autovalores em ordem decrescente)."""
    vals, vecs = np.linalg.eigh(R)
    ordem = np.argsort(vals)[::-1]
    vals, vecs = vals[ordem], vecs[:, ordem]
    w = vecs[:, 0]
    if w.sum() < 0:
        w = -w
    return w, vals


def calcular(base, com_prop=False):
    """Função pura: recebe ANO e os 18 itens e devolve as colunas novas e os parâmetros.
    O resultado de um ano depende apenas das linhas daquele ano."""
    ano_arr = base["ANO"].astype(int).to_numpy()
    anos = sorted(set(ano_arr.tolist()))
    itens_f = base[ITENS].astype("float64")          # contas em float; saída volta a Int8/Float64

    z = {d: pd.Series(np.nan, index=base.index) for d in DIMENSOES}
    prop = {d: pd.Series(np.nan, index=base.index) for d in DIMENSOES}
    completos = pd.Series(0, index=base.index, dtype="int64")
    itens_ano, est_ano, avisos = {}, [], []

    for ano in anos:
        idx = base.index[ano_arr == ano]
        itens_ano[ano] = {}
        todas_completas = True
        for d, lista in DIMENSOES.items():
            disp = [i for i in lista if itens_f.loc[idx, i].notna().any()]
            itens_ano[ano][d] = disp
            for i in disp:
                cob = float(itens_f.loc[idx, i].notna().mean())
                if cob < 1:
                    avisos.append(f"{ano} {i}: item disponível mas só {cob*100:.1f}% das escolas têm valor")
            if len(disp) != len(lista):
                todas_completas = False
            if len(disp) < MIN_ITENS_DIM:
                est_ano.append({"ano": ano, "dim": d, "n_itens": len(disp), "n": 0,
                                "media_soma": None, "dp_soma": None, "valido": False})
                continue
            s = itens_f.loc[idx, disp].sum(axis=1, min_count=len(disp))
            v = s.dropna()
            media, dp = (float(v.mean()), float(v.std(ddof=0))) if len(v) else (np.nan, np.nan)
            valido = bool(len(v) >= MIN_ESCOLAS_ANO and dp > 0)
            est_ano.append({"ano": ano, "dim": d, "n_itens": len(disp), "n": int(len(v)),
                            "media_soma": None if np.isnan(media) else media,
                            "dp_soma": None if np.isnan(dp) else dp, "valido": valido})
            prop[d].loc[idx] = s / len(disp)
            if valido:
                z[d].loc[idx] = (s - media) / dp
        if todas_completas:
            completos.loc[idx] = 1

    # IIE: PC1 das 4 dimensões z, no próprio ano
    iie = pd.Series(np.nan, index=base.index)
    pca_ano = {}
    for ano in anos:
        idx = base.index[ano_arr == ano]
        Z = pd.DataFrame({d: z[d].loc[idx] for d in DIMENSOES}).dropna()
        if len(Z) < MIN_ESCOLAS_ANO:
            pca_ano[ano] = None
            continue
        R = np.corrcoef(Z.to_numpy().T)
        if not np.isfinite(R).all():
            pca_ano[ano] = None
            continue
        w, vals = pc1(R)
        iie.loc[Z.index] = Z.to_numpy() @ w
        var = vals / vals.sum()
        pca_ano[ano] = {"n": int(len(Z)),
                        "pesos_pc1": dict(zip(DIMENSOES.keys(), [float(x) for x in w])),
                        "autovalores": [float(x) for x in vals],
                        "variancia_explicada": [float(x) for x in var],
                        "kaiser": bool(vals[0] > 1), "pc1_acima_60": bool(var[0] > 0.6)}

    novas = {f"DIM_{d}_zano": z[d] for d in DIMENSOES}
    novas["IIE_zano"] = iie
    if com_prop:
        for d in DIMENSOES:
            novas[f"DIM_{d}_prop"] = prop[d]
        novas["IIE_prop"] = pd.DataFrame({d: prop[d] for d in DIMENSOES}).mean(
            axis=1, skipna=False)
    novas_df = pd.DataFrame(novas, index=base.index).astype("Float64")
    novas_df[COL_FLAG] = completos.astype("Int8")
    params = {
        "metodo": "zano (z-score dentro de cada ano) com itens disponíveis por ano; "
                  "IIE = PC1 das 4 dimensões z do próprio ano",
        "com_prop": bool(com_prop),
        "min_escolas_ano": MIN_ESCOLAS_ANO,
        "min_itens_dim": MIN_ITENS_DIM,
        "itens_por_ano": {str(a): v for a, v in itens_ano.items()},
        "z_por_ano": est_ano,
        "pca_por_ano": {str(a): v for a, v in pca_ano.items()},
        "avisos": avisos,
    }
    return novas_df[nomes_colunas(com_prop)], params


def relatorio(tab, params):
    """`tab`: ANO + as colunas derivadas."""
    L = ["ÍNDICES DE INFRAESTRUTURA — grupo infraestrutura (zano, ano a ano)", "=" * 78,
         f"Linhas: {tab.shape[0]} ({len(DERIVADAS)} colunas novas)", "",
         "Itens usados por dimensão em cada ano (IIB IDA IDP IEP) — artigo: 4 5 5 4:"]
    for a, v in params["itens_por_ano"].items():
        n = [len(v[d]) for d in DIMENSOES]
        L.append(f"  {a}:  {n[0]}  {n[1]}  {n[2]}  {n[3]}" + ("" if n == [4, 5, 5, 4]
                                                              else "   <- dimensão parcial"))
    L += ["", "PCA das 4 dimensões z, por ano (correlação do próprio ano):",
          f"{'ano':>5}{'n':>6}{'autoval.':>9}{'var.PC1':>9}   pesos PC1 (IIB IDA IDP IEP)   Kaiser  >60%"]
    for a, p in params["pca_por_ano"].items():
        if p is None:
            L.append(f"{a:>5}   sem PCA (n<{MIN_ESCOLAS_ANO} ou correlação inválida)")
            continue
        L.append(f"{a:>5}{p['n']:>6}{p['autovalores'][0]:>9.3f}{p['variancia_explicada'][0]*100:>8.1f}%   "
                 + "  ".join(f"{x:.3f}" for x in p["pesos_pc1"].values())
                 + f"        {'sim' if p['kaiser'] else 'NÃO':>4}   {'sim' if p['pc1_acima_60'] else 'NÃO':>4}")
    L += ["", "Cobertura (% das escolas com valor) por ano:",
          f"{'ano':>5}{'n':>6}" + "".join(f"{c.replace('_zano', ''):>10}" for c in nomes_colunas()[:5])]
    for ano in sorted(tab["ANO"].astype(int).unique()):
        sub = tab[tab["ANO"].astype(int) == ano]
        L.append(f"{ano:>5}{len(sub):>6}" + "".join(
            f"{sub[c].notna().mean()*100:>9.1f}%" for c in nomes_colunas()[:5]))
    ea = pd.DataFrame(params["z_por_ano"])
    L += ["", "Soma bruta por dimensão e ano — média ± desvio (itens usados):"]
    for ano in sorted(ea["ano"].unique()):
        sub = ea[ea["ano"] == ano].set_index("dim")
        L.append(f"  {ano}: " + " | ".join(
            f"{d} {sub.loc[d, 'media_soma']:.2f}±{sub.loc[d, 'dp_soma']:.2f} ({int(sub.loc[d, 'n_itens'])})"
            if sub.loc[d, "valido"] else f"{d} --" for d in DIMENSOES))
    if params["avisos"]:
        L += ["", "AVISOS:"] + [f"  {x}" for x in params["avisos"]]
    return L


def derivar(tab: pd.DataFrame, relatorios: Path) -> pd.DataFrame:
    """`tab`: ANO + COLUNAS deste grupo, com o índice e as linhas da base. Devolve as DERIVADAS.
    Grava indices_infra.txt e indices_infra_parametros.json em `relatorios`."""
    novas, params = calcular(tab)
    (relatorios / "indices_infra_parametros.json").write_text(
        json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8")
    L = relatorio(pd.concat([tab[["ANO"]], novas], axis=1), params)
    (relatorios / "indices_infra.txt").write_text("\n".join(L), encoding="utf-8")
    if params["avisos"]:
        print("  [aviso] itens com cobertura parcial dentro do ano — ver indices_infra.txt")
    return novas
