"""Testa a série mensal de segurança.

A aba "Como mudou" só oferecia dengue e IDEB, e o painel parecia pobre por
isso. Mas a tabela de ocorrências já guarda ano e mês desde a primeira carga:
o que faltava era uma consulta e uma rota. São sete meses de 2026, a única
janela que a Secretaria publicou até agora.
"""

import pytest

from radar import banco, indicadores

pytestmark = pytest.mark.skipif(not banco.disponivel(), reason="sem banco; suba o docker compose")


@pytest.fixture
def conn():
    with banco.conecta() as c:
        banco.aplica_esquema(c)
        c.execute("truncate ocorrencia, municipio restart identity cascade")
        banco.carrega_municipios(c)
        c.cursor().executemany(
            "insert into ocorrencia (codigo_ibge, ano, mes, evento, abrangencia, vitimas)"
            " values (%s, %s, %s, %s, %s, %s)",
            [
                ("5208707", 2026, 1, "Homicídio doloso", "Municipal", 10),
                ("5208707", 2026, 2, "Homicídio doloso", "Municipal", 20),
                ("5201405", 2026, 2, "Homicídio doloso", "Municipal", 5),
                ("5208707", 2026, 3, "Homicídio doloso", "Municipal", 7),
                ("5208707", 2026, 2, "Roubo seguido de morte (latrocínio)", "Municipal", 99),
                # a fonte publica linha para todo município, inclusive com zero
                ("5200050", 2026, 2, "Homicídio doloso", "Municipal", 0),
                ("5200100", 2026, 2, "Homicídio doloso", "Municipal", 0),
            ],
        )
        yield c


# Verifica que a série sai um ponto por mês, em ordem.
def test_um_ponto_por_mes_em_ordem(conn):
    serie = indicadores.serie_homicidio(conn)
    assert [(l["ano"], l["mes"]) for l in serie] == [(2026, 1), (2026, 2), (2026, 3)]


# Verifica que o mês soma as vítimas de todos os municípios.
def test_o_mes_soma_o_estado(conn):
    serie = indicadores.serie_homicidio(conn)
    assert serie[1]["vitimas"] == 25


# Verifica que só homicídio doloso entra. Latrocínio e morte no trânsito são
# outros crimes, e somar tudo mudaria o que o número quer dizer.
def test_so_homicidio_doloso_entra(conn):
    assert indicadores.serie_homicidio(conn)[1]["vitimas"] == 25


# Verifica que dá para pedir a série de um município só.
def test_filtra_por_municipio(conn):
    serie = indicadores.serie_homicidio(conn, "5201405")
    assert len(serie) == 1
    assert serie[0]["vitimas"] == 5


# Verifica que município sem ocorrência devolve série vazia, e não erro.
def test_municipio_sem_ocorrencia_devolve_vazio(conn):
    assert indicadores.serie_homicidio(conn, "5200050") == []


# Verifica que a série traz quantos municípios entraram em cada mês, que é o
# que separa "subiu em todo lugar" de "subiu numa cidade só".
def test_conta_municipios_do_mes(conn):
    assert indicadores.serie_homicidio(conn)[1]["municipios"] == 2


# Verifica que município com linha de zero vítima não entra na contagem. A
# fonte publica uma linha por município por mês mesmo quando não houve nenhum
# homicídio: contar linha em vez de ocorrência dizia que os 246 municípios de
# Goiás tiveram homicídio em janeiro, quando foram 29.
def test_municipio_com_zero_nao_conta_como_municipio_com_homicidio(conn):
    fevereiro = [l for l in indicadores.serie_homicidio(conn) if l["mes"] == 2][0]
    assert fevereiro["municipios"] == 2
    assert fevereiro["vitimas"] == 25


# Verifica que o mês em que ninguém teve homicídio some da série em vez de
# aparecer como um mês de zero municípios.
def test_mes_inteiro_de_zeros_nao_vira_ponto(conn):
    conn.execute(
        "insert into ocorrencia (codigo_ibge, ano, mes, evento, abrangencia, vitimas)"
        " values ('5200050', 2026, 9, 'Homicídio doloso', 'Estadual', 0)"
    )
    assert 9 not in [l["mes"] for l in indicadores.serie_homicidio(conn)]
