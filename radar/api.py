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
    "gasto-educacao-por-aluno": {
        "id": "gasto-educacao-por-aluno",
        "nome": "Gasto municipal em educação por aluno da rede municipal",
        "unidade": "reais por aluno no ano",
        "formula": "despesa empenhada na função educação / matrículas da rede municipal",
        "dimensao": "municipio",
        "fontes": [
            "apidatalake.tesouro.gov.br",
            "download.inep.gov.br",
            "servicodados.ibge.gov.br",
        ],
    },
    "gasto-educacao-por-habitante": {
        "id": "gasto-educacao-por-habitante",
        "nome": "Gasto municipal em educação por habitante",
        "unidade": "reais por habitante no ano",
        "formula": "despesa empenhada na função educação / habitantes",
        "dimensao": "municipio",
        "fontes": ["apidatalake.tesouro.gov.br", "servicodados.ibge.gov.br"],
    },
    "focos-de-queimada": {
        "id": "focos-de-queimada",
        "nome": "Focos de calor detectados por satélite nos últimos sete dias",
        "unidade": "focos em sete dias",
        "formula": "contagem de detecções de satélite, sem dividir por nada",
        "dimensao": "municipio",
        "atualizacao": "diária, e o arquivo do dia enche ao longo das horas",
        "ressalva": (
            "Um foco é uma detecção de satélite, não um incêndio. Doze satélites"
            " cobrem o Brasil e vários veem o mesmo fogo, então o número é piso e"
            " não conta de incêndios distintos."
        ),
        "fontes": ["dataserver-coids.inpe.br"],
    },
    "homicidio-por-100mil": {
        "id": "homicidio-por-100mil",
        "nome": "Homicídio doloso por 100 mil habitantes",
        "unidade": "vítimas por 100 mil habitantes no ano",
        "formula": "vítimas de homicídio doloso no ano / habitantes * 100000",
        "dimensao": "municipio",
        "fontes": ["www.gov.br/mj", "servicodados.ibge.gov.br"],
    },
    "ubs-noturnas": {
        "id": "ubs-noturnas",
        "nome": "Unidades de saúde que atendem à noite, por 10 mil habitantes",
        "unidade": "unidades noturnas por 10 mil hab",
        "formula": "unidades com turno noturno ou plantão de 24 horas / habitantes * 10000",
        "dimensao": "municipio",
        "ressalva": (
            "29 unidades do estado declaram 'sempre aberto' e, na mesma linha,"
            " declaram atender só de manhã e à tarde. Quando os dois campos se"
            " contradizem o Radar segue o turno, então essas 29 não contam como"
            " porta noturna nem como aberta no fim de semana."
        ),
        "fontes": ["dadosabertos.go.gov.br", "servicodados.ibge.gov.br"],
    },
    "km-ate-porta-noturna": {
        "id": "km-ate-porta-noturna",
        "nome": "Distância até a unidade de saúde aberta à noite mais próxima",
        "unidade": "quilômetros em linha reta",
        "formula": (
            "haversine entre a média das coordenadas das unidades do município e"
            " a unidade noturna mais próxima do estado; zero para quem tem a sua"
        ),
        "dimensao": "municipio",
        "ressalva": (
            "Distância em linha reta, não por estrada: o percurso real é maior."
            " A origem é a média das coordenadas das unidades do município, que"
            " fica perto de onde as pessoas moram, e não o centro do território."
        ),
        "fontes": ["dadosabertos.go.gov.br", "servicodados.ibge.gov.br"],
    },
    "ideb-anos-iniciais": {
        "id": "ideb-anos-iniciais",
        "nome": "IDEB dos anos iniciais na rede municipal",
        "unidade": "nota de 0 a 10",
        "formula": "indicador de rendimento multiplicado pela nota média padronizada",
        "dimensao": "municipio",
        "etapa": "anos_iniciais",
        "rede": "municipal",
        "fontes": ["download.inep.gov.br"],
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
    "gasto-educacao-por-aluno": "por_aluno",
    "ideb-anos-iniciais": "ideb",
    "ubs-noturnas": "por_10mil",
    "focos-de-queimada": "focos",
    "km-ate-porta-noturna": "km",
    "ouvidoria-por-orgao": "tempo_medio",
    "homicidio-por-100mil": "por_100mil",
}


