import tempfile
from pathlib import Path
from urllib.parse import quote

from radar import banco, municipios
from radar.fontes import ckan_go, ibge, inep, ms_cnes, siconfi, sinesp


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


def executa_seguranca(conn, cliente, ano: int = 2026, caminho=None) -> dict:
    """Baixa a planilha do SINESP, se preciso, e grava as ocorrências de Goiás.

    O arquivo tem 13 MB e a planilha interna passa de 200 MB descomprimidos,
    então fica num comando separado e é lido em fluxo.
    """
    banco.aplica_esquema(conn)
    banco.carrega_municipios(conn)
    if caminho is None:
        caminho = Path(tempfile.gettempdir()) / f"sinesp{ano}.xlsx"
        if not caminho.exists():
            resposta = cliente.arquivo(sinesp.url_planilha(ano), caminho)
            coleta = banco.grava_coleta(
                conn, "sinesp", resposta.url, resposta.status, resposta.bytes
            )
        else:
            coleta = banco.grava_coleta(conn, "sinesp", str(caminho), 200, caminho.stat().st_size)
    else:
        coleta = banco.grava_coleta(conn, "sinesp", str(caminho), 200, Path(caminho).stat().st_size)
    ocorrencias = sinesp.le_planilha(caminho)
    return {
        "ocorrencias": banco.grava_ocorrencias(conn, ocorrencias, coleta),
        "eventos": len({o.evento for o in ocorrencias}),
    }


def executa_educacao(conn, cliente, ano: int = 2024, caminho=None) -> dict:
    """Baixa o Censo Escolar do INEP, se preciso, e grava as matrículas de Goiás.

    Fica num comando separado porque o ZIP tem 33 MB e o CSV de dentro passa de
    200 MB, e porque o censo sai uma vez por ano.
    """
    banco.aplica_esquema(conn)
    banco.carrega_municipios(conn)
    if caminho is None:
        caminho = Path(tempfile.gettempdir()) / f"censo{ano}.zip"
        if not caminho.exists():
            resposta = cliente.arquivo(inep.url_censo(ano), caminho, tentativas=4)
            coleta = banco.grava_coleta(
                conn, "inep", resposta.url, resposta.status, resposta.bytes
            )
        else:
            coleta = banco.grava_coleta(conn, "inep", str(caminho), 200, caminho.stat().st_size)
    else:
        coleta = banco.grava_coleta(conn, "inep", str(caminho), 200, Path(caminho).stat().st_size)
    matriculas = inep.le_censo(caminho)
    return {
        "matriculas": banco.grava_matriculas(conn, matriculas, coleta),
        "alunos": sum(m.alunos for m in matriculas),
    }
