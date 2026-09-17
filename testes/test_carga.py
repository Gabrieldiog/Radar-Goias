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


# Verifica que a coleta guarda o endereço de origem, e não o caminho do arquivo
# no disco. A página de procedência mostrou esse bug: reusar o arquivo baixado
# fazia o registro apontar para a máquina de quem rodou, em vez da fonte.
def test_arquivo_reusado_guarda_a_origem_e_nao_o_caminho(conn, tmp_path):
    arquivo = tmp_path / "ja_baixado.zip"
    arquivo.write_bytes(b"x" * 500)
    url = "https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2024.zip"
    # cliente None prova que o arquivo em disco é reusado sem tocar a rede
    coleta = carga._baixa_uma_vez(conn, None, "inep", url, arquivo)
    linha = conn.execute(
        "select fonte, url, status_http, bytes from coleta where id = %s", (coleta,)
    ).fetchone()
    assert linha == ("inep", url, 200, 500)


# Verifica que, quando o arquivo não existe, quem manda é a resposta do servidor.
def test_arquivo_novo_guarda_o_que_o_servidor_respondeu(conn, tmp_path):
    destino = tmp_path / "novo.zip"
    cliente = Cliente(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, content=b"abc")),
        dorme=lambda s: None,
    )
    coleta = carga._baixa_uma_vez(conn, cliente, "inep", "https://x.gov.br/a.zip", destino)
    linha = conn.execute("select url, bytes from coleta where id = %s", (coleta,)).fetchone()
    assert linha == ("https://x.gov.br/a.zip", 3)
    assert destino.read_bytes() == b"abc"
