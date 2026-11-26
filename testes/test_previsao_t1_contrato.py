"""Contratos `pares.csv` e `importancias.csv` e o gerador sintético (issue #15, R0a).

Só dados sintéticos e os exemplos do CONTRATO.md; nenhum dado real é lido.
  1. os exemplos do CONTRATO.md passam no validador, e as colunas do contrato estão no texto;
  2. o sintético segue o contrato, é reprodutível e sobrevive a gravar e reler;
  3. os efeitos plantados aparecem nos pares e as importâncias falsas põem as plantadas no topo;
  4. cada violação do contrato é denunciada.
"""
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experimentos.previsao_t1 import contrato as C
from experimentos.previsao_t1 import sintetico as S

RAIZ = Path(__file__).resolve().parents[1]
TEXTO = (RAIZ / "experimentos" / "previsao_t1" / "CONTRATO.md").read_text(encoding="utf-8")
EXEMPLOS = re.findall(r"```csv\n(.*?)```", TEXTO, flags=re.DOTALL)


@pytest.fixture(scope="module")
def pares():
    return S.gerar_pares(0)


@pytest.fixture(scope="module")
def imp(pares):
    return S.gerar_importancias(C.preditores(pares), 0)


# ------------------------------------------------------------------ 1. o texto e o código dizem o mesmo
def test_exemplos_do_contrato_passam():
    assert len(EXEMPLOS) == 2, "o CONTRATO.md deve ter um exemplo de cada arquivo"
    pares = C.ler_pares(io.StringIO(EXEMPLOS[0]))
    C.ler_importancias(io.StringIO(EXEMPLOS[1]), C.preditores(pares))


@pytest.mark.parametrize("coluna", C.OBRIGATORIAS_PARES + C.COLUNAS_IMPORTANCIAS + list(C.HISTORICO)
                         + list(C.NAO_PREDITORAS))
def test_colunas_do_contrato_estao_no_texto(coluna):
    assert f"`{coluna}`" in TEXTO


def test_nomes_dos_pares_existem_no_dicionario(pares):
    dicionario = (RAIZ / "dataset" / "DICIONARIO.md").read_text(encoding="utf-8")
    for c in pares.columns:
        assert f"| `{c}` |" in dicionario, f"{c} não está no dataset/DICIONARIO.md (regra 11)"


# ------------------------------------------------------------------ 2. o sintético segue o contrato
def test_sintetico_segue_o_contrato(pares, imp):
    C.validar_pares(pares)
    C.validar_importancias(imp, C.preditores(pares))
    assert set(pares["etapa"]) == {"AF", "EM"}
    assert set(C.preditores(pares)) == set(S.PLANTADAS) | set(S.RUIDO)
    assert pares[list(S.RUIDO)].isna().any().any(), "o sintético deve ter vazios para exercitar a imputação"
    assert not pares["co_entidade"].str.startswith("14").any(), "código de escola sintético parece real"


def test_sintetico_reprodutivel():
    pd.testing.assert_frame_equal(S.gerar_pares(3), S.gerar_pares(3))
    assert not S.gerar_pares(3).equals(S.gerar_pares(4))


def test_gravar_e_reler(tmp_path, pares, imp):
    S.main(["--semente", "0", "--saida", str(tmp_path)])
    relido = C.ler_pares(tmp_path / "pares.csv")
    pd.testing.assert_frame_equal(relido, pares, check_dtype=False)
    assert relido["co_entidade"].dtype == "string"
    relida = C.ler_importancias(tmp_path / "importancias.csv", C.preditores(relido))
    pd.testing.assert_frame_equal(relida, imp, check_dtype=False)
    assert b"\r\n" not in (tmp_path / "pares.csv").read_bytes()


def test_cada_escola_segue_no_tempo(pares):
    """O abandono_t de um ano é o abandono_t1 do ano anterior, como nos pares reais."""
    p = pares.sort_values(["co_entidade", "etapa", "ano"])
    seguinte = p.groupby(["co_entidade", "etapa"])["abandono_t"].shift(-1)
    ok = seguinte.notna()
    assert ok.any() and (seguinte[ok] == p.loc[ok, "abandono_t1"]).all()


# ------------------------------------------------------------------ 3. os efeitos plantados
@pytest.mark.parametrize("etapa", C.ETAPAS)
def test_efeitos_plantados_recuperados(pares, etapa):
    g = pares[pares["etapa"] == etapa].dropna()
    nomes = ["abandono_t", "localizacao", "dim_iib_prop", *S.RUIDO]
    X = np.column_stack([np.ones(len(g))] + [
        (g[c] == "Rural").to_numpy(float) if c == "localizacao" else g[c].to_numpy(float) for c in nomes])
    b = dict(zip(nomes, np.linalg.lstsq(X, g[C.ALVO].to_numpy(float), rcond=None)[0][1:]))
    for v, efeito in S.PLANTADAS.items():
        assert b[v] == pytest.approx(efeito, rel=0.25), v
    for v in S.RUIDO:
        assert abs(b[v]) < 0.4, v


