"""Registro de anos novos no manifesto (src/aquisicao.registrar e aplicar_registro) — sem rede.

O servidor falso serve as páginas do INEP (microdados, índice de indicadores, página e aba de
tx_rend) e os zips. Os nomes dos zips são os reais de 2007, 2014 e 2018, lidos nas abas do INEP em
2026-11-18: mudam de padrão ao longo dos anos, e a pasta de 2007 no servidor é a de 2011.
"""
from __future__ import annotations

import csv
import pathlib

import pytest

from src.aquisicao import (
    BASE_INEP,
    PAGINA_INDICADORES,
    PAGINA_MICRODADOS,
    ClienteInep,
    ErroAquisicao,
    Link,
    acrescentar_fontes,
    ano_do_nome,
    aplicar_registro,
    escolher_para_registro,
    parse_anos,
    parse_microdados,
    registrar,
    tabela_do_link,
)
from src.integridade import ErroIntegridade
from testes.conftest import sha256
from testes.test_download import RespostaFalsa, ServidorFalso, _zip

RAIZ = pathlib.Path(__file__).resolve().parents[1]
FIXTURE_MICRODADOS = RAIZ / "testes" / "fixtures" / "html" / "2026-09-30" / "microdados" / "censo-escolar.html"
MANIFEST_REAL = RAIZ / "dados" / "MANIFEST.csv"

PAGINA_TX = PAGINA_INDICADORES + "/taxas-de-rendimento-escolar"
DL = "https://download.inep.gov.br/"
URL_CENSO_2007 = DL + "dados_abertos/microdados_censo_escolar_2007.zip"
URL_CENSO_2019 = DL + "dados_abertos/microdados_censo_escolar_2019.zip"
URL_TX_2007 = DL + "informacoes_estatisticas/2011/indicadores_educacionais/taxa_rendimento/2007/"
CENSO_2007 = _zip(b"microdados de 2007")
TX_2007 = _zip(b"rendimento por escola de 2007")


# ------------------------------------------------------------------ nomes e anos
def test_parse_anos():
    assert parse_anos("2007-2018") == set(range(2007, 2019))
    assert parse_anos("2007, 2010-2011") == {2007, 2010, 2011}
    for ruim in ("2018-2007", "07-18", "", "2007;2008"):
        with pytest.raises(ValueError):
            parse_anos(ruim)


@pytest.mark.parametrize("nome, ano, tabela", [
    ("microdados_censo_escolar_2007.zip", 2007, "microdados"),
    ("microdados_censo_escolar_2025_.zip", 2025, "microdados"),
    ("tx_rendimento_escolas_2007.zip", 2007, "indicador_tx_rend_escolas"),
    ("tx_rendimento_escolas_2014.zip", 2014, "indicador_tx_rend_escolas"),
    ("TX_REND_ESCOLAS_2018.zip", 2018, "indicador_tx_rend_escolas"),
    ("tx_rend_escolas_2019.zip", 2019, "indicador_tx_rend_escolas"),
    ("tx_rendimento_municipios_2007.zip", 2007, None),
    ("tx_rendimento_brasil_regioes_UFs_2007.zip", 2007, None),
    ("TX_REND_MUNICIPIOS_2018.zip", 2018, None),
    ("ATU_2019_ESCOLAS.zip", 2019, None),
])
def test_tabela_e_ano_pelo_nome(nome, ano, tabela):
    assert ano_do_nome(nome) == ano
    assert tabela_do_link(nome) == tabela


def test_nome_sem_ano_ou_com_dois_anos():
    assert ano_do_nome("microdados_censo_escolar.zip") is None
    assert ano_do_nome("tx_rend_2018_2019.zip") is None


def test_pagina_real_de_microdados_tem_os_doze_anos_antigos():
    links = parse_microdados(FIXTURE_MICRODADOS.read_text(encoding="utf-8"))
    escolhidos = escolher_para_registro(links, set(range(2007, 2019)))
    assert sorted(escolhidos) == [(ano, "microdados") for ano in range(2007, 2019)]
    assert escolhidos[(2007, "microdados")].url == URL_CENSO_2007


def test_dois_zips_para_o_mesmo_ano_param():
    links = [Link("tx_rend_escolas_2010.zip", "u1", "p", None), Link("TX_REND_ESCOLAS_2010_v2.zip", "u2", "p", None)]
    with pytest.raises(ErroAquisicao, match="Dois zips"):
        escolher_para_registro(links, {2010})


