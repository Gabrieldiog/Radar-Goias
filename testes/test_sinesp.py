"""Testa a leitura das ocorrências criminais do SINESP, do Ministério da Justiça.

A planilha real tem 206 MB descomprimidos, então os testes montam uma pequena
com a mesma estrutura, em vez de carregar um arquivo enorme no repositório.
"""

from datetime import datetime

import openpyxl
import pytest

from radar.fontes.sinesp import MUNICIPALIZADOS, le_planilha

COLUNAS = [
    "uf", "municipio", "evento", "data_referencia", "agente", "arma",
    "faixa_etaria", "feminino", "masculino", "nao_informado",
    "total_vitima", "total", "total_peso", "abrangencia",
]


def planilha(tmp_path, linhas):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "2026"
    ws.append(COLUNAS)
    for l in linhas:
        ws.append(l)
    caminho = tmp_path / "sinesp.xlsx"
    wb.save(caminho)
    return caminho


def linha(uf="GO", municipio="GOIÂNIA", evento="Homicídio doloso", mes=1,
          vitimas=6, total=None, abrangencia="Estadual"):
    return [uf, municipio, evento, datetime(2026, mes, 1), None, None, None,
            0, 5, 1, vitimas, total, None, abrangencia]


# Verifica que só as ocorrências de Goiás entram.
def test_le_apenas_o_estado_pedido(tmp_path):
    caminho = planilha(tmp_path, [linha(), linha(uf="SP", municipio="SANTOS")])
    assert len(le_planilha(caminho, "GO")) == 1


# Verifica que o nome do município vira o código IBGE de 7 dígitos.
def test_converte_o_nome_em_codigo(tmp_path):
    caminho = planilha(tmp_path, [linha()])
    assert le_planilha(caminho, "GO")[0].codigo_ibge == "5208707"


# Verifica que o nome com acento da fonte encontra o município.
def test_nome_com_acento_da_fonte_e_resolvido(tmp_path):
    caminho = planilha(tmp_path, [linha(municipio="ABADIA DE GOIÁS")])
    assert le_planilha(caminho, "GO")[0].codigo_ibge == "5200050"


# Verifica que o valor sentinela da fonte é descartado. Ele existe porque 20 dos
# 31 eventos só são publicados no total do estado, sem município.
def test_municipio_nao_informado_e_descartado(tmp_path):
    caminho = planilha(tmp_path, [linha(municipio="NÃO INFORMADO")])
    assert le_planilha(caminho, "GO") == []


# Verifica que evento que a fonte não municipaliza é ignorado.
def test_evento_sem_recorte_municipal_e_ignorado(tmp_path):
    caminho = planilha(tmp_path, [linha(evento="Estupro")])
    assert le_planilha(caminho, "GO") == []
    assert "Estupro" not in MUNICIPALIZADOS


# Verifica que o mês vem da data da fonte.
def test_extrai_o_mes_e_o_ano(tmp_path):
    caminho = planilha(tmp_path, [linha(mes=7)])
    o = le_planilha(caminho, "GO")[0]
    assert (o.ano, o.mes) == (2026, 7)


# Verifica que, quando total_vitima vem vazio, usa a coluna total. A fonte
# preenche uma ou a outra, nunca as duas.
def test_usa_total_quando_nao_ha_total_vitima(tmp_path):
    caminho = planilha(tmp_path, [linha(vitimas=None, total=9)])
    assert le_planilha(caminho, "GO")[0].vitimas == 9


# Verifica que linha sem vítima nenhuma não é descartada, porque zero homicídio
# num mês é informação, e não ausência de dado.
def test_zero_vitima_continua_valendo(tmp_path):
    caminho = planilha(tmp_path, [linha(vitimas=0)])
    assert le_planilha(caminho, "GO")[0].vitimas == 0


# Verifica que a abrangência é guardada. Trânsito aparece com dois eventos de
# fontes diferentes, e somar os dois misturaria universos.
def test_guarda_a_abrangencia(tmp_path):
    caminho = planilha(tmp_path, [linha(abrangencia="Polícia Rodoviária Federal")])
    assert le_planilha(caminho, "GO")[0].abrangencia == "Polícia Rodoviária Federal"


# Verifica que município de fora de Goiás na coluna não derruba a carga inteira.
def test_municipio_desconhecido_nao_quebra_a_leitura(tmp_path):
    caminho = planilha(tmp_path, [linha(municipio="CIDADE QUE NAO EXISTE"), linha()])
    assert len(le_planilha(caminho, "GO")) == 1
