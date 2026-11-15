# -*- coding: utf-8 -*-
"""
Estudo de fatores associados ao nível de abandono — implementação do docs/PROTOCOLO.md, seção C.

RODA UMA VEZ, e só com --executar (CLI no fim). Sem --executar, nada é calculado com o desfecho real.
Cada função leva o número da seção do protocolo no nome ou na docstring; os valores fixados (sementes,
reamostragens, margem, limiares) são os da seção C e são conferidos contra o texto do protocolo por
testes/test_fatores.py. Lê só dataset/escolas_rr_v0.2.0.csv e as funções de src/; escreve só em saida/.

Travas da execução única (regra 10 e C.13):
  - sem --executar, o script imprime o aviso e sai;
  - com --executar, recusa rodar se a pasta saida/ já existir;
  - recusa rodar com a árvore do git suja; toda saída começa com uma linha de comentário com o commit,
    o branch e o sha256 do dataset;
  - ordem: tabela 0 → controle negativo (C.9) → se passar, o resto; se falhar, grava SÓ o 07 e para.
"""
import argparse
import hashlib
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / "src" / "avaliacao").is_dir())
sys.path.insert(0, str(RAIZ / "src" / "avaliacao"))
sys.path.insert(0, str(RAIZ))
import bootstrap as B  # noqa: E402  (p_bootstrap e holm, o padrão do projeto — seção B do protocolo)
from src.dataset import DIM_ITENS, ITENS  # noqa: E402  (itens por dimensão: a mesma fonte do dataset)

from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.linear_model import LinearRegression, Ridge  # noqa: E402
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402
from sklearn.neural_network import MLPRegressor  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402

DATASET = RAIZ / "dataset" / "escolas_rr_v0.2.0.csv"
PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "saida"

# ------------------------------------------------------------------ valores fixados no protocolo (seção C)
DESFECHO = "abandono_t"                       # C.2: o nível, no próprio ano t
ETAPAS = ("AF", "EM")                         # C.2: sempre separadas
JANELA = (2013, 2018)                         # C.2
JANELA_ROBUSTEZ = (2012, 2019)                # C.10
CATEGORICAS = {"localizacao": "Urbana", "dependencia": "Estadual"}   # C.3: fator → referência
DIMENSOES = {f"dim_{d.lower()}_prop": len(itens) for d, itens in DIM_ITENS.items()}  # C.3/C.5: nº de itens
INDICE = "iie_prop"                           # C.4: modelo secundário
PASSO_IIE = 0.25                              # C.6: uma dimensão inteira a mais
CONTROLE = "ano"                              # C.3: controle, não é fator
MIN_CATEGORIA = 30                            # C.3: regra dos 30
N_BOOT = 5000                                 # C.6
SEMENTE = 20261115                            # C.6, C.8, C.9
MAX_INVALIDAS = 0.10                          # C.6: reamostragens inválidas
MARGEM = 1.0                                  # C.6: margem prática, em pp, sobre o efeito que decide
ALFA = 0.05                                   # C.6 (Holm, seção B)
N_DOBRAS = 5                                  # C.7: GroupKFold(n_splits=5)
SEMENTES_MLP = tuple(range(1, 11))            # C.7: 10 sementes
LIMIAR_CONTROLE = 0.02                        # C.9: ΔR² do desfecho embaralhado
N_REPETICOES_PERM = 20                        # C.8: n_repeats
MODELOS_Q1 = ("linear", "ridge", "mlp")       # C.7
GRUPOS_PERMUTACAO = {"territorio": ["localizacao"], "rede": ["dependencia"],
                     "infraestrutura": list(DIMENSOES), "ano": [CONTROLE]}  # C.8


def ler_dataset(caminho=DATASET):
    """Lê o dataset versionado como está (códigos como string, regra 9)."""
    return pd.read_csv(caminho, dtype={"co_entidade": str, "co_municipio": str})


# ------------------------------------------------------------------ C.2 e C.3: universo e lista fechada
def c2_universo(d, etapa, anos=JANELA):
    """C.2: escolas públicas com abandono_t da etapa, t dentro da janela; linha com preditor vazio sai.

    Devolve (universo, nº de linhas retiradas por preditor vazio)."""
    a0, a1 = anos
    u = d[(d["etapa"] == etapa) & (d["rede_publica"] == 1) & d[DESFECHO].notna()
          & (d["ano"] >= a0) & (d["ano"] <= a1)]
    pred = list(CATEGORICAS) + list(DIMENSOES) + [INDICE]
    completos = u[pred].notna().all(axis=1)
    return u[completos].copy(), int((~completos).sum())