# ------------------------------------------------------------------ fallback estático
def _ler_csv(caminho: pathlib.Path) -> list[dict]:
    with caminho.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_acrescentar_fontes_nao_mexe_nas_linhas_existentes(tmp_path):
    fontes = tmp_path / "fontes.csv"
    original = ("arquivo,url,pagina,atualizado_em,capturado_em\n"
                "tx_rend_escolas_2019.zip,u19,p19,19/05/2023 11h41,2026-09-30\n")
    fontes.write_text(original, encoding="utf-8")
    novos = [Link("tx_rendimento_escolas_2007.zip", "u07", "p07", None),
             Link("tx_rend_escolas_2019.zip", "OUTRA", "p", None)]
    assert acrescentar_fontes(novos, "2026-11-18", fontes) == 1
    texto = fontes.read_text(encoding="utf-8")
    assert "\r" not in texto
    assert "\ntx_rend_escolas_2019.zip,u19,p19,19/05/2023 11h41,2026-09-30\n" in texto
    assert [r["arquivo"] for r in _ler_csv(fontes)] == ["tx_rend_escolas_2019.zip", "tx_rendimento_escolas_2007.zip"]


# ------------------------------------------------------------------ registrar
def _manifesto(tmp_path: pathlib.Path) -> pathlib.Path:
    m = tmp_path / "MANIFEST.csv"
    m.write_text(
        "estagio,origem,ano,tabela,arquivo,sha256,data_download\n"
        f"origem,inep,2019,microdados,origem/censo/microdados_censo_escolar_2019.zip,{'a' * 64},2026-09-15\n"
        f"origem,inep,2019,indicador_tx_rend_escolas,origem/indicadores/tx_rend_escolas_2019.zip,{'b' * 64},2026-09-15\n"
        f"cache,gustavo,2007,cache_censo,cache/censo/2007.parquet,{'c' * 64},2026-11-11\n",
        encoding="utf-8")
    return m


class SessaoInep:
    """Páginas do INEP em HTML mínimo, no layout real, e os zips pelo ServidorFalso."""

    def __init__(self, zips: dict[str, bytes]):
        aba = PAGINA_TX + "/2007"
        self.paginas = {
            PAGINA_MICRODADOS: f'<ul><li><a href="{URL_CENSO_2007}">2007</a></li>'
                               f'<li><a href="{URL_CENSO_2019}">2019</a></li></ul>',
            PAGINA_INDICADORES: f'<a href="{PAGINA_TX}">Taxas de rendimento</a>',
            PAGINA_TX: f'<div data-id="2007" data-url="{aba}"></div>',
            aba: "<p>Atualizado em 19/05/2023 11h41</p><ul>"
                 f'<li><a href="{URL_TX_2007}tx_rendimento_brasil_regioes_UFs_2007.zip">Brasil</a></li>'
                 f'<li><a href="{URL_TX_2007}tx_rendimento_municipios_2007.zip">Municípios</a></li>'
                 f'<li><a href="{URL_TX_2007}tx_rendimento_escolas_2007.zip">Escolas</a></li></ul>',
        }
        self.servidor = ServidorFalso(zips)

    @property
    def baixados(self) -> list[str]:
        return [p["url"] for p in self.servidor.pedidos]

    def get(self, url, headers=None, stream=False, timeout=None):
        if url in self.paginas:
            return RespostaFalsa(200, self.paginas[url].encode("utf-8"), {})
        return self.servidor.get(url, headers=headers, stream=stream, timeout=timeout)


def _registrar(tmp_path, sessao, anos, **kw):
    fontes = tmp_path / "fontes.csv"
    if not fontes.exists():
        fontes.write_text("arquivo,url,pagina,atualizado_em,capturado_em\n", encoding="utf-8")
    return registrar(anos, cliente=ClienteInep(sessao, pausa=0, espera_base=0), manifesto=kw.pop("manifesto"),
                     pasta=tmp_path / "registro", cache=tmp_path / "cache", fontes_estaticas=fontes, **kw)


