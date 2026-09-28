"""Testa a leitura das unidades de saúde, uma por uma.

Até aqui o projeto lia só uma coluna deste arquivo, a contagem de unidades por
município. As outras vinte e sete iam pro lixo, inclusive coordenada, turno de
atendimento e região de saúde. Estes testes cobrem o que passou a ser lido.

A fonte traz uma linha por unidade e por dia da semana, então a mesma unidade
aparece até sete vezes, e juntar isso numa linha só é metade do trabalho.
"""

import pytest

from radar.fontes.ckan_go import (
    NOTURNO_EXATO,
    NOTURNO_PREFIXO,
    Unidade,
    atende_a_noite,
    le_unidades,
    sql_unidades,
)


def registro(**campos):
    base = {
        "cnes": "2878453",
        "ibge": "520870",
        "nome": "CS NOVO HORIZONTE",
        "tipo": "CENTRO DE SAUDE/UNIDADE BASICA",
        "turno": "ATENDIMENTOS NOS TURNOS DA MANHA E A TARDE",
        "sempre_aberto": "N",
        "dia": "Segunda-Feira",
        "latitude": "-16.72038505",
        "longitude": "-49.31872129",
        "regiao": "Central",
        "macrorregiao": "Centro Oeste",
    }
    return {**base, **campos}


def payload(registros):
    return {"success": True, "result": {"records": registros}}


# Verifica que a mesma unidade em vários dias vira uma linha só.
def test_junta_os_dias_numa_unidade(tmp_path):
    p = payload([registro(dia="Segunda-Feira"), registro(dia="Terça-Feira")])
    unidades = le_unidades(p)
    assert len(unidades) == 1
    assert unidades[0].dias == 2


# Verifica que o código de município de 6 dígitos vira o de 7.
def test_converte_o_codigo_do_municipio():
    assert le_unidades(payload([registro()]))[0].codigo_ibge == "5208707"


# Verifica que a coordenada vira número, porque a fonte manda texto.
def test_coordenada_vira_numero():
    u = le_unidades(payload([registro()]))[0]
    assert (round(u.latitude, 5), round(u.longitude, 5)) == (-16.72039, -49.31872)


# Verifica que unidade sem coordenada não quebra a leitura nem vira zero. Zero
# seria um ponto no Atlântico, na costa da África.
@pytest.mark.parametrize("valor", ["", None, "NAO INFORMADO"])
def test_coordenada_vazia_fica_nula(valor):
    u = le_unidades(payload([registro(latitude=valor, longitude=valor)]))[0]
    assert u.latitude is None and u.longitude is None


# Verifica os dois turnos que contam como noturno, com o texto exato da fonte.
def test_turnos_que_contam_como_noite():
    assert NOTURNO_EXATO == "ATENDIMENTO NOS TURNOS DA MANHA, TARDE E NOITE"
    assert NOTURNO_PREFIXO == "ATENDIMENTO CONTINUO DE 24 HORAS"


# Verifica o texto do plantão exatamente como a fonte escreve hoje, com espaço
# depois da vírgula. Escrever sem o espaço fez as 38 unidades de 24 horas serem
# contadas como diurnas, e este teste existe para isso não voltar.
def test_plantao_com_a_pontuacao_real_da_fonte():
    real = (
        "ATENDIMENTO CONTINUO DE 24 HORAS/DIA"
        " (PLANTAO:INCLUI SABADOS, DOMINGOS E FERIADOS)"
    )
    assert atende_a_noite(real) is True


# Verifica que a pontuação do parêntese não decide nada: o que vale é o começo.
@pytest.mark.parametrize(
    "variacao",
    [
        "ATENDIMENTO CONTINUO DE 24 HORAS/DIA (PLANTAO:INCLUI SABADOS,DOMINGOS E FERIADOS)",
        "ATENDIMENTO CONTINUO DE 24 HORAS/DIA (PLANTAO:INCLUI SABADOS, DOMINGOS E FERIADOS)",
        "ATENDIMENTO CONTINUO DE 24 HORAS/DIA",
    ],
)
def test_plantao_casa_por_prefixo(variacao):
    assert atende_a_noite(variacao) is True


# Verifica que o turno vira uma marca de atende à noite.
@pytest.mark.parametrize(
    "turno,espera",
    [
        ("ATENDIMENTO NOS TURNOS DA MANHA, TARDE E NOITE", True),
        ("ATENDIMENTOS NOS TURNOS DA MANHA E A TARDE", False),
        ("ATENDIMENTO SOMENTE PELA MANHA", False),
        ("ATENDIMENTO COM TURNOS INTERMITENTES", False),
    ],
)
def test_marca_quem_atende_a_noite(turno, espera):
    assert le_unidades(payload([registro(turno=turno)]))[0].noite is espera


