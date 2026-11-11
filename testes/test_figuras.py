"""Testes de src/figuras.py: mensagens de entrada ausente, padrão de figura e
bytes reprodutíveis. Sem rede e sem tocar em dados/."""
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from src import figuras


def test_exigir_lista_o_que_falta_e_o_que_existe(tmp_path):
    presente = tmp_path / "a.csv"
    presente.write_text("x\n1\n", encoding="utf-8")
    with pytest.raises(figuras.EntradaAusente) as erro:
        figuras.exigir({"a": presente, "b": tmp_path / "b.csv"}, como_gerar="python -m src.x")
    msg = str(erro.value)
    assert "b: " in msg and "b.csv" in msg
    assert "Presentes: a" in msg
    assert "python -m src.x" in msg


def test_exigir_passa_quando_tudo_existe(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("x\n", encoding="utf-8")
    figuras.exigir({"a": p})


def test_localizar_pasta_sobe_a_arvore(tmp_path):
    (tmp_path / "gustavo").mkdir()
    fundo = tmp_path / "abandono-escolar" / "notebooks"
    fundo.mkdir(parents=True)
    assert figuras.localizar_pasta("gustavo", fundo) == tmp_path / "gustavo"


def test_localizar_pasta_diz_o_que_falta(tmp_path):
    with pytest.raises(figuras.EntradaAusente, match="Dados-do-Projeto"):
        figuras.localizar_pasta("pasta_que_nao_existe_xyz", tmp_path)


def test_titulo_exige_nivel_da_sintese():
    fig, ax = plt.subplots()
    figuras.titulo(ax, "Largura do intervalo", "FATO")
    assert ax.get_title(loc="left") == "[FATO] Largura do intervalo"
    with pytest.raises(ValueError, match="nível"):
        figuras.titulo(ax, "x", "ACHADO")
    plt.close(fig)


def test_sem_intervalo_usa_marca_aberta_e_diz_na_legenda():
    fig, ax = plt.subplots()
    figuras.pontos(ax, [0, 1, 2], [0.1, 0.2, 0.3], [0.0, np.nan, 0.2], [0.2, np.nan, 0.4], rotulo="B1R")
    _, rotulos = ax.get_legend_handles_labels()
    assert rotulos == ["B1R", f"B1R ({figuras.SEM_INTERVALO})"]
    aberta = ax.collections[-1]
    assert np.allclose(aberta.get_facecolors()[0], [1, 1, 1, 1])     # branca por dentro
    assert len(ax.collections[0].get_segments()) == 2                # duas barras de intervalo
    plt.close(fig)


def test_linha_zero_em_x_para_intervalos_horizontais():
    fig, ax = plt.subplots()
    figuras.linha_zero(ax)
    assert ax.lines[0].get_xdata()[0] == 0
    plt.close(fig)


def test_intervalos_ordena_de_cima_para_baixo_e_separa_o_destaque():
    fig, ax = plt.subplots()
    figuras.intervalos(ax, ["a", "b", "c"], [0.1, -0.02, 0.2], [0.05, -0.1, 0.1], [0.15, 0.06, 0.3],
                       [True, False, True], rotulo_destaque="sobrevive", rotulo_resto="não sobrevive")
    posicao = {t.get_text(): t.get_position()[1] for t in ax.get_yticklabels()}
    assert posicao == {"a": 2, "b": 1, "c": 0}                               # "a" no topo
    _, rotulos = ax.get_legend_handles_labels()
    assert rotulos == ["sobrevive", "não sobrevive"]
    assert len(ax.collections[0].get_segments()) == 2                      # dois intervalos em destaque
    assert ax.lines[0].get_xdata()[0] == 0                                   # linha do zero
    plt.close(fig)


def test_intervalos_sem_destaque_nem_zero():
    fig, ax = plt.subplots()
    figuras.intervalos(ax, ["a", "b"], [0.3, 0.2], [0.2, 0.1], [0.4, 0.3], zero=False)
    assert not ax.lines
    assert ax.get_legend_handles_labels()[1] == []
    plt.close(fig)


def test_salvar_gera_png_e_pdf_com_os_mesmos_bytes(tmp_path):
    def figura():
        fig, ax = plt.subplots(figsize=(3, 2))
        figuras.pontos(ax, [0, 1], [0.1, -0.05], [0.0, -0.2], [0.2, 0.1])
        figuras.linha_zero(ax)
        return fig
    f1 = figura()
    a = figuras.salvar(f1, tmp_path / "um", "fig")
    f2 = figura()
    b = figuras.salvar(f2, tmp_path / "dois", "fig")
    plt.close(f1)
    plt.close(f2)
    assert [p.suffix for p in a] == [".png", ".pdf"]
    for x, y in zip(a, b):
        assert x.read_bytes() == y.read_bytes(), x.name


def test_barras_contagem_separa_tipos_e_escreve_vazio():
    fig, ax = plt.subplots()
    figuras.barras_contagem(ax, ["a", "b", "c", "d"], [10, 3, 13, np.nan],
                            ["funil", "fora do funil", "total", "funil"])
    barras = ax.patches
    assert len(barras) == 3                                   # o vazio não vira barra de 0
    assert barras[1].get_hatch() == "////"                    # fora do funil, hachurado
    textos = [t.get_text() for t in ax.texts]
    assert "vazio" in textos and "13" in textos
    assert ax.get_xlim()[0] == 0
    plt.close(fig)


def test_matriz_presenca_marca_ausente():
    fig, ax = plt.subplots()
    figuras.matriz_presenca(ax, ["TDI", "ATU"], [2024, 2025], [[1200, 1300], [900, np.nan]])
    textos = [t.get_text() for t in ax.texts]
    assert textos == ["1.200", "1.300", "900", "ausente"]
    plt.close(fig)


def test_conferir_ambiente_acusa_versao_diferente(tmp_path):
    from importlib.metadata import version
    req = tmp_path / "requirements.txt"
    req.write_text(f"pandas=={version('pandas')}\nnumpy==0.0.1\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="numpy .* instalado, 0.0.1 fixado"):
        figuras.conferir_ambiente(req, ("pandas", "numpy"))
    req.write_text(f"pandas=={version('pandas')}\n", encoding="utf-8")
    assert figuras.conferir_ambiente(req, ("pandas",)) == {"pandas": version("pandas")}


def test_titulo_figura_com_nivel_e_subtitulo():
    fig, _ = plt.subplots(1, 2)
    figuras.titulo_figura(fig, "Funil", "FATO", "Brasil fora da escala")
    assert fig._suptitle.get_text() == "[FATO] Funil\nBrasil fora da escala"
    with pytest.raises(ValueError):
        figuras.titulo_figura(fig, "x", "fato")
    plt.close(fig)


def test_barras_contagem_aceita_contagem_nullable():
    import pandas as pd
    fig, ax = plt.subplots()
    figuras.barras_contagem(ax, ["a", "b"], pd.array([5, pd.NA], dtype="Int64"), ["funil", "total"])
    assert len(ax.patches) == 1 and "vazio" in [t.get_text() for t in ax.texts]
    plt.close(fig)


def test_matriz_presenca_separa_ausente_de_presente_sem_valor():
    fig, ax = plt.subplots()
    figuras.matriz_presenca(ax, ["tx_rend"], [2019, 2020, 2025], [[np.nan, 192, np.nan]],
                            presente=[[True, True, False]], sem_valor="RR não identificável")
    assert [t.get_text() for t in ax.texts] == ["RR não identificável", "192", "ausente"]
    plt.close(fig)