def test_registrar_baixa_os_dois_zips_e_propoe_as_linhas(tmp_path):
    manifesto = _manifesto(tmp_path)
    antes = manifesto.read_bytes()
    sessao = SessaoInep({URL_CENSO_2007: CENSO_2007, URL_TX_2007 + "tx_rendimento_escolas_2007.zip": TX_2007})
    r = _registrar(tmp_path, sessao, {2007, 2019}, manifesto=manifesto, baixar_da_rede=True)

    assert r["faltando"] == []
    assert r["ja_no_manifesto"] == [(2019, "indicador_tx_rend_escolas"), (2019, "microdados")]
    assert {(lin["tabela"], lin["arquivo"], lin["sha256"]) for lin in r["linhas"]} == {
        ("microdados", "origem/censo/microdados_censo_escolar_2007.zip", sha256(CENSO_2007)),
        ("indicador_tx_rend_escolas", "origem/indicadores/tx_rendimento_escolas_2007.zip", sha256(TX_2007)),
    }
    # só os dois zips de 2007 foram baixados; nada de 2019, municípios nem Brasil
    assert sorted(sessao.baixados) == sorted([URL_CENSO_2007, URL_TX_2007 + "tx_rendimento_escolas_2007.zip"])
    # proposta gravada; manifesto intocado; links novos no fallback, com o "Atualizado em" da aba
    assert _ler_csv(tmp_path / "registro" / "manifesto_proposto.csv") == r["linhas"]
    assert manifesto.read_bytes() == antes
    fontes = {f["arquivo"]: f for f in _ler_csv(tmp_path / "fontes.csv")}
    assert set(fontes) == {"microdados_censo_escolar_2007.zip", "tx_rendimento_escolas_2007.zip"}
    assert fontes["tx_rendimento_escolas_2007.zip"]["atualizado_em"] == "19/05/2023 11h41"


def test_registrar_retoma_sem_baixar_de_novo(tmp_path):
    manifesto = _manifesto(tmp_path)
    zips = {URL_CENSO_2007: CENSO_2007, URL_TX_2007 + "tx_rendimento_escolas_2007.zip": TX_2007}
    _registrar(tmp_path, SessaoInep(zips), {2007}, manifesto=manifesto, baixar_da_rede=True)
    sessao = SessaoInep(zips)
    r = _registrar(tmp_path, sessao, {2007}, manifesto=manifesto, baixar_da_rede=True)
    assert len(r["linhas"]) == 2 and sessao.baixados == []


def test_registrar_sem_rede_copia_da_pasta_local_pelo_fallback(tmp_path):
    manifesto = _manifesto(tmp_path)
    local = tmp_path / "zips_antigos"
    local.mkdir()
    (local / "microdados_censo_escolar_2007.zip").write_bytes(CENSO_2007)
    fontes = tmp_path / "fontes.csv"
    fontes.write_text("arquivo,url,pagina,atualizado_em,capturado_em\n"
                      f"microdados_censo_escolar_2007.zip,{URL_CENSO_2007},p,,2026-09-30\n"
                      f"tx_rendimento_escolas_2007.zip,{URL_TX_2007}tx_rendimento_escolas_2007.zip,p,,2026-11-18\n",
                      encoding="utf-8")
    r = _registrar(tmp_path, SessaoInep({}), {2007}, manifesto=manifesto, origens_locais=[local])
    assert [lin["tabela"] for lin in r["linhas"]] == ["microdados"]
    assert r["faltando"] == ["tx_rendimento_escolas_2007.zip"]   # sem rede e sem cópia local


def test_registrar_com_paginas_fora_do_ar_baixa_pelo_fallback(tmp_path, caplog):
    """O caso de 2026-11-18: o www.gov.br derrubou a conexão, mas o download.inep.gov.br respondeu."""
    manifesto = _manifesto(tmp_path)
    url_tx = URL_TX_2007 + "tx_rendimento_escolas_2007.zip"
    (tmp_path / "fontes.csv").write_text(
        "arquivo,url,pagina,atualizado_em,capturado_em\n"
        f"microdados_censo_escolar_2007.zip,{URL_CENSO_2007},p,,2026-09-30\n"
        f"tx_rendimento_escolas_2007.zip,{url_tx},p,19/05/2023 11h41,2026-11-18\n", encoding="utf-8")
    sessao = SessaoInep({URL_CENSO_2007: CENSO_2007, url_tx: TX_2007})
    sessao.paginas = {}                                   # nenhuma página do gov.br responde
    r = _registrar(tmp_path, sessao, {2007}, manifesto=manifesto, baixar_da_rede=True)
    assert r["faltando"] == []
    assert {lin["sha256"] for lin in r["linhas"]} == {sha256(CENSO_2007), sha256(TX_2007)}
    assert "fallback estático" in caplog.text


