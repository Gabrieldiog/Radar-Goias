"""API REST do Radar. Chave por requisição e limite por chave, não por IP."""

import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from radar import banco, indicadores, malha

CATALOGO = {
    "incidencia-dengue": {
        "id": "incidencia-dengue",
        "nome": "Incidência de dengue por 100 mil habitantes",
        "unidade": "casos por 100 mil habitantes",
        "formula": "casos notificados no ano / habitantes * 100000",
        "dimensao": "municipio",
        "fontes": ["dadosabertos.go.gov.br", "servicodados.ibge.gov.br"],
    },
    "leitos-rede-estadual": {
        "id": "leitos-rede-estadual",
        "nome": "Leitos da rede estadual por 100 mil habitantes",
        "unidade": "leitos por 100 mil habitantes",
        "formula": "leitos implantados na rede estadual / habitantes * 100000",
        "dimensao": "municipio",
        "fontes": [
            "dadosabertos.go.gov.br",
            "apidadosabertos.saude.gov.br",
            "servicodados.ibge.gov.br",
        ],
    },
    "ubs-por-habitante": {
        "id": "ubs-por-habitante",
        "nome": "Unidades básicas de saúde por 10 mil habitantes",
        "unidade": "unidades por 10 mil habitantes",
        "formula": "unidades básicas / habitantes * 10000",
        "dimensao": "municipio",
        "fontes": ["dadosabertos.go.gov.br", "servicodados.ibge.gov.br"],
    },
    "gasto-saude-por-habitante": {
        "id": "gasto-saude-por-habitante",
        "nome": "Gasto municipal em saúde por habitante",
        "unidade": "reais por habitante no ano",
        "formula": "despesa empenhada na função saúde / habitantes",
        "dimensao": "municipio",
        "fontes": ["apidatalake.tesouro.gov.br", "servicodados.ibge.gov.br"],
    },
    "gasto-educacao-por-habitante": {
        "id": "gasto-educacao-por-habitante",
        "nome": "Gasto municipal em educação por habitante",
        "unidade": "reais por habitante no ano",
        "formula": "despesa empenhada na função educação / habitantes",
        "dimensao": "municipio",
        "fontes": ["apidatalake.tesouro.gov.br", "servicodados.ibge.gov.br"],
    },
    "homicidio-por-100mil": {
        "id": "homicidio-por-100mil",
        "nome": "Homicídio doloso por 100 mil habitantes",
        "unidade": "vítimas por 100 mil habitantes no ano",
        "formula": "vítimas de homicídio doloso no ano / habitantes * 100000",
        "dimensao": "municipio",
        "fontes": ["www.gov.br/mj", "servicodados.ibge.gov.br"],
    },
    "ouvidoria-por-orgao": {
        "id": "ouvidoria-por-orgao",
        "nome": "Atendimento da ouvidoria por órgão",
        "unidade": "dias e porcentagem",
        "formula": "média de dias até finalizar, e proporção finalizada dentro do prazo",
        "dimensao": "orgao",
        "prazo_padrao_dias": 30,
        "fontes": ["dadosabertos.go.gov.br"],
    },
}


def chaves() -> set[str]:
    return {c.strip() for c in os.environ.get("RADAR_CHAVES", "").split(",") if c.strip()}


def exige_chave(request: Request) -> str:
    chave = request.headers.get("x-api-key") or request.query_params.get("chave")
    if not chave or chave not in chaves():
        raise HTTPException(401, "chave ausente ou inválida; use o cabeçalho x-api-key ou ?chave=")
    return chave


def balde(request: Request) -> str:
    chave = request.headers.get("x-api-key") or request.query_params.get("chave")
    return f"chave:{chave}" if chave in chaves() else f"ip:{get_remote_address(request)}"


# o campo que carrega o valor muda de indicador para indicador
CAMPO = {
    "incidencia-dengue": "por_100k",
    "leitos-rede-estadual": "por_100mil",
    "ubs-por-habitante": "por_10mil",
    "gasto-saude-por-habitante": "por_habitante",
    "gasto-educacao-por-habitante": "por_habitante",
    "ouvidoria-por-orgao": "tempo_medio",
    "homicidio-por-100mil": "por_100mil",
}


