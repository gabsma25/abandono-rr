# -*- coding: utf-8 -*-
"""
ANÁLISE 04 — Funil de recorte da base avaliada, com contagem por ano e etapa.
[FATO]: só contagem; o desfecho não é critério de nada.

A base avaliada é a base_atual (tx_rend de escolas de RR, 2007–2025), espinha
da Etapa 1 e do painel da Etapa 2. Ela NÃO é a base oficial do abandono-escolar
(6.054 linhas em 2019–2025, união de todos os indicadores): a base_atual tem
só as escolas com linha no tx_rend (4.733 linhas em 2019–2025).

Degraus (coluna `ordem`):
  1 Brasil ......... linhas da planilha tx_rend de escolas do ano, lidas de
                     abandono-escolar/docs/inventario_indicadores.csv
                     (n_linhas_dados). Só 2019–2025: os zips de 2007–2018 não
                     estão nesta máquina (verificado em 2026-11-03; SINTESE
                     §5.2), então nesses anos o funil começa em RR.
  2 RR ............. linhas da base_atual no ano (todas as redes)
  3 públicas ....... REDE_PUBLICA == 1
  4 com a etapa em t ............... públicas com taxa de abandono da etapa
  5 com a etapa em t e alvo em t+1 . encaixado no 4
  6 com alvo em t+1, sem a etapa em t (o `n_sem_t` da Etapa 1)
  7 universo da avaliação = 5 + 6 .. públicas com alvo em t+1
                                     (baselines.universo); NÃO é encaixado
                                     no 5
  8 painel da Etapa 2 .............. o universo, só ANO 2019–2024
                                     (painel.montar)

Os degraus 1–3 não dependem da etapa e se repetem em AF e EM. Ausência
estrutural fica vazia (nunca 0), com o motivo em `observacao`: Brasil em
2007–2018, alvo em t+1 no último ano (t+1 ainda não publicado), painel fora
de 2019–2024.

`tipo`, com o mesmo vocabulário do abandono-escolar/docs/funil_contagem.csv
(o notebook 02 desenha cada degrau por ele): "funil" para os degraus
encaixados (1–5 e 8, que é o 7 restrito a 2019–2024), "fora do funil" para o
6 (nunca somado a outro degrau) e "total" para o 7 (= 5 + 6).

Saída: gustavo/saida/relatorios/funil_recorte.csv
       (ano, etapa, ordem, degrau, tipo, n, fonte, observacao)
Uso:   python src/relatorios/04_funil_recorte.py
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "estendida").is_dir())
GUSTAVO = RAIZ  # raiz do abandono-rr (no projeto anterior, a pasta gustavo/)
sys.path.insert(0, str(GUSTAVO / "src" / "avaliacao"))
import baselines as B  # noqa: E402
import painel as P  # noqa: E402

SAIDA = GUSTAVO / "saida" / "relatorios" / "funil_recorte.csv"
F_ATUAL = "saida/base_atual.parquet"
TIPO = {6: "fora do funil", 7: "total"}   # os demais degraus: "funil"


# abandono-rr: os degraus 1 (Brasil) e 8 (painel da Etapa 2) do projeto anterior dependiam do pipeline
# oficial 2019–2025 (inventário de indicadores e base com TDI/ATU/IED), que fica fora até a meta M5
# (docs/DECISOES.md). O funil começa em RR; os degraus 2 a 7 são os mesmos, calculados da mesma forma.
def funil(atual):
    anos = sorted(atual["ANO"].astype(int).unique())
    ultimo = anos[-1]
    pub = atual["REDE_PUBLICA"].astype("Int8") == 1
    linhas = []

    def reg(ano, etapa, ordem, degrau, n, fonte, obs=""):
        linhas.append({"ano": ano, "etapa": etapa, "ordem": ordem, "degrau": degrau,
                       "tipo": TIPO.get(ordem, "funil"), "n": n, "fonte": fonte, "observacao": obs})

    for etapa, col in B.ETAPAS.items():
        u = B.universo(atual, etapa)
        for ano in anos:
            a = (atual["ANO"] == ano).to_numpy()
            com_t = a & pub & atual[col].notna()
            com_t1 = a & pub & atual[f"{col}_T1"].notna()
            sem_t1 = ano == ultimo
            reg(ano, etapa, 2, "RR", int(a.sum()), F_ATUAL)
            reg(ano, etapa, 3, "públicas", int((a & pub).sum()), F_ATUAL + " (REDE_PUBLICA = 1)")
            reg(ano, etapa, 4, "com a etapa em t", int(com_t.sum()), F_ATUAL + f" ({col} não nulo)")
            if sem_t1:
                obs = "t+1 ainda não publicado"
                for ordem, nome in ((5, "com a etapa em t e alvo em t+1"),
                                    (6, "com alvo em t+1, sem a etapa em t"),
                                    (7, "universo da avaliação")):
                    reg(ano, etapa, ordem, nome, pd.NA, "", obs)
                continue
            reg(ano, etapa, 5, "com a etapa em t e alvo em t+1", int((com_t & com_t1).sum()),
                F_ATUAL + f" ({col} e {col}_T1 não nulos)")
            reg(ano, etapa, 6, "com alvo em t+1, sem a etapa em t", int((com_t1 & ~com_t).sum()),
                F_ATUAL + f" ({col}_T1 não nulo, {col} nulo)")
            reg(ano, etapa, 7, "universo da avaliação", int((u["ANO"] == ano).sum()), "baselines.universo")
    out = pd.DataFrame(linhas)
    out["n"] = out["n"].astype("Int64")
    return out


def main():
    atual = pd.read_parquet(P.P_ATUAL)
    out = funil(atual)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(SAIDA, index=False, encoding="utf-8")
    print(out.pivot_table(index=["etapa", "ano"], columns="ordem", values="n", aggfunc="first").to_string())
    print(f">>> {SAIDA}")


if __name__ == "__main__":
    main()
