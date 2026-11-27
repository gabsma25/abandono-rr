"""Recortes da previsão do abandono de t+1: janela expansiva e teste final trancado (issue #16, M1a).

Um recorte diz com que anos o modelo aprende (treino) e em que ano ele é avaliado (validação). Os pares são os do
`pares.csv` (#15): uma linha por escola × ano t × etapa, com as variáveis até t e o abandono de t+1 (`ano_alvo`).

**A regra de tempo (folga de 1 ano).** A previsão do abandono de t+1 é feita no começo de t+1. Nesse momento o INEP
ainda não publicou o rendimento de t: ele sai durante t+1 (`docs/BASELINE.md`, seção 1; `docs/PROTOCOLO.md`, 4.1).
Então, para validar os pares de `ano` = t_v (desfecho de t_v + 1), o treino só usa pares cujo desfecho já tinha
saído no começo de t_v + 1:

    ano_alvo do treino <= t_v - folga        (folga = 1  ->  ano do treino <= t_v - 2)

`folga=0` (treino com `ano_alvo <= t_v`) existe só como análise de sensibilidade: usa um desfecho que ainda não
estava publicado na hora da previsão, então é um **limite superior**, não a previsão que se faria de verdade.

**Janela expansiva.** O treino começa sempre no primeiro ano disponível e ganha um ano a cada recorte. Só há recorte
quando o treino tem pelo menos `MIN_ANOS_TREINO` anos. A janela deslizante fica para a versão completa.

**Teste final trancado.** O par t = `ANO_T_TESTE_FINAL` (2024, desfecho de 2025) é o teste final. Ele é descartado
antes de qualquer conta e nunca aparece em recorte algum, nem no treino nem na validação; `dividir` levanta erro se
ele aparecer. Nenhuma função deste módulo devolve essas linhas: o acesso ao teste final fica para o modo real do
`rodar.py` (#22), bloqueado até o protocolo ser congelado no `docs/PROTOCOLO.md`.

**Anos já vistos.** Os desfechos de 2016–2019 e de 2021–2024 já foram usados como teste (`CLAUDE.md`, regra 10). O
que sair dos recortes nesses anos é exploratório e não escolhe nada.

O módulo não lê arquivo nenhum: trabalha só com o DataFrame que recebe e não o modifica.

Uso:
    python -m experimentos.previsao_t1.recortes            # imprime a tabela dos recortes de t = 2008 a 2024
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# O par t = 2024 -> desfecho de 2025 é o teste final, fechado (docs/DECISOES.md).
ANO_T_TESTE_FINAL = 2024
# O rendimento de t só é publicado durante t + 1: o último desfecho conhecido na hora da previsão é o de t_v - 1.
FOLGA_PADRAO = 1
# Menor número de anos t no treino do primeiro recorte: o mínimo da faixa de 3 a 5 anos que o professor deu para a
# janela deslizante, usado também como piso da expansiva. Fixado antes de rodar; não sai de nenhum resultado.
MIN_ANOS_TREINO = 3


class RecorteInvalido(ValueError):
    """O recorte ou a divisão viola a regra de tempo ou o trancamento do teste final."""


@dataclass(frozen=True)
class Recorte:
    id: str                     # "expansiva_{t_v}", o mesmo identificador do importancias.csv (#15)
    tipo: str                   # "expansiva"
    ano_validacao: int          # t_v: a validação usa os pares de ano = t_v (desfecho de t_v + 1)
    anos_treino: tuple[int, ...]
    folga: int


def gerar_recortes(anos, folga: int = FOLGA_PADRAO, min_anos_treino: int = MIN_ANOS_TREINO) -> list[Recorte]:
    """Os recortes da janela expansiva para os anos t disponíveis, em ordem de `ano_validacao`."""
    if folga < 0:
        raise ValueError("folga não pode ser negativa")
    if min_anos_treino < 1:
        raise ValueError("min_anos_treino tem de ser pelo menos 1")
    # O teste final sai antes de qualquer conta.
    disponiveis = sorted({int(a) for a in anos if int(a) < ANO_T_TESTE_FINAL})
    recortes = []
    for t_v in disponiveis:
        treino = tuple(a for a in disponiveis if a + 1 <= t_v - folga)
        if len(treino) >= min_anos_treino:
            recortes.append(Recorte(id=f"expansiva_{t_v}", tipo="expansiva", ano_validacao=t_v,
                                    anos_treino=treino, folga=folga))
    return recortes


def _conferir(recorte: Recorte) -> None:
    problemas = []
    if recorte.ano_validacao >= ANO_T_TESTE_FINAL:
        problemas.append(f"a validação t = {recorte.ano_validacao} é o teste final ou depois dele")
    tardios = [a for a in recorte.anos_treino if a >= ANO_T_TESTE_FINAL]
    if tardios:
        problemas.append(f"o treino tem o teste final ou anos depois dele: {tardios}")
    fora = [a for a in recorte.anos_treino if a + 1 > recorte.ano_validacao - recorte.folga]
    if fora:
        problemas.append(f"o treino tem anos cujo desfecho ainda não saiu na hora da previsão: {fora}")
    if problemas:
        raise RecorteInvalido(f"recorte {recorte.id}: " + "; ".join(problemas))


def dividir(pares: pd.DataFrame, recorte: Recorte, etapa: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Treino e validação do recorte (cópias), opcionalmente de uma etapa só. Não modifica `pares`."""
    _conferir(recorte)
    base = pares if etapa is None else pares[pares["etapa"] == etapa]
    treino = base[base["ano"].isin(recorte.anos_treino)].copy()
    validacao = base[base["ano"] == recorte.ano_validacao].copy()

    problemas = []
    for nome, parte in (("treino", treino), ("validação", validacao)):
        if (parte["ano"] >= ANO_T_TESTE_FINAL).any() or (parte["ano_alvo"] >= ANO_T_TESTE_FINAL + 1).any():
            problemas.append(f"o {nome} tem linhas do teste final")
    if len(treino) and treino["ano_alvo"].max() > recorte.ano_validacao - recorte.folga:
        problemas.append("o treino tem desfecho que ainda não saiu na hora da previsão")
    if len(treino.index.intersection(validacao.index)):
        problemas.append("treino e validação têm linhas em comum")
    if problemas:
        raise RecorteInvalido(f"recorte {recorte.id}: " + "; ".join(problemas))
    return treino, validacao


