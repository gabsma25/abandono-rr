"""Funções de figura dos notebooks (CLAUDE.md §4: o notebook exibe, não calcula).

Nenhuma função aqui calcula estatística: todas recebem colunas prontas de um
CSV gerado por código. Padrão de figura (decisão da pesquisadora, 2026-11-03):

- estimativa com intervalo: ponto central mais barra do intervalo, nunca
  barra de altura sozinha (`pontos`);
- comparação contra baseline: diferença com intervalo e a linha do zero
  marcada (`pontos` + `linha_zero`), para que se veja o intervalo cruzar o zero;
- estimativa sem intervalo: marca aberta, e a legenda diz "sem intervalo";
- o nível de evidência da docs/SINTESE_DO_PROJETO.md vai no título
  (`titulo`); uma figura que mistura níveis os distingue na legenda;
- o eixo começa onde o dado exige: nada aqui fixa limite de eixo;
- cada figura é salva em PNG 300 dpi e PDF vetorial (`salvar`), com metadados
  fixos para que duas execuções gerem os mesmos bytes.

Os notebooks 02 e 03 leem `gustavo/`, do repositório Dados-do-Projeto;
`localizar_pasta` sobe a árvore sem resolver junctions e diz o que falta se
não achar (README, limitações).
"""
from __future__ import annotations

import os
import pathlib
from collections.abc import Mapping, Sequence

import matplotlib as mpl
import numpy as np
import pandas as pd

NIVEIS = ("FATO", "MEDIDO", "PONTUAL", "EXPLORATÓRIO", "INTERPRETAÇÃO", "REFUTADO")
SEM_INTERVALO = "sem intervalo"
COR = "#1f4e79"
COR_SECUNDARIA = "#8c8c8c"
COR_EVENTO = "#555555"

ESTILO = {
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "pdf.fonttype": 42,   # texto editável no PDF
    "figure.dpi": 100,
}


class EntradaAusente(FileNotFoundError):
    """Arquivo ou pasta de entrada do notebook que não existe."""


def aplicar_estilo() -> None:
    mpl.rcParams.update(ESTILO)


def conferir_ambiente(requirements: pathlib.Path,
                      pacotes: Sequence[str] = ("pandas", "numpy", "matplotlib")) -> dict[str, str]:
    """Para se a versão instalada de um pacote difere da fixada em `requirements`.

    O kernel "python3" chama o "python" do PATH: sem o .venv ativado, cai no Python
    global (outras versões), mesmo com o jupyter lançado pelo .venv — visto em
    2026-11-03. Os números e as figuras só valem no ambiente do .venv (CLAUDE.md §7).
    """
    from importlib.metadata import version

    fixadas = {}
    for linha in pathlib.Path(requirements).read_text(encoding="utf-8").splitlines():
        nome, _, ver = linha.split(";")[0].strip().partition("==")
        if ver:
            fixadas[nome.lower()] = ver.strip()
    instaladas = {p: version(p) for p in pacotes}
    erradas = {p: (v, fixadas.get(p)) for p, v in instaladas.items() if fixadas.get(p) not in (None, v)}
    if erradas:
        detalhe = "; ".join(f"{p} {v} instalado, {f} fixado" for p, (v, f) in erradas.items())
        raise RuntimeError(
            f"Ambiente diferente do fixado em {requirements.name}: {detalhe}. O kernel 'python3' chama o "
            f"'python' do PATH: ative o .venv do abandono-escolar antes de abrir ou rodar o notebook "
            rf"(.venv\Scripts\activate; jupyter nbconvert --to notebook --execute --inplace "
            f"notebooks/<notebook>.ipynb).")
    return instaladas


def exigir(arquivos: Mapping[str, pathlib.Path], como_gerar: str = "") -> None:
    """Para com mensagem clara se algum arquivo de entrada não existe."""
    faltam = {nome: p for nome, p in arquivos.items() if not pathlib.Path(p).exists()}
    if not faltam:
        return
    linhas = ["Faltam arquivos de entrada do notebook:"]
    linhas += [f"  - {nome}: {p}" for nome, p in faltam.items()]
    presentes = [nome for nome in arquivos if nome not in faltam]
    if presentes:
        linhas.append("Presentes: " + ", ".join(presentes))
    if como_gerar:
        linhas.append(f"Como gerar: {como_gerar}")
    raise EntradaAusente("\n".join(linhas))