def c3_regra_dos_30(u):
    """C.3: categoria de dependencia com menos de MIN_CATEGORIA escolas-ano sai com as suas linhas.

    Regra mecânica, aplicada só pela contagem (nunca pela associação).
    Devolve (universo filtrado, {categoria excluída: contagem})."""
    cont = u["dependencia"].value_counts()
    fora = sorted(c for c in cont.index if cont[c] < MIN_CATEGORIA)
    return u[~u["dependencia"].isin(fora)].copy(), {c: int(cont[c]) for c in fora}


def universo_pronto(d, etapa, anos=JANELA):
    """C.2 + C.3: o universo da regressão da etapa, com os registros da tabela 0."""
    u, vazios = c2_universo(d, etapa, anos)
    u, excluidas = c3_regra_dos_30(u)
    return u, {"linhas_preditor_vazio": vazios, "categorias_excluidas": excluidas}


# ------------------------------------------------------------------ C.4: matriz e modelos da tabela de fatores
def matriz_x(u, modelo="principal", anos=JANELA, com_ano=True):
    """C.4: X do modelo principal (4 dimensões) ou secundário (iie_prop); dummies com as referências do C.3.

    As dummies de ano (referência = primeiro ano da janela) são controle, nunca fator."""
    if modelo not in ("principal", "secundario"):
        raise ValueError(modelo)
    cols = {}
    for var, ref in CATEGORICAS.items():
        for cat in sorted(u[var].unique()):
            if cat != ref:
                cols[f"{var}={cat}"] = (u[var] == cat).astype("float64").to_numpy()
    continuas = list(DIMENSOES) if modelo == "principal" else [INDICE]
    for c in continuas:
        cols[c] = u[c].astype("float64").to_numpy()
    if com_ano:
        for a in range(anos[0] + 1, anos[1] + 1):
            cols[f"ano={a}"] = (u["ano"] == a).astype("float64").to_numpy()
    X = pd.DataFrame(cols, index=u.index)
    y = u[DESFECHO].astype("float64").to_numpy()
    return X, y


def _ols(X, y):
    """Coeficientes do OLS (LinearRegression, C.4); NA para coluna sem variação na amostra."""
    m = LinearRegression().fit(X, y)
    coef = pd.Series(m.coef_, index=X.columns, dtype="float64")
    sem_variacao = X.std(ddof=0) == 0
    coef[sem_variacao] = np.nan
    return coef


def c4_vif(X):
    """C.4: VIF = 1/(1−R²) por regressões auxiliares entre as colunas de X (sem dependência nova).

    Relatado, nunca decide: nenhum VIF exclui variável."""
    M = X.to_numpy(dtype="float64")
    out = {}
    for j, c in enumerate(X.columns):
        y = M[:, j]
        Z = np.column_stack([np.ones(len(M)), np.delete(M, j, axis=1)])
        coef, *_ = np.linalg.lstsq(Z, y, rcond=None)
        res = y - Z @ coef
        sst = float(((y - y.mean()) ** 2).sum())
        r2 = 1.0 - float(res @ res) / sst if sst > 0 else 0.0
        out[c] = float("inf") if r2 >= 1.0 else 1.0 / (1.0 - r2)
    return pd.Series(out, name="vif")


# ------------------------------------------------------------------ C.5: os efeitos relatados
def _fatores_do_modelo(X, modelo):
    """As colunas de X que são fatores (recebem efeito e veredito); as de ano ficam fora (controle)."""
    if modelo == "principal":
        return [c for c in X.columns if not c.startswith("ano=") and c not in (INDICE,)]
    return [INDICE]


def _escala_decide(fator):
    """C.5/C.6: o efeito que decide = coeficiente × esta escala (1 para categoria; 1/nº itens para
    dimensão; PASSO_IIE para o índice)."""
    if fator in DIMENSOES:
        return 1.0 / DIMENSOES[fator]
    if fator == INDICE:
        return PASSO_IIE
    return 1.0


