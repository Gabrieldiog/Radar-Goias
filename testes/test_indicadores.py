import pytest

from radar import banco, indicadores
from radar.fontes.ckan_go import Caso
from radar.fontes.ibge import Populacao

pytestmark = pytest.mark.skipif(not banco.disponivel(), reason="sem banco; suba o docker compose")


@pytest.fixture
def conn():
    with banco.conecta() as c:
        banco.aplica_esquema(c)
        c.execute("truncate caso_dengue, populacao, municipio, coleta restart identity cascade")
        banco.carrega_municipios(c)
        banco.grava_populacao(c, [Populacao("5208707", 2025, 1503256, "estimativa")])
        yield c


def test_incidencia_por_100_mil_habitantes(conn):
    banco.grava_casos_dengue(conn, [Caso("5208707", 2025, 15033)])
    linha = indicadores.incidencia_dengue(conn, 2025)[0]
    assert linha["por_100k"] == pytest.approx(1000.0, abs=0.5)


def test_o_resultado_declara_qual_populacao_foi_usada(conn):
    banco.grava_casos_dengue(conn, [Caso("5208707", 2025, 100)])
    linha = indicadores.incidencia_dengue(conn, 2025)[0]
    assert linha["base_populacional"] == "estimativa"
    assert linha["ano_populacao"] == 2025


def test_ano_sem_populacao_usa_a_mais_recente_e_avisa(conn):
    banco.grava_populacao(conn, [Populacao("5208707", 2020, 1000000, "estimativa")])
    banco.grava_casos_dengue(conn, [Caso("5208707", 2015, 500)])
    linha = indicadores.incidencia_dengue(conn, 2015)[0]
    assert linha["ano_populacao"] == 2025
    assert linha["habitantes"] == 1503256


def test_municipio_sem_populacao_fica_de_fora(conn):
    banco.grava_casos_dengue(conn, [Caso("5200050", 2025, 10)])
    assert indicadores.incidencia_dengue(conn, 2025) == []


def test_ordena_do_maior_para_o_menor(conn):
    banco.grava_populacao(conn, [Populacao("5200050", 2025, 22052, "estimativa")])
    banco.grava_casos_dengue(conn, [Caso("5208707", 2025, 100), Caso("5200050", 2025, 100)])
    resultado = indicadores.incidencia_dengue(conn, 2025)
    assert [l["codigo_ibge"] for l in resultado] == ["5200050", "5208707"]


def test_traz_o_nome_do_municipio_para_o_painel(conn):
    banco.grava_casos_dengue(conn, [Caso("5208707", 2025, 100)])
    assert indicadores.incidencia_dengue(conn, 2025)[0]["nome"] == "Goiânia"
