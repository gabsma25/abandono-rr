# -*- coding: utf-8 -*-
"""
04 — Valida o instrumento de avaliação (avaliacao/metricas.py e baselines.py).

  A. métricas de regressão contra contas feitas à mão
  B. Recall@K: casos à mão, desempate exato (enumeração de todas as ordens),
     previsão constante = K/n, previsão perfeita = 1
  C. baselines: B1 = coluna de abandono em t; fallback só onde falta y_t;
     B0 sem vazamento (perturbar o ano avaliado e os seguintes não muda o B0)
  D. universo: só pública, só com alvo, chave única por ano
  E. conferência cruzada: MAE do B1 (pares completos) contra
     testes/referencias/desfechos_persistencia.csv (cópia congelada; código independente)
  F. B2: mediana do treino por estrato, conta à mão
  (G e H, painel e walk-forward da Etapa 2, saíram no abandono-rr)
  I. bootstrap: reamostragem pareada, previsão constante = K/n em toda
     reamostragem, diferença de um preditor com ele mesmo = 0, classes
  J. bootstrap agrupado: sorteio por escola leva todos os anos da escola,
     repetição duplica as linhas
  K. testes múltiplos: Holm contra conta à mão; p bootstrap; grupos de
     permutação com TDI e ATU separados formam partição das colunas do bloco 4

Saída: gustavo/saida/relatorios/validacao_avaliacao.txt
Uso:   python testes/04_validar_avaliacao.py
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
sys.path.insert(0, str(GUSTAVO / "src" / "avaliacao"))
import baselines as B  # noqa: E402
import metricas as M  # noqa: E402
import painel as P  # noqa: E402
import bootstrap as BS  # noqa: E402

P_BASE = GUSTAVO / "saida" / "base_atual.parquet"
P_REF = GUSTAVO / "testes" / "referencias" / "desfechos_persistencia.csv"  # cópia congelada de abandono-escolar/docs (878930f)
REPORT = GUSTAVO / "saida" / "relatorios" / "validacao_avaliacao.txt"
TOL = 1e-12

log, cont = [], {"ok": 0, "warn": 0, "fail": 0}


def secao(t):
    log.extend(["", "=" * 78, t, "=" * 78])


def ok(m):
    cont["ok"] += 1; log.append(f"  ✅ {m}")


def warn(m):
    cont["warn"] += 1; log.append(f"  ⚠️  {m}")


def fail(m):
    cont["fail"] += 1; log.append(f"  ❌ {m}")


def check(cond, msg_ok, msg_fail):
    ok(msg_ok) if cond else fail(msg_fail)


def recall_enumerado(y, yhat, k):
    """Média exata sobre todas as ordens de desempate (força bruta)."""
    n = len(y)
    tot, cnt = 0.0, 0
    for p1 in itertools.permutations(range(n)):
        top_hat = set(sorted(range(n), key=lambda i: (-yhat[i], p1.index(i)))[:k])
        for p2 in itertools.permutations(range(n)):
            top_y = set(sorted(range(n), key=lambda i: (-y[i], p2.index(i)))[:k])
            tot += len(top_hat & top_y); cnt += 1
    return tot / cnt / k


# ------------------------------------------------------------------
secao("A. Métricas de regressão (contas à mão)")
# ------------------------------------------------------------------
y, p = [0, 2, 4], [1, 2, 7]
check(abs(M.mae(y, p) - 4 / 3) < TOL, "MAE([0,2,4],[1,2,7]) = 4/3", f"MAE = {M.mae(y, p)}")
check(abs(M.rmse(y, p) - np.sqrt(10 / 3)) < TOL, "RMSE = sqrt(10/3)", f"RMSE = {M.rmse(y, p)}")
check(abs(M.r2(y, p) - (1 - 10 / 8)) < TOL, "R² = 1 - 10/8 = -0,25 (negativo permitido)", f"R² = {M.r2(y, p)}")
check(abs(M.r2(y, [2, 2, 2])) < TOL, "R² da média do próprio conjunto = 0", "R² da média ≠ 0")
check(M.k_de_fracao(233, .10) == 23 and M.k_de_fracao(165, .10) == 17 and M.k_de_fracao(5, .10) == 1,
      "K = round(f·n), mínimo 1 (233→23, 165→17 [16,5↑], 5→1)", "K incorreto")

# ------------------------------------------------------------------
secao("B. Recall@K")
# ------------------------------------------------------------------
check(M.recall_at_k([5, 4, 3, 2, 1], [9, 8, 1, 1, 1], 2) == 1.0, "ordem perfeita no topo → 1", "perfeito ≠ 1")
check(M.recall_at_k([5, 4, 3, 2, 1], [1, 1, 1, 8, 9], 2) == 0.0, "ordem invertida → 0", "invertido ≠ 0")
check(abs(M.recall_at_k([5, 4, 3, 2, 1], [9, 1, 8, 1, 1], 2) - 0.5) < TOL, "1 de 2 acertos → 0,5", "caso 0,5 falhou")
rng = np.random.default_rng(0)
yy = rng.integers(0, 5, 40).astype(float)
for k in (1, 4, 8, 20):
    check(abs(M.recall_at_k(yy, np.full(40, 3.3), k) - k / 40) < TOL,
          f"previsão constante → K/n (k={k})", f"constante ≠ K/n (k={k})")
pior = 0.0
for _ in range(25):
    n = 5
    y5 = rng.integers(0, 3, n).astype(float)
    p5 = rng.integers(0, 3, n).astype(float)
    k = int(rng.integers(1, n + 1))
    pior = max(pior, abs(M.recall_at_k(y5, p5, k) - recall_enumerado(y5, p5, k)))
check(pior < 1e-12, f"empates: valor esperado = média sobre todas as ordens (25 casos, erro máx {pior:.1e})",
      f"empates divergem da enumeração ({pior:.2e})")

# ------------------------------------------------------------------
secao("C. Baselines")
# ------------------------------------------------------------------
base = pd.read_parquet(P_BASE)
for etapa, col in B.ETAPAS.items():
    u = B.universo(base, etapa)
    for ano in (2015, 2021, 2025):
        te = u[u["ANO_ALVO"] == ano]
        mu = B.b0_media(u[u["ANO_ALVO"] < ano])
        p1 = B.b1_persistencia(te, mu)
        tem = te["y_t"].notna().to_numpy()
        check(np.array_equal(p1[tem], te["y_t"].to_numpy()[tem]) and np.all(p1[~tem] == mu),
              f"{etapa} {ano}: B1 = y_t; B0 do treino só nas {int((~tem).sum())} sem y_t",
              f"{etapa} {ano}: B1 incorreto")
    # vazamento: bagunçar alvo do ano avaliado e dos seguintes não muda B0
    a = 2016
    u2 = u.copy()
    fut = u2["ANO_ALVO"] >= a
    u2.loc[fut, "y_t1"] = rng.uniform(0, 100, int(fut.sum()))
    check(B.avaliar_ano(u, a)["media_treino"] == B.avaliar_ano(u2, a)["media_treino"],
          f"{etapa}: B0 de {a} não muda com alvos de {a}+ perturbados (sem vazamento)",
          f"{etapa}: B0 usa dado do ano avaliado ou futuro")

# ------------------------------------------------------------------
secao("D. Universo")
# ------------------------------------------------------------------
for etapa, col in B.ETAPAS.items():
    u = B.universo(base, etapa)
    m = base.merge(u[["ANO", "CO_ENTIDADE"]], on=["ANO", "CO_ENTIDADE"], how="inner", validate="1:1")
    check((m["REDE_PUBLICA"].astype("Int8") == 1).all(), f"{etapa}: só escolas públicas", f"{etapa}: entrou privada")
    check(u["y_t1"].notna().all(), f"{etapa}: todas com alvo (oferecem a etapa em t+1)", f"{etapa}: alvo nulo")
    check(not u.duplicated(["ANO", "CO_ENTIDADE"]).any(), f"{etapa}: chave (ANO, CO_ENTIDADE) única",
          f"{etapa}: chave duplicada")
    check(((u["ANO_ALVO"] - u["ANO"]) == 1).all(), f"{etapa}: ANO_ALVO = ANO + 1", f"{etapa}: defasagem errada")
    esperado = int(((base["REDE_PUBLICA"].astype("Int8") == 1) & base[f"{col}_T1"].notna()).sum())
    check(len(u) == esperado, f"{etapa}: {len(u)} escolas-ano no universo", f"{etapa}: contagem diverge")

# ------------------------------------------------------------------
secao("E. Conferência cruzada com o projeto oficial (B1, pares completos)")
# ------------------------------------------------------------------
if not P_REF.exists():
    warn(f"referência ausente: {P_REF}")
else:
    ref = pd.read_csv(P_REF)
    res = pd.concat([B.avaliar(base, e) for e in B.ETAPAS], ignore_index=True)
    dif = []
    for _, r in ref.iterrows():
        alvo = int(r["transicao"].split("->")[1])
        lin = res[(res["etapa"] == r["etapa"]) & (res["ano_alvo"] == alvo)]
        dif.append(abs(float(lin["B1_MAE_pares"].iloc[0]) - r["mae_b1_persistencia"]))
    pior = max(dif)
    # a referência vem da base v1.0 do orientador e é arredondada a 2 casas
    if pior <= 0.005 + 1e-9:
        ok(f"MAE do B1 bate com desfechos_persistencia.csv nas {len(dif)} transições (dif. máx {pior:.3f})")
    elif pior <= 0.10:
        warn(f"MAE do B1 próximo da referência (dif. máx {pior:.3f}; bases de origem diferentes)")
    else:
        fail(f"MAE do B1 diverge da referência (dif. máx {pior:.3f})")

# ------------------------------------------------------------------
secao("F. B2 (mediana do treino por localização × dependência)")
# ------------------------------------------------------------------
tr = pd.DataFrame({"LOCALIZACAO": ["U", "U", "U", "R", "R"], "DEPENDENCIA": ["E"] * 5,
                   "y_t1": [1.0, 3.0, 10.0, 0.0, 4.0]})
te = pd.DataFrame({"LOCALIZACAO": ["U", "R", "X"], "DEPENDENCIA": ["E", "E", "E"]})
p2 = B.b2_mediana_estrato(tr, te)
check(np.allclose(p2, [3.0, 2.0, 3.0]), "B2: U→3, R→2, célula nova → mediana geral 3",
      f"B2 incorreto: {p2}")

# abandono-rr: as seções G (painel da Etapa 2) e H (walk-forward) saíram com a Etapa 2 e a base oficial.

# ------------------------------------------------------------------
secao("I. Bootstrap de escolas")
# ------------------------------------------------------------------
yb = rng.integers(0, 10, 60).astype(float)
pb = yb + rng.normal(0, 3, 60)
cel_b = {"y": yb, "p": {"um": pb, "dois": pb.copy(), "const": np.full(60, 2.0)}}
rb = np.random.default_rng(5)
db = BS.distribuicoes_ano(cel_b, rb)
check(all(len(v) == BS.N_BOOT for v in db.values()), f"{BS.N_BOOT} reamostragens por preditor e métrica",
      "número de reamostragens errado")
check(np.array_equal(db[("um", "Rec@10")], db[("dois", "Rec@10")]),
      "pareado: dois preditores iguais têm a mesma distribuição (mesmos índices)",
      "reamostragens não pareadas")
k6 = M.k_de_fracao(60, .10)
check(np.allclose(db[("const", "Rec@10")], k6 / 60), "previsão constante = K/n em toda reamostragem",
      "constante ≠ K/n no bootstrap")
lo_b, hi_b = BS.intervalo(db[("um", "Rec@10")])
check(lo_b <= M.recall_at_k(yb, pb, k6) <= hi_b and lo_b < hi_b,
      f"intervalo [{lo_b:.2f}, {hi_b:.2f}] contém a estimativa pontual", "intervalo não contém a estimativa")
check(BS.classe(0.01, 0.2) == "vence" and BS.classe(-0.2, -0.01) == "perde" and BS.classe(-0.1, 0.1) == "indeterminado",
      "classes: IC > 0 vence, IC < 0 perde, cruza zero indeterminado", "classes erradas")

# ------------------------------------------------------------------
secao("J. Bootstrap agrupado por escola")
# ------------------------------------------------------------------
cels = [{"ano_alvo": 2021, "y": np.array([1., 2, 3]), "co": np.array(["a", "b", "c"]), "p": {}},
        {"ano_alvo": 2022, "y": np.array([4., 5]), "co": np.array(["a", "c"]), "p": {}}]
ag = BS.Agrupado(cels)
sorteios = ag.sorteios(np.random.default_rng(3), n_boot=200)
ok_esc = True
for idx in sorteios:
    co_s = np.concatenate([c["co"] for c in cels])[idx]
    for e in ("a", "b", "c"):
        n_linhas = {"a": 2, "b": 1, "c": 2}[e]
        ok_esc &= (co_s == e).sum() % n_linhas == 0       # escola entra com todos os seus anos
check(ok_esc, "sorteio por escola: cada escola sorteada entra com todos os seus anos (repetições inteiras)",
      "sorteio quebrou o agrupamento por escola")
check(sorted(ag.por_ano(np.arange(5)).keys()) == [2021, 2022] and len(ag.escolas) == 3,
      "agrupado: 3 escolas, 2 anos, por_ano separa as linhas", "Agrupado mal construído")
# abandono-rr: a conferência com o 02_walkforward.csv saiu com a Etapa 2.

# ------------------------------------------------------------------
secao("K. Testes múltiplos e grupos de permutação")
# ------------------------------------------------------------------
ph = BS.holm([0.01, 0.04, 0.03, 0.20])
check(np.allclose(ph, [0.04, 0.09, 0.09, 0.20]),
      "Holm: [0,01; 0,04; 0,03; 0,20] → [0,04; 0,09; 0,09; 0,20] (step-down, monótono)",
      f"Holm incorreto: {ph}")
check(BS.p_bootstrap(np.full(999, 0.5)) == 2 / 1000 and BS.p_bootstrap(np.zeros(99)) == 1.0
      and abs(BS.p_bootstrap(np.r_[np.full(50, -1.0), np.full(50, 1.0)]) - 1.0) < 1e-12,
      "p bootstrap: tudo > 0 → 2/(B+1); tudo = 0 → 1; simétrico → 1", "p bootstrap incorreto")
for etapa in ("AF", "EM"):
    for cen in P.CENARIOS:
        gi = P.blocos_importancia(etapa, cen)
        cols_gi = [c for v in gi.values() for c in v]
        check(sorted(cols_gi) == sorted(P.colunas_bloco(etapa, cen, 4)) and len(cols_gi) == len(set(cols_gi))
              and gi["TDI"][0].startswith("TDI_") and gi["ATU"][0].startswith("ATU_"),
              f"{etapa}/{cen}: grupos TDI e ATU separados particionam as colunas do bloco 4",
              f"{etapa}/{cen}: grupos de permutação não particionam o bloco 4")

# ------------------------------------------------------------------
secao("RESUMO")
# ------------------------------------------------------------------
log.append(f"  ✅ OK:      {cont['ok']}")
log.append(f"  ⚠️  Warn:   {cont['warn']}")
log.append(f"  ❌ Falhas:  {cont['fail']}")
log.append("")
log.append("  🎉 INSTRUMENTO VALIDADO" if cont["fail"] == 0 else f"  ❌ {cont['fail']} falhas — revisar")
txt = "\n".join(log)
print(txt)
REPORT.write_text(txt, encoding="utf-8")
print(f"\n>>> Relatório: {REPORT}")
sys.exit(1 if cont["fail"] else 0)
