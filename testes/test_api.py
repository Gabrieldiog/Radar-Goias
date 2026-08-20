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
        c.execute("truncate caso_dengue, populacao, municipio, coleta restart identity cascade")
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
    assert ids == {"incidencia-dengue", "leitos-rede-estadual"}


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
