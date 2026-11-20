# -*- coding: utf-8 -*-
"""
Código comum dos 7 grupos do Censo (censo_matriculas, censo_docentes, censo_turmas_salas, censo_equipamentos,
censo_oferta_turno, censo_escola_indigena, censo_predio_servicos). NÃO é grupo: não tem NOME nem vai no
ligados.txt (o nome começa com "_").

Origem das colunas: a lista fechada do estudo E (censo_bruto_v0.COLUNAS), dividida pelos blocos de
censo_bruto_v0.BLOCOS (docs/DECISOES.md, 2026-11-20, "Grupos do Censo ligados"). O censo_bruto_v0.py não muda.

EXTRAIR (linha a linha, só do cache completo do Censo, dados/cache/censo_completo/)
-------------------------------------------------------------------------------------
- Anos 2007 a 2025, todas as escolas do cache (quem filtra anos e universo é quem usa a base).
- 2007–2024: lê {ano}_escola.parquet. 2025: a tabela escola foi dividida no cache em escola, docente, matricula
  e turma; cada coluna é pega na tabela em que existe COM O MESMO NOME, e as tabelas são juntadas 1:1 por
  CO_ENTIDADE (how="left" a partir da escola, validate="1:1"). Nenhuma equivalência é inventada (regra 11):
  coluna que não existe com o mesmo nome em 2025 fica ausente em 2025 e entra em grupos_censo_2025.txt.
- Conversão: pd.to_numeric(errors="coerce"); '--', vazio e não numérico viram ausente, nunca 0 (regra 8).
- Regra "coletada" (grupos/README.md, regra 4), pelo arquivo nacional da tabela de onde a coluna vem:
  IN_ foi coletada no ano se alguma escola do Brasil tem 1 (n_um > 0); QT_ se alguma tem valor > 0
  (n_positivo > 0). Não coletada → a coluna inteira fica ausente naquele ano (como no infraestrutura.py).
  A matriz coluna × ano fica em grupos_censo_coleta.csv.

RELATÓRIOS (saida/relatorios/; só descrevem, não bloqueiam)
- grupos_censo_2025.txt: as tabelas de 2025 usadas e as colunas sem o mesmo nome em 2025;
- grupos_censo_coleta.csv: coluna × ano → tabela de origem e status (coletada, nao_coletada, fora_do_layout);
- grupos_censo_continuidade.csv: mediana e % preenchido em 2023, 2024 e 2025, nas escolas públicas em
  funcionamento, com a variação da mediana e a marca de variação acima de 50%.

Tipos (regra 9): ANO Int16, CO_ENTIDADE string (sem '.0'), as colunas Float64 nullable.
"""
import functools
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
CACHE = RAIZ / "dados" / "cache" / "censo_completo"

ANOS = range(2007, 2026)
ANO_DIVIDIDO = 2025
TABELAS_2025 = ("escola", "docente", "matricula", "turma")   # a escola é a base da junção
ANOS_CONTINUIDADE = (2023, 2024, 2025)
LIMIAR_VARIACAO = 50.0                                        # % de variação da mediana que recebe marca
SITUACAO_EM_FUNCIONAMENTO = 1
DEPENDENCIAS_PUBLICAS = (1, 2, 3)


