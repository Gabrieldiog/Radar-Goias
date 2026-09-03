import pytest

from radar import banco, indicadores
from radar.fontes.ckan_go import Manifestacao, Ubs
from radar.fontes.ibge import Populacao

pytestmark = pytest.mark.skipif(not banco.disponivel(), reason="sem banco; suba o docker compose")


@pytest.fixture
def conn():
    with banco.conecta() as c:
        banco.aplica_esquema(c)
        c.execute(
            "truncate manifestacao, ubs, leito, caso_dengue, populacao, municipio, coleta"
            " restart identity cascade"
        )
        banco.carrega_municipios(c)
        banco.grava_populacao(c, [Populacao("5208707", 2025, 1500000, "estimativa")])
        yield c


# Verifica a conta: unidades divididas por habitantes, vezes 10 mil.
def test_ubs_por_10_mil_habitantes(conn):
    banco.grava_ubs(conn, [Ubs("5208707", 150)])
    linha = indicadores.ubs_por_10mil(conn)[0]
    assert linha["por_10mil"] == pytest.approx(1.0, abs=0.01)


# Verifica que município sem população fica de fora, porque não dá para dividir.
def test_ubs_sem_populacao_fica_de_fora(conn):
    banco.grava_ubs(conn, [Ubs("5200050", 10)])
    assert indicadores.ubs_por_10mil(conn) == []


# Verifica que a taxa de resposta conta só o que já foi finalizado.
def test_ouvidoria_taxa_de_finalizacao(conn):
    banco.grava_manifestacoes(
        conn,
        [
            Manifestacao(2026, "SEDUC", "Reclamação", "Fechada", 5, 30),
            Manifestacao(2026, "SEDUC", "Reclamação", "Aberta", 0, 70),
        ],
    )
    linha = indicadores.ouvidoria_por_orgao(conn, 2026)[0]
    assert linha["total"] == 100
    assert linha["finalizadas"] == 30
    assert linha["taxa_finalizacao"] == pytest.approx(30.0)


# Verifica a taxa de resposta dentro do prazo legal de 30 dias.
def test_ouvidoria_taxa_dentro_do_prazo(conn):
    banco.grava_manifestacoes(
        conn,
        [
            Manifestacao(2026, "SEDUC", "Reclamação", "Fechada", 10, 75),
            Manifestacao(2026, "SEDUC", "Reclamação", "Fechada", 40, 25),
        ],
    )
    linha = indicadores.ouvidoria_por_orgao(conn, 2026)[0]
    assert linha["no_prazo"] == 75
    assert linha["taxa_no_prazo"] == pytest.approx(75.0)


# Verifica que o prazo pode ser mudado, porque a LAI tem prazo diferente.
def test_ouvidoria_aceita_outro_prazo(conn):
    banco.grava_manifestacoes(
        conn,
        [
            Manifestacao(2026, "SEDUC", "LAI", "Fechada", 25, 50),
            Manifestacao(2026, "SEDUC", "LAI", "Fechada", 5, 50),
        ],
    )
    linha = indicadores.ouvidoria_por_orgao(conn, 2026, prazo=20)[0]
    assert linha["no_prazo"] == 50


# Verifica que o tempo médio pondera pela quantidade, e não é média de médias.
def test_ouvidoria_tempo_medio_e_ponderado(conn):
    banco.grava_manifestacoes(
        conn,
        [
            Manifestacao(2026, "SEDUC", "Reclamação", "Fechada", 10, 90),
            Manifestacao(2026, "SEDUC", "Reclamação", "Fechada", 100, 10),
        ],
    )
    linha = indicadores.ouvidoria_por_orgao(conn, 2026)[0]
    assert linha["tempo_medio"] == pytest.approx(19.0, abs=0.1)


# Verifica que o órgão que só tem manifestação aberta não some do ranking.
def test_orgao_sem_nenhuma_finalizada_aparece_com_taxa_zero(conn):
    banco.grava_manifestacoes(conn, [Manifestacao(2026, "AGR", "Denúncia", "Aberta", 0, 5)])
    linha = [l for l in indicadores.ouvidoria_por_orgao(conn, 2026) if l["orgao"] == "AGR"][0]
    assert linha["finalizadas"] == 0
    assert linha["taxa_no_prazo"] is None


