"""Testa a posição que a ficha de um município mostra.

91 municípios têm exatamente 0 km até a porta noturna, porque a unidade que
atende à noite fica dentro deles. A posição vinha do lugar na lista, então
esses 91 recebiam 91 posições diferentes: a tela do comparador dizia que
Aparecida de Goiânia era 163ª e Goiânia era 191ª, com o mesmo 0 escrito do lado.
Quem lê conclui que uma está à frente da outra, e não está.
"""

from radar.api import _ranking


def linhas(*valores, campo="km"):
    return [
        {"codigo_ibge": f"52{i:05d}", campo: v} for i, v in enumerate(valores, 1)
    ]


def posicao(dados, indice, campo="km"):
    r = _ranking(dados, dados[indice]["codigo_ibge"], campo)
    return r["posicao"]


# Verifica que valores diferentes continuam recebendo posições diferentes.
def test_sem_empate_a_posicao_e_a_ordem():
    d = linhas(30.0, 20.0, 10.0)
    assert [posicao(d, i) for i in range(3)] == [1, 2, 3]


# Verifica que quem empata divide a mesma posição.
def test_empate_divide_a_posicao():
    d = linhas(30.0, 20.0, 20.0, 10.0)
    assert [posicao(d, i) for i in range(4)] == [1, 2, 2, 4]


# Verifica o caso que motivou o conserto: um bloco grande empatado no começo.
def test_bloco_empatado_no_comeco():
    d = linhas(0.0, 0.0, 0.0, 5.0, 9.0)
    assert [posicao(d, i) for i in range(5)] == [1, 1, 1, 4, 5]


# Verifica que a posição seguinte pula o tamanho do empate, e não anda um só.
# Dizer que o próximo é o 3º quando dois estão empatados em 1º inventaria um
# município à frente dele.
def test_a_posicao_apos_o_empate_pula_o_bloco():
    d = linhas(7.0, 7.0, 7.0, 1.0)
    assert posicao(d, 3) == 4


# Verifica que o total conta só quem tem o dado.
def test_o_total_ignora_quem_nao_tem_o_dado():
    d = linhas(9.0, None, 4.0)
    assert _ranking(d, d[0]["codigo_ibge"], "km")["de"] == 2


# Verifica que município sem o dado não recebe posição nenhuma.
def test_sem_dado_nao_tem_posicao():
    d = linhas(9.0, None)
    assert _ranking(d, d[1]["codigo_ibge"], "km") is None


# Verifica que município fora da lista não inventa posição.
def test_municipio_fora_da_lista():
    assert _ranking(linhas(9.0), "5299999", "km") is None
