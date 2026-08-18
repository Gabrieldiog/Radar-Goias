"""API REST do Radar. Chave por requisição e limite por chave, não por IP."""

import os

from fastapi import Depends, FastAPI, HTTPException, Request
from psycopg.rows import dict_row
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from radar import banco, indicadores

CATALOGO = {
    "incidencia-dengue": {
        "id": "incidencia-dengue",
        "nome": "Incidência de dengue por 100 mil habitantes",
        "unidade": "casos por 100 mil habitantes",
        "formula": "casos notificados no ano / habitantes * 100000",
        "fontes": ["dadosabertos.go.gov.br", "servicodados.ibge.gov.br"],
    }
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
        return linha

    @app.get("/v1/indicadores")
    def catalogo(request: Request, chave: str = Depends(exige_chave)):
        return {"dados": list(CATALOGO.values()), "total": len(CATALOGO)}

    @app.get("/v1/indicadores/{indicador_id}")
    def valores(
        request: Request,
        indicador_id: str,
        ano: int = 2025,
        municipio: str | None = None,
        chave: str = Depends(exige_chave),
    ):
        if indicador_id not in CATALOGO:
            raise HTTPException(404, f"indicador desconhecido: {indicador_id}")
        with banco.conecta() as conn:
            linhas = indicadores.incidencia_dengue(conn, ano)
        if municipio:
            linhas = [l for l in linhas if l["codigo_ibge"] == municipio]
        return {
            "dados": linhas,
            "total": len(linhas),
            "meta": {
                "ano": ano,
                "fontes": CATALOGO[indicador_id]["fontes"],
                "base_populacional": linhas[0]["base_populacional"] if linhas else None,
            },
        }

    return app
