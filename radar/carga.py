from radar import banco
from radar.fontes import ckan_go, ibge, ms_cnes


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
