"""Testa a leitura das contas municipais no SICONFI, do Tesouro Nacional."""

import json
from pathlib import Path

import httpx
import pytest

from radar.fontes.siconfi import (
    FUNCOES,
    RespostaSemDados,
    busca_despesas,
    le_despesas,
    url_dca,
)
from radar.http import Cliente

FIXTURE = Path(__file__).parent / "fixtures" / "siconfi_dca.json"


@pytest.fixture
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def cliente(resposta):
    return Cliente(transport=httpx.MockTransport(resposta), dorme=lambda s: None)


# Verifica que o endereço leva o município e o ano pedidos.
def test_url_carrega_municipio_e_exercicio():
    u = url_dca("5208707", 2025)
    assert "id_ente=5208707" in u
    assert "an_exercicio=2025" in u


# Verifica que só as três funções que interessam são guardadas.
def test_le_apenas_as_funcoes_escolhidas(payload):
    funcoes = {d.funcao for d in le_despesas(payload, "5208707")}
    assert funcoes == set(FUNCOES.values())


# Verifica o valor real de saúde de Goiânia em 2025.
def test_valor_de_saude_de_goiania(payload):
    empenhado = {
        d.funcao: d.empenhado for d in le_despesas(payload, "5208707")
    }
    assert empenhado["saude"] == pytest.approx(2123805780.42, abs=0.01)


# Verifica que guardamos empenhado e pago, que são números diferentes.
def test_guarda_empenhado_e_pago(payload):
    saude = [d for d in le_despesas(payload, "5208707") if d.funcao == "saude"][0]
    assert saude.pago == pytest.approx(2089005643.09, abs=0.01)
    assert saude.pago < saude.empenhado


# Verifica que subfunção não é confundida com função. A fonte traz
# "12 - Educação" e também "12.365 - Educação Infantil" no mesmo campo, então
# casar por pedaço do nome contaria educação quatro vezes.
def test_subfuncao_nao_entra_como_funcao(payload):
    contas_da_fonte = {i["conta"] for i in payload["items"]}
    assert "12.365 - Educação Infantil" in contas_da_fonte, "a fonte mudou de formato"

    educacao = [d for d in le_despesas(payload, "5208707") if d.funcao == "educacao"]
    assert len(educacao) == 1
    # o valor tem que ser o da função, não a soma dela com as subfunções
    assert educacao[0].empenhado == pytest.approx(1994550414.32, abs=0.01)


# Verifica que resposta vazia vira erro. O Tesouro responde 200 com zero linhas
# quando o parâmetro está errado, o que passaria despercebido.
def test_resposta_vazia_e_recusada():
    with pytest.raises(RespostaSemDados):
        le_despesas({"items": []}, "5208707")


# Verifica que município sem entrega no ano é recusado com o código na mensagem.
def test_erro_diz_qual_municipio_falhou():
    with pytest.raises(RespostaSemDados, match="5200050"):
        le_despesas({"items": []}, "5200050")


# Verifica que a busca devolve os dados e a procedência.
def test_busca_devolve_despesas_e_procedencia(payload):
    despesas, resposta = busca_despesas(
        cliente(lambda req: httpx.Response(200, json=payload)), "5208707", 2025
    )
    assert len(despesas) == 3
    assert resposta.status == 200