def _linhas(conn, indicador_id, ano=None, prazo=30):
    if indicador_id == "leitos-rede-estadual":
        return indicadores.leitos_por_100mil(conn)
    if indicador_id == "ubs-por-habitante":
        return indicadores.ubs_por_10mil(conn)
    if indicador_id.startswith("gasto-"):
        return indicadores.despesa_per_capita(conn, indicador_id.split("-")[1])
    if indicador_id == "homicidio-por-100mil":
        return indicadores.ocorrencias_por_100mil(conn, "Homicídio doloso", ano)
    if indicador_id == "ouvidoria-por-orgao":
        return indicadores.ouvidoria_por_orgao(conn, ano, prazo)
    return indicadores.incidencia_dengue(conn, ano or 2025)


def _do_municipio(linhas, codigo_ibge, campo):
    for l in linhas:
        if l["codigo_ibge"] == codigo_ibge:
            return l[campo]
    return None


def cria_app(limite: str = "60/minute") -> FastAPI:
    limiter = Limiter(key_func=balde, default_limits=[limite], headers_enabled=True)
    app = FastAPI(title="Radar Goiás", version="0.1.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/saude")
    def saude(request: Request):
        return {"ok": True}

    @app.get("/v1/municipios")
    def lista_municipios(request: Request, chave: str = Depends(exige_chave)):
        with banco.conecta() as conn, conn.cursor(row_factory=dict_row) as cur:
            linhas = cur.execute(
                "select codigo_ibge, nome from municipio order by nome"
            ).fetchall()
        return {"dados": linhas, "total": len(linhas)}

    @app.get("/v1/municipios/{codigo_ibge}")
    def um_municipio(request: Request, codigo_ibge: str, chave: str = Depends(exige_chave)):
        with banco.conecta() as conn, conn.cursor(row_factory=dict_row) as cur:
            linha = cur.execute(
                "select m.codigo_ibge, m.nome, p.habitantes, p.ano as ano_populacao"
                " from municipio m left join populacao p using (codigo_ibge)"
                " where m.codigo_ibge = %s order by p.ano desc limit 1",
                (codigo_ibge,),
            ).fetchone()
        if not linha:
            raise HTTPException(404, f"município desconhecido: {codigo_ibge}")
        with banco.conecta() as conn:
            linha["indicadores"] = {
                id: _do_municipio(_linhas(conn, id), codigo_ibge, CAMPO[id])
                for id, meta in CATALOGO.items()
                if meta["dimensao"] == "municipio"
            }
        return linha

    @app.get("/v1/malha")
    def contorno(request: Request, chave: str = Depends(exige_chave)):
        # a geometria é fixa: deixa o navegador guardar por um dia
        return JSONResponse(
            malha.geojson(), headers={"cache-control": "public, max-age=86400"}
        )

    # a série alimenta o gráfico de evolução; sem município vem o estado inteiro
    @app.get("/v1/series/dengue")
    def serie_dengue(
        request: Request, municipio: str | None = None, chave: str = Depends(exige_chave)
    ):
        with banco.conecta() as conn:
            linhas = indicadores.serie_dengue(conn, municipio)
        return {"dados": linhas, "total": len(linhas)}

    @app.get("/v1/indicadores")
    def catalogo(request: Request, chave: str = Depends(exige_chave)):
        return {"dados": list(CATALOGO.values()), "total": len(CATALOGO)}

    @app.get("/v1/indicadores/{indicador_id}")
    def valores(
        request: Request,
        indicador_id: str,
        ano: int | None = None,
        municipio: str | None = None,
        prazo: int = 30,
        chave: str = Depends(exige_chave),
    ):
        if indicador_id not in CATALOGO:
            raise HTTPException(404, f"indicador desconhecido: {indicador_id}")
        with banco.conecta() as conn:
            linhas = _linhas(conn, indicador_id, ano, prazo)
        if municipio:
            linhas = [l for l in linhas if l.get("codigo_ibge") == municipio]
        return {
            "dados": linhas,
            "total": len(linhas),
            "meta": {
                "ano": ano,
                "dimensao": CATALOGO[indicador_id]["dimensao"],
                "fontes": CATALOGO[indicador_id]["fontes"],
                "base_populacional": (
                    linhas[0].get("base_populacional") if linhas else None
                ),
            },
        }

    return app
