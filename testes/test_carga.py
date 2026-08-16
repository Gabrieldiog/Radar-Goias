import json
from pathlib import Path

import httpx
import pytest

from radar import banco, carga
from radar.http import Cliente

pytestmark = pytest.mark.skipif(not banco.disponivel(), reason="sem banco; suba o docker compose")

FIXTURE = Path(__file__).parent / "fixtures" / "ibge_populacao_go.json"


@pytest.fixture
def conn():
    with banco.conecta() as c:
        banco.aplica_esquema(c)
        c.execute("truncate populacao, municipio, coleta restart identity cascade")
        yield c


@pytest.fixture
def cliente():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return Cliente(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=payload)),
        dorme=lambda s: None,
    )


def test_carga_completa_deixa_o_banco_pronto(conn, cliente):
    resumo = carga.executa(conn, cliente)
    assert resumo == {"municipios": 246, "populacao": 246}


def test_registra_a_procedencia_da_coleta(conn, cliente):
    carga.executa(conn, cliente)
    fonte, url, status = conn.execute("select fonte, url, status_http from coleta").fetchone()
    assert fonte == "ibge"
    assert url.startswith("https://servicodados.ibge.gov.br")
    assert status == 200


def test_populacao_aponta_para_a_coleta_que_a_trouxe(conn, cliente):
    carga.executa(conn, cliente)
    orfas = conn.execute("select count(*) from populacao where coleta_id is null").fetchone()[0]
    assert orfas == 0


def test_rodar_duas_vezes_nao_duplica(conn, cliente):
    carga.executa(conn, cliente)
    carga.executa(conn, cliente)
    assert conn.execute("select count(*) from populacao").fetchone()[0] == 246
    assert conn.execute("select count(*) from coleta").fetchone()[0] == 2


def test_fonte_incompleta_nao_grava_nada(conn):
    meio = json.loads(FIXTURE.read_text(encoding="utf-8"))
    meio[0]["resultados"][0]["series"] = meio[0]["resultados"][0]["series"][:100]
    c = Cliente(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=meio)),
        dorme=lambda s: None,
    )
    with pytest.raises(Exception):
        carga.executa(conn, c)
    assert conn.execute("select count(*) from populacao").fetchone()[0] == 0
