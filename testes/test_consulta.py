import pytest

from radar.consulta import SqlSemLimite, exige_limite


def test_consulta_com_limite_passa():
    sql = 'SELECT "dmun_codibge" FROM "abc" LIMIT 250'
    assert exige_limite(sql) == sql


def test_limite_em_caixa_baixa_tambem_vale():
    assert exige_limite('SELECT 1 FROM "abc" limit 10')


def test_consulta_sem_limite_e_barrada_antes_de_sair_da_maquina():
    with pytest.raises(SqlSemLimite):
        exige_limite('SELECT "dmun_codibge", COUNT(*) FROM "abc" GROUP BY "dmun_codibge"')


def test_erro_explica_que_o_firewall_bloqueia():
    with pytest.raises(SqlSemLimite, match="firewall"):
        exige_limite("SELECT 1")


def test_palavra_limit_dentro_de_texto_nao_conta_como_limite():
    with pytest.raises(SqlSemLimite):
        exige_limite("SELECT 'sem limite aqui' FROM \"abc\"")


def test_limite_precisa_de_numero():
    with pytest.raises(SqlSemLimite):
        exige_limite('SELECT 1 FROM "abc" LIMIT')