def _linhas(conn, indicador_id, ano=None, prazo=30):
    if indicador_id == "leitos-rede-estadual":
        return indicadores.leitos_por_100mil(conn)
    if indicador_id == "ubs-por-habitante":
        return indicadores.ubs_por_10mil(conn)
    if indicador_id == "km-ate-porta-noturna":
        return indicadores.km_ate_porta_noturna(conn)
    if indicador_id == "focos-de-queimada":
        return indicadores.focos_por_municipio(conn)
    if indicador_id == "ubs-noturnas":
        return indicadores.unidades_por_turno(conn)
    if indicador_id == "ideb-anos-iniciais":
        return indicadores.ideb_por_municipio(conn, ano=ano)
    if indicador_id == "gasto-educacao-por-aluno":
        return indicadores.gasto_por_aluno(conn)
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


# as consultas de indicador já voltam ordenadas do maior para o menor, então a
# posição é o índice; município sem valor fica de fora da contagem, senão a
# ausência de dado viraria último lugar
def _ranking(linhas, codigo_ibge, campo):
    com_valor = [l for l in linhas if l.get(campo) is not None]
    for posicao, l in enumerate(com_valor, 1):
        if l["codigo_ibge"] == codigo_ibge:
            return {"posicao": posicao, "de": len(com_valor)}
    return None


def _cabecalho(conn, codigo_ibge: str) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        linha = cur.execute(
            "select m.codigo_ibge, m.nome, p.habitantes, p.ano as ano_populacao"
            " from municipio m left join populacao p using (codigo_ibge)"
            " where m.codigo_ibge = %s order by p.ano desc limit 1",
            (codigo_ibge,),
        ).fetchone()
    if not linha:
        raise HTTPException(404, f"município desconhecido: {codigo_ibge}")
    return linha


# uma consulta por indicador, e não uma por município: o indicador varre o
# estado inteiro de qualquer jeito, então dois municípios saem no mesmo passeio
def _ficha(conn, cabecalhos: list[dict]) -> list[dict]:
    for c in cabecalhos:
        c["indicadores"], c["posicoes"] = {}, {}
    for id, meta in CATALOGO.items():
        if meta["dimensao"] != "municipio":
            continue
        linhas = _linhas(conn, id)
        for c in cabecalhos:
            c["indicadores"][id] = _do_municipio(linhas, c["codigo_ibge"], CAMPO[id])
            c["posicoes"][id] = _ranking(linhas, c["codigo_ibge"], CAMPO[id])
    return cabecalhos


DESCRICAO = """
Indicadores dos 246 municípios de Goiás, calculados a partir de seis fontes
públicas que não conversam entre si. Toda resposta diz de onde o número veio.

## Como usar no seu sistema

Peça uma chave e mande ela no cabeçalho `x-api-key` de cada requisição.

```bash
curl -H "x-api-key: SUA_CHAVE" \\
  "https://SEU_HOST/v1/indicadores/ideb-anos-iniciais?municipio=5208707"
```

Se preferir, a chave também vale como parâmetro: `?chave=SUA_CHAVE`. O cabeçalho
é a forma recomendada, porque a query fica gravada em log de servidor.

Sem chave, a resposta é **401**. Com chave inválida, também.

## Limite de requisições

**60 por minuto, contados por chave e não por IP.** Numa faculdade todo mundo
sai pelo mesmo IP, e um balde compartilhado faria um usuário derrubar os
colegas. Ao estourar, a resposta é **429**, e os cabeçalhos `X-RateLimit-*`
dizem quanto sobrou e quando reabre.

## Como achar o município

A chave de junção é o **código IBGE de 7 dígitos**, que é o mesmo do mapa do
IBGE. `GET /v1/municipios` devolve os 246 com código e nome. Não use nome como
identificador: as fontes escrevem acento e apóstrofo de jeitos diferentes.

## O que vem em cada resposta

Lista de indicadores em `dados`, o total em `total`, e em `meta` as fontes que
produziram aquele número, a dimensão (município ou órgão) e a base populacional
usada como denominador. Indicador por habitante traz `habitantes` e
`ano_populacao` em cada linha, para você conferir a conta.

`GET /v1/indicadores` devolve o catálogo com a fórmula de cada um.

## Procedência

`GET /v1/procedencia` devolve, para cada conjunto de dados, o endereço de onde
ele veio, o status que o servidor respondeu, o tamanho e a data da coleta.
Qualquer número desta API pode ser rastreado até a requisição que o trouxe.

## Ressalvas que valem para todo indicador por habitante

Município pequeno oscila muito: poucos casos numa cidade de dois mil habitantes
viram uma taxa alta que não se repete no ano seguinte. E o cálculo usa a
estimativa populacional mais recente do IBGE, que o campo `ano_populacao`
declara em cada linha.
"""


