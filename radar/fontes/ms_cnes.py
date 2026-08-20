"""Cadastro Nacional de Estabelecimentos de Saúde: dado um CNES, qual município."""

import httpx

from radar.municipios import MunicipioDesconhecido, para_codigo7

BASE = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"


def busca_municipio(cliente, cnes: str) -> str | None:
    try:
        resposta = cliente.json(f"{BASE}/{cnes}")
    except httpx.HTTPStatusError:
        return None
    codigo = resposta.payload.get("codigo_municipio")
    try:
        return para_codigo7(codigo) if codigo else None
    except MunicipioDesconhecido:
        return None
