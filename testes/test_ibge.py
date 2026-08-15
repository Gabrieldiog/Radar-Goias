import json
from pathlib import Path

import pytest

from radar.fontes.ibge import RespostaVazia, le_populacao

FIXTURE = Path(__file__).parent / "fixtures" / "ibge_populacao_go.json"


@pytest.fixture
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_le_os_246_municipios(payload):
    assert len(le_populacao(payload)) == 246


def test_devolve_codigo_de_7_digitos_e_habitantes(payload):
    linhas = {l.codigo_ibge: l for l in le_populacao(payload)}
    assert linhas["5208707"].habitantes == 1503256


def test_soma_de_goias_bate_com_a_estimativa_publicada(payload):
    assert sum(l.habitantes for l in le_populacao(payload)) == 7423629


def test_ano_vem_da_resposta_nao_do_relogio(payload):
    assert {l.ano for l in le_populacao(payload)} == {2025}


def test_base_populacional_fica_declarada(payload):
    # estimativa e censo divergem 5%; o indicador precisa dizer qual usou
    assert {l.base for l in le_populacao(payload)} == {"estimativa"}


def test_nao_usa_o_nome_do_ibge_como_chave(payload):
    # o IBGE devolve "Goiânia - GO", sufixado; casar por nome quebraria
    assert all(not l.codigo_ibge.endswith("GO") for l in le_populacao(payload))


def test_resposta_sem_municipios_e_recusada():
    with pytest.raises(RespostaVazia):
        le_populacao([{"resultados": [{"series": []}]}])


def test_resposta_incompleta_e_recusada(payload):
    payload[0]["resultados"][0]["series"].pop()
    with pytest.raises(RespostaVazia, match="245"):
        le_populacao(payload)
