import pytest

from radar.municipios import (
    MunicipioDesconhecido,
    Sentinela,
    normaliza_nome,
    para_codigo7,
    por_nome,
    todos,
)


def test_goias_tem_246_municipios():
    assert len(todos()) == 246


def test_codigo_de_6_digitos_vira_7():
    assert para_codigo7("520870") == "5208707"


def test_codigo_de_7_digitos_passa_intacto():
    assert para_codigo7("5208707") == "5208707"


def test_aceita_inteiro_porque_algumas_fontes_mandam_assim():
    assert para_codigo7(520870) == "5208707"


def test_conversao_de_6_para_7_funciona_para_todos_os_246():
    convertidos = {para_codigo7(c[:6]) for c in todos()}
    assert convertidos == set(todos())


def test_codigo_desconhecido_e_recusado():
    with pytest.raises(MunicipioDesconhecido):
        para_codigo7("529999")


def test_sentinela_520000_nao_e_municipio():
    # rotulado "MUNICIPIO IGNORADO - GO" no arquivo de dengue; faz o distinct dar 247
    with pytest.raises(Sentinela):
        para_codigo7("520000")


def test_nome_com_acento_encontra_o_municipio():
    # os casos abaixo saíram do arquivo de manifestações, escritos assim mesmo
    assert por_nome("IPIRANGA DE GOIÁS") == "5210158"


def test_nome_em_caixa_mista_encontra_o_municipio():
    assert por_nome("cidade OCIDENTAL") == "5205497"


def test_nome_sem_apostrofo_encontra_o_municipio():
    assert por_nome("SAO JOAO DALIANCA") == por_nome("São João d'Aliança")


def test_nome_de_municipio_de_outro_estado_e_recusado():
    # aparece uma vez no arquivo de ouvidoria, mas é de MT e MG
    with pytest.raises(MunicipioDesconhecido):
        por_nome("AGUA BOA")


@pytest.mark.parametrize("valor", ["NÃO INFORMADO", "MUNICIPIO IGNORADO - GO"])
def test_sentinelas_de_nome_sao_recusadas(valor):
    with pytest.raises(Sentinela):
        por_nome(valor)


def test_normaliza_nome_tira_acento_caixa_e_espaco():
    assert normaliza_nome("  Águas Lindas de Goiás ") == "AGUAS LINDAS DE GOIAS"


def test_nome_normalizado_e_unico_entre_os_246():
    nomes = {normaliza_nome(n) for n in todos().values()}
    assert len(nomes) == 246
