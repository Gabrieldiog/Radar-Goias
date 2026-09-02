from urllib.parse import quote

from radar import banco, municipios
from radar.fontes import ckan_go, ibge, ms_cnes, siconfi


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


def executa_leitos(conn, cliente, ano: int = 2026) -> dict:
    leitos, data, resposta = ckan_go.busca_leitos(cliente, ano)
    coleta = banco.grava_coleta(conn, "ckan-go", resposta.url, resposta.status, resposta.bytes)
    dia = f"{data[6:]}-{data[3:5]}-{data[:2]}"
    linhas, sem_municipio = [], set()
    for cnes in sorted({l.cnes for l in leitos}):
        municipio = ms_cnes.busca_municipio(cliente, cnes)
        if municipio is None:
            sem_municipio.add(cnes)
            continue
        linhas += [
            (municipio, l.cnes, l.tipo, dia, l.implantados, l.ocupados)
            for l in leitos
            if l.cnes == cnes
        ]
    return {
        "leitos": banco.grava_leitos(conn, linhas, coleta),
        "leitos_sem_municipio": len(sem_municipio),
    }


def executa_ubs(conn, cliente) -> dict:
    resposta = cliente.json(
        f"{ckan_go.BASE}?sql={quote(ckan_go.sql_ubs())}", ckan_go.ESPERA_MAXIMA
    )
    unidades = ckan_go.le_ubs(resposta.payload)
    coleta = banco.grava_coleta(conn, "ckan-go", resposta.url, resposta.status, resposta.bytes)
    return {"ubs": banco.grava_ubs(conn, unidades, coleta)}


def executa_ouvidoria(conn, cliente, ano: int = 2026) -> dict:
    resposta = cliente.json(
        f"{ckan_go.BASE}?sql={quote(ckan_go.sql_manifestacoes(ano))}", ckan_go.ESPERA_MAXIMA
    )
    linhas = ckan_go.le_manifestacoes(resposta.payload, ano)
    coleta = banco.grava_coleta(conn, "ckan-go", resposta.url, resposta.status, resposta.bytes)
    return {"manifestacoes": banco.grava_manifestacoes(conn, linhas, coleta)}


def executa_financas(conn, cliente, exercicio: int = 2025) -> dict:
    """Busca a despesa por função dos 246 municípios no Tesouro.

    É lento de propósito: uma requisição por segundo, então leva alguns minutos.
    Por isso fica num comando separado, e não na carga de todo dia.
    """
    banco.aplica_esquema(conn)
    banco.carrega_municipios(conn)
    linhas, sem_entrega = [], []
    for codigo in sorted(municipios.todos()):
        try:
            despesas, resposta = siconfi.busca_despesas(cliente, codigo, exercicio)
        except siconfi.RespostaSemDados:
            sem_entrega.append(codigo)
            continue
        coleta = banco.grava_coleta(
            conn, "siconfi", resposta.url, resposta.status, resposta.bytes
        )
        banco.grava_despesas(conn, despesas, coleta)
        linhas += despesas
    return {"despesas": len(linhas), "municipios_sem_entrega": len(sem_entrega)}
