"""Contas municipais no SICONFI, do Tesouro Nacional.

O anexo I-E da declaração anual traz a despesa por função de governo. Só três
delas interessam ao projeto, e elas vêm com o número da função na frente.
"""

from typing import NamedTuple
from urllib.parse import quote

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
ANEXO = "DCA-Anexo I-E"
# o Tesouro escreve a função com o código na frente, e os acentos importam
FUNCOES = {"06 - Segurança Pública": "seguranca", "10 - Saúde": "saude", "12 - Educação": "educacao"}


class RespostaSemDados(Exception): ...


class Despesa(NamedTuple):
    codigo_ibge: str
    exercicio: int
    funcao: str
    empenhado: float
    pago: float


def url_dca(codigo_ibge: str, exercicio: int) -> str:
    return (
        f"{BASE}?an_exercicio={exercicio}&id_ente={codigo_ibge}"
        f"&no_anexo={quote(ANEXO)}"
    )


def le_despesas(payload, codigo_ibge: str) -> list[Despesa]:
    itens = payload.get("items") or []
    if not itens:
        # o Tesouro responde 200 com zero linhas quando o parâmetro está errado
        raise RespostaSemDados(f"o Tesouro não devolveu linhas para {codigo_ibge}")
    valores: dict[str, dict[str, float]] = {}
    for item in itens:
        funcao = FUNCOES.get(item["conta"])
        if funcao is None:
            continue
        valores.setdefault(funcao, {})[item["coluna"]] = float(item["valor"])
    exercicio = int(itens[0]["exercicio"])
    return [
        Despesa(
            codigo_ibge,
            exercicio,
            funcao,
            colunas.get("Despesas Empenhadas", 0.0),
            colunas.get("Despesas Pagas", 0.0),
        )
        for funcao, colunas in sorted(valores.items())
    ]


def busca_despesas(cliente, codigo_ibge: str, exercicio: int):
    resposta = cliente.json(url_dca(codigo_ibge, exercicio), 90.0)
    return le_despesas(resposta.payload, codigo_ibge), resposta
