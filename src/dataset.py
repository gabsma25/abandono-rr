"""
Gera dataset/escolas_rr_v<versão>.csv (versão em src/versao.py) e dataset/DICIONARIO.md a partir de saida/base_atual.parquet.

Uma linha por escola × ano (t) × etapa (AF = anos finais do fundamental, EM = ensino médio), de 2007 a
2025, no estilo de um dataset tabular comum: identificação, alvos em colunas próprias e variáveis
explicativas separadas. Entra a escola-ano que tem a taxa de abandono da etapa em t ou em t+1.

Alvos (ano t+1):
  abandono_t1     taxa de abandono da etapa no ano seguinte
  alto_risco_t1   1 se abandono_t1 está entre os 20% maiores da etapa no ano e é maior que zero;
                  a mesma regra da classificação de 2026-11-10 (classificacao.rotular), aplicada ao
                  mesmo universo: escolas públicas com a taxa da etapa em t−1, t e t+1. Fora dele, vazio.

Nenhum número é digitado: os anos disponíveis do dicionário são contados aqui.
Uso: python -m src.dataset
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src" / "avaliacao"))
import classificacao as C

sys.path.insert(0, str(RAIZ))
from src.versao import VERSAO

P_BASE = RAIZ / "saida" / "base_atual.parquet"
DESTINO = RAIZ / "dataset" / f"escolas_rr_v{VERSAO}.csv"
DICIONARIO = RAIZ / "dataset" / "DICIONARIO.md"
JANELA = range(2013, 2019)                       # t da janela segura
SUF = {"AF": "FUN_AF", "EM": "MED"}
CHAVE = ["ANO", "CO_ENTIDADE"]
F_RENDIMENTO = "INEP, Indicadores Educacionais: taxas de rendimento por escola (tx_rend)"
F_CENSO = "INEP, Censo Escolar (tabela de escolas)"
F_PROJETO = "calculada pelo projeto (src/estendida/05_indices_infra.py)"

ITENS = ["IIB_agua_potavel", "IIB_energia_rede", "IIB_coleta_lixo", "IIB_banheiro", "IDA_despensa",
         "IDA_refeitorio", "IDA_sala_diretoria", "IDA_sala_professor", "IDA_secretaria", "IDP_biblioteca",
         "IDP_lab_informatica", "IDP_patio_coberto", "IDP_patio_descoberto", "IDP_quadra_esportes",
         "IEP_computador", "IEP_impressora", "IEP_projetor", "IEP_internet"]
DESC_ITEM = {"IIB": "infraestrutura básica", "IDA": "dependência administrativa",
             "IDP": "dependência pedagógica", "IEP": "equipamento pedagógico"}

# (coluna, papel, significado, unidade, fonte)
COLUNAS = [
    ("co_entidade", "identificação", "código INEP da escola (id)", "código", F_CENSO),
    ("ano", "identificação", "ano t das variáveis explicativas", "ano", F_RENDIMENTO),
    ("ano_alvo", "identificação", "ano t+1 dos alvos", "ano", F_RENDIMENTO),
    ("etapa", "identificação", "AF = anos finais do ensino fundamental; EM = ensino médio", "categoria", "projeto"),
    ("co_municipio", "identificação", "código IBGE do município", "código", F_RENDIMENTO),
    ("no_municipio", "identificação", "nome do município", "texto", F_RENDIMENTO),
    ("janela_segura", "identificação", "1 se t está na janela segura (2013 a 2018); ver as faixas abaixo", "0/1", "projeto"),
    ("abandono_t1", "alvo", "taxa de abandono da etapa no ano t+1", "% (0 a 100)", F_RENDIMENTO),
    ("alto_risco_t1", "alvo", "1 se abandono_t1 está entre os 20% maiores da etapa no ano e é maior que zero (definição completa abaixo)", "0/1", "projeto"),
    ("localizacao", "explicativa", "localização da escola (Urbana, Rural)", "categoria", F_RENDIMENTO),
    ("dependencia", "explicativa", "rede (Estadual, Municipal, Federal, Privada)", "categoria", F_RENDIMENTO),
    ("rede_publica", "explicativa", "1 se a escola é pública (estadual, municipal ou federal)", "0/1", F_RENDIMENTO),
    ("aprovacao_t", "explicativa", "taxa de aprovação da etapa em t", "% (0 a 100)", F_RENDIMENTO),
    ("reprovacao_t", "explicativa", "taxa de reprovação da etapa em t", "% (0 a 100)", F_RENDIMENTO),
    ("abandono_t", "explicativa", "taxa de abandono da etapa em t", "% (0 a 100)", F_RENDIMENTO),
    ("abandono_tm1", "explicativa", "taxa de abandono da etapa em t−1 (a régua B1R_lag)", "% (0 a 100)", F_RENDIMENTO),
    ("reprovacao_tm1", "explicativa", "taxa de reprovação da etapa em t−1", "% (0 a 100)", F_RENDIMENTO),
    ("abandono_tm2", "explicativa", "taxa de abandono da etapa em t−2", "% (0 a 100)", F_RENDIMENTO),
    ("variacao_abandono_defasada", "explicativa", "abandono_tm1 − abandono_tm2", "pontos percentuais", "projeto"),
] + [(i.lower(), "explicativa", f"{DESC_ITEM[i[:3]]}: {i[4:].replace('_', ' ')} (1 = tem)", "0/1", F_CENSO) for i in ITENS] + [
    ("dim_iib_zano", "explicativa", "dimensão de infraestrutura básica, padronizada dentro do ano", "desvios-padrão", F_PROJETO),
    ("dim_ida_zano", "explicativa", "dimensão de dependências administrativas, padronizada dentro do ano", "desvios-padrão", F_PROJETO),
    ("dim_idp_zano", "explicativa", "dimensão de dependências pedagógicas, padronizada dentro do ano", "desvios-padrão", F_PROJETO),
    ("dim_iep_zano", "explicativa", "dimensão de equipamentos pedagógicos, padronizada dentro do ano", "desvios-padrão", F_PROJETO),
    ("iie_zano", "explicativa", "índice de infraestrutura escolar (1ª componente principal das 4 dimensões, por ano)", "desvios-padrão", F_PROJETO),
    ("infra_itens_completos", "explicativa", "1 se os 18 itens de infraestrutura estão preenchidos no ano", "0/1", F_PROJETO),
    ("infra_fonte_artigo", "explicativa", "1 se todos os itens vieram das colunas do artigo de referência (Almeida & Mussato, 2023)", "0/1", F_PROJETO),
]

FAIXAS = [
    ("2007–2010", "fora", "o ensino fundamental passava de 8 para 9 anos (Lei 11.274/2006); as etapas não se comparam com as dos anos seguintes"),
    ("2011–2012", "fora", "só entram como anos anteriores (t−1 e t−2) das primeiras transições da janela"),
    ("2013–2018", "**janela segura**", "um único formato de dados e antes da pandemia; desfechos de 2014 a 2019"),
    ("2019", "fora", "o desfecho seria 2020, ano da pandemia"),
    ("2020–2021", "fora", "pandemia: com as escolas fechadas, o abandono registrado despencou (ver saida/relatorios/desfecho_por_ano.csv)"),
    ("2022–2023", "fora", "regime pós-pandemia; foram os anos de teste da Etapa 2 do projeto anterior"),
    ("2024–2025", "fora", "começa o Pé-de-Meia no ensino médio; o desfecho de 2025 já foi usado em análises e testes de modelos"),
]


def _taxas(base, s):
    """Rendimento da etapa em t, t−1 e t−2, pela chave ANO + CO_ENTIDADE (mesma lógica de classificacao.montar)."""
    t = base[CHAVE + [f"APROVACAO_{s}", f"REPROVACAO_{s}", f"ABANDONO_{s}", f"ABANDONO_{s}_T1"]].rename(columns={
        f"APROVACAO_{s}": "aprovacao_t", f"REPROVACAO_{s}": "reprovacao_t", f"ABANDONO_{s}": "abandono_t",
        f"ABANDONO_{s}_T1": "abandono_t1"})
    for lag, tag in ((1, "tm1"), (2, "tm2")):
        r = base[CHAVE + [f"ABANDONO_{s}", f"REPROVACAO_{s}"]].copy()
        r["ANO"] = r["ANO"] + lag
        r = r.rename(columns={f"ABANDONO_{s}": f"abandono_{tag}", f"REPROVACAO_{s}": f"reprovacao_{tag}"})
        t = t.merge(r, on=CHAVE, how="left", validate="1:1")
    return t.drop(columns="reprovacao_tm2")


def montar(base):
    partes = []
    for etapa, s in SUF.items():
        d = base[CHAVE + ["ANO_ALVO", "CO_MUNICIPIO", "NO_MUNICIPIO", "LOCALIZACAO", "DEPENDENCIA", "REDE_PUBLICA"]
                 + ITENS + ["DIM_IIB_zano", "DIM_IDA_zano", "DIM_IDP_zano", "DIM_IEP_zano", "IIE_zano",
                            "INFRA_ITENS_COMPLETOS", "INFRA_FONTE_ARTIGO"]]
        d = d.merge(_taxas(base, s), on=CHAVE, how="left", validate="1:1")
        d = d[d["abandono_t"].notna() | d["abandono_t1"].notna()].copy()
        d.columns = [c.lower() for c in d.columns]
        d.insert(3, "etapa", etapa)
        for c in [c for c in d.columns if c.startswith(("abandono_", "aprovacao_", "reprovacao_"))]:
            d[c] = d[c].astype("Float64")
        d["variacao_abandono_defasada"] = d["abandono_tm1"] - d["abandono_tm2"]
        univ = ((d["rede_publica"] == 1) & d["abandono_t1"].notna() & d["abandono_t"].notna()
                & d["abandono_tm1"].notna()).fillna(False).astype(bool)
        d["alto_risco_t1"] = pd.array([pd.NA] * len(d), dtype="Int8")
        for _, g in d[univ].groupby("ano_alvo"):
            d.loc[g.index, "alto_risco_t1"] = C.rotular(g["abandono_t1"].to_numpy(dtype="float64"))
        d["janela_segura"] = d["ano"].isin(JANELA).astype("Int8")
        partes.append(d)
    out = pd.concat(partes, ignore_index=True)
    out = out[[c for c, *_ in COLUNAS]].sort_values(["etapa", "ano", "co_entidade"]).reset_index(drop=True)
    assert not out.duplicated(["co_entidade", "ano", "etapa"]).any(), "chave escola × ano × etapa repetida"
    return out


def _br(n):
    """Inteiro com ponto de milhar (7.550)."""
    return f"{int(n):,}".replace(",", ".")


def _anos(serie, anos):
    """Faixas de anos com valor não nulo, ex.: '2007–2018, 2020–2025'."""
    a = sorted(set(anos[serie.notna()].astype(int)))
    if not a:
        return "nenhum"
    faixas, ini, ant = [], a[0], a[0]
    for x in a[1:] + [None]:
        if x is not None and x == ant + 1:
            ant = x
            continue
        faixas.append(f"{ini}–{ant}" if ini != ant else f"{ini}")
        if x is not None:
            ini = ant = x
    return ", ".join(faixas)


def dicionario(d):
    L = [f"# Dicionário de dados — `{DESTINO.name}`", "",
         "Gerado por `python -m src.dataset` a partir de `saida/base_atual.parquet` (não edite à mão).", "",
         (f"**Uma linha por escola × ano (t) × etapa.** {_br(len(d))} linhas e {d.shape[1]} colunas; "
         f"{_br(d['co_entidade'].nunique())} escolas; anos t de {int(d['ano'].min())} a {int(d['ano'].max())}. "
         "Entra a escola-ano que tem a taxa de abandono da etapa em t ou em t+1. "
         "Chave: `co_entidade` + `ano` + `etapa`. O nome da escola não é incluído."), "",
         ("**Papéis.** *Alvo*: o que se quer prever, sempre do ano t+1; nunca entra como variável explicativa. "
         "*Explicativa*: informação disponível sobre a escola até o ano t. *Identificação*: chave e descrição, "
         "não entram em modelo."), "",
         "| Coluna | Papel | Significado | Unidade | Fonte | Anos t com valor |", "|---|---|---|---|---|---|"]
    for c, papel, sig, uni, fonte in COLUNAS:
        L.append(f"| `{c}` | {papel} | {sig} | {uni} | {fonte} | {_anos(d[c], d['ano'])} |")
    n_rot = d.groupby("etapa")["alto_risco_t1"].count()
    L += ["", "## Definição completa de `alto_risco_t1`", "",
          "Para cada etapa e cada ano t+1:", "",
          ("1. **Universo:** escolas públicas (`rede_publica` = 1) com a taxa de abandono da etapa em t−1, t e t+1. "
          "Fora dele, `alto_risco_t1` fica vazio (não é 0)."),
          "2. **K** = arredondamento de 20% do número de escolas do universo naquele ano e etapa.",
          "3. **Limiar** = o K-ésimo maior `abandono_t1` do universo.",
          ("4. `alto_risco_t1` = 1 se `abandono_t1` ≥ limiar **e** `abandono_t1` > 0; senão, 0. Empates no limiar entram "
          "todos, então a proporção de 1 pode passar um pouco de 20%."), "",
          ("É a regra da classificação de alto risco do projeto anterior (função `classificacao.rotular`), aplicada ao "
          "mesmo universo; na janela segura, o teste `testes/test_dataset.py` confere que os rótulos são idênticos. "
          f"Linhas com rótulo: AF {_br(n_rot.get('AF', 0))}, EM {_br(n_rot.get('EM', 0))}."), "",
          "## A janela segura e por que cada faixa de anos fica fora", "",
          "| Anos t | Situação | Motivo |", "|---|---|---|"]
    L += [f"| {a} | {s} | {m} |" for a, s, m in FAIXAS]
    L += ["", "Nenhum ano sai do dataset: `janela_segura` só marca os anos usados nas análises.", "",
          "## Ressalva sobre a procedência", "",
          ("Os dados de 2007 a 2018 vêm do recorte de Roraima em `dados/cache/` (sha256 no `dados/MANIFEST.csv`). "
          "Eles foram conferidos contra a fonte do INEP uma vez, em 14/10/2026, na máquina do Gustavo "
          "(`docs/procedencia/relatorio_04_*.md`, §4), e não podem ser reverificados neste projeto, porque os zips "
          "originais desses anos não estão aqui. Os anos de 2019 a 2025 são conferidos célula a célula contra os "
          "zips originais em `dados/origem/` pelo teste 03 (`testes/03_validar_censo_pos04.py --completo`)."), ""]
    return "\n".join(L)


def para_csv(d):
    """Texto CSV do dataset, como gravado no arquivo (UTF-8, quebra de linha LF)."""
    return d.to_csv(index=False, lineterminator="\n")


def main():
    base = pd.read_parquet(P_BASE)
    d = montar(base)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_bytes(para_csv(d).encode("utf-8"))
    DICIONARIO.write_text(dicionario(d), encoding="utf-8", newline="\n")
    print(f"{_br(len(d))} linhas × {d.shape[1]} colunas → {DESTINO}\n→ {DICIONARIO}")


if __name__ == "__main__":
    main()