def c5_efeitos(coef, X, modelo):
    """C.5: efeito em pp, efeito que decide, efeito padronizado (só contínuos). Todos os fatores aparecem."""
    linhas = []
    for f in _fatores_do_modelo(X, modelo):
        continuo = f in DIMENSOES or f == INDICE
        linhas.append({
            "modelo": modelo, "fator": f,
            "efeito_pp": coef[f],
            "efeito_decide": coef[f] * _escala_decide(f),
            "efeito_padronizado": coef[f] * float(X[f].std(ddof=1)) if continuo else np.nan,
        })
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ C.6: bootstrap, Holm, margem e vereditos
def c6_veredito(p_holm, efeito_decide, lo_decide, hi_decide, fracao_invalida):
    """C.6, na ordem declarada: ASSOCIADO (p com Holm e margem) → SEM ASSOCIAÇÃO PRÁTICA (IC 95% sem
    correção inteiro dentro da margem) → INCONCLUSIVO. Mais de MAX_INVALIDAS inválidas força INCONCLUSIVO."""
    if not np.isfinite([p_holm, efeito_decide, lo_decide, hi_decide]).all():
        return "INCONCLUSIVO"
    if fracao_invalida > MAX_INVALIDAS:
        return "INCONCLUSIVO"
    if p_holm <= ALFA and abs(efeito_decide) >= MARGEM:
        return "ASSOCIADO"
    if -MARGEM < lo_decide and hi_decide < MARGEM:
        return "SEM ASSOCIAÇÃO PRÁTICA"
    return "INCONCLUSIVO"


def _sorteios_escolas(u, n_boot, rng):
    """C.6: bootstrap agrupado por escola — sorteia escolas com reposição, leva todas as linhas delas."""
    escolas, inverso = np.unique(u["co_entidade"].to_numpy(), return_inverse=True)
    linhas = [np.flatnonzero(inverso == e) for e in range(len(escolas))]
    ne = len(escolas)
    return [np.concatenate([linhas[e] for e in rng.integers(0, ne, ne)]) for _ in range(n_boot)]


def _coef_reamostra(X, y, idx):
    """Reajusta o OLS numa reamostragem; coluna sem variação na reamostragem fica NA (C.6)."""
    return _ols(X.iloc[idx], y[idx])


def c6_inferencia(u, anos=JANELA, n_boot=N_BOOT, semente=SEMENTE, com_vereditos=True):
    """C.6: tabela de fatores da etapa, com IC 95%, p, p Holm (família F7 da etapa) e veredito.

    As mesmas reamostragens servem aos dois modelos (diferenças pareadas, seção B). A família F7 junta os
    fatores do modelo principal e o iie_prop do secundário; o ano fica fora. Com com_vereditos=False
    (robustez, C.10), devolve efeitos e IC sem Holm nem veredito."""
    rng = np.random.default_rng(semente)
    sorteios = _sorteios_escolas(u, n_boot, rng)
    tabelas = []
    for modelo in ("principal", "secundario"):
        X, y = matriz_x(u, modelo, anos)
        coef = _ols(X, y)
        ef = c5_efeitos(coef, X, modelo).set_index("fator")
        fatores = list(ef.index)
        draws = np.vstack([_coef_reamostra(X, y, idx)[fatores].to_numpy() for idx in sorteios])
        escala = np.array([_escala_decide(f) for f in fatores])
        decide = draws * escala
        for j, f in enumerate(fatores):
            v = decide[:, j]
            validos = v[np.isfinite(v)]
            ef.loc[f, "fracao_invalidas"] = 1.0 - len(validos) / len(v)
            if len(validos):
                lo, hi = np.percentile(validos, [2.5, 97.5])
                ef.loc[f, ["ic_lo_decide", "ic_hi_decide"]] = [lo, hi]
                ef.loc[f, ["ic_lo_pp", "ic_hi_pp"]] = [lo / escala[j], hi / escala[j]]
                ef.loc[f, "p"] = B.p_bootstrap(validos)
            else:
                ef.loc[f, ["ic_lo_decide", "ic_hi_decide", "ic_lo_pp", "ic_hi_pp", "p"]] = np.nan
        tabelas.append(ef.reset_index())
    tab = pd.concat(tabelas, ignore_index=True)
    if com_vereditos:
        p = tab["p"].to_numpy()
        ajustado = np.full(len(p), np.nan)
        ok = np.isfinite(p)
        if ok.any():
            ajustado[ok] = B.holm(p[ok])
        tab["p_holm"] = ajustado
        tab["n_familia"] = int(ok.sum())
        tab["veredito"] = [c6_veredito(r.p_holm, r.efeito_decide, r.ic_lo_decide, r.ic_hi_decide,
                                       r.fracao_invalidas) for r in tab.itertuples()]
    return tab


