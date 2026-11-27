"""experimentos/previsao_t1/recortes.py (issue #16, M1a): janela expansiva, folga de 1 ano e teste final trancado.

  1. regra de tempo: o treino só tem desfechos já publicados na hora da previsão (folga 1 e 0);
  2. com os padrões e t = 2008–2024, os recortes vão de expansiva_2012 a expansiva_2023 (valores escritos aqui);
  3. o teste final (t = 2024, desfecho 2025) nunca aparece e um recorte montado à mão com ele dá erro;
  4. a janela é expansiva: mesmo começo, um ano a mais por recorte;
  5. validação só com ano = t_v, sem linha em comum com o treino, e o filtro por etapa;
  6. o mínimo de anos de treino;
  7. o DataFrame de entrada não muda;
  8. o módulo não abre arquivo nenhum;
  9. o resultado é determinístico.

Só DataFrames montados aqui, com códigos de escola começando por 99 (não é UF). Nenhum dado real é lido."""
from __future__ import annotations

import builtins

import pandas as pd
import pytest

from experimentos.previsao_t1 import recortes as R

ANOS = range(2008, 2025)          # t = 2008 a 2024; 2024 é o teste final


def _pares(anos=ANOS, escolas=3, etapas=("AF", "EM")):
    linhas = [{"co_entidade": f"99{e:06d}", "ano": t, "ano_alvo": t + 1, "etapa": etapa,
               "abandono_t1": float((e + t) % 7), "abandono_tm1": float((e * t) % 5)}
              for e in range(1, escolas + 1) for etapa in etapas for t in anos]
    p = pd.DataFrame(linhas)
    p["co_entidade"] = p["co_entidade"].astype("string")
    return p


# ------------------------------------------------------------------ 1. regra de tempo
@pytest.mark.parametrize("folga", [1, 0])
def test_treino_so_com_desfecho_ja_publicado(folga):
    pares = _pares()
    recortes = R.gerar_recortes(ANOS, folga=folga)
    assert recortes
    for r in recortes:
        assert all(a + 1 <= r.ano_validacao - folga for a in r.anos_treino)
        treino, _ = R.dividir(pares, r)
        assert treino["ano_alvo"].max() <= r.ano_validacao - folga


def test_recorte_que_fura_a_folga_da_erro():
    r = R.Recorte(id="expansiva_2015", tipo="expansiva", ano_validacao=2015,
                  anos_treino=(2011, 2012, 2013, 2014), folga=1)     # 2014 -> desfecho 2015 > 2015 - 1
    with pytest.raises(R.RecorteInvalido):
        R.dividir(_pares(), r)


# ------------------------------------------------------------------ 2. recortes com os padrões
def test_recortes_padrao_escritos_literalmente():
    recortes = R.gerar_recortes(ANOS)
    assert [r.id for r in recortes] == [f"expansiva_{a}" for a in range(2012, 2024)]
    primeiro, ultimo = recortes[0], recortes[-1]
    assert primeiro.ano_validacao == 2012 and primeiro.anos_treino == (2008, 2009, 2010)
    assert ultimo.ano_validacao == 2023 and ultimo.anos_treino == tuple(range(2008, 2022))
    assert all(r.folga == 1 and r.tipo == "expansiva" for r in recortes)
    assert (R.ANO_T_TESTE_FINAL, R.FOLGA_PADRAO, R.MIN_ANOS_TREINO) == (2024, 1, 3)


def test_tabela_recortes():
    tab = R.tabela_recortes(R.gerar_recortes(ANOS))
    assert len(tab) == 12
    assert tab.iloc[0].to_dict() == {
        "recorte": "expansiva_2012", "tipo": "expansiva", "ano_validacao": 2012, "ano_alvo_validacao": 2013,
        "primeiro_ano_treino": 2008, "ultimo_ano_treino": 2010, "ultimo_ano_alvo_treino": 2011,
        "n_anos_treino": 3, "folga": 1}
    assert (tab["ultimo_ano_alvo_treino"] == tab["ano_validacao"] - 1).all()
    assert R.tabela_recortes([]).empty


