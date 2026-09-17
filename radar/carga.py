import tempfile
from pathlib import Path
from urllib.parse import quote

from radar import banco, municipios
from radar.fontes import ckan_go, ibge, ideb, inep, ms_cnes, siconfi, sinesp


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
    caminho = caminho or Path(tempfile.gettempdir()) / f"sinesp{ano}.xlsx"
    coleta = _baixa_uma_vez(conn, cliente, "sinesp", sinesp.url_planilha(ano), caminho, 1)
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
    caminho = caminho or Path(tempfile.gettempdir()) / f"censo{ano}.zip"
    coleta = _baixa_uma_vez(conn, cliente, "inep", inep.url_censo(ano), caminho)
    matriculas = inep.le_censo(caminho)
    return {
        "matriculas": banco.grava_matriculas(conn, matriculas, coleta),
        "alunos": sum(m.alunos for m in matriculas),
    }


def _baixa_uma_vez(conn, cliente, fonte, url, caminho, tentativas=4) -> int:
    """Reusa o arquivo já baixado, para não pedir de novo o mesmo ao servidor.

    A coleta guarda sempre o endereço de origem, e nunca o caminho no disco: o
    arquivo em cache veio daquela URL, e gravar o caminho local faria a página
    de procedência apontar para a máquina de quem rodou, em vez da fonte.
    """
    if Path(caminho).exists():
        return banco.grava_coleta(conn, fonte, url, 200, Path(caminho).stat().st_size)
    resposta = cliente.arquivo(url, caminho, tentativas=tentativas)
    return banco.grava_coleta(conn, fonte, resposta.url, resposta.status, resposta.bytes)


def executa_ideb(conn, cliente, ano: int = 2025, pasta=None) -> dict:
    """Baixa as três planilhas do IDEB e grava as notas de Goiás.

    São três arquivos, um por etapa, somando 58 MB, e o IDEB sai a cada dois
    anos, então isso não entra na carga de todo dia.
    """
    banco.aplica_esquema(conn)
    banco.carrega_municipios(conn)
    pasta = Path(pasta or tempfile.gettempdir())
    gravadas, etapas = 0, {}
    for etapa in ideb.ETAPAS:
        caminho = pasta / f"{ideb.ETAPAS[etapa]}_{ano}.zip"
        coleta = _baixa_uma_vez(conn, cliente, "inep-ideb", ideb.url_ideb(etapa, ano), caminho)
        notas = ideb.le_ideb(caminho, etapa)
        etapas[etapa] = len(notas)
        gravadas += banco.grava_ideb(conn, notas, coleta)
    return {"ideb": gravadas, **etapas}