# ------------------------------------------------------------------ C.7: Q1 (R², ΔR² sobre o modelo só com o ano)
def _pipeline_q1(modelo, so_ano, semente=None):
    """C.7: o mesmo pré-processamento para os três modelos, ajustado só no treino de cada dobra (regra 5)."""
    categoricas = [CONTROLE] if so_ano else list(CATEGORICAS) + [CONTROLE]
    partes = [("cat", OneHotEncoder(handle_unknown="ignore"), categoricas)]
    if not so_ano:
        partes.append(("num", StandardScaler(), list(DIMENSOES)))
    pre = ColumnTransformer(partes, remainder="drop")
    if modelo == "linear":
        est = LinearRegression()
    elif modelo == "ridge":
        est = Ridge(alpha=1.0)
    elif modelo == "mlp":
        est = MLPRegressor(hidden_layer_sizes=(50,), activation="logistic", solver="adam",
                           max_iter=5000, tol=1e-7, momentum=0.8, early_stopping=True, epsilon=1e-08,
                           n_iter_no_change=10, random_state=semente)
    else:
        raise ValueError(modelo)
    return Pipeline([("pre", pre), ("m", est)])


def dobras_por_escola(u, n_dobras=N_DOBRAS):
    """C.7: GroupKFold por co_entidade — a mesma escola nunca fica dos dois lados de uma dobra."""
    gkf = GroupKFold(n_splits=n_dobras)
    return list(gkf.split(u, groups=u["co_entidade"].to_numpy()))


def _metricas(y, prev):
    return {"mae": mean_absolute_error(y, prev), "rmse": root_mean_squared_error(y, prev),
            "r2": r2_score(y, prev)}


def _rodada_q1(u, modelo, so_ano, semente, dobras):
    """Uma passada de C.7: na amostra inteira e fora-da-dobra (previsões agrupadas), em pp; alvo ÷ 100."""
    ent = u[list(CATEGORICAS) + list(DIMENSOES) + [CONTROLE]]
    y = u[DESFECHO].astype("float64").to_numpy()
    pipe = _pipeline_q1(modelo, so_ano, semente)
    pipe.fit(ent, y / 100.0)
    dentro = pipe.predict(ent) * 100.0
    fora = np.full(len(u), np.nan)
    for tr, va in dobras:
        p = _pipeline_q1(modelo, so_ano, semente)
        p.fit(ent.iloc[tr], y[tr] / 100.0)
        fora[va] = p.predict(ent.iloc[va]) * 100.0
    return {"dentro": _metricas(y, dentro), "cv": _metricas(y, fora),
            "fora_de_0_100_dentro": int(((dentro < 0) | (dentro > 100)).sum()),
            "fora_de_0_100_cv": int(((fora < 0) | (fora > 100)).sum())}


