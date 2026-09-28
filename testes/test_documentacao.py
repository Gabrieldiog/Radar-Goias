"""Testa o texto que a API mostra em /docs.

O exemplo de curl ensinava a chamar "https://SEU_HOST", um lugar pra preencher
que sobrou de quando o projeto só rodava na máquina de quem escreveu. Quem
copiava o exemplo recebia erro de DNS. O endereço agora vem do ambiente, então
o mesmo código serve a máquina local e o servidor publicado.
"""

from radar import api


# Verifica que o exemplo traz o endereço real de quem está servindo.
def test_o_exemplo_usa_o_endereco_configurado(monkeypatch):
    monkeypatch.setenv("RADAR_ENDERECO_PUBLICO", "http://exemplo.br:8010")
    texto = api.descricao()
    assert "http://exemplo.br:8010/v1/indicadores/" in texto


# Verifica que não sobrou lugar pra preencher no texto publicado.
def test_nao_sobra_lugar_pra_preencher(monkeypatch):
    monkeypatch.setenv("RADAR_ENDERECO_PUBLICO", "http://exemplo.br:8010")
    assert "SEU_HOST" not in api.descricao()


# Verifica que sem configuração o texto ensina o endereço local, que é onde a
# API responde quando alguém sobe o projeto pela primeira vez.
def test_sem_configuracao_ensina_o_endereco_local(monkeypatch):
    monkeypatch.delenv("RADAR_ENDERECO_PUBLICO", raising=False)
    assert "http://127.0.0.1:8000/v1/indicadores/" in api.descricao()


# Verifica que barra sobrando no fim do endereço não vira barra dupla na URL.
def test_barra_no_fim_do_endereco_nao_duplica(monkeypatch):
    monkeypatch.setenv("RADAR_ENDERECO_PUBLICO", "http://exemplo.br:8010/")
    assert "8010//v1" not in api.descricao()


# Verifica que a documentação diz como mandar a chave e o que acontece sem ela,
# porque é a primeira coisa que trava quem tenta consumir.
def test_ensina_a_chave_e_o_limite():
    texto = api.descricao()
    for pedaco in ("x-api-key", "401", "429", "60 por minuto"):
        assert pedaco in texto, pedaco
