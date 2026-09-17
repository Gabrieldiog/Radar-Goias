import pytest
from fastapi.testclient import TestClient

from radar import api, banco
from radar.fontes.ckan_go import Caso
from radar.fontes.ibge import Populacao

pytestmark = pytest.mark.skipif(not banco.disponivel(), reason="sem banco; suba o docker compose")

CHAVE = "chave-de-teste"
OUTRA = "chave-de-outro-cliente"


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("RADAR_CHAVES", f"{CHAVE},{OUTRA}")
    with banco.conecta() as c:
        banco.aplica_esquema(c)
        c.execute(
            "truncate caso_dengue, matricula, despesa_funcao, populacao, municipio, coleta"
            " restart identity cascade"
        )
        banco.carrega_municipios(c)
        banco.grava_populacao(c, [Populacao("5208707", 2025, 1503256, "estimativa")])
        banco.grava_casos_dengue(c, [Caso("5208707", 2025, 38232)])
    return TestClient(api.cria_app())


def test_saude_responde_sem_chave(cliente):
    r = cliente.get("/saude")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_dado_sem_chave_e_recusado(cliente):
    assert cliente.get("/v1/municipios").status_code == 401


def test_chave_errada_e_recusada(cliente):
    assert cliente.get("/v1/municipios", headers={"x-api-key": "nao-e"}).status_code == 401


def test_chave_no_cabecalho_funciona(cliente):
    r = cliente.get("/v1/municipios", headers={"x-api-key": CHAVE})
    assert r.status_code == 200
    assert r.json()["total"] == 246


def test_chave_na_query_tambem_funciona(cliente):
    assert cliente.get(f"/v1/municipios?chave={CHAVE}").status_code == 200


def test_municipio_por_codigo(cliente):
    r = cliente.get(f"/v1/municipios/5208707?chave={CHAVE}")
    assert r.json()["nome"] == "Goiânia"


def test_municipio_inexistente_da_404(cliente):
    assert cliente.get(f"/v1/municipios/9999999?chave={CHAVE}").status_code == 404


def test_catalogo_lista_o_indicador(cliente):
    r = cliente.get(f"/v1/indicadores?chave={CHAVE}")
    ids = {i["id"] for i in r.json()["dados"]}
    assert ids == {
        "incidencia-dengue",
        "leitos-rede-estadual",
        "ubs-por-habitante",
        "ouvidoria-por-orgao",
        "gasto-saude-por-habitante",
        "gasto-educacao-por-habitante",
        "gasto-educacao-por-aluno",
        "ideb-anos-iniciais",
        "homicidio-por-100mil",
    }


def test_indicador_devolve_valor_e_procedencia(cliente):
    r = cliente.get(f"/v1/indicadores/incidencia-dengue?ano=2025&chave={CHAVE}")
    corpo = r.json()
    assert corpo["total"] == 1
    assert corpo["dados"][0]["por_100k"] == pytest.approx(2543.5, abs=1)
    assert corpo["meta"]["base_populacional"] == "estimativa"
    assert corpo["meta"]["fontes"]


def test_indicador_desconhecido_da_404(cliente):
    assert cliente.get(f"/v1/indicadores/nao-existe?chave={CHAVE}").status_code == 404


def test_filtra_por_municipio(cliente):
    r = cliente.get(f"/v1/indicadores/incidencia-dengue?ano=2025&municipio=5200050&chave={CHAVE}")
    assert r.json()["total"] == 0


def test_estourar_o_limite_devolve_429(cliente):
    app = api.cria_app(limite="3/minute")
    c = TestClient(app)
    codigos = [c.get(f"/v1/municipios?chave={CHAVE}").status_code for _ in range(5)]
    assert 429 in codigos


def test_cada_chave_tem_seu_proprio_balde(cliente):
    c = TestClient(api.cria_app(limite="2/minute"))
    for _ in range(2):
        assert c.get(f"/v1/municipios?chave={CHAVE}").status_code == 200
    assert c.get(f"/v1/municipios?chave={CHAVE}").status_code == 429
    assert c.get(f"/v1/municipios?chave={OUTRA}").status_code == 200


# Verifica que a API serve o mapa para o painel desenhar.
def test_malha_tem_os_246_municipios(cliente):
    r = cliente.get(f"/v1/malha?chave={CHAVE}")
    assert r.status_code == 200
    assert len(r.json()["features"]) == 246


# Verifica que o mapa é servido com cache, porque a geometria não muda.
def test_malha_pede_para_o_navegador_guardar(cliente):
    r = cliente.get(f"/v1/malha?chave={CHAVE}")
    assert "max-age" in r.headers.get("cache-control", "")


