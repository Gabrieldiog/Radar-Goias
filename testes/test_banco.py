import pytest

from radar import banco
from radar.fontes.ibge import Populacao

pytestmark = pytest.mark.skipif(not banco.disponivel(), reason="sem banco; suba o docker compose")


@pytest.fixture
def conn():
    with banco.conecta() as c:
        banco.aplica_esquema(c)
        c.execute("truncate populacao, matricula, municipio restart identity cascade")
        yield c
        c.rollback()


def test_carrega_os_246_municipios(conn):
    assert banco.carrega_municipios(conn) == 246
    assert conn.execute("select count(*) from municipio").fetchone()[0] == 246


def test_carregar_duas_vezes_nao_duplica(conn):
    banco.carrega_municipios(conn)
    banco.carrega_municipios(conn)
    assert conn.execute("select count(*) from municipio").fetchone()[0] == 246


def test_populacao_precisa_de_municipio_existente(conn):
    banco.carrega_municipios(conn)
    with pytest.raises(Exception):
        banco.grava_populacao(conn, [Populacao("9999999", 2025, 100, "estimativa")])


def test_grava_populacao_e_le_de_volta(conn):
    banco.carrega_municipios(conn)
    banco.grava_populacao(conn, [Populacao("5208707", 2025, 1503256, "estimativa")])
    linha = conn.execute("select habitantes, base from populacao").fetchone()
    assert linha == (1503256, "estimativa")


def test_as_duas_bases_populacionais_convivem(conn):
    banco.carrega_municipios(conn)
    banco.grava_populacao(
        conn,
        [
            Populacao("5208707", 2022, 1437366, "censo"),
            Populacao("5208707", 2025, 1503256, "estimativa"),
        ],
    )
    assert conn.execute("select count(*) from populacao").fetchone()[0] == 2


def test_recarregar_populacao_atualiza_em_vez_de_duplicar(conn):
    banco.carrega_municipios(conn)
    for valor in (1500000, 1503256):
        banco.grava_populacao(conn, [Populacao("5208707", 2025, valor, "estimativa")])
    assert conn.execute("select habitantes from populacao").fetchall() == [(1503256,)]


def test_matricula_atualiza_em_vez_de_duplicar(conn):
    banco.carrega_municipios(conn)
    banco.grava_matriculas(conn, [("5208707", 2024, "municipal", 306, 102505)])
    banco.grava_matriculas(conn, [("5208707", 2024, "municipal", 306, 102600)])
    assert conn.execute("select count(*), max(alunos) from matricula").fetchone() == (1, 102600)


def test_redes_do_mesmo_municipio_convivem(conn):
    banco.carrega_municipios(conn)
    banco.grava_matriculas(
        conn,
        [("5208707", 2024, "municipal", 306, 102505), ("5208707", 2024, "estadual", 105, 62277)],
    )
    assert conn.execute("select count(*) from matricula").fetchone()[0] == 2