def cria_app(limite: str = "60/minute") -> FastAPI:
    limiter = Limiter(key_func=balde, default_limits=[limite], headers_enabled=True)
    app = FastAPI(
        title="Radar Goiás",
        version="0.1.0",
        description=DESCRICAO,
        contact={"name": "Radar Goiás", "url": "https://github.com/Gabrieldiog/Radar-Goias"},
    )
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
        with banco.conecta() as conn:
            return _ficha(conn, [_cabecalho(conn, codigo_ibge)])[0]

    # comparar dois municípios roda as mesmas consultas de um só: o custo está
    # no indicador, que varre o estado inteiro, e não no município pedido
    @app.get("/v1/comparar")
    def compara(request: Request, a: str, b: str, chave: str = Depends(exige_chave)):
        if a == b:
            raise HTTPException(400, "escolha dois municípios diferentes")
        with banco.conecta() as conn:
            fichas = _ficha(conn, [_cabecalho(conn, a), _cabecalho(conn, b)])
        return {"dados": fichas, "total": len(fichas)}

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

    # a série do IDEB traz as duas metades da nota, para o painel poder mostrar
    # se o município subiu por aprovar mais ou por aprender mais
    @app.get("/v1/series/ideb")
    def serie_ideb(
        request: Request,
        municipio: str | None = None,
        etapa: str = "anos_iniciais",
        rede: str = "municipal",
        chave: str = Depends(exige_chave),
    ):
        with banco.conecta() as conn:
            linhas = indicadores.serie_ideb(conn, municipio, etapa, rede)
        return {"dados": linhas, "total": len(linhas), "fontes": ["download.inep.gov.br"]}

    # a promessa do projeto é que todo número é rastreável até a requisição que
    # o trouxe, e esta rota é onde essa promessa fica conferível
    @app.get("/v1/procedencia")
    def procedencia(request: Request, chave: str = Depends(exige_chave)):
        with banco.conecta() as conn:
            return {
                "conjuntos": indicadores.frescor(conn),
                "fontes": indicadores.por_fonte(conn),
            }

    # 18 regiões de saúde, que é como o estado organiza a rede de fato. É um
    # nível de comparação que não existe em nenhum outro indicador do painel.
    # a única série do painel que se move de um dia para o outro
    @app.get("/v1/series/fogo")
    def serie_fogo(
        request: Request, municipio: str | None = None, chave: str = Depends(exige_chave)
    ):
        with banco.conecta() as conn:
            linhas = indicadores.serie_fogo(conn, municipio)
        return {
            "dados": linhas,
            "total": len(linhas),
            "fontes": ["dataserver-coids.inpe.br"],
        }

    @app.get("/v1/regioes-de-saude")
    def regioes_de_saude(request: Request, chave: str = Depends(exige_chave)):
        with banco.conecta() as conn:
            linhas = indicadores.por_regiao_de_saude(conn)
        return {"dados": linhas, "total": len(linhas), "fontes": ["dadosabertos.go.gov.br"]}

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
        catalogo = CATALOGO[indicador_id]
        meta = {
            "ano": ano,
            "dimensao": catalogo["dimensao"],
            "fontes": catalogo["fontes"],
            "base_populacional": linhas[0].get("base_populacional") if linhas else None,
        }
        # ressalva e frequência de atualização viajam com o número, e não só no
        # catálogo: quem consome a rota direto não vê a outra página
        for extra in ("ressalva", "atualizacao"):
            if extra in catalogo:
                meta[extra] = catalogo[extra]
        return {"dados": linhas, "total": len(linhas), "meta": meta}

    return app