# ------------------------------------------------------------------ 3. teste final trancado
def test_teste_final_nunca_aparece():
    pares = pd.concat([_pares(), _pares(anos=[2025])], ignore_index=True)   # 2024 e até 2025 na entrada
    for folga in (1, 0):
        for r in R.gerar_recortes(sorted(pares["ano"].unique()), folga=folga):
            assert r.ano_validacao < 2024 and max(r.anos_treino) < 2024
            treino, validacao = R.dividir(pares, r)
            for parte in (treino, validacao):
                assert (parte["ano"] < 2024).all() and (parte["ano_alvo"] <= 2024).all()


@pytest.mark.parametrize("ano_validacao, anos_treino", [
    (2024, (2008, 2009, 2010)),                 # validar no teste final
    (2026, (2008, 2009, 2024)),                 # teste final no treino
])
def test_recorte_com_o_teste_final_da_erro(ano_validacao, anos_treino):
    r = R.Recorte(id="feito_a_mao", tipo="expansiva", ano_validacao=ano_validacao,
                  anos_treino=anos_treino, folga=1)
    with pytest.raises(R.RecorteInvalido):
        R.dividir(_pares(anos=range(2008, 2026)), r)


# ------------------------------------------------------------------ 4. janela expansiva
def test_janela_expansiva():
    recortes = R.gerar_recortes(ANOS)
    assert len({r.anos_treino[0] for r in recortes}) == 1
    for antes, depois in zip(recortes, recortes[1:]):
        assert set(antes.anos_treino) < set(depois.anos_treino)
        assert len(depois.anos_treino) == len(antes.anos_treino) + 1
        assert depois.ano_validacao == antes.ano_validacao + 1


# ------------------------------------------------------------------ 5. partição e etapa
def test_particao_e_etapa():
    pares = _pares()
    for r in R.gerar_recortes(ANOS):
        treino, validacao = R.dividir(pares, r)
        assert (validacao["ano"] == r.ano_validacao).all() and len(validacao) == 6
        assert set(treino["ano"]) == set(r.anos_treino)
        assert treino.index.intersection(validacao.index).empty
        t_af, v_af = R.dividir(pares, r, etapa="AF")
        assert set(t_af["etapa"]) == {"AF"} and set(v_af["etapa"]) == {"AF"}
        assert len(t_af) == len(treino) // 2


# ------------------------------------------------------------------ 6. mínimo de anos
def test_minimo_de_anos_de_treino():
    assert [r.id for r in R.gerar_recortes(range(2008, 2014))] == ["expansiva_2012", "expansiva_2013"]
    assert [r.id for r in R.gerar_recortes(range(2008, 2014), min_anos_treino=4)] == ["expansiva_2013"]
    assert R.gerar_recortes(range(2008, 2012)) == []
    assert R.gerar_recortes([]) == []
    # com t = 2020–2025 só sobram 2020–2023 (o resto é teste final ou depois): 2 anos de treino no máximo
    assert R.gerar_recortes(range(2020, 2026)) == []


def test_parametros_invalidos():
    with pytest.raises(ValueError):
        R.gerar_recortes(ANOS, folga=-1)
    with pytest.raises(ValueError):
        R.gerar_recortes(ANOS, min_anos_treino=0)


# ------------------------------------------------------------------ 7. sem efeito colateral
def test_nao_modifica_a_entrada():
    pares = _pares()
    copia = pares.copy(deep=True)
    for r in R.gerar_recortes(ANOS):
        treino, validacao = R.dividir(pares, r)
        treino["abandono_t1"] = -1.0
        validacao["abandono_t1"] = -1.0
    pd.testing.assert_frame_equal(pares, copia)


# ------------------------------------------------------------------ 8. não abre arquivo
def test_nao_abre_arquivo(monkeypatch):
    pares = _pares()

    def proibido(*a, **k):
        raise AssertionError("recortes.py não pode abrir arquivo")

    monkeypatch.setattr(builtins, "open", proibido)
    for r in R.gerar_recortes(ANOS):
        R.dividir(pares, r)


# ------------------------------------------------------------------ 9. determinismo
def test_deterministico():
    pares = _pares()
    a, b = R.gerar_recortes(ANOS), R.gerar_recortes(list(reversed(ANOS)))
    assert a == b
    for r in a:
        t1, v1 = R.dividir(pares, r)
        t2, v2 = R.dividir(pares, r)
        pd.testing.assert_frame_equal(t1, t2)
        pd.testing.assert_frame_equal(v1, v2)
