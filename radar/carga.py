from radar import banco
from radar.fontes import ckan_go, ibge


def executa(conn, cliente) -> dict:
    banco.aplica_esquema(conn)
    municipios = banco.carrega_municipios(conn)
    linhas, resposta = ibge.busca_populacao(cliente)
    coleta = banco.grava_coleta(conn, "ibge", resposta.url, resposta.status, resposta.bytes)
    return {"municipios": municipios, "populacao": banco.grava_populacao(conn, linhas, coleta)}


def executa_dengue(conn, cliente) -> dict:
    casos, resposta = ckan_go.busca_casos(cliente)
    coleta = banco.grava_coleta(conn, "ckan-go", resposta.url, resposta.status, resposta.bytes)
    return {"dengue": banco.grava_casos_dengue(conn, casos, coleta)}