def tabela_recortes(recortes: list[Recorte]) -> pd.DataFrame:
    """Uma linha por recorte, para o README e a apresentação (regra 3: número gerado por código)."""
    colunas = ["recorte", "tipo", "ano_validacao", "ano_alvo_validacao", "primeiro_ano_treino",
               "ultimo_ano_treino", "ultimo_ano_alvo_treino", "n_anos_treino", "folga"]
    linhas = [{
        "recorte": r.id, "tipo": r.tipo, "ano_validacao": r.ano_validacao, "ano_alvo_validacao": r.ano_validacao + 1,
        "primeiro_ano_treino": r.anos_treino[0], "ultimo_ano_treino": r.anos_treino[-1],
        "ultimo_ano_alvo_treino": r.anos_treino[-1] + 1, "n_anos_treino": len(r.anos_treino), "folga": r.folga,
    } for r in recortes]
    return pd.DataFrame(linhas, columns=colunas)


def main() -> None:
    tabela = tabela_recortes(gerar_recortes(range(2008, ANO_T_TESTE_FINAL + 1)))
    print(f"Recortes da janela expansiva, anos t de 2008 a {ANO_T_TESTE_FINAL} (o último é o teste final, trancado):")
    print(tabela.to_string(index=False))


if __name__ == "__main__":
    main()
