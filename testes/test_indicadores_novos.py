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
            "truncate manifestacao, ubs, leito, caso_dengue, ideb, matricula, despesa_funcao, populacao, municipio, coleta"
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


# Verifica a série de dengue por ano, que alimenta o gráfico de evolução.
def test_serie_de_dengue_por_ano(conn):
    from radar.fontes.ckan_go import Caso

    banco.grava_casos_dengue(
        conn,
        [
            Caso("5208707", 2024, 40000),
            Caso("5208707", 2025, 38000),
            Caso("5200050", 2024, 500),
        ],
    )
    serie = indicadores.serie_dengue(conn)
    assert [l["ano"] for l in serie] == [2024, 2025]
    assert serie[0]["casos"] == 40500
    assert serie[0]["municipios"] == 2


# Verifica que dá para pedir a série de um município só.
def test_serie_de_um_municipio(conn):
    from radar.fontes.ckan_go import Caso

    banco.grava_casos_dengue(
        conn, [Caso("5208707", 2024, 40000), Caso("5200050", 2024, 500)]
    )
    serie = indicadores.serie_dengue(conn, "5208707")
    assert serie[0]["casos"] == 40000


def educacao(conn, empenhado, alunos, dependencia="municipal", escolas=1):
    banco.grava_despesas(conn, [("5208707", 2025, "educacao", empenhado, empenhado)])
    banco.grava_matriculas(conn, [("5208707", 2024, dependencia, escolas, alunos)])


# Verifica a conta: empenhado dividido por aluno da rede municipal.
def test_gasto_por_aluno_da_rede_municipal(conn):
    educacao(conn, 1000000, 100)
    assert indicadores.gasto_por_aluno(conn)[0]["por_aluno"] == pytest.approx(10000.0)


# Verifica que o aluno da rede estadual não entra no denominador do município.
# Se entrasse, o município pareceria gastar menos da metade do que gasta.
def test_aluno_de_outra_rede_nao_entra_no_denominador(conn):
    educacao(conn, 1000000, 100)
    banco.grava_matriculas(conn, [("5208707", 2024, "estadual", 9, 900)])
    linhas = indicadores.gasto_por_aluno(conn)
    assert len(linhas) == 1
    assert linhas[0]["por_aluno"] == pytest.approx(10000.0)


# Verifica que o resultado declara de que ano é cada metade do cruzamento, já
# que a despesa é de um exercício e a matrícula é de outro.
def test_declara_o_exercicio_e_o_ano_do_censo(conn):
    educacao(conn, 500000, 50)
    linha = indicadores.gasto_por_aluno(conn)[0]
    assert (linha["exercicio"], linha["ano_censo"]) == (2025, 2024)


# Verifica que município com despesa mas sem matrícula fica de fora, porque não
# dá para dividir por um denominador que não existe.
def test_municipio_sem_matricula_fica_de_fora(conn):
    banco.grava_despesas(conn, [("5208707", 2025, "educacao", 900000, 900000)])
    assert indicadores.gasto_por_aluno(conn) == []


# Verifica que o censo mais recente é o que vale, e não o primeiro que existir.
def test_usa_o_censo_mais_recente(conn):
    educacao(conn, 1000000, 500)
    banco.grava_matriculas(conn, [("5208707", 2023, "municipal", 1, 100)])
    linha = indicadores.gasto_por_aluno(conn)[0]
    assert (linha["ano_censo"], linha["alunos"]) == (2024, 500)


def nota(conn, codigo="5208707", ano=2025, etapa="anos_iniciais", rede="municipal",
         ideb=6.6, meta=6.1, rendimento=0.99, valor=6.66):
    banco.grava_ideb(conn, [(codigo, ano, etapa, rede, ideb, meta, rendimento, valor)])


# Verifica que o recorte pedido é o que volta. Anos iniciais na rede municipal
# é o único em que o município manda: 241 dos 246 têm rede ali.
def test_ideb_filtra_etapa_e_rede(conn):
    nota(conn)
    nota(conn, etapa="ensino_medio", rede="estadual", ideb=4.9)
    linhas = indicadores.ideb_por_municipio(conn)
    assert len(linhas) == 1
    assert (linhas[0]["etapa"], linhas[0]["rede"], linhas[0]["ideb"]) == (
        "anos_iniciais", "municipal", 6.6)


# Verifica que sem ano pedido vale o mais recente, e não o primeiro da série.
def test_ideb_usa_o_ano_mais_recente(conn):
    nota(conn, ano=2005, ideb=3.9)
    nota(conn, ano=2025, ideb=6.6)
    assert indicadores.ideb_por_municipio(conn)[0]["ano"] == 2025