def c7_q1(u, modelos=MODELOS_Q1, sementes=SEMENTES_MLP, n_dobras=N_DOBRAS):
    """C.7: MAE, RMSE e R² dentro da amostra e na validação cruzada agrupada, por modelo, com o modelo de
    referência só com o ano da mesma classe e o ΔR² (a resposta da Q1 é o ΔR² da regressão linear)."""
    dobras = dobras_por_escola(u, n_dobras)
    linhas = []
    for modelo in modelos:
        lista_sementes = sementes if modelo == "mlp" else (None,)
        rodadas = {so_ano: [_rodada_q1(u, modelo, so_ano, s, dobras) for s in lista_sementes]
                   for so_ano in (False, True)}
        for so_ano in (False, True):
            rs = rodadas[so_ano]
            linha = {"modelo": modelo, "variaveis": "so_ano" if so_ano else "completo",
                     "n_sementes": len(rs),
                     # nº de previsões fora de [0, 100]; no MLP, a média das sementes (sem truncar)
                     "fora_de_0_100_dentro": float(np.mean([r["fora_de_0_100_dentro"] for r in rs])),
                     "fora_de_0_100_cv": float(np.mean([r["fora_de_0_100_cv"] for r in rs]))}
            for onde in ("dentro", "cv"):
                for met in ("mae", "rmse", "r2"):
                    v = [r[onde][met] for r in rs]
                    linha[f"{met}_{onde}"] = float(np.mean(v))
                    linha[f"{met}_{onde}_dp"] = float(np.std(v, ddof=1)) if len(v) > 1 else np.nan
            linhas.append(linha)
        delta = [c["cv"]["r2"] - a["cv"]["r2"] for c, a in zip(rodadas[False], rodadas[True])]
        linhas[-2]["delta_r2_cv"] = float(np.mean(delta))
        linhas[-2]["delta_r2_cv_dp"] = float(np.std(delta, ddof=1)) if len(delta) > 1 else np.nan
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ C.8: importância por permutação (MLP)
def c8_permutacao(u, sementes=SEMENTES_MLP, n_dobras=N_DOBRAS, n_repeticoes=N_REPETICOES_PERM,
                  semente=SEMENTE):
    """C.8: queda de R² fora-da-dobra ao permutar cada variável e cada grupo (colunas do grupo com o MESMO
    sorteio de linhas), só para o MLP; IC pelos percentis das repetições. Descrição: não muda veredito."""
    rng = np.random.default_rng(semente)
    alvos = {v: [v] for v in list(CATEGORICAS) + list(DIMENSOES)}
    alvos.update({f"grupo:{g}": cols for g, cols in GRUPOS_PERMUTACAO.items()})
    ent = u[list(CATEGORICAS) + list(DIMENSOES) + [CONTROLE]]
    y = u[DESFECHO].astype("float64").to_numpy()
    dobras = dobras_por_escola(u, n_dobras)
    quedas = {a: [] for a in alvos}
    for s in sementes:
        for tr, va in dobras:
            pipe = _pipeline_q1("mlp", so_ano=False, semente=s)
            pipe.fit(ent.iloc[tr], y[tr] / 100.0)
            base = r2_score(y[va], pipe.predict(ent.iloc[va]) * 100.0)
            for nome, cols in alvos.items():
                for _ in range(n_repeticoes):
                    emb = ent.iloc[va].copy()
                    ordem = rng.permutation(len(emb))
                    emb[cols] = emb[cols].to_numpy()[ordem]
                    quedas[nome].append(base - r2_score(y[va], pipe.predict(emb) * 100.0))
    linhas = []
    for nome, v in quedas.items():
        v = np.asarray(v)
        lo, hi = np.percentile(v, [2.5, 97.5])
        linhas.append({"alvo": nome, "queda_r2": float(v.mean()), "ic_lo": float(lo), "ic_hi": float(hi)})
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ C.9: controle negativo
def c9_controle_negativo(u, modelos=MODELOS_Q1, sementes=SEMENTES_MLP, n_dobras=N_DOBRAS,
                         semente=SEMENTE):
    """C.9: abandono_t embaralhado entre as escolas DENTRO de cada ano (o nível do ano fica de propósito);
    o ΔR² da validação cruzada sobre o modelo só com o ano deve ficar abaixo de LIMIAR_CONTROLE para cada
    modelo (no MLP, a média das sementes). Se não ficar, a execução PARA."""
    rng = np.random.default_rng(semente)
    emb = u.copy()
    for _, g in emb.groupby(CONTROLE):
        emb.loc[g.index, DESFECHO] = g[DESFECHO].to_numpy()[rng.permutation(len(g))]
    q1 = c7_q1(emb, modelos, sementes, n_dobras)
    completo = q1[q1["variaveis"] == "completo"].set_index("modelo")
    so_ano = q1[q1["variaveis"] == "so_ano"].set_index("modelo").loc[completo.index]
    tab = pd.DataFrame({"modelo": completo.index,
                        "r2_cv_embaralhado": completo["r2_cv"].to_numpy(),
                        "r2_cv_so_ano_embaralhado": so_ano["r2_cv"].to_numpy(),
                        "delta_r2_cv_embaralhado": completo["delta_r2_cv"].to_numpy()})
    tab["limiar"] = LIMIAR_CONTROLE
    tab["passou"] = tab["delta_r2_cv_embaralhado"] < LIMIAR_CONTROLE
    return tab, bool(tab["passou"].all())