def test_fallback_real_tem_os_24_zips_de_2007_a_2018():
    """src/fontes_inep.csv cobre o registro de 2007–2018 mesmo sem raspagem."""
    from src.aquisicao import FONTES_ESTATICAS, ler_fontes_estaticas
    escolhidos = escolher_para_registro(list(ler_fontes_estaticas(FONTES_ESTATICAS).values()), set(range(2007, 2019)))
    assert sorted(escolhidos) == sorted((ano, t) for ano in range(2007, 2019)
                                        for t in ("microdados", "indicador_tx_rend_escolas"))


def test_registrar_recusa_pagina_html_no_lugar_do_zip(tmp_path):
    manifesto = _manifesto(tmp_path)
    sessao = SessaoInep({URL_CENSO_2007: b"<!DOCTYPE html><html>Acesso negado</html>",
                         URL_TX_2007 + "tx_rendimento_escolas_2007.zip": TX_2007})
    r = _registrar(tmp_path, sessao, {2007}, manifesto=manifesto, baixar_da_rede=True)
    assert r["faltando"] == ["microdados_censo_escolar_2007.zip"]
    assert [lin["tabela"] for lin in r["linhas"]] == ["indicador_tx_rend_escolas"]
    assert not (tmp_path / "registro" / "microdados_censo_escolar_2007.zip").exists()


# ------------------------------------------------------------------ aplicar_registro
def _proposta(tmp_path, linhas):
    p = tmp_path / "proposta.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["estagio", "origem", "ano", "tabela", "arquivo", "sha256", "data_download"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    return p


def _linha(ano, tabela, sha="d" * 64):
    sub = "censo" if tabela == "microdados" else "indicadores"
    return {"estagio": "origem", "origem": "inep", "ano": str(ano), "tabela": tabela,
            "arquivo": f"origem/{sub}/z_{tabela}_{ano}.zip", "sha256": sha, "data_download": "2026-11-18"}


def test_aplicar_insere_em_ordem_antes_de_2019_e_e_idempotente(tmp_path):
    manifesto = _manifesto(tmp_path)
    proposta = _proposta(tmp_path, [_linha(2008, "microdados"), _linha(2007, "microdados"),
                                    _linha(2007, "indicador_tx_rend_escolas")])
    assert aplicar_registro(proposta, manifesto) == 3
    linhas = _ler_csv(manifesto)
    assert [(lin["ano"], lin["tabela"]) for lin in linhas] == [
        ("2007", "microdados"), ("2008", "microdados"), ("2019", "microdados"),
        ("2007", "indicador_tx_rend_escolas"), ("2019", "indicador_tx_rend_escolas"),
        ("2007", "cache_censo")]
    depois = manifesto.read_bytes()
    assert b"\r" not in depois
    assert aplicar_registro(proposta, manifesto) == 0
    assert manifesto.read_bytes() == depois


def test_aplicar_recusa_sha256_diferente_para_o_mesmo_arquivo(tmp_path):
    manifesto = _manifesto(tmp_path)
    aplicar_registro(_proposta(tmp_path, [_linha(2007, "microdados")]), manifesto)
    antes = manifesto.read_bytes()
    with pytest.raises(ErroIntegridade, match="outro sha256"):
        aplicar_registro(_proposta(tmp_path, [_linha(2007, "microdados", sha="e" * 64)]), manifesto)
    assert manifesto.read_bytes() == antes


def test_aplicar_no_manifesto_real_so_acrescenta_linhas(tmp_path):
    """As linhas existentes do dados/MANIFEST.csv saem byte a byte iguais depois da regravação."""
    manifesto = tmp_path / "MANIFEST.csv"
    original = MANIFEST_REAL.read_bytes()
    manifesto.write_bytes(original)
    nova = _linha(2007, "microdados")
    aplicar_registro(_proposta(tmp_path, [nova]), manifesto)
    linhas_novas = manifesto.read_bytes().split(b"\n")
    acrescentada = ",".join(nova[c] for c in nova).encode("utf-8")
    assert acrescentada in linhas_novas
    assert b"\n".join(lin for lin in linhas_novas if lin != acrescentada) == original
