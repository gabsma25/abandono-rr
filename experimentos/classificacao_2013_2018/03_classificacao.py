# -*- coding: utf-8 -*-
"""
03 — Ferramenta de classificação de alto risco na janela 2013–2018 (execução).

Protocolo registrado antes de rodar: abandono-escolar/docs/DECISOES.md,
2026-11-10 ("Protocolo da ferramenta de classificação de alto risco").
RODA UMA VEZ: nenhum modelo, bloco, limiar ou K é escolhido pelo resultado.

Para cada etapa (AF, EM): walk-forward com teste nos alvos de 2016 a 2019,
3 modelos × 3 blocos, réguas B1R_lag e B2, acaso. Bootstrap por escola
agrupado nas 4 transições (5.000 reamostragens); cada métrica é calculada
dentro do ano e o valor agrupado é a média simples dos anos.

  F6  modelo − B1R_lag em PR-AUC e Recall@20%: 2 etapas × 3 modelos × 3 blocos
      × 2 métricas = 36 testes, p bootstrap bilateral e Holm
  "acima do acaso": IC 95% de (métrica − acaso), sem Holm
  sensibilidade: alvo com limiar absoluto (abandono ≥ 10), só estimativa
      pontual, fora da F6

Saídas em gustavo/saida/avaliacao/:
  03_classificacao.csv  métricas por alvo × etapa × modelo × bloco × período
  03_previsoes.csv      uma linha por escola-ano de teste × modelo × bloco
  03_testes.csv         F6 (com Holm e leitura) e comparações com o acaso
  03_classificacao.md   resumo gerado por código
Uso: python avaliacao/03_classificacao.py [--n-boot 5000]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "avaliacao").is_dir()) / "src" / "avaliacao"))
import bootstrap as BS  # noqa: E402
import classificacao as C  # noqa: E402
import metricas as M  # noqa: E402
import painel as P  # noqa: E402

SAIDA = Path(__file__).resolve().parent / "saida"
SEMENTE = 20261111
PRIMARIAS = ("PR_AUC", "Rec@20pct")
PERIODO = f"{C.ANOS_TESTE[0]}–{C.ANOS_TESTE[-1]}"
ALFA = 0.05


def ids(celulas):
    return list(celulas[0]["p"].keys())


def tabela_metricas(celulas, alvo):
    """Métricas por ano e agrupadas (média simples dos anos; contagens somadas)."""
    linhas = []
    for pid in ids(celulas) + [("acaso", 0)]:
        por_ano = []
        for c in celulas:
            rot = c["y"]
            if pid[0] == "acaso":
                n, pos = len(rot), int(rot.sum())
                k20 = M.k_de_fracao(n, C.FRACAO_ALTO)
                m = {"n": n, "n_alto": pos, "prevalencia": pos / n, "K20pct": k20, "PR_AUC": pos / n,
                     "ROC_AUC": 0.5, "Rec@20pct": k20 / n, "Prec@20pct": pos / n}
                for k in C.KS_ESCOLAS:
                    m[f"Rec@{k}"], m[f"Prec@{k}"] = k / n, pos / n
            else:
                m = C.metricas_ano(rot, c["p"][pid], pid[0] in C.MODELOS)
            por_ano.append({"periodo": str(c["ano_alvo"]), "n_treino": c["n_treino"], **m})
        df = pd.DataFrame(por_ano)
        soma = {"n", "n_alto", "VP", "FP", "FN", "VN"}
        agr = {c_: (df[c_].sum() if c_ in soma else df[c_].mean()) for c_ in df.columns
               if c_ not in ("periodo", "n_treino")}
        df = pd.concat([df, pd.DataFrame([{"periodo": PERIODO, **agr}])], ignore_index=True)
        df.insert(0, "bloco", pid[1])
        df.insert(0, "modelo", pid[0])
        linhas.append(df)
    out = pd.concat(linhas, ignore_index=True)
    out.insert(0, "etapa", celulas[0]["etapa"])
    out.insert(0, "alvo", alvo)
    return out


def bootstrap(celulas, rng, n_boot):
    """Distribuições agrupadas de PR-AUC e Recall@20% por nota, e do acaso, nas mesmas reamostragens."""
    ag = BS.Agrupado(celulas)
    pids = ids(celulas)
    nota = {pid: np.concatenate([c["p"][pid] for c in celulas]) for pid in pids}
    rot = ag.y
    dist = {(pid, m): np.empty(n_boot) for pid in pids + [("acaso", 0)] for m in PRIMARIAS}
    for b, idx in enumerate(ag.sorteios(rng, n_boot)):
        sel = ag.por_ano(idx)
        acc = {k: 0.0 for k in dist}
        for a in ag.anos:
            s = sel[a]
            r = rot[s]
            pos = r.sum()
            if pos == 0:
                raise RuntimeError(f"reamostragem sem escola de alto risco em {a}")
            k20 = M.k_de_fracao(len(s), C.FRACAO_ALTO)
            acc[(("acaso", 0), "PR_AUC")] += pos / len(s)
            acc[(("acaso", 0), "Rec@20pct")] += k20 / len(s)
            for pid in pids:
                v = nota[pid][s]
                acc[(pid, "PR_AUC")] += C.pr_auc_rapida(r, v)
                acc[(pid, "Rec@20pct")] += C.acertos_topk(r, v, k20) / pos
        for k, v in acc.items():
            dist[k][b] = v / len(ag.anos)
    return dist


def previsoes(celulas):
    linhas = []
    for c in celulas:
        for pid, nota in c["p"].items():
            linhas.append(pd.DataFrame({
                "etapa": c["etapa"], "ANO": c["ano"], "ANO_ALVO": c["ano_alvo"], "CO_ENTIDADE": c["co"],
                "modelo": pid[0], "bloco": pid[1], "e_probabilidade": pid[0] in C.MODELOS, "nota": nota,
                "posicao": pd.Series(-nota).rank(method="min").astype(int).to_numpy(),
                "alto_risco": c["y"], "abandono_t1": c["y_t1"]}))
    return pd.concat(linhas, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=5000)
    n_boot = ap.parse_args().n_boot
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    SAIDA.mkdir(parents=True, exist_ok=True)
    atual = pd.read_parquet(P.P_ATUAL)
    rng = np.random.default_rng(SEMENTE)

    tabelas, prevs, testes = [], [], []
    for etapa in ("AF", "EM"):
        painel = C.montar(etapa, atual)
        cel = C.rodar_etapa(painel, etapa, "top20")
        tab = tabela_metricas(cel, "top20")
        dist = bootstrap(cel, rng, n_boot)
        # IC das primárias na linha agrupada
        for (pid, m), d in dist.items():
            lo, hi = BS.intervalo(d)
            sel = (tab["modelo"] == pid[0]) & (tab["bloco"] == pid[1]) & (tab["periodo"] == PERIODO)
            tab.loc[sel, f"{m}_lo"], tab.loc[sel, f"{m}_hi"] = lo, hi
        tabelas.append(tab)
        prevs.append(previsoes(cel))
        agr = tab[tab["periodo"] == PERIODO].set_index(["modelo", "bloco"])
        alto_ano = float(np.mean([c["y"].sum() for c in cel]))
        for pid in ids(cel):
            for m in PRIMARIAS:
                for ref, familia in ((("acaso", 0), "acaso"), (("B1R_lag", 0), "F6")):
                    if pid == ref or (familia == "F6" and pid[0] not in C.MODELOS):
                        continue
                    d = dist[(pid, m)] - dist[(ref, m)]
                    lo, hi = BS.intervalo(d)
                    lin = {"familia": familia, "etapa": etapa, "modelo": pid[0], "bloco": pid[1],
                           "referencia": ref[0], "metrica": m,
                           "dif": float(agr.loc[pid, m] - agr.loc[ref, m]), "lo": lo, "hi": hi,
                           "p": BS.p_bootstrap(d), "alto_risco_por_ano": alto_ano}
                    if m == "Rec@20pct":
                        lin.update({"dif_escolas": lin["dif"] * alto_ano, "lo_escolas": lo * alto_ano,
                                    "hi_escolas": hi * alto_ano, "largura_escolas": (hi - lo) * alto_ano})
                    testes.append(lin)
        # sensibilidade: limiar absoluto, só estimativa pontual
        tabelas.append(tabela_metricas(C.rodar_etapa(painel, etapa, "abs10"), "abs10"))
        print(f"[{etapa}] ok: {len(painel)} escolas-ano na janela, {sum(len(c['y']) for c in cel)} de teste")

    tab = pd.concat(tabelas, ignore_index=True)
    prev = pd.concat(prevs, ignore_index=True)
    tes = pd.DataFrame(testes)
    f6 = tes["familia"] == "F6"
    tes.loc[f6, "p_holm"] = BS.holm(tes.loc[f6, "p"].to_numpy())
    tes.loc[f6, "n_familia"] = int(f6.sum())
    tes.loc[f6, "leitura"] = [C.leitura(r.metrica, r.dif, r.lo, r.hi, r.p_holm, ALFA)
                              for r in tes[f6].itertuples()]
    tes.loc[~f6, "leitura"] = np.where(tes.loc[~f6, "lo"] > 0, "acima do acaso", "não distinguível do acaso")
    if int(f6.sum()) != 36:
        raise RuntimeError(f"F6 deveria ter 36 testes, tem {int(f6.sum())}")

    tab.to_csv(SAIDA / "03_classificacao.csv", index=False, lineterminator="\n")
    prev.to_csv(SAIDA / "03_previsoes.csv", index=False, lineterminator="\n")
    tes.to_csv(SAIDA / "03_testes.csv", index=False, lineterminator="\n")
    (SAIDA / "03_classificacao.md").write_text(resumo(tab, tes, n_boot), encoding="utf-8", newline="\n")
    print(f"Gravado em {SAIDA}: 03_classificacao.csv ({len(tab)}), 03_previsoes.csv ({len(prev)}), "
          f"03_testes.csv ({len(tes)}), 03_classificacao.md")


def _n(v, casas=3):
    return "—" if pd.isna(v) else f"{v:+.{casas}f}".replace(".", ",")


def _v(v, casas=3):
    return "—" if pd.isna(v) else f"{v:.{casas}f}".replace(".", ",")


def resumo(tab, tes, n_boot):
    L = ["# 03 — Classificação de alto risco, janela 2013–2018 (alvos de teste 2016–2019)", "",
         "Gerado por `gustavo/avaliacao/03_classificacao.py`. Protocolo: `abandono-escolar/docs/DECISOES.md`,",
         f"2026-11-10. Bootstrap por escola agrupado, {n_boot} reamostragens; IC 95% por percentis.",
         "Valor agrupado = média simples das 4 transições de teste.", ""]
    t = tab[(tab["alvo"] == "top20") & (tab["periodo"] == PERIODO)]
    for etapa in ("AF", "EM"):
        s = t[t["etapa"] == etapa]
        ac = s[s["modelo"] == "acaso"].iloc[0]
        L += [f"## {etapa}", "",
              f"Escolas-ano de teste: {int(ac['n'])}; de alto risco: {int(ac['n_alto'])} "
              f"(prevalência média {_v(ac['prevalencia'])}).", "",
              "| Nota | Bloco | PR-AUC [IC 95%] | Recall@20% [IC 95%] | ROC-AUC | Precisão (0,5) | Recall (0,5) | F1 (0,5) |",
              "|---|---|---|---|---|---|---|---|"]
        for i, r in s.iterrows():
            def ic(m):
                if pd.isna(r.get(f"{m}_lo")):
                    return _v(r[m])
                return f"{_v(r[m])} [{_v(r[m + '_lo'])}; {_v(r[m + '_hi'])}]"
            L.append(f"| {C.NOME_MODELO.get(r['modelo'], r['modelo'])} | {r['bloco'] if r['bloco'] else '—'} | "
                     f"{ic('PR_AUC')} | {ic('Rec@20pct')} | {_v(r['ROC_AUC'])} | {_v(r.get('precisao_05'))} | "
                     f"{_v(r.get('recall_05'))} | {_v(r.get('F1_05'))} |")
        L += ["", f"### {etapa}: modelo − B1R_lag (família F6, Holm em 36 testes)", "",
              "| Modelo | Bloco | Métrica | Diferença [IC 95%] | p Holm | Leitura | IC em escolas por ano |",
              "|---|---|---|---|---|---|---|"]
        for r in tes[(tes["familia"] == "F6") & (tes["etapa"] == etapa)].itertuples():
            esc = "—" if pd.isna(r.lo_escolas) else f"{_n(r.lo_escolas, 1)} a {_n(r.hi_escolas, 1)}"
            L.append(f"| {C.NOME_MODELO[r.modelo]} | {r.bloco} | {r.metrica} | {_n(r.dif)} [{_n(r.lo)}; {_n(r.hi)}] | "
                     f"{_v(r.p_holm)} | {r.leitura} | {esc} |")
        L.append("")
    f6 = tes[tes["familia"] == "F6"]
    L += ["## Contagem das leituras da F6", ""]
    for (etapa, met), g in f6.groupby(["etapa", "metrica"]):
        L.append(f"- {etapa}, {met}: " + "; ".join(f"{k} {v}" for k, v in g["leitura"].value_counts().items()))
    ac = tes[tes["familia"] == "acaso"]
    L += ["", "## Acima do acaso (IC 95% de métrica − acaso acima de zero; sem Holm)", ""]
    for (etapa, met), g in ac.groupby(["etapa", "metrica"]):
        mod = g[g["modelo"].isin(C.MODELOS)]
        reg = g[~g["modelo"].isin(C.MODELOS)]
        L.append(f"- {etapa}, {met}: modelos {int((mod['lo'] > 0).sum())} de {len(mod)}; "
                 + "; ".join(f"{r.modelo} {'sim' if r.lo > 0 else 'não'}" for r in reg.itertuples()))
    s = tab[(tab["alvo"] == "abs10") & (tab["periodo"] == PERIODO)]
    L += ["", "## Sensibilidade: alvo com limiar absoluto (abandono ≥ 10), estimativa pontual", "",
          "| Etapa | Nota | Bloco | Prevalência | PR-AUC | Recall@20% | ROC-AUC |", "|---|---|---|---|---|---|---|"]
    for r in s.itertuples():
        L.append(f"| {r.etapa} | {C.NOME_MODELO.get(r.modelo, r.modelo)} | {r.bloco if r.bloco else '—'} | "
                 f"{_v(r.prevalencia)} | {_v(r.PR_AUC)} | {_v(tab.loc[r.Index, 'Rec@20pct'])} | {_v(r.ROC_AUC)} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