# ------------------------------------------------------------------ C.10: robustez
def c10_media_por_escola(u, n_boot=N_BOOT, semente=SEMENTE):
    """C.10 (a): cada escola vira uma linha (média dos anos da janela; dummies viram frações; ano sai);
    bootstrap simples de escolas. Sem Holm e sem veredito."""
    X, y = matriz_x(u, "principal", com_ano=False)
    Xm = X.groupby(u["co_entidade"].to_numpy()).mean()
    ym = pd.Series(y, index=X.index).groupby(u["co_entidade"].to_numpy()).mean().to_numpy()
    coef = _ols(Xm, ym)
    rng = np.random.default_rng(semente)
    n = len(Xm)
    draws = np.vstack([_coef_reamostra(Xm, ym, rng.integers(0, n, n)).to_numpy() for _ in range(n_boot)])
    linhas = []
    for j, f in enumerate(Xm.columns):
        v = draws[:, j] * _escala_decide(f)
        v = v[np.isfinite(v)]
        lo, hi = np.percentile(v, [2.5, 97.5]) if len(v) else (np.nan, np.nan)
        linhas.append({"analise": "media_por_escola", "fator": f,
                       "efeito_decide": coef[f] * _escala_decide(f),
                       "ic_lo_decide": float(lo), "ic_hi_decide": float(hi)})
    return pd.DataFrame(linhas)


def c10_janela_2012_2019(d, etapa, categorias, n_boot=N_BOOT, semente=SEMENTE):
    """C.10 (b): a mesma análise com t = 2012–2019 (2012 porque dim_ida_prop e dim_idp_prop começam em
    2012; 2019 porque o desfecho é do próprio ano). Sem Holm e sem veredito.

    `categorias` são as de dependencia que ficaram na tabela 0 da janela principal: a regra dos 30 NÃO é
    reaplicada aqui (C.13: a tabela 0 é o único lugar), para o modelo ter os mesmos fatores do principal.
    As linhas retiradas (preditor vazio; categoria fora da tabela 0) vão como colunas da tabela."""
    u, vazios = c2_universo(d, etapa, JANELA_ROBUSTEZ)
    fora = ~u["dependencia"].isin(set(categorias))
    u = u[~fora]
    tab = c6_inferencia(u, anos=JANELA_ROBUSTEZ, n_boot=n_boot, semente=semente, com_vereditos=False)
    tab.insert(0, "analise", "janela_2012_2019")
    tab["linhas_preditor_vazio"] = vazios
    tab["linhas_categoria_fora_da_tabela_0"] = int(fora.sum())
    return tab


# ------------------------------------------------------------------ C.13: tabela 0, itens, correlação e gravação
def c13_tabela0(d, anos=JANELA):
    """C.13: a tabela 0 — contagens por etapa (escolas, escolas-ano, categorias), linhas com preditor
    vazio, a aplicação da regra dos 30 e o tamanho da família F7. É gerada ANTES de qualquer modelo e é o
    único lugar onde a regra dos 30 é aplicada."""
    linhas, universos = [], {}
    for etapa in ETAPAS:
        u, reg = universo_pronto(d, etapa, anos)
        universos[etapa] = u
        linhas.append({"etapa": etapa, "chave": "escolas", "valor": u["co_entidade"].nunique()})
        linhas.append({"etapa": etapa, "chave": "escolas_ano", "valor": len(u)})
        linhas.append({"etapa": etapa, "chave": "linhas_preditor_vazio",
                       "valor": reg["linhas_preditor_vazio"]})
        for ano, n in u["ano"].value_counts().sort_index().items():
            linhas.append({"etapa": etapa, "chave": f"escolas_ano:ano={ano}", "valor": int(n)})
        for var in CATEGORICAS:
            for cat, n in u[var].value_counts().items():
                linhas.append({"etapa": etapa, "chave": f"{var}={cat}", "valor": int(n)})
        for cat, n in reg["categorias_excluidas"].items():
            linhas.append({"etapa": etapa, "chave": f"excluida_regra_30:dependencia={cat}", "valor": n})
        X, _ = matriz_x(u, "principal", anos)
        n_familia = len(_fatores_do_modelo(X, "principal")) + 1  # + iie_prop do secundário (C.6)
        linhas.append({"etapa": etapa, "chave": "familia_f7", "valor": n_familia})
    return pd.DataFrame(linhas), universos