# Verifica que a ficha do município traz os indicadores dele.
def test_ficha_do_municipio_traz_os_indicadores(cliente):
    r = cliente.get(f"/v1/municipios/5208707?chave={CHAVE}")
    corpo = r.json()
    assert corpo["nome"] == "Goiânia"
    assert corpo["indicadores"]["incidencia-dengue"] == pytest.approx(2543.2, abs=1)
    # sem leito cadastrado o campo existe, mas vem vazio em vez de sumir
    assert corpo["indicadores"]["leitos-rede-estadual"] is None


# Verifica que o catálogo diz se o indicador é por município ou por órgão,
# porque o painel precisa saber se desenha mapa ou tabela.
def test_catalogo_declara_a_dimensao(cliente):
    r = cliente.get(f"/v1/indicadores?chave={CHAVE}")
    dims = {i["id"]: i["dimensao"] for i in r.json()["dados"]}
    assert dims["incidencia-dengue"] == "municipio"
    assert dims["ouvidoria-por-orgao"] == "orgao"


# Verifica que o indicador por órgão responde sem quebrar na parte de município.
def test_indicador_por_orgao_responde(cliente):
    r = cliente.get(f"/v1/indicadores/ouvidoria-por-orgao?chave={CHAVE}")
    assert r.status_code == 200
    assert r.json()["meta"]["dimensao"] == "orgao"


# Verifica que a ficha do município acompanha o catálogo sozinha. Antes os
# indicadores estavam fixos no código e a ficha ficava para trás a cada um novo.
def test_ficha_cobre_todos_os_indicadores_por_municipio(cliente):
    catalogo = cliente.get(f"/v1/indicadores?chave={CHAVE}").json()["dados"]
    esperados = {i["id"] for i in catalogo if i["dimensao"] == "municipio"}
    ficha = cliente.get(f"/v1/municipios/5208707?chave={CHAVE}").json()
    assert set(ficha["indicadores"]) == esperados


# Verifica que a série de dengue responde, para o gráfico de evolução.
def test_serie_de_dengue_responde(cliente):
    r = cliente.get(f"/v1/series/dengue?chave={CHAVE}")
    assert r.status_code == 200
    assert r.json()["dados"][0]["ano"] == 2025


# Verifica que gasto por aluno não cai na rota do gasto por habitante. Os dois
# começam com "gasto-educacao" e a ordem do despacho é o que os separa.
def test_gasto_por_aluno_nao_e_confundido_com_por_habitante(cliente):
    with banco.conecta() as c:
        banco.grava_despesas(c, [("5208707", 2025, "educacao", 1000000, 1000000)])
        banco.grava_matriculas(c, [("5208707", 2024, "municipal", 3, 100)])
    r = cliente.get(f"/v1/indicadores/gasto-educacao-por-aluno?chave={CHAVE}")
    assert r.status_code == 200
    linha = r.json()["dados"][0]
    assert linha["por_aluno"] == pytest.approx(10000.0)
    assert "por_habitante" not in linha
    assert "download.inep.gov.br" in r.json()["meta"]["fontes"]


# Verifica que a ficha diz em que posição o município está, e de quantos.
def test_ficha_traz_a_posicao_no_ranking(cliente):
    with banco.conecta() as c:
        banco.grava_casos_dengue(c, [Caso("5200050", 2025, 10)])
        banco.grava_populacao(c, [Populacao("5200050", 2025, 10000, "estimativa")])
    ficha = cliente.get(f"/v1/municipios/5208707?chave={CHAVE}").json()
    assert ficha["posicoes"]["incidencia-dengue"] == {"posicao": 1, "de": 2}


# Verifica que indicador sem valor para aquele município não vira último lugar.
# Sem dado é diferente de estar no fim da fila.
def test_sem_dado_nao_vira_ultima_posicao(cliente):
    ficha = cliente.get(f"/v1/municipios/5208707?chave={CHAVE}").json()
    assert ficha["indicadores"]["leitos-rede-estadual"] is None
    assert ficha["posicoes"]["leitos-rede-estadual"] is None


# Verifica direto na função: linha sem valor sai da contagem e não empurra os
# outros para trás. O teste de ponta a ponta não pegava isso, porque o indicador
# que eu usei lá não devolve linha com valor nulo.
def test_ranking_ignora_linha_sem_valor():
    linhas = [
        {"codigo_ibge": "1", "v": 10.0},
        {"codigo_ibge": "2", "v": None},
        {"codigo_ibge": "3", "v": 5.0},
    ]
    assert api._ranking(linhas, "1", "v") == {"posicao": 1, "de": 2}
    assert api._ranking(linhas, "3", "v") == {"posicao": 2, "de": 2}
    assert api._ranking(linhas, "2", "v") is None