# Verifica que a unidade de plantão de 24 horas conta como noturna, mesmo o
# nome do turno sendo longo e diferente dos outros.
def test_plantao_de_24_horas_conta_como_noite():
    vinte_e_quatro = (
        "ATENDIMENTO CONTINUO DE 24 HORAS/DIA"
        " (PLANTAO:INCLUI SABADOS, DOMINGOS E FERIADOS)"
    )
    u = le_unidades(payload([registro(turno=vinte_e_quatro, sempre_aberto="S", dia="")]))[0]
    assert u.noite is True and u.sempre_aberto is True


# Verifica que unidade sempre aberta de verdade conta como fim de semana. A
# fonte não escreve sábado nem domingo para ela: simplesmente não gera linha de
# dia nenhum, e ler isso como "não abre" inverteria o sentido.
def test_sempre_aberta_de_verdade_conta_como_fim_de_semana():
    vinte_e_quatro = (
        "ATENDIMENTO CONTINUO DE 24 HORAS/DIA"
        " (PLANTAO:INCLUI SABADOS, DOMINGOS E FERIADOS)"
    )
    u = le_unidades(payload([registro(sempre_aberto="S", turno=vinte_e_quatro, dia="")]))[0]
    assert u.fim_de_semana is True
    assert u.dias == 7


# Verifica o conflito de cadastro: 29 unidades dizem "sempre aberto" e, na
# mesma linha, dizem atender só de manhã e à tarde. Os dois campos brigam, e
# acreditar só no sinalizador marcava as 29 como abertas no sábado, inflando a
# conta de 116 para 145. Quando eles se contradizem, vale o turno.
def test_sempre_aberto_que_briga_com_o_turno_nao_vira_fim_de_semana():
    u = le_unidades(
        payload([
            registro(
                sempre_aberto="S",
                turno="ATENDIMENTOS NOS TURNOS DA MANHA E A TARDE",
                dia="",
            )
        ])
    )[0]
    assert u.fim_de_semana is False
    assert u.dias == 0


# Verifica que o sábado de verdade continua valendo mesmo com o conflito, porque
# aí existe evidência e não só um sinalizador.
def test_sabado_real_vence_o_conflito():
    p = payload([
        registro(sempre_aberto="S", turno="ATENDIMENTOS NOS TURNOS DA MANHA E A TARDE", dia="Sábado"),
    ])
    assert le_unidades(p)[0].fim_de_semana is True


# Verifica que sábado ou domingo na lista de dias marca fim de semana.
@pytest.mark.parametrize("dia", ["Sábado", "Domingo"])
def test_sabado_ou_domingo_marca_fim_de_semana(dia):
    p = payload([registro(dia="Segunda-Feira"), registro(dia=dia)])
    assert le_unidades(p)[0].fim_de_semana is True


# Verifica que só dia útil não marca fim de semana.
def test_so_dia_util_nao_marca_fim_de_semana():
    p = payload([registro(dia="Segunda-Feira"), registro(dia="Sexta-Feira")])
    assert le_unidades(p)[0].fim_de_semana is False


# Verifica que a região de saúde é guardada. São 18 em Goiás, e elas dão um
# nível de comparação que o painel não tinha: região contra região.
def test_guarda_regiao_e_macrorregiao():
    u = le_unidades(payload([registro()]))[0]
    assert (u.regiao_saude, u.macrorregiao) == ("Central", "Centro Oeste")


# Verifica que o valor sentinela de município é descartado sem derrubar o resto.
def test_municipio_sentinela_e_descartado():
    p = payload([registro(ibge="520000"), registro()])
    assert len(le_unidades(p)) == 1


# Verifica que município fora dos 246 não derruba a carga inteira.
def test_municipio_desconhecido_nao_quebra():
    p = payload([registro(ibge="999999"), registro()])
    assert len(le_unidades(p)) == 1


# Verifica que a consulta pede as colunas que o indicador vai precisar e que
# ela sai com LIMIT, porque o firewall do portal recusa consulta sem ele.
def test_sql_pede_as_colunas_e_tem_limite():
    sql = sql_unidades()
    for coluna in (
        "codigo_cnes",
        "turno_atendimento",
        "estabelecimento_sempre_aberto",
        "latitude",
        "longitude",
        "regiao_saude",
        "dia_da_semana",
    ):
        assert coluna in sql, coluna
    assert sql.rstrip().lower().endswith("limit 9000")


# Verifica que a tupla carrega tudo que o banco vai guardar.
def test_forma_da_tupla():
    assert Unidade._fields == (
        "cnes",
        "codigo_ibge",
        "nome",
        "tipo",
        "turno",
        "noite",
        "sempre_aberto",
        "fim_de_semana",
        "dias",
        "latitude",
        "longitude",
        "regiao_saude",
        "macrorregiao",
    )