def localizar_pasta(nome: str, inicio: pathlib.Path | None = None) -> pathlib.Path:
    """Sobe a árvore a partir de `inicio` (padrão: pasta atual) até achar `nome`.

    Usa o caminho como foi dado, sem resolver junctions: aberto a partir de
    Dados-do-Projeto/abandono-escolar, sobe por Dados-do-Projeto.
    """
    origem = pathlib.Path(os.path.abspath(inicio or pathlib.Path.cwd()))
    for pasta in (origem, *origem.parents):
        if (pasta / nome).is_dir():
            return pasta / nome
    raise EntradaAusente(
        f"Pasta '{nome}' não encontrada subindo a partir de {origem}. Este notebook depende "
        f"do repositório Dados-do-Projeto: abra-o a partir de Dados-do-Projeto/abandono-escolar/"
        f"notebooks, com Dados-do-Projeto/{nome} ao lado (README do abandono-escolar, limitações).")


def titulo(ax, texto: str, nivel: str) -> None:
    """Título com o nível de evidência da síntese entre colchetes."""
    if nivel not in NIVEIS:
        raise ValueError(f"nível '{nivel}' não existe na síntese; use um de {NIVEIS}")
    ax.set_title(f"[{nivel}] {texto}", loc="left")


def titulo_figura(fig, texto: str, nivel: str, subtitulo: str = "") -> None:
    """Título geral (figura com vários painéis), com o nível de evidência."""
    if nivel not in NIVEIS:
        raise ValueError(f"nível '{nivel}' não existe na síntese; use um de {NIVEIS}")
    fig.suptitle(f"[{nivel}] {texto}" + (f"\n{subtitulo}" if subtitulo else ""), x=0.01, ha="left",
                 fontsize=10)


def pontos(ax, posicao: Sequence[float], valor: Sequence[float],
           lo: Sequence[float] | None = None, hi: Sequence[float] | None = None, *,
           orientacao: str = "h", cor: str = COR, rotulo: str | None = None,
           marcador: str = "o", tamanho: float = 22) -> None:
    """Ponto central com a barra do intervalo; sem intervalo, marca aberta.

    orientacao="h": valor no eixo x, posição no y (gráfico de intervalos);
    orientacao="v": posição no x (ano), valor no y (série).
    """
    pos = np.asarray(posicao, dtype=float)
    val = np.asarray(valor, dtype=float)
    lo = np.full_like(val, np.nan) if lo is None else np.asarray(lo, dtype=float)
    hi = np.full_like(val, np.nan) if hi is None else np.asarray(hi, dtype=float)
    com = np.isfinite(lo) & np.isfinite(hi)
    xy = (lambda p, v: (v, p)) if orientacao == "h" else (lambda p, v: (p, v))
    if com.any():
        barras = ax.hlines if orientacao == "h" else ax.vlines
        barras(pos[com], lo[com], hi[com], color=cor, linewidth=1.3, zorder=2)
        ax.scatter(*xy(pos[com], val[com]), s=tamanho, color=cor, marker=marcador, zorder=3, label=rotulo)
    if (~com).any():
        rot = f"{rotulo} ({SEM_INTERVALO})" if rotulo else SEM_INTERVALO
        ax.scatter(*xy(pos[~com], val[~com]), s=tamanho, facecolors="white", edgecolors=cor,
                   marker=marcador, linewidths=1.2, zorder=3, label=rot)


def linha_zero(ax, orientacao: str = "h") -> None:
    """Linha do zero de uma figura de diferenças."""
    (ax.axvline if orientacao == "h" else ax.axhline)(0, color="black", linewidth=0.9, zorder=1)


def intervalos(ax, rotulos: Sequence[str], valor: Sequence[float], lo: Sequence[float],
               hi: Sequence[float], destaque: Sequence[bool] | None = None, *,
               rotulo_destaque: str | None = None, rotulo_resto: str | None = None,
               zero: bool = True) -> None:
    """Gráfico de intervalos: uma estimativa por linha, na ordem de `rotulos`, de cima para baixo.

    `destaque` vem pronto do CSV (ex.: `rejeita_holm`) e só separa duas cores: nada aqui
    decide quem sobrevive a um teste. Com `zero`, marca a linha do zero (figura de diferenças).
    """
    y = np.arange(len(rotulos))[::-1]
    val, lo, hi = (pd.Series(list(v), dtype="Float64").to_numpy(dtype=float, na_value=np.nan)
                   for v in (valor, lo, hi))
    marca = np.zeros(len(y), dtype=bool) if destaque is None else np.asarray(destaque, dtype=bool)
    if marca.any():
        pontos(ax, y[marca], val[marca], lo[marca], hi[marca], cor=COR, rotulo=rotulo_destaque)
    if (~marca).any():
        cor = COR if destaque is None else COR_SECUNDARIA
        pontos(ax, y[~marca], val[~marca], lo[~marca], hi[~marca], cor=cor, rotulo=rotulo_resto)
    if zero:
        linha_zero(ax)
    ax.set_yticks(y, list(rotulos))


