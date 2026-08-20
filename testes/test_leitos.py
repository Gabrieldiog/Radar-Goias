import json
from pathlib import Path

import httpx
import pytest

from radar.fontes.ckan_go import le_leitos, sql_leitos
from radar.fontes.ms_cnes import busca_municipio
from radar.http import Cliente

LEITOS = Path(__file__).parent / "fixtures" / "ckan_leitos.json"
CNES = Path(__file__).parent / "fixtures" / "ms_cnes.json"


@pytest.fixture
def payload():
    return json.loads(LEITOS.read_text(encoding="utf-8"))


def cliente(resposta):
    return Cliente(transport=httpx.MockTransport(resposta), dorme=lambda s: None)


def test_a_consulta_de_leitos_sai_com_limite():
    assert "LIMIT" in sql_leitos("20/08/2026")


def test_le_as_linhas_do_retrato(payload):
    assert len(le_leitos(payload)) == 105


def test_extrai_o_cnes_do_texto_da_unidade(payload):
    # a unidade vem como "547484/ HCN/ HOSPITAL ESTADUAL DO CENTRO NORTE GOIANO"
    assert le_leitos(payload)[0].cnes == "0547484"


def test_completa_o_cnes_com_zeros_a_esquerda(payload):
    # a fonte come os zeros; sem completar, o cruzamento com o cadastro falha
    assert all(len(l.cnes) == 7 for l in le_leitos(payload))


def test_converte_os_numeros_de_texto_para_inteiro(payload):
    assert sum(l.implantados for l in le_leitos(payload)) == 4259


def test_resolve_o_municipio_pelo_cnes():
    resposta = json.loads(CNES.read_text(encoding="utf-8"))
    c = cliente(lambda req: httpx.Response(200, json=resposta))
    # o Ministério devolve 6 dígitos; guardamos sempre 7
    assert busca_municipio(c, "0547484") == "5221601"  # Uruaçu; o dígito vem da tabela, não de cálculo


def test_cnes_inexistente_devolve_nada():
    c = cliente(lambda req: httpx.Response(404, json={"message": "not found"}))
    assert busca_municipio(c, "9999999") is None
