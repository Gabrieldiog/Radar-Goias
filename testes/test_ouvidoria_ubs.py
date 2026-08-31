import json
from pathlib import Path

import httpx
import pytest

from radar.fontes.ckan_go import le_manifestacoes, le_ubs, sql_manifestacoes, sql_ubs
from radar.http import Cliente

OUV = Path(__file__).parent / "fixtures" / "ckan_ouvidoria.json"
UBS = Path(__file__).parent / "fixtures" / "ckan_ubs.json"


@pytest.fixture
def ouvidoria():
    return json.loads(OUV.read_text(encoding="utf-8"))


@pytest.fixture
def ubs():
    return json.loads(UBS.read_text(encoding="utf-8"))


# Verifica que as duas consultas saem com limite de linhas.
def test_as_consultas_saem_com_limite():
    assert "LIMIT" in sql_ubs()
    assert "LIMIT" in sql_manifestacoes(2026)


# Verifica que as UBS vêm para os 246 municípios.
def test_ubs_cobre_os_246_municipios(ubs):
    assert len(le_ubs(ubs)) == 246


# Verifica o total de unidades básicas do estado.
def test_ubs_soma_1558_unidades(ubs):
    assert sum(u.unidades for u in le_ubs(ubs)) == 1558


# Verifica que o código de 6 dígitos da fonte vira o de 7 do projeto.
def test_ubs_converte_a_chave_do_municipio(ubs):
    codigos = {u.codigo_ibge for u in le_ubs(ubs)}
    assert all(len(c) == 7 for c in codigos)


# Verifica que a leitura da ouvidoria não perde nem inventa manifestação.
def test_ouvidoria_soma_as_30459_manifestacoes(ouvidoria):
    assert sum(m.total for m in le_manifestacoes(ouvidoria, 2026)) == 30459


# Verifica que os dias vêm como número, e não como o texto "34.0" da fonte.
# Quem não tem prazo registrado fica vazio, o que é diferente de zero.
def test_ouvidoria_converte_dias_para_inteiro(ouvidoria):
    dias = [m.dias for m in le_manifestacoes(ouvidoria, 2026)]
    assert all(d is None or isinstance(d, int) for d in dias)
    assert sum(1 for d in dias if d is None) == 9


# Verifica que o ano fica registrado, porque a fonte tem um arquivo por ano.
def test_ouvidoria_registra_o_ano(ouvidoria):
    assert {m.ano for m in le_manifestacoes(ouvidoria, 2026)} == {2026}


# Verifica que os 51 órgãos aparecem.
def test_ouvidoria_traz_os_51_orgaos(ouvidoria):
    assert len({m.orgao for m in le_manifestacoes(ouvidoria, 2026)}) == 51


# Verifica que a resposta recusada do portal não passa como dado.
def test_resposta_recusada_nao_passa():
    from radar.fontes.ckan_go import ConsultaRecusada

    with pytest.raises(ConsultaRecusada):
        le_ubs({"success": False, "error": {"message": "x"}})


# Verifica que dias vazio na fonte fica vazio, e não vira zero. Tratar como zero
# faria a manifestação parecer respondida na hora e baixaria a média.
def test_dias_vazio_nao_vira_zero():
    payload = {
        "success": True,
        "result": {
            "records": [
                {"orgao": "X", "tipo": "Reclamação", "status": "Aberta", "dias": None, "total": "2"}
            ]
        },
    }
    assert le_manifestacoes(payload, 2026)[0].dias is None


# Verifica que nenhuma manifestação se perde por colisão de chave.
def test_nenhuma_manifestacao_se_perde(ouvidoria):
    linhas = le_manifestacoes(ouvidoria, 2026)
    chaves = {(m.ano, m.orgao, m.tipo, m.status, m.dias) for m in linhas}
    assert len(chaves) == len(linhas)
