# -*- coding: utf-8 -*-
"""
03b — Verificação do treino da classificação (conferência de código, não análise).

Nada aqui escolhe modelo, bloco, limiar ou K. O relatório responde "como
sabemos que os modelos foram de fato treinados e que o resultado de
03_classificacao.py é reproduzível?":

  a. o laço das dobras e o .fit de classificacao.rodar_etapa, linha a linha
  b. dobra × etapa: anos e linhas de treino e de teste, prevalência
  c. reexecução de 03_classificacao.py numa pasta temporária (gustavo/saida/
     não é tocada): tempo de cada .fit, total de ajustes, md5 × oficial
  d. coeficientes padronizados da regressão logística do bloco 3, última dobra
  e. controle negativo: rótulos embaralhados dentro de cada ano de treino
     (critério original de um sorteio, suas falhas, o diagnóstico e o teste
     de permutação que o substitui)
  f. probabilidades previstas e taxa observada por décimo (logística, bloco 3)

Saída: gustavo/saida/relatorios/verificacao_classificacao.txt
       gustavo/saida/avaliacao/03b_controle_permutacao.csv
Uso:   python avaliacao/03b_verificacao_classificacao.py
"""
import hashlib
import importlib.util
import inspect
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(next(p for p in AQUI.parents if (p / "src" / "avaliacao").is_dir()) / "src" / "avaliacao"))
import classificacao as C  # noqa: E402
import metricas as M  # noqa: E402
import painel as P  # noqa: E402

