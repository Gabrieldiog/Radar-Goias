"""Testa o pedido e a conferência de chave de API.

Até aqui a chave era uma variável de ambiente: para dar acesso a alguém era
preciso editar um arquivo no servidor e reiniciar a API. Isso não é um sistema,
é um bilhete. Agora existe uma tabela, um pedido e um registro de uso.

As chaves do ambiente continuam valendo. São as do painel e as de quem já tem
a sua, e tirá-las quebraria o que está no ar.
"""

import pytest

from radar import banco, chaves

pytestmark = pytest.mark.skipif(not banco.disponivel(), reason="sem banco; suba o docker compose")


@pytest.fixture
def conn():
    with banco.conecta() as c:
        banco.aplica_esquema(c)
        c.execute("truncate chave_api")
        yield c


# Verifica que a chave gerada tem tamanho suficiente para não ser adivinhada.
# 32 caracteres do alfabeto seguro dão mais combinações do que qualquer força
# bruta que passe por um limite de 60 requisições por minuto.
def test_a_chave_gerada_e_longa(conn):
    nova = chaves.emite(conn, "Turma de Projeto 2", "testar em aula")
    assert len(nova.chave) >= 32


# Verifica que duas emissões seguidas não saem iguais.
def test_duas_chaves_nunca_saem_iguais(conn):
    a = chaves.emite(conn, "um", "x").chave
    b = chaves.emite(conn, "dois", "y").chave
    assert a != b


# Verifica que a chave emitida é aceita na conferência.
def test_chave_emitida_e_aceita(conn):
    nova = chaves.emite(conn, "fulano", "integrar")
    assert chaves.confere(conn, nova.chave) is True


# Verifica que chave inventada é recusada.
@pytest.mark.parametrize("falsa", ["", "   ", "nao-existe", "x" * 40, None])
def test_chave_inventada_e_recusada(conn, falsa):
    assert chaves.confere(conn, falsa) is False


# Verifica que o nome de quem pediu fica guardado. Sem isso não há como saber
# quem está consumindo, que é metade do motivo de existir chave.
def test_guarda_quem_pediu(conn):
    nova = chaves.emite(conn, "Prefeitura de Goiânia", "painel interno")
    linha = chaves.busca(conn, nova.chave)
    assert linha["nome"] == "Prefeitura de Goiânia"
    assert linha["motivo"] == "painel interno"


# Verifica que pedido sem nome é recusado, porque chave anônima não diz nada.
@pytest.mark.parametrize("nome", ["", "   ", None])
def test_pedido_sem_nome_e_recusado(conn, nome):
    with pytest.raises(ValueError):
        chaves.emite(conn, nome, "qualquer")


# Verifica que o nome muito longo não passa: é campo de formulário aberto na
# internet, e sem limite ele vira depósito de texto.
def test_nome_absurdamente_longo_e_recusado(conn):
    with pytest.raises(ValueError):
        chaves.emite(conn, "n" * 300, "x")


# Verifica que o uso é contado. É o que deixa mostrar na apresentação que a
# chave recém-criada acabou de funcionar.
def test_conta_o_uso(conn):
    nova = chaves.emite(conn, "fulano", "integrar")
    assert chaves.busca(conn, nova.chave)["chamadas"] == 0
    chaves.confere(conn, nova.chave)
    chaves.confere(conn, nova.chave)
    assert chaves.busca(conn, nova.chave)["chamadas"] == 2


# Verifica que a data do último uso é registrada.
def test_registra_o_ultimo_uso(conn):
    nova = chaves.emite(conn, "fulano", "integrar")
    assert chaves.busca(conn, nova.chave)["ultimo_uso"] is None
    chaves.confere(conn, nova.chave)
    assert chaves.busca(conn, nova.chave)["ultimo_uso"] is not None


# Verifica que conferir chave errada não conta uso de ninguém.
def test_chave_errada_nao_conta_uso_de_ninguem(conn):
    nova = chaves.emite(conn, "fulano", "integrar")
    chaves.confere(conn, "outra-coisa")
    assert chaves.busca(conn, nova.chave)["chamadas"] == 0


