"""População municipal do IBGE, tabela 6579."""

from typing import NamedTuple

from radar.municipios import para_codigo7

ESPERADO = 246


class RespostaVazia(Exception): ...


class Populacao(NamedTuple):
    codigo_ibge: str
    ano: int
    habitantes: int
    base: str


def le_populacao(payload, base: str = "estimativa") -> list[Populacao]:
    # a chave é o id da localidade; o nome vem sufixado ("Goiânia - GO") e não serve
    series = payload[0]["resultados"][0]["series"] if payload else []
    linhas = [
        Populacao(para_codigo7(s["localidade"]["id"]), int(ano), int(valor), base)
        for s in series
        for ano, valor in s["serie"].items()
    ]
    if len(linhas) != ESPERADO:
        raise RespostaVazia(f"esperado {ESPERADO} municípios de Goiás, veio {len(linhas)}")
    return linhas
