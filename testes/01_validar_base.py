# -*- coding: utf-8 -*-
"""
01 — Valida a base completa (todas as etapas do pipeline).

Lê os parquets de saida/etapas/ e roda ~30 checks:
  - selecionado (02a)  : tipagem, chave única, taxas em [0,100], sem '--'
  - longitudinal (02b) : LAG/DELTA/T1 coerentes escola a escola, ANO_ALVO
  - censo (03)         : 18 features binárias, sem "zeros estruturais"
  - base final (04)    : cobertura no universo tx_rend, chaves únicas
  - índices (05)       : 04 + 6 colunas (a validação detalhada está em
                         testes/02_validar_indices.py)
  - base_atual.parquet : idêntica ao 05
  - 01 bruto x 02b     : mesmas escolas em cada ano (seção 14)

Saída:
    gustavo/saida/relatorios/validacao_base.txt

Uso:  python testes/01_validar_base.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# Descoberta das pastas
# ------------------------------------------------------------------


RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
BASE_PROJETO = RAIZ  # antes: a pasta abandono-escolar; os dados agora ficam em RAIZ/dados

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
SAIDA_ETAPAS = GUSTAVO / "saida" / "etapas"
SAIDA_REL = GUSTAVO / "saida" / "relatorios"
SAIDA_REL.mkdir(parents=True, exist_ok=True)

P_SEL = SAIDA_ETAPAS / "02a_tx_rend_selecionado.parquet"
P_LONG = SAIDA_ETAPAS / "02b_tx_rend_longitudinal.parquet"
P_CENSO = SAIDA_ETAPAS / "03_censo_features.parquet"
P_FINAL = SAIDA_ETAPAS / "04_base_com_censo.parquet"
P_IND = SAIDA_ETAPAS / "05_base_com_indices.parquet"
P_FONTES = SAIDA_REL / "fontes_features_censo.csv"
P_BRUTO = SAIDA_ETAPAS / "01_tx_rend_bruto.parquet"
P_ATUAL = GUSTAVO / "saida" / "base_atual.parquet"

REPORT = SAIDA_REL / "validacao_base.txt"

# ------------------------------------------------------------------
# Acumuladores
# ------------------------------------------------------------------
log = []
n_ok = n_warn = n_fail = 0


def secao(t):
    log.append("")
    log.append("=" * 78)
    log.append(t)
    log.append("=" * 78)


def ok(msg):
    global n_ok
    n_ok += 1
    log.append(f"  ✅ {msg}")


def warn(msg):
    global n_warn
    n_warn += 1
    log.append(f"  ⚠️  {msg}")


def fail(msg):
    global n_fail
    n_fail += 1
    log.append(f"  ❌ {msg}")


def info(msg):
    log.append(f"     {msg}")


def normalizar_id(serie):
    return pd.to_numeric(serie, errors="coerce").dropna().astype("Int64").astype("string")


# ==================================================================
# Carregamento
# ==================================================================
secao("0. CARREGAMENTO")

paths_obrigatorios = {
    "02a selecionado": P_SEL,
    "02b longitudinal": P_LONG,
    "03 censo": P_CENSO,
    "04 base final": P_FINAL,
    "05 base com índices": P_IND,
    "fontes do censo": P_FONTES,
    "base_atual": P_ATUAL,
}
for nome, p in paths_obrigatorios.items():
    if not p.exists():
        print(f"[ERRO] falta {nome}: {p}")
        sys.exit(1)

sel = pd.read_parquet(P_SEL)
lon = pd.read_parquet(P_LONG)
censo = pd.read_parquet(P_CENSO)
base = pd.read_parquet(P_FINAL)
ind = pd.read_parquet(P_IND)
fontes = pd.read_csv(P_FONTES, dtype={'coluna_usada': 'string'}).fillna({'coluna_usada': ''})
atual = pd.read_parquet(P_ATUAL)

ok(f"02a selecionado:    {sel.shape[0]:>7,} × {sel.shape[1]:>3}")
ok(f"02b longitudinal:   {lon.shape[0]:>7,} × {lon.shape[1]:>3}")
ok(f"03 censo features:  {censo.shape[0]:>7,} × {censo.shape[1]:>3}")
ok(f"04 base final:      {base.shape[0]:>7,} × {base.shape[1]:>3}")
ok(f"05 com índices:     {ind.shape[0]:>7,} × {ind.shape[1]:>3}")
ok(f"base_atual:         {atual.shape[0]:>7,} × {atual.shape[1]:>3}")

anos = sorted(base["ANO"].dropna().unique().tolist())
info(f"anos: {anos}")


# ==================================================================
# 1. Tipagem (regra 6)
# ==================================================================
secao("1. TIPAGEM (regra 6 do CLAUDE.md)")

if str(sel["CO_ENTIDADE"].dtype) == "string":
    ok("CO_ENTIDADE é string")
else:
    fail(f"CO_ENTIDADE é {sel['CO_ENTIDADE'].dtype}")

if str(sel["CO_MUNICIPIO"].dtype) == "string":
    ok("CO_MUNICIPIO é string")
else:
    warn(f"CO_MUNICIPIO é {sel['CO_MUNICIPIO'].dtype}")

if "int" in str(sel["ANO"].dtype).lower():
    ok(f"ANO é inteiro ({sel['ANO'].dtype})")
else:
    fail(f"ANO é {sel['ANO'].dtype}")

TAXAS = [c for c in sel.columns
         if c.startswith(("APROVACAO_", "REPROVACAO_", "ABANDONO_"))]
nao_float = [c for c in TAXAS if str(sel[c].dtype) != "Float64"]
if not nao_float:
    ok(f"todas as {len(TAXAS)} taxas são Float64 nullable")
else:
    fail(f"taxas não-Float64: {nao_float}")


for nome_est, df_est in [("02b", lon), ("03", censo), ("04", base), ("05", ind)]:
    if str(df_est["CO_ENTIDADE"].dtype) == "string" and str(df_est["ANO"].dtype) in ("Int16", "int16"):
        ok(f"{nome_est}: CO_ENTIDADE string e ANO inteiro 16 bits")
    else:
        fail(f"{nome_est}: CO_ENTIDADE={df_est['CO_ENTIDADE'].dtype}, ANO={df_est['ANO'].dtype}")
v18 = [c for c in base.columns if c.startswith(("IIB_", "IDA_", "IDP_", "IEP_"))]
if all(str(base[c].dtype) == "Int8" for c in v18) and str(base["INFRA_FONTE_ARTIGO"].dtype) == "Int8":
    ok("04: 18 variáveis do Censo e INFRA_FONTE_ARTIGO são Int8 nullable")
else:
    fail("04: variáveis do Censo fora do tipo Int8")

# ==================================================================
# 2. Chave composta única
# ==================================================================
secao("2. CHAVE (ANO, CO_ENTIDADE)")

for nome, df in [("02a", sel), ("02b", lon), ("04", base), ("atual", atual)]:
    n_max = df.groupby(["ANO", "CO_ENTIDADE"]).size().max()
    if n_max == 1:
        ok(f"{nome}: chave única")
    else:
        fail(f"{nome}: chave não única (máx {n_max})")


# ==================================================================
# 3. '--' residual
# ==================================================================
secao("3. VALORES '--' RESIDUAIS (regra 5)")

for nome, df in [("02a", sel), ("02b", lon), ("04", base)]:
    encontrados = 0
    for c in df.columns:
        if df[c].dtype == object or "string" in str(df[c].dtype):
            encontrados += int((df[c].astype(str).str.strip() == "--").sum())
    if encontrados == 0:
        ok(f"{nome}: nenhum '--'")
    else:
        fail(f"{nome}: {encontrados} '--' residuais")


# ==================================================================
# 4. Cobertura de escolas por ano
# ==================================================================
secao("4. COBERTURA POR ANO")

por_ano = sel.groupby("ANO").agg(
    linhas=("CO_ENTIDADE", "size"),
    escolas=("CO_ENTIDADE", "nunique"),
)
if (por_ano["linhas"] == por_ano["escolas"]).all():
    ok("todos os anos: linhas == escolas únicas")
else:
    fail("há duplicatas em algum ano")

if len(por_ano) == 19:
    ok("19 anos cobertos (2007-2025)")
else:
    fail(f"esperado 19 anos, obtido {len(por_ano)}")


# ==================================================================
# 5. Taxas em [0, 100]
# ==================================================================
secao("5. TAXAS EM [0, 100]")

for c in TAXAS:
    v = pd.to_numeric(sel[c], errors="coerce")
    fora = int(((v < 0) | (v > 100)).sum())
    if fora > 0:
        fail(f"{c}: {fora} valores fora de [0, 100]")
if all((pd.to_numeric(sel[c], errors="coerce").between(0, 100) |
        pd.to_numeric(sel[c], errors="coerce").isna()).all() for c in TAXAS):
    ok(f"todas as {len(TAXAS)} taxas dentro de [0, 100]")


# ==================================================================
# 6. Curva temporal — 2020 é a anomalia
# ==================================================================
secao("6. CURVA TEMPORAL")

curva = sel.groupby("ANO")["ABANDONO_FUN_AF"].mean().round(2)
log.append(curva.to_string())

if curva.get(2020, 99) < curva.get(2019, 0):
    ok(f"2020 ({curva.get(2020):.2f}) < 2019 ({curva.get(2019):.2f})")
else:
    fail("2020 não é vale")

if curva.get(2022, 0) > curva.get(2021, 0):
    ok(f"2022 ({curva.get(2022):.2f}) > 2021 ({curva.get(2021):.2f})")
else:
    warn("2022 não é maior que 2021")


# ==================================================================
# 7. LAG1 = valor do ano anterior
# ==================================================================
secao("7. LAG1 COERENTE")

lon_ord = lon.sort_values(["CO_ENTIDADE", "ANO"]).reset_index(drop=True)
lon_ord["_esp"] = lon_ord.groupby("CO_ENTIDADE")["ABANDONO_FUN_AF"].shift(1)
mask = lon_ord["ABANDONO_FUN_AF_LAG1"].notna()
esperado = lon_ord.loc[mask, "_esp"]
obtido = lon_ord.loc[mask, "ABANDONO_FUN_AF_LAG1"]
comparaveis = esperado.notna() & obtido.notna()
diff = (esperado[comparaveis].astype(float) - obtido[comparaveis].astype(float)).abs()
n_diff = int((diff > 0.01).sum())
if n_diff == 0:
    ok(f"ABANDONO_FUN_AF_LAG1 = ABANDONO_FUN_AF[t-1] em {comparaveis.sum()} linhas")
else:
    fail(f"LAG1 divergente em {n_diff} linhas")


# ==================================================================
# 8. DELTA1 = valor - LAG1
# ==================================================================
secao("8. DELTA1 COERENTE")

mask = lon["ABANDONO_FUN_AF_DELTA1"].notna() & lon["ABANDONO_FUN_AF_LAG1"].notna()
esp = lon.loc[mask, "ABANDONO_FUN_AF"].astype(float) - lon.loc[mask, "ABANDONO_FUN_AF_LAG1"].astype(float)
obt = lon.loc[mask, "ABANDONO_FUN_AF_DELTA1"].astype(float)
n_diff = int(((esp - obt).abs() > 0.01).sum())
if n_diff == 0:
    ok(f"DELTA1 = valor - LAG1 em {mask.sum()} linhas")
else:
    fail(f"DELTA1 divergente em {n_diff}")


# ==================================================================
# 9. T1 = valor do ano seguinte
# ==================================================================
secao("9. T1 COERENTE")

lon_ord["_esp_t1"] = lon_ord.groupby("CO_ENTIDADE")["ABANDONO_FUN_AF"].shift(-1)
mask = lon_ord["ABANDONO_FUN_AF_T1"].notna()
esp = lon_ord.loc[mask, "_esp_t1"]
obt = lon_ord.loc[mask, "ABANDONO_FUN_AF_T1"]
comp = esp.notna() & obt.notna()
n_diff = int(((esp[comp].astype(float) - obt[comp].astype(float)).abs() > 0.01).sum())
if n_diff == 0:
    ok(f"ABANDONO_FUN_AF_T1 = ABANDONO_FUN_AF[t+1] em {comp.sum()} linhas")
else:
    fail(f"T1 divergente em {n_diff}")


# ==================================================================
# 10. ANO_ALVO
# ==================================================================
secao("10. ANO_ALVO")

sem_alvo = lon[lon["ANO_ALVO"].isna()]
n_2025 = int((sem_alvo["ANO"] == 2025).sum())
if n_2025 == 687:
    ok(f"2025: {n_2025} sem alvo (esperado — último ano)")
else:
    warn(f"2025: {n_2025} sem alvo (esperado 687)")

# confirmar hipótese: sem alvo (2007-2024) => escola ausente em t+1
ids_sel = set(zip(sel["ANO"].tolist(), sel["CO_ENTIDADE"].tolist()))
suspeitas = sem_alvo[sem_alvo["ANO"] < 2025]
nao_conf = sum(1 for a, e in zip(suspeitas["ANO"], suspeitas["CO_ENTIDADE"])
               if (a + 1, e) in ids_sel)
if nao_conf == 0:
    ok(f"todas as {len(suspeitas)} linhas sem alvo (2007-2024) confirmam escola ausente em t+1")
else:
    fail(f"{nao_conf} linhas sem alvo têm escola presente em t+1")


# ==================================================================
# 11. Features do Censo — 18 variáveis binárias
# ==================================================================
secao("11. CENSO — 18 VARIÁVEIS BINÁRIAS")

vars_censo = [c for c in base.columns
              if c.startswith(("IIB_", "IDA_", "IDP_", "IEP_"))]
if len(vars_censo) == 18:
    ok("18 variáveis do artigo presentes (inclui IDP_patio_descoberto)")
else:
    fail(f"esperava 18 variáveis do artigo, achei {len(vars_censo)}")
nao_bin = []
for c in vars_censo:
    uniq = set(base[c].dropna().unique().tolist())
    if not uniq <= {0.0, 1.0}:
        nao_bin.append((c, sorted(uniq)[:5]))
if nao_bin:
    fail(f"valores fora de {{0, 1}}: {nao_bin}")
else:
    ok(f"{len(vars_censo)} variáveis do Censo são binárias (0/1)")

fa = base.groupby("ANO")["INFRA_FONTE_ARTIGO"].nunique()
if (fa == 1).all() and set(base["INFRA_FONTE_ARTIGO"].dropna().unique()) <= {0, 1}:
    ok("INFRA_FONTE_ARTIGO é 0/1 e constante dentro de cada ano")
else:
    fail("INFRA_FONTE_ARTIGO inconsistente")

# ==================================================================
# 12. Cobertura e "zeros estruturais" (coluna não coletada != 0)
# ==================================================================
secao("12. CENSO — AUSÊNCIA REAL x ZERO ESTRUTURAL")

aus_esp = (fontes[fontes["coluna_usada"] == ""]
           .groupby("ano")["variavel"].apply(set).to_dict())
prob_aus, prob_zero = [], []
for ano in sorted(base["ANO"].unique()):
    sub = base[base["ANO"] == ano]
    todo_nan = {c for c in vars_censo if sub[c].isna().all()}
    esperado = aus_esp.get(int(ano), set())
    if todo_nan != esperado:
        prob_aus.append((int(ano), sorted(todo_nan ^ esperado)))
    for c in vars_censo:
        if c in esperado:
            continue
        v = sub[c].dropna()
        if len(v) >= 30 and (v == 0).all():
            prob_zero.append((int(ano), c))
    cob = sub[vars_censo].notna().mean().mean() * 100
    info(f"{int(ano)}: n={len(sub):>4}, ausentes={len(esperado)}, cobertura={cob:.1f}%")
if prob_aus:
    fail(f"variáveis todo-NaN diferem do esperado (fontes): {prob_aus[:5]}")
else:
    ok("variáveis ausentes por ano batem com fontes_features_censo.csv")
if prob_zero:
    fail(f"variável 'coletada' vem toda zero (zero estrutural): {prob_zero[:6]}")
else:
    ok("nenhuma variável coletada vem toda zero em algum ano")
cob_2012 = base[base["ANO"].between(2012, 2021)][vars_censo].notna().mean().mean() * 100
if cob_2012 > 99:
    ok(f"2012-2021: cobertura das 18 = {cob_2012:.1f}%")
else:
    warn(f"2012-2021: cobertura das 18 = {cob_2012:.1f}%")


# ==================================================================
# 13. base_atual idêntica ao 05 e 05 preserva o 04
# ==================================================================
secao("13. base_atual = 05 e 05 preserva 04")

if ind.equals(atual):
    ok("base_atual.parquet é idêntico ao 05_base_com_indices.parquet")
else:
    fail("base_atual e 05 divergem")
if ind[list(base.columns)].equals(base):
    ok("05 contém todas as colunas do 04 sem alteração")
else:
    fail("05 alterou colunas do 04")
esperado_05 = 11 if "IIE_prop" in ind.columns else 6   # 5 zano + marcador (+5 prop com --com-prop)
if ind.shape[1] - base.shape[1] == esperado_05:
    ok(f"05 acrescenta exatamente {esperado_05} colunas ao 04")
else:
    fail(f"05 acrescenta {ind.shape[1] - base.shape[1]} colunas (esperado {esperado_05})")


# ==================================================================
# 14. 01 bruto x 02b — mesmas escolas, ano a ano (pendência do relatório 03)
# ==================================================================
secao("14. 01 BRUTO x 02b — CONJUNTO DE ESCOLAS POR ANO")

if not P_BRUTO.exists():
    warn("01_tx_rend_bruto.parquet ausente — seção pulada")
else:
    b01 = pd.read_parquet(P_BRUTO, columns=["ANO", "Ano", "CO_ENTIDADE", "Código da Escola"])
    ano01 = b01["ANO"].fillna(b01["Ano"])
    ent01 = b01["CO_ENTIDADE"].fillna(b01["Código da Escola"])
    if ano01.isna().sum() == 0 and ent01.isna().sum() == 0:
        ok("01: ano e código da escola preenchidos em todas as linhas (3 layouts do INEP)")
    else:
        fail(f"01: {int(ano01.isna().sum())} anos e {int(ent01.isna().sum())} códigos nulos")
    conf = (((b01["ANO"].notna() & b01["Ano"].notna()) & (b01["ANO"] != b01["Ano"])).sum()
            + ((b01["CO_ENTIDADE"].notna() & b01["Código da Escola"].notna())
               & (b01["CO_ENTIDADE"] != b01["Código da Escola"])).sum())
    if conf == 0:
        ok("01: colunas harmonizadas e originais nunca se contradizem")
    else:
        fail(f"01: {int(conf)} linhas com ano/código contraditórios")
    k01 = pd.DataFrame({"ANO": ano01.astype("Int64"), "E": ent01.astype("Int64").astype(str)})
    if len(k01) == len(lon) and k01.duplicated().sum() == 0:
        ok(f"01: {len(k01):,} linhas, chave (ano, escola) única, mesmo total do 02b")
    else:
        fail(f"01: {len(k01)} linhas / {int(k01.duplicated().sum())} duplicadas (02b tem {len(lon)})")
    difer = []
    for ano_i, g in k01.groupby("ANO"):
        s1 = set(g["E"])
        s2 = set(lon.loc[lon["ANO"].astype(int) == int(ano_i), "CO_ENTIDADE"].astype(str))
        if s1 != s2:
            difer.append((int(ano_i), len(s1 ^ s2)))
    if not difer:
        ok("01 e 02b têm exatamente as mesmas escolas em cada um dos 19 anos")
    else:
        fail(f"conjuntos de escolas diferem (ano, nº de escolas divergentes): {difer}")


# ==================================================================
# RESUMO
# ==================================================================
secao("RESUMO")
log.append(f"  ✅ OK:      {n_ok}")
log.append(f"  ⚠️  Warn:   {n_warn}")
log.append(f"  ❌ Falhas:  {n_fail}")
log.append("")
if n_fail == 0:
    log.append("  🎉 BASE VALIDADA — nenhuma falha crítica")
elif n_fail <= 2:
    log.append(f"  ⚠️  {n_fail} falhas — revisar antes de usar")
else:
    log.append(f"  ❌ {n_fail} falhas — base precisa correção")

texto = "\n".join(log)
print(texto)
REPORT.write_text(texto, encoding="utf-8")
print(f"\n>>> Relatório: {REPORT}")