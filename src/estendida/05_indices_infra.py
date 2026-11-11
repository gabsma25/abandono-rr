# -*- coding: utf-8 -*-
"""
05 — Índices de infraestrutura (Almeida & Mussato, 2023), calculados ano a ano.

Entrada:  gustavo/saida/etapas/04_base_com_censo.parquet   (18 variáveis 0/1)
Saída:    gustavo/saida/etapas/05_base_com_indices.parquet (+6 colunas)
          gustavo/saida/base_atual.parquet                 (cópia deste)
          gustavo/saida/relatorios/indices_infra.txt
          gustavo/saida/relatorios/indices_infra_parametros.json

As 18 variáveis ORIGINAIS ficam na base. As colunas novas são derivadas e podem
ser descartadas livremente na hora de montar o modelo (nível 18 -> 4 -> 1).

MÉTODO (decisão de 14/10/2026, relatório 05; análise em analises/01 e 02)
---------------------------------------------------------------------------
Dimensões do artigo (Quadro 3): IIB (4 itens), IDA (5), IDP (5), IEP (4).

1. Itens disponíveis por ano. Um item está disponível num ano se alguma escola
   tem valor nele (o Censo não perguntava despensa, refeitório, secretaria e
   os dois pátios em 2007-2011; ver relatório 04). A dimensão de um ano é a
   SOMA dos itens disponíveis naquele ano. Uma escola só recebe a dimensão se
   tiver TODOS os itens disponíveis do ano (item faltando numa escola isolada
   dá NaN; nunca se calcula com "menos itens" por escola).
   Consequência: IIB e IEP usam sempre todos os itens. IDA usa 2 itens e IDP 3
   itens em 2007-2011 (dimensão menos fiel ao artigo); de 2012 em diante usam
   os 5 itens do artigo.

2. z-score DENTRO de cada ano (média e desvio de todas as escolas da base no
   ano; desvio populacional, ddof=0; exige n >= 30 e desvio > 0). Cada ano usa
   só os dados do próprio ano: não há dado futuro (regra 4 do CLAUDE.md).

3. IIE = primeiro componente principal (PC1) da matriz de correlação das 4
   dimensões z, calculado NO PRÓPRIO ANO (pesos de norma 1 e soma > 0).
   IIE = soma(peso_i * DIM_i). Escala = autovalor do ano (desvio ~1,7 a 1,9).

4. INFRA_ITENS_COMPLETOS = 1 quando as 4 dimensões do ano usam todos os itens
   do artigo (2012+); 0 em 2007-2011. É marcador de regime (para filtrar e
   auditar), não feature: coincide com o período.

LIMITAÇÃO REGISTRADA: em 2007-2011 IDA/IDP (e portanto o IIE) são
aproximações com menos itens. Medido em 2012+, a versão parcial concorda com a
completa em Spearman ~0,89-0,93 (dimensões) e ~0,99 (IIE). Na virada 2011->2012
a persistência da posição da mesma escola cai em IDA (0,89 contra ~0,95) e
pouco em IDP/IIE. Ver analises/02_preenchimento_2007_2011.py.

Colunas criadas (6):
  DIM_IIB_zano DIM_IDA_zano DIM_IDP_zano DIM_IEP_zano IIE_zano INFRA_ITENS_COMPLETOS
Opção --com-prop (não faz parte do padrão) acrescenta DIM_<d>_prop (soma/nº de
itens disponíveis, 0 a 1) e IIE_prop (média simples das 4 dimensões prop).

Tipagem (regra 6): derivadas Float64 nullable; INFRA_ITENS_COMPLETOS Int8.

Uso:  python programas/05_indices_infra.py [--com-prop]
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
SAIDA_ETAPAS = GUSTAVO / "saida" / "etapas"
SAIDA_REL = GUSTAVO / "saida" / "relatorios"
SAIDA_BASE = GUSTAVO / "saida" / "base_atual.parquet"
IN_BASE = SAIDA_ETAPAS / "04_base_com_censo.parquet"
OUT = SAIDA_ETAPAS / "05_base_com_indices.parquet"
OUT_REL = SAIDA_REL / "indices_infra.txt"
OUT_JSON = SAIDA_REL / "indices_infra_parametros.json"

DIMENSOES = {
    "IIB": ["IIB_agua_potavel", "IIB_energia_rede", "IIB_coleta_lixo", "IIB_banheiro"],
    "IDA": ["IDA_despensa", "IDA_refeitorio", "IDA_sala_diretoria",
            "IDA_sala_professor", "IDA_secretaria"],
    "IDP": ["IDP_biblioteca", "IDP_lab_informatica", "IDP_patio_coberto",
            "IDP_patio_descoberto", "IDP_quadra_esportes"],
    "IEP": ["IEP_computador", "IEP_impressora", "IEP_projetor", "IEP_internet"],
}
ITENS = [i for l in DIMENSOES.values() for i in l]
MIN_ESCOLAS_ANO = 30
MIN_ITENS_DIM = 2
COL_FLAG = "INFRA_ITENS_COMPLETOS"


def nomes_colunas(com_prop=False):
    zano = [f"DIM_{d}_zano" for d in DIMENSOES] + ["IIE_zano"]
    prop = [f"DIM_{d}_prop" for d in DIMENSOES] + ["IIE_prop"] if com_prop else []
    return zano + prop + [COL_FLAG]


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
    """Função pura: recebe a base (04) e devolve as colunas novas e os parâmetros.
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


def relatorio(base, params, com_prop):
    L = ["ÍNDICES DE INFRAESTRUTURA — 05 (zano, ano a ano)", "=" * 78,
         f"Base: {base.shape[0]} × {base.shape[1]} ({len(nomes_colunas(com_prop))} colunas novas)", "",
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
    for ano in sorted(base["ANO"].astype(int).unique()):
        sub = base[base["ANO"].astype(int) == ano]
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--com-prop", action="store_true",
                    help="acrescenta DIM_*_prop e IIE_prop (fora do padrão)")
    args = ap.parse_args()

    print("=" * 78)
    print("05 — ÍNDICES DE INFRAESTRUTURA (zano, ano a ano)")
    print("=" * 78)
    if not IN_BASE.exists():
        print(f"[ERRO] não achei {IN_BASE} — rode 04 antes")
        sys.exit(1)
    base = pd.read_parquet(IN_BASE)
    faltam = [i for i in ITENS if i not in base.columns]
    if faltam:
        print(f"[ERRO] faltam colunas: {faltam} — rode 03 e 04")
        sys.exit(1)

    novas, params = calcular(base, com_prop=args.com_prop)
    saida = pd.concat([base, novas], axis=1)
    saida.to_parquet(OUT, index=False)
    shutil.copy2(OUT, SAIDA_BASE)
    print(f">>> {OUT}  ({saida.shape[0]} × {saida.shape[1]})")
    print(f">>> {SAIDA_BASE} (cópia)")

    SAIDA_REL.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8")
    L = relatorio(saida, params, args.com_prop)
    OUT_REL.write_text("\n".join(L), encoding="utf-8")
    print(f">>> {OUT_REL}\n>>> {OUT_JSON}\n")
    print("\n".join(L[:40]))
    if params["avisos"]:
        print("\n[AVISO] itens com cobertura parcial dentro do ano — ver relatório")


if __name__ == "__main__":
    main()