# Verifica que, sem ano informado, o indicador usa o ano mais recente que existe.
# Fixar 2025 no código deixaria o painel vazio quando a fonte virasse o ano.
def test_ouvidoria_sem_ano_usa_o_mais_recente(conn):
    banco.grava_manifestacoes(
        conn,
        [
            Manifestacao(2025, "SEDUC", "Reclamação", "Fechada", 5, 10),
            Manifestacao(2026, "SEDUC", "Reclamação", "Fechada", 5, 20),
        ],
    )
    assert indicadores.ouvidoria_por_orgao(conn)[0]["total"] == 20


# Verifica a conta do gasto por habitante.
def test_gasto_per_capita(conn):
    from radar.fontes.siconfi import Despesa

    banco.grava_despesas(conn, [Despesa("5208707", 2025, "saude", 1500000000.0, 1400000000.0)])
    linha = indicadores.despesa_per_capita(conn, "saude")[0]
    assert linha["por_habitante"] == pytest.approx(1000.0, abs=1)


# Verifica que o indicador usa o empenhado, e informa também o pago, porque os
# dois números contam histórias diferentes sobre o mesmo orçamento.
def test_traz_empenhado_e_pago(conn):
    from radar.fontes.siconfi import Despesa

    banco.grava_despesas(conn, [Despesa("5208707", 2025, "educacao", 300.0, 200.0)])
    linha = indicadores.despesa_per_capita(conn, "educacao")[0]
    assert float(linha["empenhado"]) == 300.0
    assert float(linha["pago"]) == 200.0


# Verifica que cada função é consultada separadamente.
def test_cada_funcao_e_separada(conn):
    from radar.fontes.siconfi import Despesa

    banco.grava_despesas(
        conn,
        [
            Despesa("5208707", 2025, "saude", 100.0, 100.0),
            Despesa("5208707", 2025, "educacao", 200.0, 200.0),
        ],
    )
    assert len(indicadores.despesa_per_capita(conn, "saude")) == 1
    assert float(indicadores.despesa_per_capita(conn, "educacao")[0]["empenhado"]) == 200.0


# Verifica que, sem exercício informado, usa o mais recente que existe.
def test_sem_exercicio_usa_o_mais_recente(conn):
    from radar.fontes.siconfi import Despesa

    banco.grava_despesas(
        conn,
        [
            Despesa("5208707", 2024, "saude", 100.0, 100.0),
            Despesa("5208707", 2025, "saude", 999.0, 999.0),
        ],
    )
    assert float(indicadores.despesa_per_capita(conn, "saude")[0]["empenhado"]) == 999.0


# Verifica a taxa por 100 mil habitantes, somando os meses do ano.
def test_ocorrencias_por_100mil(conn):
    from radar.fontes.sinesp import Ocorrencia

    banco.grava_ocorrencias(
        conn,
        [
            Ocorrencia("5208707", 2026, 1, "Homicídio doloso", "Estadual", 10),
            Ocorrencia("5208707", 2026, 2, "Homicídio doloso", "Estadual", 5),
        ],
    )
    linha = indicadores.ocorrencias_por_100mil(conn, "Homicídio doloso")[0]
    assert linha["vitimas"] == 15
    assert linha["por_100mil"] == pytest.approx(1.0, abs=0.01)


# Verifica que evento diferente não é somado junto.
def test_cada_evento_e_separado(conn):
    from radar.fontes.sinesp import Ocorrencia

    banco.grava_ocorrencias(
        conn,
        [
            Ocorrencia("5208707", 2026, 1, "Homicídio doloso", "Estadual", 10),
            Ocorrencia("5208707", 2026, 1, "Suicídio", "Estadual", 40),
        ],
    )
    assert indicadores.ocorrencias_por_100mil(conn, "Suicídio")[0]["vitimas"] == 40


# Verifica que abrangências diferentes não são somadas. Trânsito aparece duas
# vezes, uma pela polícia estadual e outra pela federal, e somar mistura fontes.
def test_abrangencias_nao_se_somam(conn):
    from radar.fontes.sinesp import Ocorrencia

    banco.grava_ocorrencias(
        conn,
        [
            Ocorrencia("5208707", 2026, 1, "Mortes no trânsito", "Estadual", 30),
            Ocorrencia("5208707", 2026, 1, "Mortes no trânsito", "Polícia Rodoviária Federal", 12),
        ],
    )
    r = indicadores.ocorrencias_por_100mil(conn, "Mortes no trânsito")
    assert {l["abrangencia"]: l["vitimas"] for l in r} == {
        "Estadual": 30,
        "Polícia Rodoviária Federal": 12,
    }