def test_importancias_falsas_poem_as_plantadas_no_topo(imp):
    media = imp.groupby(C.GRUPO_MODELO + ["variavel"])["importancia"].mean().reset_index()
    for chave, g in media.groupby(C.GRUPO_MODELO):
        plantadas = g[g["variavel"].isin(list(S.PLANTADAS))]["importancia"]
        ruido = g[~g["variavel"].isin(list(S.PLANTADAS))]["importancia"]
        assert plantadas.min() > ruido.max(), chave
    assert (imp.loc[~imp["variavel"].isin(list(S.PLANTADAS)), "importancia"] < 0).any()


# ------------------------------------------------------------------ 4. violações denunciadas
def _quebra_pares(pares, f):
    p = pares.copy()
    f(p)
    return p


def _com(p, col, valor):
    p[col] = valor


VIOLACOES_PARES = {
    "co_entidade número": lambda p: _com(p, "co_entidade", p["co_entidade"].astype("int64")),
    "co_entidade curto": lambda p: _com(p, "co_entidade", p["co_entidade"].str[1:]),
    "ano_alvo errado": lambda p: _com(p, "ano_alvo", p["ano"] + 2),
    "etapa inválida": lambda p: p.loc.__setitem__((p.index[0], "etapa"), "EF"),
    "chave repetida": lambda p: p.loc.__setitem__((p.index[1], ["ano", "ano_alvo"]),
                                                  p.loc[p.index[0], ["ano", "ano_alvo"]].to_numpy()),
    "alvo vazio": lambda p: p.loc.__setitem__((p.index[0], C.ALVO), np.nan),
    "alvo acima de 100": lambda p: p.loc.__setitem__((p.index[0], C.ALVO), 101.0),
    "preditor de t+1": lambda p: _com(p, "alto_risco_t1", 0),
    "preditor _zano": lambda p: _com(p, "dim_iib_zano", 0.0),
    "identificação como preditor": lambda p: _com(p, "co_municipio", "1400100"),
    "três taxas juntas": lambda p: _com(p, "aprovacao_t", 100 - p["reprovacao_t"] - p["abandono_t"]),
    "preditor todo vazio": lambda p: _com(p, "iep_projetor", np.nan),
}


@pytest.mark.parametrize("nome", VIOLACOES_PARES)
def test_pares_violacao_denunciada(pares, nome):
    with pytest.raises(C.ContratoInvalido) as e:
        C.validar_pares(_quebra_pares(pares, VIOLACOES_PARES[nome]))
    assert len(e.value.problemas) == 1, e.value.problemas     # denunciada pelo motivo certo, e só por ele


def test_pares_sem_coluna_obrigatoria(pares):
    with pytest.raises(C.ContratoInvalido, match="obrigatórias"):
        C.validar_pares(pares.drop(columns=[C.PERSISTENCIA]))


def test_pares_lista_todos_os_problemas(pares):
    p = pares.copy()
    p["ano_alvo"] = p["ano"] + 2
    p["dim_iib_zano"] = 0.0
    with pytest.raises(C.ContratoInvalido) as e:
        C.validar_pares(p)
    assert len(e.value.problemas) == 2


VIOLACOES_IMP = {
    "chave repetida": lambda i: pd.concat([i, i.iloc[[0]]], ignore_index=True),
    "supera muda entre sementes": lambda i: i.assign(supera_persistencia=i["semente"] % 2),
    "sem histórico com abandono_t": lambda i: i.assign(historico=1 - i["historico"]),
    "semente com variável a menos": lambda i: i.drop(i.index[(i["semente"] == 0)][:1]),
    "importância vazia": lambda i: i.assign(importancia=i["importancia"].where(i.index != 0)),
    "historico fora de 0/1": lambda i: i.assign(historico=i["historico"] * 2),
    "coluna a mais": lambda i: i.assign(mae=0.0),
    "dois anos num recorte": lambda i: i.assign(ano_validacao=np.where(
        i["etapa"] == "EM", i["ano_validacao"] + 1, i["ano_validacao"])),
}


@pytest.mark.parametrize("nome", VIOLACOES_IMP)
def test_importancias_violacao_denunciada(pares, imp, nome):
    with pytest.raises(C.ContratoInvalido) as e:
        C.validar_importancias(VIOLACOES_IMP[nome](imp.copy()), C.preditores(pares))
    assert len(e.value.problemas) == 1, e.value.problemas


def test_importancias_variavel_fora_dos_pares(pares, imp):
    with pytest.raises(C.ContratoInvalido, match="não são preditoras"):
        C.validar_importancias(imp, [v for v in C.preditores(pares) if v != "iep_internet"])