def eventos(ax, marcas: Mapping[float, str]) -> None:
    """Linhas verticais tracejadas com rótulo (rupturas, início de programa)."""
    for x, texto in marcas.items():
        ax.axvline(x, color=COR_EVENTO, linestyle="--", linewidth=0.8, zorder=0)
        ax.annotate(texto, xy=(x, 1), xycoords=("data", "axes fraction"), xytext=(3, -3),
                    textcoords="offset points", ha="left", va="top", rotation=90,
                    fontsize=8, color=COR_EVENTO)


ESTILO_DEGRAU = {
    "funil": {"facecolor": COR, "edgecolor": COR},
    "fora do funil": {"facecolor": "white", "edgecolor": COR_SECUNDARIA, "hatch": "////"},
    "total": {"facecolor": "white", "edgecolor": COR, "linewidth": 1.4},
}


def _milhar(v: float) -> str:
    return f"{int(v):,}".replace(",", ".")


def barras_contagem(ax, rotulos: Sequence[str], n: Sequence[float], tipos: Sequence[str]) -> None:
    """Contagens (não são estimativas: sem intervalo) em barras horizontais a partir do zero.

    `tipos` vem do CSV do funil: "funil", "fora do funil" (hachurado, nunca somado a
    outro degrau) ou "total" (só contorno). Contagem vazia é escrita como "vazio".
    """
    y = np.arange(len(rotulos))[::-1]
    n = pd.Series(list(n), dtype="Float64").to_numpy(dtype=float, na_value=np.nan)
    for yi, valor, tipo in zip(y, n, tipos):
        if not np.isfinite(valor):
            ax.annotate("vazio", xy=(0, yi), xytext=(3, 0), textcoords="offset points", va="center", fontsize=8)
            continue
        ax.barh(yi, float(valor), height=0.62, **ESTILO_DEGRAU[tipo])
        ax.annotate(_milhar(valor), xy=(float(valor), yi), xytext=(3, 0), textcoords="offset points",
                    va="center", fontsize=8)
    ax.set_yticks(y, rotulos)
    ax.set_xlim(left=0)
    presentes = [t for t in ESTILO_DEGRAU if t in set(tipos)]
    ax.legend(handles=[mpl.patches.Patch(label=t, **ESTILO_DEGRAU[t]) for t in presentes],
              loc="lower right", fontsize=8)


def matriz_presenca(ax, linhas: Sequence[str], colunas: Sequence, valores, presente=None,
                    sem_valor: str = "não identificável") -> None:
    """Grade linha × coluna. Célula ausente: "ausente". Presente com valor: o valor.
    Presente sem valor (contagem vazia no CSV): `sem_valor` — nunca 0 nem "ausente".
    Sem `presente`, presença = ter valor."""
    m = np.asarray(pd.DataFrame(valores).astype("Float64").to_numpy(dtype=float, na_value=np.nan))
    pres = np.isfinite(m) if presente is None else np.asarray(presente, dtype=bool)
    ax.imshow(pres.astype(float), cmap=mpl.colors.ListedColormap(["#f4f4f4", "#c9daea"]),
              vmin=0, vmax=1, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if not pres[i, j]:
                txt, cor, estilo = "ausente", "#b00000", "normal"
            elif np.isfinite(m[i, j]):
                txt, cor, estilo = _milhar(m[i, j]), "black", "normal"
            else:
                txt, cor, estilo = sem_valor, "#555555", "italic"
            ax.text(j, i, txt, ha="center", va="center", fontsize=7, color=cor, style=estilo)
    ax.set_xticks(range(len(colunas)), [str(c) for c in colunas])
    ax.set_yticks(range(len(linhas)), linhas)
    ax.tick_params(length=0)
    for lado in ("top", "right", "bottom", "left"):
        ax.spines[lado].set_visible(False)


def salvar(fig, pasta: pathlib.Path, nome: str) -> list[pathlib.Path]:
    """Grava `nome`.png (300 dpi) e `nome`.pdf em `pasta`; devolve os caminhos."""
    pasta = pathlib.Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    png, pdf = pasta / f"{nome}.png", pasta / f"{nome}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", metadata={"Software": None})
    fig.savefig(pdf, bbox_inches="tight", metadata={"CreationDate": None, "Producer": None,
                                                    "Creator": None})
    return [png, pdf]