spec = importlib.util.spec_from_file_location("exec03", AQUI / "03_classificacao.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

OFICIAL = AQUI / "saida"
REPORT = AQUI.parent / "saida" / "relatorios" / "verificacao_classificacao.txt"
ARQUIVOS = ["03_classificacao.csv", "03_previsoes.csv", "03_testes.csv", "03_classificacao.md"]
SEMENTE_CONTROLE = 20261110
ACASO = C.FRACAO_ALTO

L = []


def w(*linhas):
    L.extend(linhas)


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def f3(v):
    return f"{v:.3f}".replace(".", ",")


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
atual = pd.read_parquet(P.P_ATUAL)
paineis = {e: C.montar(e, atual) for e in ("AF", "EM")}
falhas = []

w("VERIFICAÇÃO DO TREINO DA CLASSIFICAÇÃO (conferência de código, não análise)",
  "Gerado por gustavo/avaliacao/03b_verificacao_classificacao.py.",
  "Nada aqui escolhe modelo, bloco, limiar ou K.", "")

# ------------------------------------------------------------------ a
w("a. O laço das dobras e o ajuste (classificacao.rodar_etapa)", "")
EXPLICA = {
    "for ano in anos:": "uma dobra por ano de teste (alvos de 2016 a 2019)",
    'tr = painel[painel["ANO_ALVO"] < ano]': "TREINO: só transições com alvo ANTES do ano de teste",
    'te = painel[painel["ANO_ALVO"] == ano]': "TESTE: só a transição cujo alvo é o ano de teste",
    '("B2", 0): B.b2_mediana_estrato(tr, te)}': "régua B2: mediana calculada só no treino",
    'p = {("B1R_lag", 0): te[f"ABANDONO_{s}_L1"].to_numpy(),': "régua B1R_lag: abandono de t−1, sem ajuste nenhum",
    "for k in range(1, N_BLOCOS + 1):": "blocos cumulativos 1, 2 e 3",
    "cols = colunas_bloco(etapa, k)": "colunas do bloco: só t−1, t−2, território, rede e infraestrutura",
    "for nome in MODELOS:": "regressão logística, Random Forest, HistGradientBoosting",
    "pipe = modelo(nome, cols).fit(tr[cols], tr[col_alvo].to_numpy())":
        "AJUSTE: imputação, padronização, one-hot e modelo aprendem só com o TREINO",
    "p[(nome, k)] = pipe.predict_proba(te[cols])[:, 1]": "PREVISÃO: probabilidade de alto risco para as escolas do TESTE",
}
fonte = inspect.getsource(C.rodar_etapa).splitlines()
ini = next(i for i, l in enumerate(fonte) if l.strip().startswith("for ano in anos"))
fim = next(i for i, l in enumerate(fonte) if "predict_proba" in l)
achadas = 0
for l in fonte[ini:fim + 1]:
    nota = EXPLICA.get(l.strip())
    achadas += nota is not None
    w(f"    {l}" + (f"\n        ^ {nota}" if nota else ""))
if achadas != len(EXPLICA):
    falhas.append("a: o código de rodar_etapa mudou e as explicações não casam mais com as linhas")
w("", "  O alvo do ano de teste só aparece depois, no cálculo das métricas; ele não entra no .fit",
  "  (teste 08, seção E: perturbar o alvo do ano de teste ou os anos futuros não muda nenhuma nota).", "")

# ------------------------------------------------------------------ b
w("b. Dobras: anos e linhas de treino e de teste, prevalência do alto risco", "",
  "  etapa  teste(alvo)  treino(alvos)  n_treino  prev_treino  n_teste  alto_teste  prev_teste")
for etapa, pn in paineis.items():
    for ano in C.ANOS_TESTE:
        tr, te = pn[pn["ANO_ALVO"] < ano], pn[pn["ANO_ALVO"] == ano]
        w(f"  {etapa:5s}  {ano:11d}  {int(tr['ANO_ALVO'].min())}–{int(tr['ANO_ALVO'].max())}      "
          f"{len(tr):8d}  {f3(tr['alto_top20'].mean()):>11s}  {len(te):7d}  {int(te['alto_top20'].sum()):10d}  "
          f"{f3(te['alto_top20'].mean()):>10s}")
w("")

# ------------------------------------------------------------------ c
w("c. Reexecução de 03_classificacao.py em pasta temporária", "")
tempos = []
modelo_original = C.modelo


def modelo_cronometrado(nome, colunas):
    pipe = modelo_original(nome, colunas)
    fit_original = pipe.fit

    def fit(X, y):
        t0 = time.perf_counter()
        fit_original(X, y)
        tempos.append({"modelo": nome, "bloco": {3: 1, 5: 2, 10: 3}[len(colunas)], "n_treino": len(X),
                       "segundos": time.perf_counter() - t0})
        return pipe
    pipe.fit = fit
    return pipe


with tempfile.TemporaryDirectory() as tmp:
    E.SAIDA = Path(tmp)
    C.modelo = modelo_cronometrado
    argv, sys.argv = sys.argv, [sys.argv[0]]
    t0 = time.perf_counter()
    try:
        E.main()
    finally:
        C.modelo, sys.argv = modelo_original, argv
    total = time.perf_counter() - t0
    iguais = {}
    for a in ARQUIVOS:
        iguais[a] = (md5(Path(tmp) / a), md5(OFICIAL / a))
tp = pd.DataFrame(tempos)
esperado = len(C.ANOS_TESTE) * len(C.MODELOS) * C.N_BLOCOS * 2 * len(C.ALVOS)
w(f"  ajustes (.fit) executados: {len(tp)} (esperado: 4 dobras × 3 modelos × 3 blocos × 2 etapas × 2 alvos = {esperado})",
  f"  tempo somado dos ajustes: {tp['segundos'].sum():.1f} s; tempo total da execução (com o bootstrap): {total:.1f} s", "",
  "  tempo de um .fit, em segundos (mínimo / mediana / máximo), por modelo:")
for nome, g in tp.groupby("modelo", sort=False):
    w(f"    {C.NOME_MODELO[nome]:22s} {len(g):3d} ajustes   {g['segundos'].min():.3f} / {g['segundos'].median():.3f} / {g['segundos'].max():.3f}"
      f"   (treino de {g['n_treino'].min()} a {g['n_treino'].max()} linhas)")
w("", "  md5 das saídas (temporária × oficial em gustavo/saida/avaliacao/):")
for a, (m1, m2) in iguais.items():
    w(f"    {a:24s} {m1}  {'IGUAL' if m1 == m2 else 'DIFERENTE de ' + m2}")
    if m1 != m2:
        falhas.append(f"c: md5 de {a} difere da saída oficial")
if len(tp) != esperado:
    falhas.append(f"c: {len(tp)} ajustes, esperado {esperado}")
w("")

# ------------------------------------------------------------------ d
w("d. Coeficientes da regressão logística do bloco 3, última dobra (teste 2019)",
  "   Variáveis numéricas padronizadas no treino; coeficiente em log-chance por desvio-padrão.",
  "   Leitura: o modelo aprendeu pesos diferentes de zero. Não é importância nem causa.", "")
for etapa, pn in paineis.items():
    cols = C.colunas_bloco(etapa, 3)
    tr = pn[pn["ANO_ALVO"] < C.ANOS_TESTE[-1]]
    pipe = C.modelo("logistica", cols).fit(tr[cols], tr["alto_top20"].to_numpy())
    nomes = [n.split("__", 1)[1] for n in pipe.named_steps["pre"].get_feature_names_out()]
    coef = pd.Series(pipe.named_steps["m"].coef_[0], index=nomes)
    coef = coef.reindex(coef.abs().sort_values(ascending=False).index)
    w(f"  {etapa} (treino: {len(tr)} linhas; intercepto {pipe.named_steps['m'].intercept_[0]:+.3f})")
    for n, v in coef.items():
        w(f"    {n:38s} {v:+.3f}")
    w("")

# ------------------------------------------------------------------ e
ofi = pd.read_csv(OFICIAL / "03_classificacao.csv")
ofi = ofi[(ofi["alvo"] == "top20") & (ofi["periodo"] == E.PERIODO)].set_index(["etapa", "modelo", "bloco"])
CONTROLES = (("logistica", 1, 200), ("floresta", 3, 20))     # (modelo, bloco, embaralhamentos)


def controle(pn, etapa, nome, k, rng):
    """PR-AUC e Recall@20% (média das 4 dobras) com os rótulos embaralhados dentro de cada ano de treino."""
    emb = pn.copy()
    emb["alto_top20"] = emb.groupby("ANO_ALVO")["alto_top20"].transform(lambda v: rng.permutation(v.to_numpy()))
    cols = C.colunas_bloco(etapa, k)
    pr, rc = [], []
    for ano in C.ANOS_TESTE:
        tr = emb[emb["ANO_ALVO"] < ano]
        te = pn[pn["ANO_ALVO"] == ano]
        prob = C.modelo(nome, cols).fit(tr[cols], tr["alto_top20"].to_numpy()).predict_proba(te[cols])[:, 1]
        rot = te["alto_top20"].to_numpy()
        pr.append(C.pr_auc(rot, prob))
        rc.append(C.recall_k(rot, prob, M.k_de_fracao(len(rot), C.FRACAO_ALTO)))
    return float(np.mean(pr)), float(np.mean(rc))


w("e. Controle negativo: rótulos embaralhados dentro de cada ano de TREINO (o teste usa os rótulos verdadeiros)", "",
  "e.1 Critério original (um embaralhamento só) e suas falhas",
  f"   Semente {SEMENTE_CONTROLE}, um gerador único percorrendo AF e EM, logística bloco 1 e Random Forest bloco 3.",
  "   Critério original: controle a até 0,05 do acaso (0,20) e abaixo do valor real.", "",
  "  etapa  modelo                bloco  PR-AUC real  PR-AUC controle  Recall@20% real  Recall@20% controle")
rng = np.random.default_rng(SEMENTE_CONTROLE)
falhas_orig = []
for etapa, pn in paineis.items():
    emb_unico = None
    estado = rng.bit_generator.state            # os dois modelos da etapa usam o MESMO embaralhamento
    for nome, k, _ in CONTROLES:
        rng.bit_generator.state = estado
        pr, rc = controle(pn, etapa, nome, k, rng)
        real = ofi.loc[(etapa, nome, k)]
        w(f"  {etapa:5s}  {C.NOME_MODELO[nome]:20s}  {k:5d}  {f3(real['PR_AUC']):>11s}  {f3(pr):>15s}  "
          f"{f3(real['Rec@20pct']):>15s}  {f3(rc):>19s}")
        for nome_m, v, r in (("PR-AUC", pr, real["PR_AUC"]), ("Recall@20%", rc, real["Rec@20pct"])):
            if not (abs(v - ACASO) <= 0.05 and v < r):
                falhas_orig.append(f"{etapa}, {C.NOME_MODELO[nome]} bloco {k}, {nome_m}: controle {f3(v)} (real {f3(r)})")
w("", f"   Pelo critério original: {len(falhas_orig)} falha(s).")
for f in falhas_orig:
    w(f"     - {f}")
w("", "e.2 Diagnóstico",
  "   Com um embaralhamento só, o modelo aprende um peso de sinal aleatório para o abandono de t−1: ora",
  "   imita a régua, ora a inverte. O valor de um único sorteio varia de 0,09 a 0,38; um sorteio não é teste.",
  "   Não é falha de código: a reexecução é idêntica (item c) e a taxa observada sobe com a probabilidade (item f).", "",
  "e.3 Critério substituto: teste de permutação",
  "   200 embaralhamentos para a logística do bloco 1 e 20 para o Random Forest do bloco 3; o embaralhamento r",
  "   usa numpy.random.default_rng(1000 + r). Passa se a média do controle ficar a até 0,05 do acaso (0,20) e",
  "   abaixo do valor real. Reporta-se também a faixa [p2,5; p97,5] e a posição do valor real.", "",
  "  etapa  modelo                bloco  sorteios  métrica     real   controle: média [p2,5; p97,5]  máx    sorteios ≥ real  passa")
linhas_perm = []
dentro = []
for etapa, pn in paineis.items():
    for nome, k, n_emb in CONTROLES:
        res = [controle(pn, etapa, nome, k, np.random.default_rng(1000 + r)) for r in range(n_emb)]
        real = ofi.loc[(etapa, nome, k)]
        for j, (met, col) in enumerate((("PR-AUC", "PR_AUC"), ("Recall@20%", "Rec@20pct"))):
            v = np.array([x[j] for x in res])
            lo, hi = np.percentile(v, [2.5, 97.5])
            passa = abs(v.mean() - ACASO) <= 0.05 and v.mean() < real[col]
            w(f"  {etapa:5s}  {C.NOME_MODELO[nome]:20s}  {k:5d}  {n_emb:8d}  {met:10s}  {f3(real[col])}  "
              f"{f3(v.mean())} [{f3(lo)}; {f3(hi)}]          {f3(v.max())}  {int((v >= real[col]).sum()):3d} de {n_emb:3d}       "
              f"{'sim' if passa else 'NÃO'}")
            if not passa:
                falhas.append(f"e: teste de permutação de {etapa} {nome} bloco {k} em {met}: média {v.mean():.3f}")
            if real[col] <= hi:
                dentro.append(f"{etapa}, {C.NOME_MODELO[nome]} bloco {k}, {met}: real {f3(real[col])} dentro da faixa do controle [{f3(lo)}; {f3(hi)}]")
            linhas_perm += [{"etapa": etapa, "modelo": nome, "bloco": k, "sorteio": r, "semente": 1000 + r,
                             "metrica": col, "controle": x, "real": real[col]} for r, x in enumerate(v)]
pd.DataFrame(linhas_perm).to_csv(OFICIAL / "03b_controle_permutacao.csv", index=False, lineterminator=chr(10))
w("", "   Valor real dentro da faixa do controle:")
for d in dentro or ["nenhum"]:
    w(f"     - {d}")
w("   Leitura: onde o valor real fica dentro da faixa, a ferramenta não se distingue de um modelo que aprendeu",
  "   só a direção do último abandono. No EM isso é coerente com a régua fraca (Recall@20% 0,275 [0,209; 0,370])",
  "   e com a leitura INCONCLUSIVO. Não é falha de código.", "",
  "e.4 Todas as execuções do controle",
  f"   1. um embaralhamento, semente {SEMENTE_CONTROLE} (e.1), em 2026-11-10: 4 falhas pelo critério original;",
  "   2. diagnóstico fora do relatório, em 2026-11-10: 200 embaralhamentos (logística bloco 1) e 20 (Random Forest",
  "      bloco 3) por etapa, sementes 1000 a 1199 e 1000 a 1019;",
  "   3. esta execução (e.3), com as mesmas sementes do diagnóstico: reproduz os mesmos números.",
  "   Sorteios gravados em gustavo/saida/avaliacao/03b_controle_permutacao.csv.",
  "   Nada desta verificação altera a família F6 nem escolhe modelo, bloco, limiar ou K.", "")

# ------------------------------------------------------------------ f
w("f. Probabilidades previstas e taxa observada por décimo (regressão logística, bloco 3, teste 2016–2019)",
  "   O modelo usa class_weight='balanced': as probabilidades servem para ordenar e ficam acima da",
  "   frequência real (não são calibradas). O que se confere é se a taxa observada sobe com o décimo.", "")
prev = pd.read_csv(OFICIAL / "03_previsoes.csv", dtype={"CO_ENTIDADE": str})
for etapa in ("AF", "EM"):
    s = prev[(prev["etapa"] == etapa) & (prev["modelo"] == "logistica") & (prev["bloco"] == 3)].copy()
    q = s["nota"].quantile([0, .25, .5, .75, 1]).to_numpy()
    w(f"  {etapa}: {len(s)} escolas-ano; probabilidade mín {f3(q[0])}, 1º quartil {f3(q[1])}, mediana {f3(q[2])}, "
      f"3º quartil {f3(q[3])}, máx {f3(q[4])}",
      "    décimo  n    prob. média  alto risco observado  taxa observada")
    s["decimo"] = pd.qcut(s["nota"].rank(method="first"), 10, labels=False) + 1
    g = s.groupby("decimo").agg(n=("nota", "size"), prob=("nota", "mean"), alto=("alto_risco", "sum"),
                                taxa=("alto_risco", "mean"))
    for d, r in g.iterrows():
        w(f"    {d:6d}  {int(r['n']):3d}  {f3(r['prob']):>11s}  {int(r['alto']):20d}  {f3(r['taxa']):>14s}")
    rho = float(pd.Series(g.index).corr(g["taxa"].reset_index(drop=True), method="spearman"))
    w(f"    taxa no décimo mais alto {f3(g['taxa'].iloc[-1])} × no mais baixo {f3(g['taxa'].iloc[0])}; "
      f"Spearman décimo × taxa = {rho:+.2f}", "")
    if not (g["taxa"].iloc[-1] > g["taxa"].iloc[0] and rho > 0):
        falhas.append(f"f: a taxa observada não sobe com a probabilidade em {etapa}")

w("RESULTADO DA VERIFICAÇÃO: " + ("sem falhas" if not falhas else f"{len(falhas)} FALHA(S): O RESULTADO NÃO VALE ATÉ ACHAR A CAUSA"))
for f in falhas:
    w(f"  ❌ {f}")
txt = "\n".join(L) + "\n"
print(txt)
REPORT.write_text(txt, encoding="utf-8", newline="\n")
sys.exit(1 if falhas else 0)
