"""
Réguas da janela segura (t de 2013 a 2018; alvos de teste de 2016 a 2019), sem modelo nenhum.

  B1R_lag  nota = abandono da etapa em t−1, o último conhecido na hora de fazer a lista
  B2       nota = mediana do abandono de t+1 no treino, por localização × dependência
  acaso    valores esperados de uma lista sorteada (PR-AUC = prevalência, Recall@K = K/n,
           ROC-AUC = 0,5), como no projeto anterior

Usa as mesmas funções da classificação (classificacao.montar, metricas_ano,
baselines.b2_mediana_estrato) e devolve as linhas no formato de
experimentos/classificacao_2013_2018/saida/03_classificacao.csv, para que o teste de
equivalência compare valor a valor. Nenhum modelo é treinado aqui.
"""
import baselines as B
import classificacao as C
import metricas as M
import painel as P
import pandas as pd

PERIODO = f"{C.ANOS_TESTE[0]}–{C.ANOS_TESTE[-1]}"
SOMA = {"n", "n_alto"}


def celulas(painel, etapa, alvo="top20", anos=C.ANOS_TESTE):
    """Uma célula por ano de teste, só com as notas das réguas (mesma divisão de classificacao.rodar_etapa)."""
    s = P.SUF[etapa]
    col = f"alto_{alvo}"
    out = []
    for ano in anos:
        tr = painel[painel["ANO_ALVO"] < ano]
        te = painel[painel["ANO_ALVO"] == ano]
        out.append({"ano_alvo": ano, "n_treino": len(tr), "y": te[col].to_numpy(),
                    "p": {"B1R_lag": te[f"ABANDONO_{s}_L1"].to_numpy(),
                          "B2": B.b2_mediana_estrato(tr, te)}})
    return out


def _acaso(rot):
    n, pos = len(rot), int(rot.sum())
    k20 = M.k_de_fracao(n, C.FRACAO_ALTO)
    m = {"n": n, "n_alto": pos, "prevalencia": pos / n, "K20pct": k20, "PR_AUC": pos / n,
         "ROC_AUC": 0.5, "Rec@20pct": k20 / n, "Prec@20pct": pos / n}
    for k in C.KS_ESCOLAS:
        m[f"Rec@{k}"], m[f"Prec@{k}"] = k / n, pos / n
    return m


def tabela(base):
    """Métricas das réguas por ano de teste e agrupadas (média simples dos anos; contagens somadas)."""
    partes = []
    for etapa in B.ETAPAS:
        painel = C.montar(etapa, base)
        for alvo in C.ALVOS:
            cels = celulas(painel, etapa, alvo)
            for nome in ("B1R_lag", "B2", "acaso"):
                por_ano = []
                for c in cels:
                    m = _acaso(c["y"]) if nome == "acaso" else C.metricas_ano(c["y"], c["p"][nome], False)
                    por_ano.append({"periodo": str(c["ano_alvo"]), "n_treino": c["n_treino"], **m})
                df = pd.DataFrame(por_ano)
                agr = {k: (df[k].sum() if k in SOMA else df[k].mean()) for k in df.columns
                       if k not in ("periodo", "n_treino")}
                df = pd.concat([df, pd.DataFrame([{"periodo": PERIODO, **agr}])], ignore_index=True)
                df.insert(0, "bloco", 0)
                df.insert(0, "modelo", nome)
                df.insert(0, "etapa", etapa)
                df.insert(0, "alvo", alvo)
                partes.append(df)
    out = pd.concat(partes, ignore_index=True)
    out["n_treino"] = out["n_treino"].astype("float64")
    return out


if __name__ == "__main__":
    import sys
    from pathlib import Path

    raiz = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
    base = pd.read_parquet(P.P_ATUAL)
    t = tabela(base)
    destino = raiz / "saida" / "avaliacao" / "reguas_janela.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(destino, index=False, lineterminator="\n")
    agr = t[(t["alvo"] == "top20") & (t["periodo"] == PERIODO)]
    print(agr[["etapa", "modelo", "PR_AUC", "Rec@20pct"]].round(3).to_string(index=False))
    print(f">>> {destino}")
    sys.exit(0)