def c13_itens(u):
    """C.13: prevalência dos 18 itens por ano — só descrição, nunca modelo (C.3)."""
    itens = [i.lower() for i in ITENS]
    tab = u.groupby("ano")[itens].mean(numeric_only=True).reset_index()
    return tab.melt(id_vars="ano", var_name="item", value_name="prevalencia")


def c13_correlacao(u):
    """C.13: correlações entre os preditores (dummies das categóricas, dimensões e índice); o desfecho à
    parte, marcado 'só exibição'."""
    X, y = matriz_x(u, "principal", com_ano=False)
    X[INDICE] = u[INDICE].astype("float64").to_numpy()
    cols = list(X.columns)
    ent = X.corr().reset_index().melt(
        id_vars="index", var_name="com", value_name="r").rename(columns={"index": "variavel"})
    ent["bloco"] = "entre_preditores"
    des = pd.DataFrame({"variavel": cols, "com": DESFECHO,
                        "r": [X[c].corr(pd.Series(y, index=X.index)) for c in cols]})
    des["bloco"] = "com_o_desfecho (só exibição, não decide)"
    return pd.concat([ent, des], ignore_index=True)


def estado_git():
    """Commit, branch e se a árvore de trabalho está limpa (sem nada modificado nem não rastreado)."""
    def git(*args):
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=RAIZ,
                              check=True).stdout.strip()
    return {"commit": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "limpa": git("status", "--porcelain") == ""}


def cabecalho(caminho_dataset, estado):
    """C.13 / D.1: commit, branch e sha256 do dataset no início de toda saída."""
    sha = hashlib.sha256(Path(caminho_dataset).read_bytes()).hexdigest()
    return (f"# commit={estado['commit']} branch={estado['branch']} dataset_sha256={sha} "
            f"gerado={date.today().isoformat()}")


def gravar(df, caminho, cab):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(cab + "\n")
        df.to_csv(f, index=False)


