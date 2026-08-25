import pytest

from radar.malha import geojson


def test_traz_os_246_municipios():
    assert len(geojson()["features"]) == 246


def test_cada_area_tem_o_codigo_ibge_de_7_digitos():
    codigos = [f["properties"]["codarea"] for f in geojson()["features"]]
    assert all(len(c) == 7 for c in codigos)


def test_os_codigos_do_mapa_batem_com_os_do_projeto():
    from radar.municipios import todos

    codigos = {f["properties"]["codarea"] for f in geojson()["features"]}
    assert codigos == set(todos())


def test_e_um_geojson_valido():
    d = geojson()
    assert d["type"] == "FeatureCollection"
    assert all(f["geometry"]["type"] in ("Polygon", "MultiPolygon") for f in d["features"])


def test_le_do_disco_uma_vez_so():
    assert geojson() is geojson()
