import httpx
import pytest

from radar.http import UA, Cliente


class Relogio:
    def __init__(self):
        self.agora = 0.0

    def __call__(self):
        return self.agora

    def dorme(self, segundos):
        self.agora += segundos


@pytest.fixture
def relogio():
    return Relogio()


def cliente(relogio, resposta=None):
    resposta = resposta or (lambda req: httpx.Response(200, json={"ok": True}))
    return Cliente(
        transport=httpx.MockTransport(resposta),
        relogio=relogio,
        dorme=relogio.dorme,
    )


def test_devolve_payload_status_e_tamanho(relogio):
    r = cliente(relogio).json("https://exemplo.gov.br/a")
    assert r.payload == {"ok": True}
    assert r.status == 200
    assert r.bytes > 0


def test_duas_chamadas_ao_mesmo_dominio_esperam_um_segundo(relogio):
    c = cliente(relogio)
    c.json("https://exemplo.gov.br/a")
    c.json("https://exemplo.gov.br/b")
    assert relogio.agora == pytest.approx(1.0)


def test_dominios_diferentes_nao_esperam(relogio):
    c = cliente(relogio)
    c.json("https://um.gov.br/a")
    c.json("https://dois.gov.br/a")
    assert relogio.agora == 0.0


def test_nao_espera_se_o_tempo_ja_passou(relogio):
    c = cliente(relogio)
    c.json("https://exemplo.gov.br/a")
    relogio.agora += 5
    c.json("https://exemplo.gov.br/b")
    assert relogio.agora == pytest.approx(5.0)


def test_manda_user_agent_identificavel(relogio):
    vistos = []

    def espia(req):
        vistos.append(req.headers.get("user-agent"))
        return httpx.Response(200, json=[])

    cliente(relogio, espia).json("https://exemplo.gov.br/a")
    assert vistos == [UA]
    assert "contato" in UA


def test_erro_da_fonte_nao_passa_como_dado(relogio):
    def falha(req):
        return httpx.Response(500, text="pane")

    with pytest.raises(httpx.HTTPStatusError):
        cliente(relogio, falha).json("https://exemplo.gov.br/a")


def test_timeout_pode_ser_esticado_por_fonte_lenta(relogio):
    vistos = []

    def espia(req):
        vistos.append(req.extensions.get("timeout", {}).get("read"))
        return httpx.Response(200, json=[])

    cliente(relogio, espia).json("https://exemplo.gov.br/a", timeout=120.0)
    assert vistos == [120.0]


class Quedas:
    """Derruba a conexão as primeiras vezes e responde na seguinte, como o INEP."""

    def __init__(self, quantas):
        self.restantes = quantas
        self.chamadas = 0

    def __call__(self, req):
        self.chamadas += 1
        if self.restantes:
            self.restantes -= 1
            raise httpx.ConnectError("connection reset by peer")
        return httpx.Response(200, content=b"conteudo")


def test_arquivo_repete_quando_a_conexao_cai(relogio, tmp_path):
    queda = Quedas(2)
    c = cliente(relogio, queda)
    r = c.arquivo("https://download.inep.gov.br/a.zip", tmp_path / "a.zip", tentativas=4)
    assert (r.status, r.bytes, queda.chamadas) == (200, 8, 3)


def test_arquivo_desiste_depois_da_ultima_tentativa(relogio, tmp_path):
    queda = Quedas(9)
    with pytest.raises(httpx.ConnectError):
        cliente(relogio, queda).arquivo("https://x.gov.br/a.zip", tmp_path / "a.zip", tentativas=3)
    assert queda.chamadas == 3


def test_arquivo_nao_repete_por_padrao(relogio, tmp_path):
    queda = Quedas(1)
    with pytest.raises(httpx.ConnectError):
        cliente(relogio, queda).arquivo("https://x.gov.br/a.zip", tmp_path / "a.zip")
    assert queda.chamadas == 1
