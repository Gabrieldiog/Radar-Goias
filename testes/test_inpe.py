"""Testa a leitura dos focos de calor do INPE.

É a primeira fonte do projeto que muda ao longo do dia: o INPE publica um CSV
por dia e vai enchendo ele conforme os satélites passam. Por isso o foco tem
identificador próprio, e recarregar o mesmo dia atualiza em vez de duplicar.
"""

import pytest

from radar.fontes.inpe_fogo import (
    SATELITE_DE_REFERENCIA,
    Foco,
    le_focos,
    url_focos,
)

CABECALHO = (
    "id,lat,lon,data_hora_gmt,satelite,municipio,estado,pais,municipio_id,"
    "estado_id,pais_id,numero_dias_sem_chuva,precipitacao,risco_fogo,bioma,frp"
)


def linha(
    id="0b53492b-b7eb-3d86-ab28-3011a33f89a1",
    lat=" -14.122000",
    lon=" -46.328701",
    quando="2026-09-27 01:15:00",
    satelite="NOAA-20",
    municipio="POSSE",
    estado="GOIÁS",
    ibge="5218300",
    bioma="Cerrado",
    frp="12.5",
):
    return (
        f"{id},{lat},{lon},{quando},{satelite},{municipio},{estado},Brasil,"
        f"{ibge},52,33,,,,{bioma},{frp}"
    )


def csv(linhas):
    return "\n".join([CABECALHO, *linhas]) + "\n"


# Verifica que só os focos do estado pedido entram.
def test_le_apenas_o_estado_pedido():
    texto = csv([linha(), linha(id="outro", estado="BAHIA", ibge="2919207")])
    focos = le_focos(texto, "GOIÁS")
    assert len(focos) == 1
    assert focos[0].codigo_ibge == "5218300"


# Verifica que quem decide é a coluna de estado, e não o código do município.
# Os dois filtros se sobrepõem no arquivo real, porque código IBGE é único no
# país, mas se o INPE rotular errado o estado de um foco de Goiás, o projeto tem
# que seguir o rótulo da fonte em vez de adivinhar pelo código.
def test_o_filtro_e_pela_coluna_de_estado():
    texto = csv([linha(ibge="5218300", estado="TOCANTINS")])
    assert le_focos(texto, "GOIÁS") == []
    assert len(le_focos(texto, "TOCANTINS")) == 1


# Verifica que o código do município vem pronto da fonte, com sete dígitos. É a
# mesma chave que o Radar usa, então não há nome para casar.
def test_o_codigo_ibge_vem_pronto():
    assert le_focos(csv([linha()]), "GOIÁS")[0].codigo_ibge == "5218300"


# Verifica que a coordenada com espaço na frente vira número. A fonte escreve
# " -14.122000" com espaço, e float() aceita, mas o teste registra que é assim.
def test_coordenada_com_espaco_vira_numero():
    f = le_focos(csv([linha()]), "GOIÁS")[0]
    assert (round(f.latitude, 3), round(f.longitude, 3)) == (-14.122, -46.329)


# Verifica que a data e hora viram um instante, e não texto.
def test_data_e_hora_viram_instante():
    f = le_focos(csv([linha(quando="2026-09-27 01:15:00")]), "GOIÁS")[0]
    assert (f.detectado_em.year, f.detectado_em.month, f.detectado_em.day) == (2026, 9, 27)
    assert (f.detectado_em.hour, f.detectado_em.minute) == (1, 15)


# Verifica qual é o satélite de referência. O INPE usa ele para a série
# histórica porque a constelação mudou ao longo dos anos, e contar todos os
# satélites de hoje contra os poucos de antigamente não compara nada.
def test_satelite_de_referencia():
    assert SATELITE_DE_REFERENCIA == "AQUA_M-T"


# Verifica que o satélite é guardado. Doze satélites veem o mesmo fogo, então
# sem essa coluna não há como separar detecção de incêndio.
def test_guarda_o_satelite():
    f = le_focos(csv([linha(satelite="NOAA-21")]), "GOIÁS")[0]
    assert f.satelite == "NOAA-21"


# Verifica que a potência do fogo vira número, e que vazio fica nulo em vez de
# zero. Zero seria dizer que o fogo não tinha energia nenhuma.
@pytest.mark.parametrize("valor,espera", [("12.5", 12.5), ("", None), ("   ", None)])
def test_potencia_do_fogo(valor, espera):
    assert le_focos(csv([linha(frp=valor)]), "GOIÁS")[0].frp == espera


# Verifica que o identificador do INPE é preservado. É ele que deixa recarregar
# o mesmo dia sem duplicar, já que o arquivo enche ao longo das horas.
def test_preserva_o_identificador_do_inpe():
    assert le_focos(csv([linha(id="abc-123")]), "GOIÁS")[0].id == "abc-123"


# Verifica que foco repetido no mesmo arquivo entra uma vez só.
def test_foco_repetido_entra_uma_vez():
    assert len(le_focos(csv([linha(id="igual"), linha(id="igual")]), "GOIÁS")) == 1


# Verifica que município fora dos 246 não derruba a leitura inteira.
def test_municipio_desconhecido_nao_quebra():
    texto = csv([linha(ibge="9999999"), linha(id="bom")])
    assert len(le_focos(texto, "GOIÁS")) == 1


# Verifica que linha sem coordenada é descartada, porque foco é um ponto no
# mapa e sem ponto ele não é foco.
def test_foco_sem_coordenada_e_descartado():
    assert le_focos(csv([linha(lat="", lon="")]), "GOIÁS") == []


# Verifica que o bioma é guardado, porque queimada no Cerrado e na Amazônia são
# assuntos diferentes e Goiás tem os dois.
def test_guarda_o_bioma():
    assert le_focos(csv([linha(bioma="Mata Atlântica")]), "GOIÁS")[0].bioma == "Mata Atlântica"


# Verifica o endereço do arquivo diário do INPE.
def test_url_do_dia():
    from datetime import date

    url = url_focos(date(2026, 9, 27))
    assert url.endswith("/focos_diario_br_20260927.csv")
    assert "dataserver-coids.inpe.br" in url


# Verifica que a tupla carrega o que o banco precisa.
def test_forma_da_tupla():
    assert Foco._fields == (
        "id",
        "codigo_ibge",
        "detectado_em",
        "satelite",
        "bioma",
        "latitude",
        "longitude",
        "frp",
    )
