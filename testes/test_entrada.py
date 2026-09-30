"""Testa o que a API aceita como código de município na URL.

Um teste dinâmico com entrada malformada achou isto: `/v1/municipios/%00`
respondia 500. O byte nulo atravessava a rota inteira e chegava ao Postgres,
que recusa NUL em campo de texto, e a exceção subia sem tratamento. O corpo da
resposta não vazava rastro de pilha, mas 500 é o servidor dizendo que quebrou,
e ele não quebrou: a entrada é que estava errada.

Conferir o formato antes de consultar mata a classe inteira de uma vez, e não
só o byte nulo.
"""

import pytest

from radar.api import codigo_valido


# Verifica que o código de Goiás de sete dígitos passa. Todo município do
# estado começa com 52, que é o código da unidade federativa no IBGE.
@pytest.mark.parametrize("codigo", ["5208707", "5201405", "5200050", "5222302"])
def test_codigo_de_goias_passa(codigo):
    assert codigo_valido(codigo) is True


# Verifica que o byte nulo é recusado antes de chegar ao banco.
def test_byte_nulo_e_recusado():
    assert codigo_valido("\x00") is False
    assert codigo_valido("5208707\x00") is False


# Verifica as outras formas de entrada torta que o fuzzing produziu.
@pytest.mark.parametrize(
    "codigo",
    [
        "",
        " ",
        "520870",
        "52087077",
        "abcdefg",
        "5208707 ",
        " 5208707",
        "-5208707",
        "52087.7",
        "a" * 5000,
        "<script>alert(1)</script>",
        "5208707 OR 1=1",
    ],
)
def test_entrada_torta_e_recusada(codigo):
    assert codigo_valido(codigo) is False


# Verifica que dígito de outra escrita não passa por dígito. O \d do Python
# casa numeral de qualquer alfabeto, então "52" seguido de algarismos árabes
# orientais atravessaria uma expressão escrita sem cuidado.
def test_digito_de_outro_alfabeto_nao_passa():
    assert codigo_valido("52٠١٢٣٤") is False
    assert codigo_valido("５２０８７０７") is False


# Verifica que município de outro estado é recusado. O Radar só tem Goiás, e
# 3550308 é São Paulo: responder 404 é mais honesto do que consultar à toa.
def test_municipio_de_outro_estado_e_recusado():
    assert codigo_valido("3550308") is False
    assert codigo_valido("5300108") is False


# Verifica que o valor nulo não explode a checagem.
def test_none_nao_quebra():
    assert codigo_valido(None) is False
