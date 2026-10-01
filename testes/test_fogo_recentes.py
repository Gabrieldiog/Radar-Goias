"""Testa a lista das detecções mais recentes.

O painel de queimadas mostrava só a contagem dos sete dias, que é um número
parado. Mas os focos chegam ao longo do dia: o GOES-19 é geoestacionário e
reporta quase de hora em hora, e os polares passam de madrugada e no fim da
tarde. Dezesseis das vinte e quatro horas de um dia têm detecção.

Esta consulta é o que deixa a tela mostrar o que acabou de chegar, com o nome
do município e o satélite que viu.
"""

import pytest

from radar import banco, indicadores

pytestmark = pytest.mark.skipif(not banco.disponivel(), reason="sem banco; suba o docker compose")


@pytest.fixture
def conn():
    with banco.conecta() as c:
        banco.aplica_esquema(c)
        c.execute("truncate foco_queimada, municipio restart identity cascade")
        banco.carrega_municipios(c)
        c.cursor().executemany(
            "insert into foco_queimada"
            " (id, codigo_ibge, detectado_em, satelite, bioma, latitude, longitude, frp)"
            " values (%s, %s, %s, %s, %s, %s, %s, %s)",
            [
                ("a", "5208707", "2026-10-01 10:00:00", "GOES-19", "Cerrado", -16.6, -49.2, 12.0),
                ("b", "5201405", "2026-10-01 12:00:00", "NOAA-20", "Cerrado", -16.8, -49.2, 30.0),
                ("c", "5208707", "2026-10-01 11:00:00", "NOAA-21", "Cerrado", -16.7, -49.3, None),
                ("d", "5200050", "2026-09-30 09:00:00", "AQUA_M-T", "Cerrado", -16.7, -49.4, 5.0),
            ],
        )
        yield c


# Verifica que vem do mais novo para o mais velho, que é como se lê uma lista
# do que acabou de acontecer.
def test_vem_do_mais_novo_para_o_mais_velho(conn):
    assert [f["id"] for f in indicadores.focos_recentes(conn)] == ["b", "c", "a", "d"]


# Verifica que o limite é respeitado, porque a tela mostra poucas linhas.
def test_respeita_o_limite(conn):
    assert len(indicadores.focos_recentes(conn, limite=2)) == 2


# Verifica que o nome do município vem junto. Sem ele a linha mostra um código
# de sete dígitos, que não diz nada a quem está olhando.
def test_traz_o_nome_do_municipio(conn):
    assert indicadores.focos_recentes(conn)[0]["nome"] == "Aparecida de Goiânia"


# Verifica que o satélite vem junto, porque é ele que explica por que às vezes
# chegam duzentos focos de uma vez: foi um polar passando.
def test_traz_o_satelite(conn):
    assert indicadores.focos_recentes(conn)[0]["satelite"] == "NOAA-20"


# Verifica que a potência do fogo vazia não vira zero. Zero diria que o fogo
# não tinha energia nenhuma, e o que houve foi o satélite não medir.
def test_potencia_vazia_continua_nula(conn):
    assert [f for f in indicadores.focos_recentes(conn) if f["id"] == "c"][0]["frp"] is None


# Verifica que a hora da detecção vem, porque é dela que sai o "há tantos
# minutos" da tela.
def test_traz_a_hora_da_deteccao(conn):
    assert indicadores.focos_recentes(conn)[0]["detectado_em"] is not None


# Verifica que banco vazio devolve lista vazia, e não erro.
def test_banco_vazio_nao_quebra(conn):
    conn.execute("truncate foco_queimada")
    assert indicadores.focos_recentes(conn) == []