def _carregar_bruto_v0():
    import importlib.util
    spec = importlib.util.spec_from_file_location("grupos_censo_bruto_v0_ref",
                                                  Path(__file__).with_name("censo_bruto_v0.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_V0 = _carregar_bruto_v0()
TODAS = list(_V0.COLUNAS)                       # as 124, em ordem alfabética
BLOCOS = {b: list(c) for b, c in _V0.BLOCOS.items()}


def colunas_do_bloco(bloco):
    """As colunas do bloco, na ordem alfabética da lista fechada."""
    return [c for c in TODAS if c in set(BLOCOS[bloco])]


def _numero(serie):
    return pd.to_numeric(serie, errors="coerce")


def _co(serie):
    return serie.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).astype("string")


def coletada(coluna, nac):
    """Regra 4 do README: IN_ com alguma escola do Brasil igual a 1; QT_ com alguma maior que 0."""
    if coluna not in nac.index:
        return False
    if coluna.startswith("IN_"):
        return int(nac.loc[coluna, "n_um"]) > 0
    if coluna.startswith("QT_"):
        return int(nac.loc[coluna, "n_positivo"]) > 0
    raise ValueError(f"{coluna}: prefixo sem regra de coletada")


def _schema(caminho):
    import pyarrow.parquet as pq
    return pq.read_schema(caminho).names


def _tabelas_do_ano(ano, cache):
    """{tabela: (caminho, nacional)} das tabelas de onde o ano é lido."""
    nomes = TABELAS_2025 if ano == ANO_DIVIDIDO else ("escola",)
    return {t: (cache / f"{ano}_{t}.parquet", cache / f"{ano}_{t}_nacional.csv") for t in nomes}


def _ler_ano(ano, colunas, cache):
    """(tabela do ano com CO_ENTIDADE, TP_SITUACAO_FUNCIONAMENTO, TP_DEPENDENCIA e colunas em número,
    lista de registros de coleta)."""
    tabelas = _tabelas_do_ano(ano, cache)
    origem, registros = {}, []
    schemas = {t: _schema(p) for t, (p, _) in tabelas.items()}
    for c in colunas:
        achadas = [t for t in tabelas if c in schemas[t]]
        if len(achadas) > 1:
            raise ValueError(f"{ano}: {c} aparece em mais de uma tabela ({achadas})")
        if achadas:
            origem[c] = achadas[0]
    nacs = {t: pd.read_csv(n).set_index("coluna") for t, (_, n) in tabelas.items()}
    chave = ["CO_ENTIDADE", "TP_SITUACAO_FUNCIONAMENTO", "TP_DEPENDENCIA"]
    base = pd.read_parquet(tabelas["escola"][0], columns=chave + [c for c, t in origem.items() if t == "escola"])
    base["CO_ENTIDADE"] = _co(base["CO_ENTIDADE"])
    for t in tabelas:
        if t == "escola":
            continue
        cols = [c for c, tt in origem.items() if tt == t]
        if not cols:
            continue
        outra = pd.read_parquet(tabelas[t][0], columns=["CO_ENTIDADE", *cols])
        outra["CO_ENTIDADE"] = _co(outra["CO_ENTIDADE"])
        base = base.merge(outra, on="CO_ENTIDADE", how="left", validate="1:1")
    out = pd.DataFrame({"ANO": pd.Series(ano, index=base.index, dtype="Int16"),
                        "CO_ENTIDADE": base["CO_ENTIDADE"],
                        "_SITUACAO": _numero(base["TP_SITUACAO_FUNCIONAMENTO"]),
                        "_DEPENDENCIA": _numero(base["TP_DEPENDENCIA"])})
    valores = {}
    for c in colunas:
        t = origem.get(c)
        if t is None:
            status = "fora_do_layout"
        elif coletada(c, nacs[t]):
            status = "coletada"
        else:
            status = "nao_coletada"
        registros.append({"ano": ano, "coluna": c, "tabela": t or "", "status": status})
        valores[c] = _numero(base[c]) if status == "coletada" else pd.Series(np.nan, index=base.index)
    out = pd.concat([out, pd.DataFrame(valores, index=base.index).astype("Float64")], axis=1)
    if out["CO_ENTIDADE"].duplicated().any():
        raise ValueError(f"{ano}: CO_ENTIDADE repetido")
    return out, registros


@functools.lru_cache(maxsize=4)
def _tudo(cache, anos):
    """As 124 colunas de todos os anos, lidas uma vez por processo (os 7 grupos dividem a leitura)."""
    partes, registros = [], []
    for ano in anos:
        tab, reg = _ler_ano(ano, TODAS, Path(cache))
        partes.append(tab)
        registros += reg
    return pd.concat(partes, ignore_index=True), pd.DataFrame(registros)


def tabela(colunas, cache=CACHE, anos=ANOS):
    """["ANO", "CO_ENTIDADE", *colunas] de todas as escolas do cache, nos anos pedidos."""
    tab, _ = _tudo(str(cache), tuple(anos))
    return tab[["ANO", "CO_ENTIDADE", *colunas]].copy()


def continuidade(cache=CACHE, anos=ANOS):
    """Mediana e % preenchido por coluna em 2023, 2024 e 2025, nas escolas públicas em funcionamento."""
    tab, reg = _tudo(str(cache), tuple(anos))
    univ = tab[(tab["_SITUACAO"] == SITUACAO_EM_FUNCIONAMENTO) & tab["_DEPENDENCIA"].isin(DEPENDENCIAS_PUBLICAS)]
    bloco_de = {c: b for b, cols in BLOCOS.items() for c in cols}
    linhas = []
    for c in TODAS:
        lin = {"coluna": c, "bloco": bloco_de[c]}
        for a in ANOS_CONTINUIDADE:
            sub = univ.loc[univ["ANO"] == a, c]
            lin[f"n_{a}"] = int(len(sub))
            lin[f"pct_preenchido_{a}"] = round(100.0 * sub.notna().mean(), 2) if len(sub) else np.nan
            lin[f"mediana_{a}"] = float(sub.median()) if sub.notna().any() else np.nan
        for a0, a1 in zip(ANOS_CONTINUIDADE[:-1], ANOS_CONTINUIDADE[1:]):
            m0, m1 = lin[f"mediana_{a0}"], lin[f"mediana_{a1}"]
            if np.isnan(m0) or np.isnan(m1):
                var = np.nan
            elif m0 == 0:
                var = 0.0 if m1 == 0 else np.inf
            else:
                var = round(100.0 * (m1 - m0) / abs(m0), 2)
            lin[f"variacao_mediana_pct_{a0}_{a1}"] = var
            lin[f"marca_{a0}_{a1}"] = ("SEM_DADO" if np.isnan(var)
                                       else ("VARIOU>50%" if abs(var) > LIMIAR_VARIACAO else ""))
        linhas.append(lin)
    return pd.DataFrame(linhas)


def relatorio_2025(cache=CACHE, anos=ANOS):
    _, reg = _tudo(str(cache), tuple(anos))
    r = reg[reg["ano"] == ANO_DIVIDIDO]
    fora = r[r["status"] == "fora_do_layout"]["coluna"].tolist()
    nao = r[r["status"] == "nao_coletada"]["coluna"].tolist()
    L = ["GRUPOS DO CENSO — 2025 (tabela escola dividida no cache)", "=" * 70,
         f"Tabelas juntadas 1:1 por CO_ENTIDADE (how='left' a partir da escola): {', '.join(TABELAS_2025)}",
         "Cada coluna vem da tabela em que existe com o mesmo nome; nenhuma equivalência foi criada.", "",
         "Colunas por tabela de origem em 2025:"]
    for t in TABELAS_2025:
        L.append(f"  {t}: {int((r['tabela'] == t).sum())}")
    L += ["", f"Colunas SEM o mesmo nome em nenhuma tabela de 2025 (ficam ausentes em 2025): {len(fora)}"]
    L += [f"  - {c}" for c in fora]
    L += ["", f"Colunas presentes em 2025 mas não coletadas no Brasil (ausentes em 2025): {len(nao)}"]
    L += [f"  - {c}" for c in nao]
    return L


def gravar_relatorios(relatorios, cache=CACHE, anos=ANOS):
    """Os três relatórios dos grupos do Censo (cobrem as 124 colunas; iguais em qualquer grupo que os grave)."""
    if relatorios is None:
        return
    relatorios = Path(relatorios)
    relatorios.mkdir(parents=True, exist_ok=True)
    _, reg = _tudo(str(cache), tuple(anos))
    reg.to_csv(relatorios / "grupos_censo_coleta.csv", index=False, encoding="utf-8", lineterminator="\n")
    if ANO_DIVIDIDO in anos:
        (relatorios / "grupos_censo_2025.txt").write_text("\n".join(relatorio_2025(cache, anos)) + "\n",
                                                          encoding="utf-8")
    if set(ANOS_CONTINUIDADE) <= set(anos):
        continuidade(cache, anos).to_csv(relatorios / "grupos_censo_continuidade.csv", index=False,
                                         encoding="utf-8", lineterminator="\n")


def extrair_bloco(colunas, relatorios=None, cache=CACHE, anos=ANOS):
    """O extrair() de cada grupo: grava os relatórios e devolve ["ANO", "CO_ENTIDADE", *colunas]."""
    gravar_relatorios(relatorios, cache, anos)
    return tabela(colunas, cache, anos)
