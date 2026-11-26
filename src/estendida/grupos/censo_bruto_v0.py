# -*- coding: utf-8 -*-
"""
Grupo CENSO_BRUTO_V0: as colunas do Censo que passam no filtro mecânico de saúde do estudo E (v0), brutas.

Protocolo: docs/PROTOCOLO.md, seção E.2 (escrito antes de qualquer execução); decisão: docs/DECISOES.md,
2026-11-20 ("Estudo E (v0)"). Segue o contrato de src/estendida/grupos/README.md, mas NÃO é ligado no
ligados.txt: o dataset não muda. Quem usa o grupo é experimentos/censo_bruto_v0/estudo_e.py.

EXTRAIR (linha a linha, só do cache completo do Censo)
------------------------------------------------------
Lê dados/cache/censo_completo/{ano}_escola.parquet de 2007 a 2024, só CO_ENTIDADE e COLUNAS, e converte o texto
com pd.to_numeric(errors="coerce"): '--', texto vazio e qualquer valor não numérico viram ausente, nunca 0
(regra 8). Devolve uma linha por escola e ano, de TODAS as escolas do cache: quem filtra o universo é o estudo.
2025 não é lido (o teste limpo fica fechado). Coluna que não existe no layout de um ano fica ausente nele.

FILTRO MECÂNICO (E.2, sem desfecho)
-----------------------------------
filtro_mecanico() recalcula a lista a partir do cache: só preditores, nas escolas públicas em funcionamento. As
regras são aplicadas na ordem da E.2 e cada coluna recebe o motivo da primeira em que cai. COLUNAS, abaixo, é a
lista fechada do protocolo, escrita literalmente; o estudo para com erro se o filtro não devolver exatamente ela.

Tipos (regra 9): ANO Int16, CO_ENTIDADE string (sem '.0'), as colunas Float64 nullable.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
CACHE = RAIZ / "dados" / "cache" / "censo_completo"

NOME = "censo_bruto_v0"
ANOS_EXTRAIR = range(2007, 2025)      # E.2: fonte 2007–2024; 2025 nunca é lido

# E.2: a lista fechada (124 colunas), em ordem alfabética
COLUNAS = [
    "IN_AGUA_CACIMBA", "IN_AGUA_FONTE_RIO", "IN_AGUA_INEXISTENTE", "IN_AGUA_POCO_ARTESIANO",
    "IN_AGUA_REDE_PUBLICA", "IN_ALMOXARIFADO", "IN_AREA_VERDE", "IN_AUDITORIO", "IN_BANHEIRO_CHUVEIRO",
    "IN_BANHEIRO_EI", "IN_BANHEIRO_PNE", "IN_COZINHA", "IN_DEPENDENCIAS_OUTRAS", "IN_DIURNO",
    "IN_EDUCACAO_INDIGENA", "IN_EJA", "IN_EJA_FUND", "IN_EJA_MED", "IN_ENERGIA_INEXISTENTE",
    "IN_EQUIP_COPIADORA", "IN_EQUIP_DVD", "IN_EQUIP_IMPRESSORA_MULT", "IN_EQUIP_PARABOLICA", "IN_EQUIP_SOM",
    "IN_EQUIP_TV", "IN_ESGOTO_FOSSA", "IN_ESGOTO_INEXISTENTE", "IN_ESGOTO_REDE_PUBLICA", "IN_ESP", "IN_ESP_CC",
    "IN_FUND", "IN_FUND_AF", "IN_FUND_AI", "IN_INF", "IN_INF_CRE", "IN_INF_PRE", "IN_LABORATORIO_CIENCIAS",
    "IN_LIXO_ENTERRA", "IN_LIXO_QUEIMA", "IN_LOCAL_FUNC_GALPAO", "IN_LOCAL_FUNC_OUTROS",
    "IN_LOCAL_FUNC_PREDIO_ESCOLAR", "IN_LOCAL_FUNC_SALAS_OUTRA_ESC", "IN_MED", "IN_NOTURNO",
    "IN_PARQUE_INFANTIL", "IN_PROF", "IN_PROF_TEC", "IN_QUADRA_ESPORTES_COBERTA",
    "IN_QUADRA_ESPORTES_DESCOBERTA", "IN_SALA_ATENDIMENTO_ESPECIAL", "IN_SALA_LEITURA", "QT_DOC_BAS",
    "QT_DOC_EJA", "QT_DOC_EJA_FUND", "QT_DOC_EJA_MED", "QT_DOC_ESP", "QT_DOC_ESP_CC", "QT_DOC_FUND",
    "QT_DOC_FUND_AF", "QT_DOC_FUND_AI", "QT_DOC_INF", "QT_DOC_INF_CRE", "QT_DOC_INF_PRE", "QT_DOC_MED",
    "QT_DOC_PROF", "QT_DOC_PROF_TEC", "QT_EQUIP_DVD", "QT_EQUIP_MULTIMIDIA", "QT_EQUIP_SOM", "QT_EQUIP_TV",
    "QT_MAT_BAS", "QT_MAT_BAS_0_3", "QT_MAT_BAS_11_14", "QT_MAT_BAS_15_17", "QT_MAT_BAS_18_MAIS",
    "QT_MAT_BAS_4_5", "QT_MAT_BAS_6_10", "QT_MAT_BAS_AMARELA", "QT_MAT_BAS_BRANCA", "QT_MAT_BAS_D",
    "QT_MAT_BAS_FEM", "QT_MAT_BAS_INDIGENA", "QT_MAT_BAS_MASC", "QT_MAT_BAS_N", "QT_MAT_BAS_ND",
    "QT_MAT_BAS_PARDA", "QT_MAT_BAS_PRETA", "QT_MAT_EJA", "QT_MAT_EJA_FUND", "QT_MAT_EJA_MED", "QT_MAT_ESP",
    "QT_MAT_ESP_CC", "QT_MAT_FUND", "QT_MAT_FUND_AF", "QT_MAT_FUND_AF_INT", "QT_MAT_FUND_AI",
    "QT_MAT_FUND_AI_INT", "QT_MAT_FUND_INT", "QT_MAT_INF", "QT_MAT_INF_CRE", "QT_MAT_INF_CRE_INT",
    "QT_MAT_INF_INT", "QT_MAT_INF_PRE", "QT_MAT_MED", "QT_MAT_MED_INT", "QT_MAT_PROF", "QT_MAT_PROF_TEC",
    "QT_SALAS_UTILIZADAS", "QT_TUR_BAS", "QT_TUR_EJA", "QT_TUR_EJA_FUND", "QT_TUR_EJA_MED", "QT_TUR_ESP",
    "QT_TUR_ESP_CC", "QT_TUR_FUND", "QT_TUR_FUND_AF", "QT_TUR_FUND_AI", "QT_TUR_INF", "QT_TUR_INF_CRE",
    "QT_TUR_INF_PRE", "QT_TUR_MED", "QT_TUR_PROF", "QT_TUR_PROF_TEC",
]

# E.2, regra 3: as 22 colunas-fonte dos 18 itens de infraestrutura (já entram pelas dimensões)
USADAS_INFRA = [
    "IN_AGUA_POTAVEL", "IN_AGUA_FILTRADA", "IN_ENERGIA_REDE_PUBLICA", "IN_LIXO_SERVICO_COLETA",
    "IN_BANHEIRO", "IN_BANHEIRO_DENTRO_PREDIO", "IN_DESPENSA", "IN_REFEITORIO", "IN_SALA_DIRETORIA",
    "IN_SALA_PROFESSOR", "IN_SECRETARIA", "IN_BIBLIOTECA", "IN_BIBLIOTECA_SALA_LEITURA",
    "IN_LABORATORIO_INFORMATICA", "IN_PATIO_COBERTO", "IN_PATIO_DESCOBERTO", "IN_QUADRA_ESPORTES",
    "IN_COMPUTADOR", "IN_EQUIP_IMPRESSORA", "IN_EQUIP_MULTIMIDIA", "IN_EQUIP_RETROPROJETOR", "IN_INTERNET",
]

# E.2: as seis faixas de idade, parcialmente mecânicas (regra 6); a robustez S2r roda sem elas
FAIXAS_IDADE = ["QT_MAT_BAS_0_3", "QT_MAT_BAS_4_5", "QT_MAT_BAS_6_10", "QT_MAT_BAS_11_14",
                "QT_MAT_BAS_15_17", "QT_MAT_BAS_18_MAIS"]

# E.2: os blocos, definidos pelo nome; servem só para a importância por permutação (E.6)
BLOCOS = {
    "predio_servicos": [
        "IN_AGUA_CACIMBA", "IN_AGUA_FONTE_RIO", "IN_AGUA_INEXISTENTE", "IN_AGUA_POCO_ARTESIANO",
        "IN_AGUA_REDE_PUBLICA", "IN_ALMOXARIFADO", "IN_AREA_VERDE", "IN_AUDITORIO", "IN_BANHEIRO_CHUVEIRO",
        "IN_BANHEIRO_EI", "IN_BANHEIRO_PNE", "IN_COZINHA", "IN_DEPENDENCIAS_OUTRAS", "IN_ENERGIA_INEXISTENTE",
        "IN_ESGOTO_FOSSA", "IN_ESGOTO_INEXISTENTE", "IN_ESGOTO_REDE_PUBLICA", "IN_LABORATORIO_CIENCIAS",
        "IN_LIXO_ENTERRA", "IN_LIXO_QUEIMA", "IN_LOCAL_FUNC_GALPAO", "IN_LOCAL_FUNC_OUTROS",
        "IN_LOCAL_FUNC_PREDIO_ESCOLAR", "IN_LOCAL_FUNC_SALAS_OUTRA_ESC", "IN_PARQUE_INFANTIL",
        "IN_QUADRA_ESPORTES_COBERTA", "IN_QUADRA_ESPORTES_DESCOBERTA", "IN_SALA_ATENDIMENTO_ESPECIAL",
        "IN_SALA_LEITURA"],
    "oferta_turno": [
        "IN_DIURNO", "IN_EJA", "IN_EJA_FUND", "IN_EJA_MED", "IN_ESP", "IN_ESP_CC", "IN_FUND", "IN_FUND_AF",
        "IN_FUND_AI", "IN_INF", "IN_INF_CRE", "IN_INF_PRE", "IN_MED", "IN_NOTURNO", "IN_PROF", "IN_PROF_TEC"],
    "escola_indigena": ["IN_EDUCACAO_INDIGENA"],
    "equipamentos": [
        "IN_EQUIP_COPIADORA", "IN_EQUIP_DVD", "IN_EQUIP_IMPRESSORA_MULT", "IN_EQUIP_PARABOLICA", "IN_EQUIP_SOM",
        "IN_EQUIP_TV", "QT_EQUIP_DVD", "QT_EQUIP_MULTIMIDIA", "QT_EQUIP_SOM", "QT_EQUIP_TV"],
    "docentes": [
        "QT_DOC_BAS", "QT_DOC_EJA", "QT_DOC_EJA_FUND", "QT_DOC_EJA_MED", "QT_DOC_ESP", "QT_DOC_ESP_CC",
        "QT_DOC_FUND", "QT_DOC_FUND_AF", "QT_DOC_FUND_AI", "QT_DOC_INF", "QT_DOC_INF_CRE", "QT_DOC_INF_PRE",
        "QT_DOC_MED", "QT_DOC_PROF", "QT_DOC_PROF_TEC"],
    "matriculas": [
        "QT_MAT_BAS", "QT_MAT_BAS_0_3", "QT_MAT_BAS_11_14", "QT_MAT_BAS_15_17", "QT_MAT_BAS_18_MAIS",
        "QT_MAT_BAS_4_5", "QT_MAT_BAS_6_10", "QT_MAT_BAS_AMARELA", "QT_MAT_BAS_BRANCA", "QT_MAT_BAS_D",
        "QT_MAT_BAS_FEM", "QT_MAT_BAS_INDIGENA", "QT_MAT_BAS_MASC", "QT_MAT_BAS_N", "QT_MAT_BAS_ND",
        "QT_MAT_BAS_PARDA", "QT_MAT_BAS_PRETA", "QT_MAT_EJA", "QT_MAT_EJA_FUND", "QT_MAT_EJA_MED", "QT_MAT_ESP",
        "QT_MAT_ESP_CC", "QT_MAT_FUND", "QT_MAT_FUND_AF", "QT_MAT_FUND_AF_INT", "QT_MAT_FUND_AI",
        "QT_MAT_FUND_AI_INT", "QT_MAT_FUND_INT", "QT_MAT_INF", "QT_MAT_INF_CRE", "QT_MAT_INF_CRE_INT",
        "QT_MAT_INF_INT", "QT_MAT_INF_PRE", "QT_MAT_MED", "QT_MAT_MED_INT", "QT_MAT_PROF", "QT_MAT_PROF_TEC"],
    "turmas_salas": [
        "QT_SALAS_UTILIZADAS", "QT_TUR_BAS", "QT_TUR_EJA", "QT_TUR_EJA_FUND", "QT_TUR_EJA_MED", "QT_TUR_ESP",
        "QT_TUR_ESP_CC", "QT_TUR_FUND", "QT_TUR_FUND_AF", "QT_TUR_FUND_AI", "QT_TUR_INF", "QT_TUR_INF_CRE",
        "QT_TUR_INF_PRE", "QT_TUR_MED", "QT_TUR_PROF", "QT_TUR_PROF_TEC"],
}

# E.2: valores do filtro, fixados pelo Gustavo antes de qualquer modelo
PREFIXOS = ("QT_", "IN_")                                                     # regra 1
PROIBIDO = re.compile(r"abandono|aprovacao|reprovacao|alto_risco|variacao|tx_rend|base_atual", re.I)  # regra 2
MIN_PREENCH = 95.0                                                            # regra 4, % em cada ano
MAX_DOMINANTE = 99.0                                                          # regra 6, % dos não ausentes
SITUACAO_EM_FUNCIONAMENTO = 1                                                 # universo do filtro
DEPENDENCIAS_PUBLICAS = (1, 2, 3)                                             # federal, estadual, municipal


def _numero(serie):
    """E.2: texto → número; '--', vazio e qualquer não numérico viram ausente (nunca 0, regra 8)."""
    return pd.to_numeric(serie, errors="coerce")


def _co(serie):
    """CO_ENTIDADE como texto, sem espaços e sem '.0' (regra 9)."""
    return serie.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).astype("string")


def _juntar(series):
    """Os valores não ausentes de várias séries (vazio se a coluna não existe em nenhum dos anos)."""
    return pd.concat(series, ignore_index=True).dropna() if series else pd.Series(dtype="float64")


def _colunas_do_ano(ano, cache):
    import pyarrow.parquet as pq
    return pq.read_schema(cache / f"{ano}_escola.parquet").names


def _universo_do_ano(ano, colunas, cache):
    """E.2: escolas públicas em funcionamento do ano; só as colunas pedidas, em número."""
    chave = ["TP_SITUACAO_FUNCIONAMENTO", "TP_DEPENDENCIA"]
    t = pd.read_parquet(cache / f"{ano}_escola.parquet", columns=chave + colunas)
    ok = (_numero(t["TP_SITUACAO_FUNCIONAMENTO"]) == SITUACAO_EM_FUNCIONAMENTO) & \
        _numero(t["TP_DEPENDENCIA"]).isin(DEPENDENCIAS_PUBLICAS)
    return t.loc[ok, colunas].apply(_numero)


def filtro_mecanico(cache=CACHE, anos_preench=range(2013, 2025), anos_info=range(2013, 2019),
                    anos_fonte=ANOS_EXTRAIR):
    """E.2: as seis regras, na ordem; uma linha por coluna da tabela escola (união dos anos da fonte).

    Devolve DataFrame (coluna, motivo, preench_min, valor_dominante_pct); motivo = 'PASSA' para as que passam.
    preench_min é o menor % de não ausentes nos anos de anos_preench (0 se a coluna não existe num deles);
    valor_dominante_pct é o % do valor mais frequente nos não ausentes de anos_info. Só olha preditores."""
    cache = Path(cache)
    por_ano = {a: _colunas_do_ano(a, cache) for a in anos_fonte}
    todas = sorted({c for cols in por_ano.values() for c in cols})
    candidatas = [c for c in todas if c.startswith(PREFIXOS) and not PROIBIDO.search(c)
                  and c not in USADAS_INFRA]
    # valores das candidatas nos anos que o filtro olha (preenchimento, escala, informação)
    anos_olhados = sorted(set(anos_preench) | set(anos_info))
    dados = {a: _universo_do_ano(a, [c for c in candidatas if c in por_ano[a]], cache) for a in anos_olhados}

    linhas = []
    for c in todas:
        lin = {"coluna": c, "motivo": None, "preench_min": np.nan, "valor_dominante_pct": np.nan}
        if not c.startswith(PREFIXOS):
            lin["motivo"] = "tipo"
        elif PROIBIDO.search(c):
            lin["motivo"] = "proibida"
        elif c in USADAS_INFRA:
            lin["motivo"] = "ja_usada"
        if lin["motivo"]:
            linhas.append(lin)
            continue
        pct = []
        for a in anos_preench:
            d = dados[a]
            pct.append(100.0 * d[c].notna().mean() if c in d and len(d) else 0.0)
        lin["preench_min"] = round(min(pct), 4)
        info = _juntar([dados[a][c] for a in anos_info if c in dados[a]])
        if len(info):
            lin["valor_dominante_pct"] = round(100.0 * info.value_counts().iloc[0] / len(info), 4)
        valores = _juntar([dados[a][c] for a in anos_preench if c in dados[a]])
        if min(pct) < MIN_PREENCH:
            lin["motivo"] = "preenchimento"
        elif ((valores < 0) | (valores != np.floor(valores))).any() or \
                (c.startswith("IN_") and not valores.isin([0, 1]).all()):
            lin["motivo"] = "escala"
        elif not len(info) or lin["valor_dominante_pct"] > MAX_DOMINANTE:
            lin["motivo"] = "informacao"
        else:
            lin["motivo"] = "PASSA"
        linhas.append(lin)
    return pd.DataFrame(linhas, columns=["coluna", "motivo", "preench_min", "valor_dominante_pct"])


def extrair(relatorios=None, cache=CACHE, anos=ANOS_EXTRAIR):
    """Contrato do grupo: ["ANO", "CO_ENTIDADE", *COLUNAS], uma linha por escola e ano, de todas as escolas do
    cache de 2007 a 2024. Coluna fora do layout de um ano fica ausente (Float64 <NA>), nunca 0."""
    cache = Path(cache)
    partes = []
    for ano in anos:
        if ano >= 2025:
            raise ValueError("o estudo E não lê 2025 (o teste limpo fica fechado)")
        presentes = [c for c in COLUNAS if c in _colunas_do_ano(ano, cache)]
        t = pd.read_parquet(cache / f"{ano}_escola.parquet", columns=["CO_ENTIDADE", *presentes])
        out = pd.DataFrame({"ANO": pd.Series(ano, index=t.index, dtype="Int16"), "CO_ENTIDADE": _co(t["CO_ENTIDADE"])})
        num = pd.DataFrame({c: (_numero(t[c]) if c in presentes else pd.Series(np.nan, index=t.index))
                            for c in COLUNAS}, index=t.index).astype("Float64")
        partes.append(pd.concat([out, num], axis=1))
    tab = pd.concat(partes, ignore_index=True)
    if tab.duplicated(["ANO", "CO_ENTIDADE"]).any():
        raise ValueError(f"{NOME}: (ANO, CO_ENTIDADE) repetido no cache")
    return tab[["ANO", "CO_ENTIDADE", *COLUNAS]]
