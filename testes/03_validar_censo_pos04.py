# -*- coding: utf-8 -*-
"""
03 — Auditoria do parquet PÓS-04 (04_base_com_censo.parquet): estado das 18
variáveis de infraestrutura depois da correção da coleta (relatório 04).

NÃO olha para os índices do 05; isso é o testes/02_validar_indices.py.
Este teste serve para VER como a base ficou e provar que ela está certa:

  A. Estrutura   : shape, colunas, tipos, chave, o 04 preserva o 02b
  B. Variáveis   : as 18 do Quadro 3 do artigo (4/5/5/4), binárias
  C. Ausências   : NaN esperado (itens não coletados) x NaN inesperado
  D. Zeros       : "zero estrutural" (coluna toda 0) e variáveis quase constantes
  E. Recomputo   : refaz a regra de fonte do zero a partir do cache + estatística
                   nacional e compara célula a célula com o 04
  F. Microdados  : compara com o arquivo ORIGINAL do INEP, sem passar pelo cache
                   nem pelo script 03 (CSV 2019-2025; zips 2007-2018 com --completo)
  G. Merge       : escolas sem registro no Censo; escolas duplicadas
  H. Plausível   : saltos de um ano para o outro, instabilidade escola a escola,
                   combinações incoerentes, urbana x rural
  I. Antes x depois: compara com o 04 anterior à correção (backup)
  J. Uso no modelo : quantas linhas têm alvo + as 18 completas, por ano

Saída: gustavo/saida/relatorios/validacao_pos04.txt
Uso:   python testes/03_validar_censo_pos04.py [--sem-bruto] [--completo]
         --completo : confere também 2007-2018, lendo os zips originais (mais lento)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
ETAPAS = GUSTAVO / "saida" / "etapas"
REL = GUSTAVO / "saida" / "relatorios"
CACHE = GUSTAVO / "dados" / "cache" / "censo"
P04 = ETAPAS / "04_base_com_censo.parquet"
P02B = ETAPAS / "02b_tx_rend_longitudinal.parquet"
P_FONTES = REL / "fontes_features_censo.csv"
P_BACKUP = GUSTAVO / "saida" / "_backup_2026-10-14" / "etapas" / "04_base_com_censo.parquet"
REPORT = REL / "validacao_pos04.txt"
SEM_BRUTO = "--sem-bruto" in sys.argv




# ------------------------------------------------------------------
# Especificação INDEPENDENTE (Quadro 3 do artigo + substitutas por ano).
# Se o 03 mudar a regra, este teste acusa a diferença.
# ------------------------------------------------------------------
GRUPOS = {
    "IIB": ["IIB_agua_potavel", "IIB_energia_rede", "IIB_coleta_lixo", "IIB_banheiro"],
    "IDA": ["IDA_despensa", "IDA_refeitorio", "IDA_sala_diretoria",
            "IDA_sala_professor", "IDA_secretaria"],
    "IDP": ["IDP_biblioteca", "IDP_lab_informatica", "IDP_patio_coberto",
            "IDP_patio_descoberto", "IDP_quadra_esportes"],
    "IEP": ["IEP_computador", "IEP_impressora", "IEP_projetor", "IEP_internet"],
}
V18 = [v for l in GRUPOS.values() for v in l]
CANDIDATAS = {  # [coluna do artigo, substitutas]
    "IIB_agua_potavel": ["IN_AGUA_POTAVEL", "IN_AGUA_FILTRADA"],
    "IIB_energia_rede": ["IN_ENERGIA_REDE_PUBLICA"],
    "IIB_coleta_lixo": ["IN_LIXO_SERVICO_COLETA"],
    "IIB_banheiro": ["IN_BANHEIRO", "IN_BANHEIRO_DENTRO_PREDIO"],
    "IDA_despensa": ["IN_DESPENSA"], "IDA_refeitorio": ["IN_REFEITORIO"],
    "IDA_sala_diretoria": ["IN_SALA_DIRETORIA"], "IDA_sala_professor": ["IN_SALA_PROFESSOR"],
    "IDA_secretaria": ["IN_SECRETARIA"],
    "IDP_biblioteca": ["IN_BIBLIOTECA", "IN_BIBLIOTECA_SALA_LEITURA"],
    "IDP_lab_informatica": ["IN_LABORATORIO_INFORMATICA"],
    "IDP_patio_coberto": ["IN_PATIO_COBERTO"], "IDP_patio_descoberto": ["IN_PATIO_DESCOBERTO"],
    "IDP_quadra_esportes": ["IN_QUADRA_ESPORTES"],
    "IEP_computador": ["IN_COMPUTADOR"], "IEP_impressora": ["IN_EQUIP_IMPRESSORA"],
    "IEP_projetor": ["IN_EQUIP_MULTIMIDIA", "IN_EQUIP_RETROPROJETOR"],
    "IEP_internet": ["IN_INTERNET"],
}
# variáveis de coluna única e estável desde 2007: não podem mudar com a correção
SEM_MUDANCA = ["IIB_energia_rede", "IIB_coleta_lixo", "IDA_sala_diretoria",
               "IDA_sala_professor", "IDP_lab_informatica", "IDP_quadra_esportes",
               "IEP_computador", "IEP_impressora", "IEP_internet"]

log, cont = [], {"ok": 0, "warn": 0, "fail": 0}


def secao(t):
    log.extend(["", "=" * 78, t, "=" * 78])


def ok(m):
    cont["ok"] += 1; log.append(f"  ✅ {m}")


def warn(m):
    cont["warn"] += 1; log.append(f"  ⚠️  {m}")


def fail(m):
    cont["fail"] += 1; log.append(f"  ❌ {m}")


def info(m):
    log.append(f"     {m}")


def check(c, m_ok, m_fail):
    ok(m_ok) if c else fail(m_fail)


def tabela(df, fmt, vazio="--", larg=4):
    """Matriz variável x ano em texto."""
    anos = list(df.columns)
    out = ["     " + f"{'':<22}" + "".join(f"{str(a)[2:]:>{larg}}" for a in anos)]
    for v in df.index:
        cel = ["{:>{w}}".format(vazio if pd.isna(x) else fmt(x), w=larg) for x in df.loc[v]]
        out.append("     " + f"{v:<22}" + "".join(cel))
    return out


def iguais(a, b, tol=1e-12):
    a, b = pd.to_numeric(a).astype("float64"), pd.to_numeric(b).astype("float64")
    return ((a.isna() & b.isna()) | ((a - b).abs() < tol)).all()


# ------------------------------------------------------------------
secao("A. ESTRUTURA")
# ------------------------------------------------------------------
for p in (P04, P02B, P_FONTES):
    if not p.exists():
        print(f"[ERRO] falta {p} — rode o pipeline (python programas/99_pipeline.py)")
        sys.exit(1)
b = pd.read_parquet(P04)
lon = pd.read_parquet(P02B)
fontes = pd.read_csv(P_FONTES, dtype={"coluna_usada": "string"}).fillna({"coluna_usada": ""})
b["ANO_I"] = b["ANO"].astype(int)
ANOS = sorted(b["ANO_I"].unique())

shape04 = (b.shape[0], b.shape[1] - 1)  # sem a coluna auxiliar ANO_I
check(shape04 == (len(lon), len(lon.columns) + 19),
      f"shape {shape04[0]:,} × {shape04[1]}: mesmas linhas do 02b + 18 variáveis + INFRA_FONTE_ARTIGO",
      f"shape inesperado: {shape04} (02b tem {lon.shape})")
extra = set(b.columns) - set(lon.columns) - set(V18) - {"INFRA_FONTE_ARTIGO", "ANO_I"}
check(not extra, "nenhuma coluna além de 02b + 18 + INFRA_FONTE_ARTIGO",
      f"colunas inesperadas: {sorted(extra)}")
check(not [c for c in b.columns if c.startswith(("DIM_", "IIE_"))],
      "sem colunas do 05 (esta é a base pós-04)", "colunas do 05 presentes no 04")
check(b.duplicated(["ANO", "CO_ENTIDADE"]).sum() == 0, "chave (ANO, CO_ENTIDADE) única",
      "chave duplicada")
mesmas_chaves = (b["ANO"].values == lon["ANO"].values).all() and \
                (b["CO_ENTIDADE"].values == lon["CO_ENTIDADE"].values).all()
check(mesmas_chaves, "mesma ordem e chaves do 02b", "ordem/chaves diferem do 02b")
dif02 = [c for c in lon.columns if not b[c].equals(lon[c])]
check(not dif02, f"as {len(lon.columns)} colunas do 02b estão intactas no 04",
      f"colunas do 02b alteradas no 04: {dif02}")
check(str(b["CO_ENTIDADE"].dtype) == "string", "CO_ENTIDADE é string (regra 6)", f"CO_ENTIDADE é {b['CO_ENTIDADE'].dtype}, deveria ser string")
check(str(b["ANO"].dtype) == "Int16", "ANO é Int16", f"ANO é {b['ANO'].dtype}")
check(all(str(b[v].dtype) == "Int8" for v in V18),
      "18 variáveis são Int8 nullable (regra 6: IN_* como Int8, nunca int8/float)",
      f"tipos fora da regra 6: {[(v, str(b[v].dtype)) for v in V18 if str(b[v].dtype) != 'Int8']}")
check(str(b["INFRA_FONTE_ARTIGO"].dtype) == "Int8", "INFRA_FONTE_ARTIGO é Int8 nullable",
      f"INFRA_FONTE_ARTIGO é {b['INFRA_FONTE_ARTIGO'].dtype}")
b[V18] = b[V18].astype("float64")  # a partir daqui, contas em float (NA -> NaN)
fa = b.groupby("ANO_I")["INFRA_FONTE_ARTIGO"].nunique(dropna=False)
check((fa == 1).all(), "INFRA_FONTE_ARTIGO constante dentro de cada ano",
      f"INFRA_FONTE_ARTIGO varia dentro do ano: {fa[fa > 1].index.tolist()}")

# ------------------------------------------------------------------
secao("B. AS 18 VARIÁVEIS DO ARTIGO (Quadro 3)")
# ------------------------------------------------------------------
check([len(l) for l in GRUPOS.values()] == [4, 5, 5, 4] and len(V18) == 18,
      "especificação do teste: IIB 4 + IDA 5 + IDP 5 + IEP 4 = 18", "especificação interna incoerente")
prefixados = [c for c in b.columns if c.startswith(("IIB_", "IDA_", "IDP_", "IEP_"))]
check(sorted(prefixados) == sorted(V18), "as colunas IIB_/IDA_/IDP_/IEP_ da base são exatamente as 18",
      f"diferença: faltam {sorted(set(V18) - set(prefixados))}, sobram {sorted(set(prefixados) - set(V18))}")
check("IDP_patio_descoberto" in b.columns, "IDP_patio_descoberto presente (a 18ª variável)",
      "IDP_patio_descoberto ausente")
nao_bin = {v: sorted(set(b[v].dropna().unique()))[:4] for v in V18
           if not set(b[v].dropna().unique()) <= {0.0, 1.0}}
check(not nao_bin, "todas binárias (0/1)", f"valores fora de 0/1: {nao_bin}")
check(not np.isinf(b[V18].to_numpy(dtype=float)).any(), "sem valores infinitos", "há infinitos")

# ------------------------------------------------------------------
secao("C. AUSÊNCIAS: NaN esperado x inesperado")
# ------------------------------------------------------------------
aus_esp = fontes[fontes["coluna_usada"] == ""].groupby("ano")["variavel"].apply(set).to_dict()
nan_tab = b.groupby("ANO_I")[V18].apply(lambda d: d.isna().mean() * 100).T
inesp, faltam_nan = [], []
for ano in ANOS:
    sub = b[b["ANO_I"] == ano]
    todo = {v for v in V18 if sub[v].isna().all()}
    esp = aus_esp.get(ano, set())
    if todo != esp:
        inesp.append((ano, sorted(todo ^ esp)))
check(not inesp, "variáveis 100% ausentes por ano = as declaradas em fontes_features_censo.csv",
      f"diferenças (ano, variáveis): {inesp[:4]}")
info("% de escolas SEM valor, por variável e ano (-- = 0%; 100 = não coletada naquele ano):")
log.extend(tabela(nan_tab.replace(0, np.nan), lambda x: f"{x:.0f}"))
parcial = [(v, int(a), round(nan_tab.loc[v, a], 1)) for v in V18 for a in ANOS
           if 0 < nan_tab.loc[v, a] < 100 and nan_tab.loc[v, a] > 10]
(warn if parcial else ok)(
    f"ausência parcial >10% (escola sem registro no Censo naquele ano): {parcial[:5]}" if parcial
    else "ausência parcial ≤10% em todos os (variável, ano) coletados")

# ------------------------------------------------------------------
secao("D. ZEROS ESTRUTURAIS E VARIÁVEIS QUASE CONSTANTES")
# ------------------------------------------------------------------
prev = b.groupby("ANO_I")[V18].mean().T * 100
zeros = [(v, a) for v in V18 for a in ANOS
         if b[(b["ANO_I"] == a)][v].notna().sum() >= 30 and prev.loc[v, a] == 0]
check(not zeros, "nenhuma variável coletada vem toda 0 em algum ano (o erro de 2019–2021 sumiu)",
      f"ZERO ESTRUTURAL (variável, ano): {zeros[:8]}")
uns = [(v, a) for v in V18 for a in ANOS
       if b[(b["ANO_I"] == a)][v].notna().sum() >= 30 and prev.loc[v, a] == 100]
(warn if uns else ok)(f"variável toda 1 em algum ano: {uns[:6]}" if uns else "nenhuma variável toda 1")
baixa = [(v, a, round(prev.loc[v, a], 1)) for v in V18 for a in ANOS
         if b[(b["ANO_I"] == a)][v].notna().sum() >= 30 and 0 < prev.loc[v, a] < 2]
(warn if baixa else ok)(f"prevalência <2% (quase constante): {baixa[:6]}" if baixa
                         else "nenhuma variável com prevalência <2% nos anos coletados")
info("PREVALÊNCIA (% de escolas com o item = 1), por variável e ano:")
log.extend(tabela(prev, lambda x: f"{x:.0f}"))

# ------------------------------------------------------------------
secao("E. RECOMPUTO DA REGRA DE FONTE (cache + estatística nacional)")
# ------------------------------------------------------------------
if not CACHE.exists() or not list(CACHE.glob("*_nacional.json")):
    warn("cache do Censo ausente — recomputo pulado (rode o 03)")
else:
    erros, fonte_div, celulas = [], [], 0
    for ano in ANOS:
        cp, sp = CACHE / f"{ano}.parquet", CACHE / f"{ano}_nacional.json"
        if not (cp.exists() and sp.exists()):
            erros.append((ano, "cache ausente")); continue
        cru = pd.read_parquet(cp)
        cru["CO_ENTIDADE"] = cru["CO_ENTIDADE"].astype(str).str.strip()
        st = json.loads(sp.read_text(encoding="utf-8"))
        sub = b[b["ANO_I"] == ano][["CO_ENTIDADE"] + V18]
        m = sub.merge(cru, on="CO_ENTIDADE", how="left", suffixes=("", "_cru"), indicator=True)
        for v in V18:
            usada = next((c for c in CANDIDATAS[v] if c in st and st[c]["uns"] > 0), None)
            f_csv = fontes[(fontes["ano"] == ano) & (fontes["variavel"] == v)]["coluna_usada"].iloc[0]
            if (usada or "") != f_csv:
                fonte_div.append((ano, v, usada, f_csv))
            esperado = pd.Series(np.nan, index=m.index) if usada is None else \
                pd.to_numeric(m[usada], errors="coerce")
            celulas += len(m)
            if not iguais(m[v], esperado):
                erros.append((ano, v, int((~((m[v].isna() & esperado.isna()) | (m[v] == esperado))).sum())))
    check(not fonte_div, "coluna usada em fontes_features_censo.csv = regra recomputada (19 anos × 18 variáveis)",
          f"fontes divergentes: {fonte_div[:4]}")
    check(not erros, f"{celulas:,} células do 04 conferem com a regra recomputada do cache",
          f"células divergentes (ano, variável, n): {erros[:6]}")

# ------------------------------------------------------------------
secao("F. COMPARAÇÃO COM O MICRODADO ORIGINAL DO INEP (sem cache, sem o script 03)")
# ------------------------------------------------------------------
import zipfile  # noqa: E402

COMPLETO = "--completo" in sys.argv
UF_COLS = ("SG_UF", "UF", "SG_UF_ESCOLA", "CO_UF", "COD_UF", "CODIGO_UF", "CO_UF_ESCOLA")
ID_COLS = ("CO_ENTIDADE", "COD_ESCOLA", "CO_ESCOLA")


def _fonte_original(base_proj, ano):
    """(abrir, descricao) do arquivo ORIGINAL do ano: CSV em bruto, senão zip em origem."""
    pasta = base_proj / "dados" / "bruto" / "censo"
    csvs = [f for f in pasta.glob(f"*{ano}*") if f.suffix.lower() == ".csv"
            and ("escola" in f.name.lower() or "ed_basica" in f.name.lower())]
    if csvs:
        arq = max(csvs, key=lambda f: f.stat().st_size)
        return (lambda: open(arq, "rb")), arq.name
    zips = list((base_proj / "dados" / "origem" / "censo").glob(f"*{ano}*.zip"))
    if not zips:
        return None, None
    zf = zipfile.ZipFile(zips[0])
    csv_int = [i for i in zf.infolist() if i.filename.lower().endswith(".csv")]
    if not csv_int:
        return None, None
    maior = max(csv_int, key=lambda i: i.file_size)
    return (lambda: zf.open(maior)), f"{zips[0].name}::{maior.filename}"


def _ler_rr(abrir, colunas):
    """Lê só as colunas pedidas e devolve as linhas de RR (CO_ENTIDADE como str)."""
    for sep in (";", ",", "|"):
        with abrir() as f:
            cab = list(pd.read_csv(f, sep=sep, encoding="latin1", nrows=0).columns)
        if len(cab) >= 5:
            break
    up = {c.upper().strip(): c for c in cab}
    uf = next((up[c] for c in UF_COLS if c in up), None)
    idc = next((up[c] for c in ID_COLS if c in up), None)
    if uf is None or idc is None:
        raise RuntimeError("sem coluna de UF ou de ID")
    usar = sorted({up[c] for c in colunas if c in up} | {uf, idc})
    partes = []
    with abrir() as f:
        for ch in pd.read_csv(f, sep=sep, encoding="latin1", usecols=usar,
                              chunksize=300_000, low_memory=False):
            if ch[uf].dtype == object or str(ch[uf].dtype).startswith("str"):
                m = ch[uf].astype(str).str.strip().str.upper() == "RR"
            else:
                m = pd.to_numeric(ch[uf], errors="coerce") == 14
            partes.append(ch[m])
    rr = pd.concat(partes, ignore_index=True)
    rr.columns = [c.upper().strip() for c in rr.columns]
    rr = rr.rename(columns={idc.upper().strip(): "CO_ENTIDADE"})
    rr["CO_ENTIDADE"] = rr["CO_ENTIDADE"].astype(str).str.strip()
    return rr


BASE = RAIZ
if SEM_BRUTO or BASE is None:
    warn("verificação nos microdados originais pulada (--sem-bruto ou pasta não achada)")
else:
    verificados, pulados = [], []
    for ano in ANOS:
        abrir, nome = _fonte_original(BASE, ano)
        eh_zip = nome is not None and "::" in nome
        if abrir is None or (eh_zip and not COMPLETO):
            pulados.append(ano); continue
        usadas = fontes[(fontes["ano"] == ano) & (fontes["coluna_usada"] != "")]
        try:
            raw = _ler_rr(abrir, set(usadas["coluna_usada"]))
        except Exception as e:  # noqa: BLE001
            warn(f"{ano}: falha lendo {nome}: {e}"); continue
        sub = b[b["ANO_I"] == ano][["CO_ENTIDADE"] + V18]
        m = sub.merge(raw, on="CO_ENTIDADE", how="left", suffixes=("", "_raw"))
        ruins = []
        for r in usadas.itertuples():
            esp = pd.to_numeric(m[r.coluna_usada], errors="coerce")
            if not iguais(m[r.variavel], esp):
                ruins.append((r.variavel, int((~((m[r.variavel].isna() & esp.isna())
                                                 | (m[r.variavel] == esp))).sum())))
        for v in set(V18) - set(usadas["variavel"]):          # não coletadas: devem ser NaN
            if m[v].notna().any():
                ruins.append((v, "esperado todo NaN"))
        sem_match = int(m[usadas["coluna_usada"].iloc[0]].isna().all()) if len(usadas) else 0
        if ruins or sem_match:
            fail(f"{ano}: divergências com o original {nome} (variável, n): {ruins or 'nenhuma escola casou'}")
        else:
            verificados.append(ano)
            info(f"{ano}: ok  ({len(sub)} escolas)  <- {nome}")
    if verificados:
        ok(f"{len(verificados)} anos conferem célula a célula com o microdado ORIGINAL: "
           f"{verificados[0]}–{verificados[-1]}" if len(verificados) > 1 else f"ano {verificados[0]} confere")
    if pulados:
        warn(f"anos NÃO conferidos com o original (só zip; use --completo): {pulados}")

# ------------------------------------------------------------------
secao("G. MERGE COM O TX_REND")
# ------------------------------------------------------------------
sem_censo = b[b["INFRA_FONTE_ARTIGO"].isna()]
check(len(sem_censo) == 0, "toda escola do tx_rend tem registro no Censo do mesmo ano",
      f"{len(sem_censo)} linhas sem registro no Censo (por ano: "
      f"{sem_censo.groupby('ANO_I').size().to_dict()})")
cob = b.groupby("ANO_I").size()
info("escolas por ano na base: " + "  ".join(f"{a}:{n}" for a, n in cob.items()))

# ------------------------------------------------------------------
secao("H. PLAUSIBILIDADE")
# ------------------------------------------------------------------
# H1. saltos ano a ano, ignorando trocas de coluna-fonte conhecidas
fmap = fontes.set_index(["variavel", "ano"])["coluna_usada"]
saltos = []
for v in V18:
    for a0, a1 in zip(ANOS[:-1], ANOS[1:]):
        if np.isnan(prev.loc[v, a0]) or np.isnan(prev.loc[v, a1]):
            continue
        if fmap.get((v, a0)) != fmap.get((v, a1)):
            continue  # troca de pergunta: salto esperado
        d = prev.loc[v, a1] - prev.loc[v, a0]
        if abs(d) > 15:
            saltos.append((v, f"{a0}->{a1}", round(d, 1)))
(warn if saltos else ok)(
    f"saltos >15 p.p. entre anos consecutivos SEM troca de coluna: {saltos}" if saltos
    else "nenhum salto >15 p.p. entre anos consecutivos sem troca de coluna")
def _n_trocas(serie):
    v = serie.astype(str).to_numpy()
    return int((v[1:] != v[:-1]).sum())


trocas = fontes.sort_values(["variavel", "ano"]).groupby("variavel")["coluna_usada"].apply(_n_trocas)
info("trocas de coluna-fonte ao longo de 2007-2025 (quebra de pergunta): " +
     ", ".join(f"{v.split('_', 1)[1]}={n}" for v, n in trocas.items() if n > 0))

# H2. instabilidade escola a escola
ordem = b.sort_values(["CO_ENTIDADE", "ANO_I"])
flip = {}
for v in V18:
    g = ordem[["CO_ENTIDADE", "ANO_I", v]].copy()
    g["prev"] = g.groupby("CO_ENTIDADE")[v].shift()
    g["ano_prev"] = g.groupby("CO_ENTIDADE")["ANO_I"].shift()
    g = g[(g["ANO_I"] - g["ano_prev"] == 1) & g[v].notna() & g["prev"].notna()]
    g = g[[fmap.get((v, int(a))) == fmap.get((v, int(a) - 1)) for a in g["ANO_I"]]]
    flip[v] = (g[v] != g["prev"]).mean() * 100 if len(g) else np.nan
fl = pd.Series(flip)
altos = fl[fl > 30]
(warn if len(altos) else ok)(
    f"variáveis que mudam >30% entre anos consecutivos (mesma escola): {altos.round(1).to_dict()}"
    if len(altos) else "instabilidade escola a escola ≤30% em todas as variáveis")
info("% de escolas que trocam 0↔1 de um ano para o seguinte: " +
     ", ".join(f"{v.split('_', 1)[1]}={x:.0f}" for v, x in fl.items()))

# H3. combinações incoerentes
sub = b[b["ANO_I"] >= 2012]
inc = {
    "lab_informatica=1 sem computador": ((sub["IDP_lab_informatica"] == 1) & (sub["IEP_computador"] == 0)).mean() * 100,
    "internet=1 sem computador": ((sub["IEP_internet"] == 1) & (sub["IEP_computador"] == 0)).mean() * 100,
    "projetor=1 sem computador": ((sub["IEP_projetor"] == 1) & (sub["IEP_computador"] == 0)).mean() * 100,
}
for k, x in inc.items():
    (warn if x > 10 else ok)(f"{k}: {x:.1f}% das linhas (2012+)")

# H4. urbana x rural
for ano in (2019, 2024):
    s = b[b["ANO_I"] == ano].groupby("LOCALIZACAO")[V18].mean()
    if {"Urbana", "Rural"} <= set(s.index):
        melhor = [v for v in V18 if s.loc["Urbana", v] >= s.loc["Rural", v]]
        (ok if len(melhor) >= 15 else warn)(
            f"{ano}: urbana ≥ rural em {len(melhor)}/18 itens"
            + ("" if len(melhor) == 18 else f" (exceções: {[v for v in V18 if v not in melhor]})"))

# ------------------------------------------------------------------
secao("I. ANTES x DEPOIS DA CORREÇÃO (04 anterior, em saida/_backup_2026-10-14)")
# ------------------------------------------------------------------
if not P_BACKUP.exists():
    info("PULADA: o backup do 04 anterior não veio para o abandono-rr; o pytest registra a seção como "
         "pulada (testes/test_validacoes.py::test_03_comparacao_com_backup_de_outubro)")
else:
    old = pd.read_parquet(P_BACKUP)
    old["ANO_I"] = old["ANO"].astype(int)
    velhas = [v for v in V18 if v in old.columns]
    m = b[["ANO_I", "CO_ENTIDADE"] + velhas].merge(
        old[["ANO_I", "CO_ENTIDADE"] + velhas], on=["ANO_I", "CO_ENTIDADE"],
        suffixes=("", "_old"), validate="1:1")
    check(len(m) == len(b) == len(old), f"mesmas {len(m):,} linhas antes e depois",
          f"linhas diferentes: novo {len(b)}, antigo {len(old)}, comum {len(m)}")
    info(f"{'variável':<22}{'células mudadas':>16}   anos com mudança")
    mudou = {}
    for v in velhas:
        d = ~((m[v].isna() & m[v + "_old"].isna()) | (m[v] == m[v + "_old"]))
        mudou[v] = d
        anos_d = sorted(m.loc[d, "ANO_I"].unique())
        txt_anos = ",".join(str(a)[2:] for a in anos_d) or "-"
        info(f"{v:<22}{int(d.sum()):>16,}   {txt_anos}")
    intactas = [v for v in SEM_MUDANCA if mudou[v].sum() == 0]
    check(len(intactas) == len(SEM_MUDANCA),
          f"as {len(SEM_MUDANCA)} variáveis sem troca de coluna estão idênticas ao 04 anterior "
          "(correção sem efeito colateral)",
          f"variáveis que NÃO deveriam mudar mas mudaram: {[v for v in SEM_MUDANCA if v not in intactas]}")
    ant = b[b["ANO_I"].between(2019, 2021)]
    antigo = old[old["ANO_I"].between(2019, 2021)]
    for v in ("IIB_agua_potavel", "IIB_banheiro", "IEP_projetor"):
        info(f"{v}: média 2019-2021 antes={antigo[v].mean():.2f} → depois={ant[v].mean():.2f}")

# ------------------------------------------------------------------
secao("J. USO NO MODELO: linhas com alvo e com as 18 completas")
# ------------------------------------------------------------------
comp = b[V18].notna().all(axis=1)
b["_comp"] = comp
linhas = []
for ano in ANOS:
    s = b[b["ANO_I"] == ano]
    linhas.append((ano, len(s), int(s["ABANDONO_FUN_AF_T1"].notna().sum()),
                   int((s["ABANDONO_FUN_AF_T1"].notna() & s["_comp"]).sum()),
                   int(s["ABANDONO_MED_T1"].notna().sum()),
                   int((s["ABANDONO_MED_T1"].notna() & s["_comp"]).sum())))
info(f"{'ano':>5}{'escolas':>9}{'alvo AF':>9}{'AF+18':>8}{'alvo EM':>9}{'EM+18':>8}")
for r in linhas:
    info(f"{r[0]:>5}{r[1]:>9}{r[2]:>9}{r[3]:>8}{r[4]:>9}{r[5]:>8}")
tot = np.array([r[1:] for r in linhas]).sum(axis=0)
info(f"{'total':>5}{tot[0]:>9}{tot[1]:>9}{tot[2]:>8}{tot[3]:>9}{tot[4]:>8}")
apto = [r[0] for r in linhas if r[3] > 0]
info(f"anos em que há linhas AF com as 18 completas: {apto[0]}–{apto[-1]}"
     if apto else "nenhum ano com as 18 completas")
check(all(r[3] > 0 for r in linhas if r[0] >= 2012 and r[0] <= 2024),
      "2012–2024 têm linhas com alvo AF e as 18 completas", "algum ano 2012–2024 sem linhas completas")

# ------------------------------------------------------------------
secao("RESUMO")
# ------------------------------------------------------------------
log += [f"  ✅ OK:      {cont['ok']}", f"  ⚠️  Warn:   {cont['warn']}",
        f"  ❌ Falhas:  {cont['fail']}", "",
        "  🎉 BASE PÓS-04 VALIDADA" if cont["fail"] == 0 else f"  ❌ {cont['fail']} falhas — revisar"]
txt = "\n".join(log)
print(txt)
REPORT.write_text(txt, encoding="utf-8")
print(f"\n>>> Relatório: {REPORT}")
sys.exit(1 if cont["fail"] else 0)
