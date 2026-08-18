import json
from pathlib import Path

import httpx
import pytest

from radar.consulta import SqlSemLimite
from radar.fontes.ckan_go import Bloqueado, ConsultaRecusada, busca_casos, le_casos, sql_casos
from radar.http import Cliente

FIXTURE = Path(__file__).parent / "fixtures" / "ckan_dengue.json"


@pytest.fixture
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def cliente(resposta):
    return Cliente(transport=httpx.MockTransport(resposta), dorme=lambda s: None)


def test_a_consulta_sempre_sai_com_limite():
    assert "LIMIT" in sql_casos()


def test_limite_invalido_nao_produz_consulta():
    with pytest.raises(SqlSemLimite):
        sql_casos(limite=0)


def test_descarta_o_sentinela_e_sobram_os_246(payload):
    assert len({c.codigo_ibge for c in le_casos(payload)}) == 246


def test_converte_a_chave_de_6_para_7_digitos(payload):
    casos = {(c.codigo_ibge, c.ano): c.casos for c in le_casos(payload)}
    assert casos[("5208707", 2025)] == 38232


def test_erro_logico_do_ckan_nao_passa_como_dado():
    with pytest.raises(ConsultaRecusada):
        le_casos({"success": False, "error": {"message": "recurso nao encontrado"}})


def test_bloqueio_do_firewall_vira_erro_que_se_explica():
    def waf(req):
        return httpx.Response(403, html="<h1>Acesso Negado</h1>")

    with pytest.raises(Bloqueado, match="firewall"):
        busca_casos(cliente(waf))


def test_outros_erros_http_nao_viram_bloqueio():
    def pane(req):
        return httpx.Response(500, text="pane")

    with pytest.raises(httpx.HTTPStatusError):
        busca_casos(cliente(pane))


def test_busca_devolve_casos_e_procedencia(payload):
    casos, resposta = busca_casos(cliente(lambda req: httpx.Response(200, json=payload)))
    assert len(casos) == 4114  # 4119 da fonte, menos 5 linhas do sentinela
    assert resposta.status == 200
    assert "datastore_search_sql" in resposta.url
