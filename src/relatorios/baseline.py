"""
Gera docs/BASELINE.md: o que é a régua, as outras réguas e o que se sabe delas, com todo número lido de um CSV.

Fontes:
  saida/avaliacao/01_baselines.csv          régua da Etapa 1, REGERADA pelo abandono-rr (src/avaliacao/01_baselines.py)
  saida/avaliacao/reguas_janela.csv         réguas da janela segura, REGERADAS (src/avaliacao/reguas.py)
  docs/projeto_anterior/02_walkforward.csv  Etapa 2, citada do projeto anterior (Dados-do-Projeto 969fc64)
  docs/projeto_anterior/02d_testes.csv      Etapa 2, idem
  experimentos/classificacao_2013_2018/saida/03_classificacao.csv e 03_testes.csv   classificação, idem

Uso: python src/relatorios/baseline.py   (o teste testes/test_baseline.py exige que o arquivo esteja em dia)
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
P_E1 = RAIZ / "saida" / "avaliacao" / "01_baselines.csv"
P_REGUAS = RAIZ / "saida" / "avaliacao" / "reguas_janela.csv"
P_WF = RAIZ / "docs" / "projeto_anterior" / "02_walkforward.csv"
P_02D = RAIZ / "docs" / "projeto_anterior" / "02d_testes.csv"
EXP = RAIZ / "experimentos" / "classificacao_2013_2018" / "saida"
DESTINO = RAIZ / "docs" / "BASELINE.md"
ULTIMO_ALVO_E1 = 2024          # a transição 2024→2025 fica fora (o desfecho de 2025 já foi usado)
PERIODO = "2016–2019"
ETAPAS = {"AF": "anos finais (AF)", "EM": "ensino médio (EM)"}
ANT = "Dados-do-Projeto `969fc64`"


def br(x, casas=3):
    return f"{x:.{casas}f}".replace(".", ",")


def etapa1():
    e = pd.read_csv(P_E1)
    e = e[e["ano_alvo"] <= ULTIMO_ALVO_E1]
    out = {}
    for etapa, g in e.groupby("etapa"):
        r20 = g["B1R_Rec@20"]
        out[etapa] = {"n": len(g), "ini": int(g["ano_alvo"].min()), "fim": int(g["ano_alvo"].max()),
                      "min": r20.min(), "med": r20.median(), "max": r20.max(),
                      "acima": int((r20 > g["B0_Rec@20"]).sum()), "acaso_med": g["B0_Rec@20"].median(),
                      "r2_pos": int((g["B1_R2"] > 0).sum()), "mae_melhor": int((g["B1_MAE"] < g["B0_MAE"]).sum())}
    return out


def etapa2():
    t = pd.read_csv(P_02D)
    p = t[t["primario"]]
    f5 = p[(p["familia"] == "F5") & (p["item"] == "− B1R_lag")]
    f5_todos = p[p["familia"] == "F5"]
    f4 = p[(p["familia"] == "F4") & (p["item"] == "− B2")]
    w = pd.read_csv(P_WF)
    w = w[w["modelo"].isin(["B1R", "B1R_lag", "B2"])]
    return {"f5": f5.groupby("etapa")["rejeita_holm"].agg(["sum", "size"]),
            "f5_total": (int(f5["rejeita_holm"].sum()), len(f5)),
            "f5_blocos": (int(f5_todos["rejeita_holm"].sum()), len(f5_todos)),
            "f4": f4.groupby("etapa")["rejeita_holm"].agg(["sum", "size"]),
            "f4_ganho_af": f4[(f4["etapa"] == "AF") & f4["rejeita_holm"]]["valor"].agg(["min", "max"]),
            "anos": w.set_index(["etapa", "ano_alvo", "modelo"])["Rec@20"].unstack("modelo")}


def classificacao():
    r = pd.read_csv(P_REGUAS)
    r = r[(r["alvo"] == "top20") & (r["periodo"] == PERIODO)].set_index(["etapa", "modelo"])
    c = pd.read_csv(EXP / "03_classificacao.csv")
    c = c[(c["alvo"] == "top20") & (c["periodo"] == PERIODO)].set_index(["etapa", "modelo", "bloco"])
    t = pd.read_csv(EXP / "03_testes.csv")
    f6 = t[t["familia"] == "F6"]
    return {"reguas": r, "ic": c, "f6_n": len(f6), "f6_ganho": int((f6["leitura"] == "GANHO").sum()),
            "f6_r20": f6[f6["metrica"] == "Rec@20pct"].groupby(["etapa", "leitura"]).size().unstack(fill_value=0),
            "p_holm_min": f6["p_holm"].min()}


def texto():
    e1, e2, cl = etapa1(), etapa2(), classificacao()
    ic = cl["ic"]
    L = ["# A régua: o que é e o que se sabe dela", "",
         "Gerado por `python src/relatorios/baseline.py` (não edite à mão). Cada número vem de um CSV, citado ao lado.",
         "Os números da Etapa 1 e das réguas da janela segura são **regerados** pelo abandono-rr; os da Etapa 2 e da",
         "classificação são **citados** do projeto anterior, sem rodar nada de novo.", "",
         "## 1. As réguas, em linguagem simples", "",
         "Uma **régua** é uma forma simples de montar a lista de escolas de maior risco, sem modelo nenhum. Ela serve de",
         "ponto de comparação: uma ferramenta só vale a pena se fizer uma lista melhor do que a régua.", "",
         "**A régua (B1R_lag): o último abandono conhecido na hora de fazer a lista.** A lista do ano t+1 precisa estar",
         "pronta no começo de t+1. Nesse momento, a taxa de abandono do ano t ainda não foi publicada pelo INEP (ela sai",
         "durante t+1). O dado mais recente disponível é o **abandono de t−1**. A régua ordena as escolas por ele: quem teve",
         "mais abandono em t−1 fica no topo.", "",
         "**A versão otimista (B1R): o abandono de t.** Ordena as escolas pelo abandono do próprio ano t. Costuma acertar mais",
         "(seção 3), porque usa um dado mais recente, mas esse dado ainda não existe quando a lista precisa ser feita. Por isso ela",
         "é só um **limite superior**, nunca o adversário da ferramenta.", "",
         "**B2: território e rede.** Para cada combinação de localização (urbana, rural) e rede (estadual, municipal,",
         "federal), calcula a mediana do abandono nos anos de treino e dá esse valor a todas as escolas da combinação.",
         "Não olha a história da própria escola: mostra quanto se acerta só sabendo onde a escola está e a que rede pertence.", "",
         "**Acaso.** Uma lista sorteada. Numa lista com 20% das escolas, o acaso encontra, em média, 20% das escolas de",
         "abandono alto; é o piso.", "",
         "**Como se mede: Recall@20%.** Das escolas que de fato tiveram abandono alto, que fração estava entre os 20% do",
         "topo da lista. Atenção: nas Etapas 1 e 2, \"abandono alto\" são os 20% de maior abandono observado; na",
         "classificação, é o rótulo `alto_risco_t1` (os 20% maiores **e** abandono > 0). Os números de uma não se",
         "comparam com os da outra.", "",
         "## 2. Etapa 1: quanto a persistência acerta, sem modelo", "",
         "Fonte: `saida/avaliacao/01_baselines.csv`, regerado pelo abandono-rr e idêntico ao do projeto anterior",
         f"(`testes/test_equivalencia.py`). Transições até o desfecho de {ULTIMO_ALVO_E1}; escolas públicas com o desfecho conhecido.",
         "A Etapa 1 só tem a **versão otimista** (abandono de t) e não tem intervalo de confiança.", "",
         "| Etapa | Transições | Recall@20% da régua otimista: mín / mediana / máx | Anos acima do acaso | Acaso (mediana) |",
         "|---|---|---|---|---|"]
    for et, d in e1.items():
        L.append(f"| {ETAPAS[et]} | {d['n']} ({d['ini'] - 1}→{d['ini']} a {d['fim'] - 1}→{d['fim']}) | "
                 f"{br(d['min'], 2)} / {br(d['med'], 2)} / {br(d['max'], 2)} | {d['acima']} de {d['n']} | {br(d['acaso_med'], 2)} |")
    L += ["", "**Como ordem, a persistência acerta acima do acaso em quase todos os anos. Como valor, não:** repetir a taxa",
          "de t como previsão de t+1 tem R² acima de zero em " +
          " e ".join(f"{d['r2_pos']} de {d['n']} transições no {et}" for et, d in e1.items()) +
          ", e erra menos que a média histórica em " +
          " e ".join(f"{d['mae_melhor']} de {d['n']} no {et}" for et, d in e1.items()) +
          ". Por isso a decisão é sempre por ordenação (Recall@K), não por R² nem por erro médio.", "",
          "## 3. Etapa 2: modelos de regressão contra a régua", "",
          f"Fonte: `docs/projeto_anterior/02d_testes.csv` e `02_walkforward.csv` ({ANT}). Ridge e árvore, 4 blocos de",
          "informação (inclusive TDI, ATU e IED), testados nos desfechos de 2021 a 2024; diferença das quatro transições",
          "agrupadas, bootstrap por escola e correção de Holm, nos K de 10% e 20%.", "",
          "| Comparação | AF | EM | Total |", "|---|---|---|---|"]
    f5, f4 = e2["f5"], e2["f4"]
    L.append(f"| modelo melhor que a **régua** (família F5), testes que resistem ao Holm | "
             f"{int(f5.loc['AF', 'sum'])} de {int(f5.loc['AF', 'size'])} | {int(f5.loc['EM', 'sum'])} de {int(f5.loc['EM', 'size'])} | "
             f"{e2['f5_total'][0]} de {e2['f5_total'][1]} |")
    L.append(f"| idem, somando as comparações entre blocos | | | {e2['f5_blocos'][0]} de {e2['f5_blocos'][1]} |")
    L.append(f"| modelo melhor que a **B2** (família F4), testes que resistem ao Holm | "
             f"{int(f4.loc['AF', 'sum'])} de {int(f4.loc['AF', 'size'])} | {int(f4.loc['EM', 'sum'])} de {int(f4.loc['EM', 'size'])} | "
             f"{int(f4['sum'].sum())} de {int(f4['size'].sum())} |")
    g = e2["f4_ganho_af"]
    L += ["", "**Leitura.** Nenhum modelo ordenou melhor que a régua. Contra a B2, os modelos ganham nos anos finais",
          f"(ganhos de +{br(g['min'], 2)} a +{br(g['max'], 2)} no Recall@K): a história da própria escola diz mais do que",
          "o território e a rede.", "",
          "**As duas réguas ano a ano** (Recall@20%, definição da Etapa 2). A régua acerta menos que a versão otimista em",
          (f"{int((e2['anos']['B1R_lag'] < e2['anos']['B1R']).sum())} dos {len(e2['anos'])} anos-etapa, e oscila mais no "
          f"ensino médio (de {br(e2['anos'].loc['EM', 'B1R_lag'].min())} a {br(e2['anos'].loc['EM', 'B1R_lag'].max())}):"), "",
          "| Etapa | Desfecho | Régua (abandono de t−1) | Otimista (abandono de t) | B2 |", "|---|---|---|---|---|"]
    for (et, ano), row in e2["anos"].iterrows():
        L.append(f"| {et} | {ano} | {br(row['B1R_lag'])} | {br(row['B1R'])} | {br(row['B2'])} |")
    L += ["", "## 4. A classificação de alto risco na janela segura", "",
          "Fontes: as réguas, em `saida/avaliacao/reguas_janela.csv`, **regeradas** pelo abandono-rr e idênticas às do",
          f"projeto anterior; a ferramenta e os intervalos, em `experimentos/classificacao_2013_2018/saida/` ({ANT}),",
          "da execução única de 2026-11-10. Desfechos de 2016 a 2019, quatro anos juntos; IC de 95% por bootstrap",
          "sorteando escolas (5.000 reamostragens).", "",
          "| Etapa | Acaso | B2 | **Régua** [IC 95%] | Ferramenta (regressão logística, bloco 3) [IC 95%] |",
          "|---|---|---|---|---|"]
    r = cl["reguas"]
    for et, nome_etapa in ETAPAS.items():
        reg, fer = ic.loc[(et, "B1R_lag", 0)], ic.loc[(et, "logistica", 3)]
        assert abs(reg["Rec@20pct"] - r.loc[(et, "B1R_lag"), "Rec@20pct"]) < 1e-12   # régua regerada = citada
        L.append(f"| {nome_etapa} | {br(r.loc[(et, 'acaso'), 'Rec@20pct'])} | {br(r.loc[(et, 'B2'), 'Rec@20pct'])} | "
                 f"**{br(r.loc[(et, 'B1R_lag'), 'Rec@20pct'])}** [{br(reg['Rec@20pct_lo'])}; {br(reg['Rec@20pct_hi'])}] | "
                 f"{br(fer['Rec@20pct'])} [{br(fer['Rec@20pct_lo'])}; {br(fer['Rec@20pct_hi'])}] |")
    f6 = cl["f6_r20"]
    L += ["", "*Recall@20%, sobre o rótulo de alto risco.*", "",
          "**O teste que decide** (família F6: ferramenta − régua, 2 etapas × 3 modelos × 3 blocos × 2 métricas, com Holm):",
          f"**{cl['f6_ganho']} GANHO em {cl['f6_n']} testes**; o menor p ajustado é {br(cl['p_holm_min'])}. No Recall@20%:", ""]
    L += [f"- {ETAPAS[et]}: " + ", ".join(f"{int(v)} {k}" for k, v in f6.loc[et].items() if v) for et in f6.index]
    L += ["", "**Leitura.** A ferramenta fica bem acima do acaso, mas não se distingue da régua. Nos anos finais, o ganho",
          "possível é pequeno demais para valer a pena; no ensino médio, os intervalos são largos demais para decidir.", "",
          "## 5. O que isso diz para o projeto", "",
          "- A régua é o adversário certo: é a regra que a secretaria poderia usar hoje, sem modelo, com o dado que já tem.",
          "- Nenhum modelo, na Etapa 2 nem na classificação, ordenou melhor do que ela.",
          "- A versão otimista acerta mais, mas usa um dado que não existe na hora da decisão; nunca é adversária.",
          "- A B2 é o piso informativo: ganhar dela mostra que a história da escola importa, não que a ferramenta é útil.", ""]
    return "\n".join(L)


def main():
    DESTINO.write_text(texto(), encoding="utf-8", newline="\n")
    print(f">>> {DESTINO}")


if __name__ == "__main__":
    main()