# Verifica que a comparação devolve os dois municípios, na ordem pedida.
def test_comparar_devolve_os_dois_na_ordem(cliente):
    with banco.conecta() as c:
        banco.grava_casos_dengue(c, [Caso("5200050", 2025, 10)])
        banco.grava_populacao(c, [Populacao("5200050", 2025, 10000, "estimativa")])
    r = cliente.get(f"/v1/comparar?a=5200050&b=5208707&chave={CHAVE}")
    assert r.status_code == 200
    assert [d["nome"] for d in r.json()["dados"]] == ["Abadia de Goiás", "Goiânia"]


# Verifica que cada lado traz valor e posição, que é o que a tela compara.
def test_comparar_traz_valor_e_posicao_dos_dois(cliente):
    with banco.conecta() as c:
        banco.grava_casos_dengue(c, [Caso("5200050", 2025, 10)])
        banco.grava_populacao(c, [Populacao("5200050", 2025, 10000, "estimativa")])
    a, b = cliente.get(f"/v1/comparar?a=5208707&b=5200050&chave={CHAVE}").json()["dados"]
    assert a["indicadores"]["incidencia-dengue"] > b["indicadores"]["incidencia-dengue"]
    assert (a["posicoes"]["incidencia-dengue"]["posicao"],
            b["posicoes"]["incidencia-dengue"]["posicao"]) == (1, 2)


# Verifica que comparar um município com ele mesmo é recusado, em vez de
# devolver duas colunas iguais que não comparam nada.
def test_comparar_o_mesmo_municipio_e_recusado(cliente):
    r = cliente.get(f"/v1/comparar?a=5208707&b=5208707&chave={CHAVE}")
    assert r.status_code == 400


# Verifica que município inexistente devolve 404, e não uma coluna vazia.
def test_comparar_com_municipio_inexistente(cliente):
    r = cliente.get(f"/v1/comparar?a=5208707&b=9999999&chave={CHAVE}")
    assert r.status_code == 404


# Verifica que a comparação precisa de chave, como todo dado da API.
def test_comparar_sem_chave_e_recusado(cliente):
    assert cliente.get("/v1/comparar?a=5208707&b=5200050").status_code == 401


# Verifica que a ficha de um município continua igual depois de passar a
# compartilhar o código com a comparação.
def test_ficha_de_um_continua_igual(cliente):
    ficha = cliente.get(f"/v1/municipios/5208707?chave={CHAVE}").json()
    assert ficha["nome"] == "Goiânia"
    assert set(ficha) >= {"codigo_ibge", "habitantes", "indicadores", "posicoes"}


# Verifica o contrato que o painel depende: todo indicador de município devolve
# habitantes junto do valor. Sem isso a ficha quebra ao clicar num município, e
# foi assim que o IDEB entrou quebrado sem ninguém notar.
def test_todo_indicador_de_municipio_devolve_habitantes(cliente):
    with banco.conecta() as c:
        banco.grava_ubs(c, [("5208707", 150)])
        banco.grava_leitos(c, [("5208707", "0000001", "UTI", "2026-01-01", 10, 5)])
        banco.grava_despesas(c, [("5208707", 2025, "educacao", 1000000, 1000000)])
        banco.grava_despesas(c, [("5208707", 2025, "saude", 1000000, 1000000)])
        banco.grava_matriculas(c, [("5208707", 2024, "municipal", 3, 100)])
        banco.grava_ideb(c, [("5208707", 2025, "anos_iniciais", "municipal", 6.6, 6.1, 0.99, 6.66)])
        banco.grava_ocorrencias(c, [("5208707", 2026, 1, "Homicídio doloso", "Estadual", 4)])
    for id, meta in api.CATALOGO.items():
        if meta["dimensao"] != "municipio":
            continue
        dados = cliente.get(f"/v1/indicadores/{id}?chave={CHAVE}").json()["dados"]
        assert dados, f"{id} não devolveu linha nenhuma no cenário do teste"
        goiania = [l for l in dados if l["codigo_ibge"] == "5208707"]
        assert goiania, f"{id} perdeu o município do cenário"
        assert goiania[0].get("habitantes"), f"{id} não devolve habitantes"
        assert goiania[0].get("ano_populacao"), f"{id} não diz de que ano é a população"