def fig_forest(fatores, caminho, cab=None):
    """C.5: figura principal — os efeitos que decidem o veredito, com IC 95%, AF e EM lado a lado.

    Cada painel tem o seu próprio eixo y: a regra dos 30 pode excluir categorias diferentes em cada etapa, e
    um eixo compartilhado poria os rótulos de uma etapa na outra. Devolve {etapa: rótulos desenhados}."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    etapas = [e for e in ETAPAS if (fatores["etapa"] == e).any()]
    fig, eixos = plt.subplots(1, max(len(etapas), 1), figsize=(13, 5), sharey=False)
    eixos = np.atleast_1d(eixos)
    for eixo, etapa in zip(eixos, etapas):
        t = fatores[fatores["etapa"] == etapa]
        pos = np.arange(len(t))
        eixo.errorbar(t["efeito_decide"], pos,
                      xerr=[t["efeito_decide"] - t["ic_lo_decide"],
                            t["ic_hi_decide"] - t["efeito_decide"]],
                      fmt="o", capsize=3)
        eixo.axvline(0, lw=0.8)
        for m in (-MARGEM, MARGEM):
            eixo.axvline(m, lw=0.8, ls="--")
        eixo.set_yticks(pos, t["fator"])
        eixo.set_title(f"{etapa} (efeito que decide, pp; tracejado = margem prática)")
        eixo.set_xlabel("pontos percentuais")
    fig.tight_layout()
    if cab:                      # D.1: a figura também leva o commit, o branch e o sha256 do dataset
        fig.text(0.005, 0.004, cab.lstrip("# "), fontsize=5, ha="left", va="bottom")
    fig.canvas.draw()
    rotulos = {etapa: [r.get_text() for r in eixo.get_yticklabels()] for eixo, etapa in zip(eixos, etapas)}
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return rotulos


# ------------------------------------------------------------------ a execução única (ordem do C.13)
def executar(d, pasta, caminho_dataset=DATASET, n_boot=N_BOOT, modelos=MODELOS_Q1,
             sementes=SEMENTES_MLP, n_repeticoes=N_REPETICOES_PERM):
    """Ordem do C.13: tabela 0 → controle negativo (C.9) → se passar, o resto.

    Se o controle falhar em qualquer etapa, grava SÓ o 07 e devolve 'PAROU' (C.9).
    Recusa rodar com a árvore do git suja: o commit do cabeçalho tem de ser o código que rodou (D.1)."""
    pasta = Path(pasta)
    estado = estado_git()
    if not estado["limpa"]:
        sys.exit("ERRO: a árvore do git não está limpa (há arquivo modificado ou não rastreado). O commit "
                 "gravado nas saídas tem de ser exatamente o código que rodou: faça o commit ou desfaça as "
                 "mudanças antes de executar.")
    cab = cabecalho(caminho_dataset, estado)
    tabela0, universos = c13_tabela0(d)
    controles = []
    for etapa in ETAPAS:
        tab, _ = c9_controle_negativo(universos[etapa], modelos, sementes)
        tab.insert(0, "etapa", etapa)
        controles.append(tab)
    controle = pd.concat(controles, ignore_index=True)
    if not controle["passou"].all():
        gravar(controle, pasta / "07_controle_negativo.csv", cab)
        return "PAROU: controle negativo reprovou (C.9); só o 07 foi gravado"

    def por_etapa(funcao):
        partes = []
        for etapa in ETAPAS:
            t = funcao(etapa, universos[etapa])
            t.insert(0, "etapa", etapa)
            partes.append(t)
        return pd.concat(partes, ignore_index=True)

    gravar(tabela0, pasta / "00_universo.csv", cab)
    gravar(controle, pasta / "07_controle_negativo.csv", cab)
    gravar(por_etapa(lambda e, u: c13_itens(u)), pasta / "01_itens.csv", cab)
    gravar(por_etapa(lambda e, u: c13_correlacao(u)), pasta / "02_correlacao.csv", cab)
    gravar(por_etapa(lambda e, u: c4_vif(matriz_x(u, "principal")[0]).rename_axis("coluna").reset_index()),
           pasta / "03_vif.csv", cab)
    fatores = por_etapa(lambda e, u: c6_inferencia(u, n_boot=n_boot))
    gravar(fatores, pasta / "04_fatores.csv", cab)
    gravar(por_etapa(lambda e, u: c7_q1(u, modelos, sementes)), pasta / "05_r2.csv", cab)
    if "mlp" in modelos:
        gravar(por_etapa(lambda e, u: c8_permutacao(u, sementes, n_repeticoes=n_repeticoes)),
               pasta / "06_permutacao.csv", cab)
    robustez = pd.concat([por_etapa(lambda e, u: c10_media_por_escola(u, n_boot)),
                          pd.concat([c10_janela_2012_2019(d, e, universos[e]["dependencia"].unique(),
                                                          n_boot).assign(etapa=e)
                                     for e in ETAPAS], ignore_index=True)], ignore_index=True)
    gravar(robustez, pasta / "08_robustez.csv", cab)
    fig_forest(fatores, pasta / "fig_forest.png", cab)  # todos os fatores com veredito, inclusive o iie_prop
    return "OK: execução única concluída"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Estudo de fatores (docs/PROTOCOLO.md, seção C). "
                                             "Execução ÚNICA, só com --executar.")
    ap.add_argument("--executar", action="store_true",
                    help="roda com o desfecho real (uma vez, depois do protocolo revisado no main)")
    args = ap.parse_args(argv)
    if not args.executar:
        print("Nada foi executado. Este script roda UMA VEZ, com --executar, depois que o protocolo "
              "(docs/PROTOCOLO.md, seção C) estiver no main por pull request revisado e o código tiver "
              "sido revisado contra o protocolo por outro integrante (regra 10).")
        return 0
    if SAIDA.exists():
        sys.exit(f"ERRO: {SAIDA} já existe. A execução é única (regra 10); uma nova execução exige "
                 "decisão registrada no docs/DECISOES.md, nunca a regravação por cima.")
    print(executar(ler_dataset(), SAIDA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
