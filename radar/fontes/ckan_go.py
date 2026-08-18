"""Portal de dados abertos de Goiás: SQL de leitura direto no DataStore."""

from typing import NamedTuple
from urllib.parse import quote

import httpx

from radar.consulta import exige_limite
from radar.municipios import Sentinela, para_codigo7

BASE = "https://dadosabertos.go.gov.br/api/3/action/datastore_search_sql"
DENGUE = "0c7c9ff8-cdb2-4cee-892d-c9ef28c0ba9f"
# a agregação no portal já levou de 2 s a mais de 30 s
ESPERA_MAXIMA = 120.0


class Bloqueado(Exception): ...


class ConsultaRecusada(Exception): ...


class Caso(NamedTuple):
    codigo_ibge: str
    ano: int
    casos: int


def sql_casos(recurso: str = DENGUE, limite: int = 5000) -> str:
    return exige_limite(
        'SELECT "dmun_codibge" AS ibge, "ano_epidemiologica" AS ano, COUNT(*) AS casos'
        f' FROM "{recurso}" GROUP BY "dmun_codibge", "ano_epidemiologica" LIMIT {limite}'
    )


def le_casos(payload) -> list[Caso]:
    if not payload.get("success"):
        raise ConsultaRecusada(f"o portal recusou a consulta: {payload.get('error')}")
    casos = []
    for reg in payload["result"]["records"]:
        try:
            codigo = para_codigo7(reg["ibge"])
        except Sentinela:
            continue
        casos.append(Caso(codigo, int(reg["ano"]), int(reg["casos"])))
    return casos


def busca_casos(cliente, recurso: str = DENGUE):
    try:
        resposta = cliente.json(f"{BASE}?sql={quote(sql_casos(recurso))}", ESPERA_MAXIMA)
    except httpx.HTTPStatusError as erro:
        if erro.response.status_code == 403:
            raise Bloqueado(
                "403 do firewall do portal de Goiás; confira se a consulta tem LIMIT"
            ) from erro
        raise
    return le_casos(resposta.payload), resposta