# Verifica que bater a meta é calculado, e não chutado pelo painel.
def test_diz_se_bateu_a_meta(conn):
    nota(conn, ideb=6.6, meta=6.1)
    nota(conn, codigo="5200050", ideb=5.0, meta=6.1)
    por_codigo = {l["codigo_ibge"]: l["bateu_meta"] for l in indicadores.ideb_por_municipio(conn)}
    assert por_codigo == {"5208707": True, "5200050": False}


# Verifica que ano sem meta publicada não vira meta batida nem meta perdida. O
# INEP só projetou metas até 2021, e inventar uma seria mentir.
def test_ano_sem_meta_nao_decide_nada(conn):
    nota(conn, ano=2025, meta=None)
    assert indicadores.ideb_por_municipio(conn)[0]["bateu_meta"] is None


# Verifica que a série traz as duas metades da nota, que é o que permite dizer
# se o município subiu por aprovar mais ou por aprender mais.
def test_serie_traz_fluxo_e_aprendizagem(conn):
    nota(conn, ano=2005, ideb=3.9, rendimento=0.85, valor=4.55)
    nota(conn, ano=2025, ideb=6.6, rendimento=0.99, valor=6.66)
    serie = indicadores.serie_ideb(conn, "5208707")
    assert [(l["ano"], l["rendimento"], l["nota"]) for l in serie] == [
        (2005, 0.85, 4.55), (2025, 0.99, 6.66)]


# Verifica que sem município a série é a média do estado, e diz de quantos.
def test_serie_sem_municipio_e_o_estado(conn):
    nota(conn, codigo="5208707", ideb=6.0)
    nota(conn, codigo="5200050", ideb=7.0)
    serie = indicadores.serie_ideb(conn)
    assert (serie[0]["ideb"], serie[0]["municipios"]) == (6.5, 2)


# Verifica que cada conjunto de dados aponta para a requisição que o trouxe, com
# o endereço e o status que o servidor devolveu. É a promessa de procedência.
def test_frescor_liga_o_dado_a_requisicao(conn):
    coleta = banco.grava_coleta(conn, "ckan-go", "https://exemplo.gov.br/x", 200, 4096)
    banco.grava_casos_dengue(conn, [("5208707", 2025, 100)], coleta)
    linha = [l for l in indicadores.frescor(conn) if l["tabela"] == "Casos de dengue"][0]
    assert (linha["linhas"], linha["fonte"], linha["status_http"], linha["bytes"]) == (
        1, "ckan-go", 200, 4096)
    assert linha["url"] == "https://exemplo.gov.br/x"


# Verifica que conjunto vazio não aparece na lista. Tabela sem linha nenhuma não
# tem procedência para mostrar, e listar ela como zero confunde com dado velho.
def test_frescor_omite_conjunto_vazio(conn):
    coleta = banco.grava_coleta(conn, "ckan-go", "https://exemplo.gov.br/x", 200, 10)
    banco.grava_casos_dengue(conn, [("5208707", 2025, 100)], coleta)
    tabelas = {l["tabela"] for l in indicadores.frescor(conn)}
    assert "Casos de dengue" in tabelas
    assert "IDEB" not in tabelas


# Verifica que o resumo por fonte conta as coletas e marca as recusadas. Foi um
# 403 do firewall do portal que ensinou o projeto a guardar o status.
def test_por_fonte_conta_coletas_e_recusas(conn):
    banco.grava_coleta(conn, "ckan-go", "https://a.gov.br/1", 200, 100)
    banco.grava_coleta(conn, "ckan-go", "https://a.gov.br/2", 403, 0)
    banco.grava_coleta(conn, "ibge", "https://b.gov.br/1", 200, 50)
    por_fonte = {l["fonte"]: l for l in indicadores.por_fonte(conn)}
    assert (por_fonte["ckan-go"]["coletas"], por_fonte["ckan-go"]["recusadas"]) == (2, 1)
    assert (por_fonte["ibge"]["coletas"], por_fonte["ibge"]["recusadas"]) == (1, 0)
    assert por_fonte["ckan-go"]["bytes"] == 100



# Verifica que o IDEB não some quando o município não tem população cadastrada.
# A nota não se divide por habitante nenhum, então exigir população seria perder
# município por um motivo que não tem a ver com o indicador.
def test_ideb_aparece_mesmo_sem_populacao(conn):
    nota(conn, codigo="5200050", ideb=7.0)
    linhas = indicadores.ideb_por_municipio(conn)
    por_codigo = {l["codigo_ibge"]: l for l in linhas}
    assert "5200050" in por_codigo
    assert por_codigo["5200050"]["habitantes"] is None
