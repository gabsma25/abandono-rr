"""A etapa 01 roda num clone limpo, sem dados/origem/ (issue #6).

dados/origem/ fica fora do git (regra 2). Sem a pasta, nenhum ano tem zip, e todo ano entra pelo cache
versionado em dados/cache/tx_rend/, o mesmo caminho de qualquer ano sem zip.
"""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("etapa01", RAIZ / "src" / "estendida" / "01_tx_rend_bruto.py")
E01 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E01)


def test_sem_a_pasta_de_origem_nao_ha_zips_nem_erro(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(E01, "INDICADORES", tmp_path / "nao_existe" / "indicadores")
    assert E01.mapear_zips_escola() == {}
    assert "entram pelo cache" in capsys.readouterr().out


def test_o_cache_versionado_cobre_todos_os_anos():
    faltam = [a for a in E01.ANOS if not (E01.CACHE / f"{a}.parquet").exists()]
    assert not faltam, f"sem zip e sem cache, estes anos ficariam de fora: {faltam}"