# Verifica que a chave não carrega caractere que atrapalhe em URL ou cabeçalho.
def test_alfabeto_da_chave_e_seguro(conn):
    nova = chaves.emite(conn, "fulano", "x")
    assert nova.chave.isascii() and nova.chave.isalnum()


# Verifica que motivo em branco é aceito: é campo opcional, e exigir texto só
# faz a pessoa escrever "teste".
def test_motivo_e_opcional(conn):
    nova = chaves.emite(conn, "fulano", "")
    assert chaves.busca(conn, nova.chave)["motivo"] == ""


# ---- a rota que entrega a chave e a que confere ----

from fastapi.testclient import TestClient  # noqa: E402

from radar import api  # noqa: E402

DO_AMBIENTE = "chave-do-painel"


@pytest.fixture
def cliente(monkeypatch, conn):
    monkeypatch.setenv("RADAR_CHAVES", DO_AMBIENTE)
    return TestClient(api.cria_app(limite="500/minute"))


# Verifica que qualquer pessoa consegue pedir uma chave e recebe uma na hora.
def test_pedir_chave_devolve_uma_chave(cliente):
    r = cliente.post("/v1/chaves", json={"nome": "Turma de Projeto 2", "motivo": "aula"})
    assert r.status_code == 201
    assert len(r.json()["chave"]) >= 32


# Verifica que a chave recém-pedida já abre as rotas de dado. É o que a
# apresentação mostra: pede, copia, chama, funciona.
def test_a_chave_recem_pedida_ja_funciona(cliente):
    nova = cliente.post("/v1/chaves", json={"nome": "fulano"}).json()["chave"]
    assert cliente.get("/v1/municipios", headers={"x-api-key": nova}).status_code == 200


# Verifica que a chave do ambiente continua valendo, senão o painel no ar cai.
def test_a_chave_do_ambiente_continua_valendo(cliente):
    assert cliente.get("/v1/municipios", headers={"x-api-key": DO_AMBIENTE}).status_code == 200


# Verifica que chave inventada continua sendo recusada.
def test_chave_inventada_continua_recusada(cliente):
    assert cliente.get("/v1/municipios", headers={"x-api-key": "a" * 32}).status_code == 401


# Verifica que pedido sem nome é recusado com 400, e não com 500.
@pytest.mark.parametrize("corpo", [{}, {"nome": ""}, {"nome": "   "}, {"motivo": "só motivo"}])
def test_pedido_sem_nome_da_400(cliente, corpo):
    assert cliente.post("/v1/chaves", json=corpo).status_code in (400, 422)


# Verifica que pedir chave não exige chave, senão ninguém consegue a primeira.
def test_pedir_chave_nao_exige_chave(cliente):
    assert cliente.post("/v1/chaves", json={"nome": "sem chave nenhuma"}).status_code == 201


# Verifica que a resposta do pedido não devolve a lista de outras chaves.
def test_o_pedido_nao_vaza_chave_de_outro(cliente):
    cliente.post("/v1/chaves", json={"nome": "primeiro"})
    corpo = cliente.post("/v1/chaves", json={"nome": "segundo"}).json()
    assert set(corpo) <= {"chave", "nome", "motivo", "criada_em", "limite"}


# Verifica que a rota de conferir diz se a chave vale, para o painel poder
# mostrar o resultado do teste sem precisar interpretar um erro.
def test_rota_de_conferir_responde_sobre_a_propria_chave(cliente):
    nova = cliente.post("/v1/chaves", json={"nome": "fulano"}).json()["chave"]
    r = cliente.get("/v1/chaves/minha", headers={"x-api-key": nova})
    assert r.status_code == 200
    assert r.json()["nome"] == "fulano"
    assert r.json()["chamadas"] >= 1


# Verifica que a conferência não entrega a chave inteira de volta na resposta,
# porque essa resposta passa pelo proxy do painel e vai parar em log.
def test_a_conferencia_nao_repete_a_chave_inteira(cliente):
    nova = cliente.post("/v1/chaves", json={"nome": "fulano"}).json()["chave"]
    assert nova not in cliente.get("/v1/chaves/minha", headers={"x-api-key": nova}).text
