"""IDEB do INEP, por município, rede e etapa.

A planilha é larga: cada ano é uma coluna, e são 133 delas. Aqui ela vira uma
linha por ano, que é a forma que o banco e o gráfico precisam.

Três armadilhas da fonte, todas previstas na pesquisa. O cabeçalho de máquina
está na linha 10, porque as nove primeiras são título e legenda para gente ler.
Ausência de medida é escrita como um traço, e virar zero seria dizer que o
município tirou a pior nota possível. E a rede "Pública" é o agregado das
outras, então ela entra com nome próprio e nunca pode ser somada junto.
"""

import io
import re
import zipfile
from typing import NamedTuple

import openpyxl

from radar.municipios import MunicipioDesconhecido, Sentinela, para_codigo7

BASE = "https://download.inep.gov.br/ideb/resultados"
ETAPAS = {
    "anos_iniciais": "divulgacao_anos_iniciais_municipios",
    "anos_finais": "divulgacao_anos_finais_municipios",
    "ensino_medio": "divulgacao_ensino_medio_municipios",
}
REDES = {
    "Estadual": "estadual",
    "Municipal": "municipal",
    "Federal": "federal",
    "Pública": "publica",
}
LINHA_DO_CABECALHO = 10
FALTANTE = "-"
FINAL_DE_ANO = re.compile(r"_(\d{4})$")


class PlanilhaInesperada(Exception):
    """O arquivo do INEP mudou de forma e o cabeçalho não está onde era."""


class Ideb(NamedTuple):
    codigo_ibge: str
    ano: int
    etapa: str
    rede: str
    ideb: float
    meta: float | None
    rendimento: float | None
    nota: float | None


def url_ideb(etapa: str, ano: int) -> str:
    return f"{BASE}/{ETAPAS[etapa]}_{ano}.zip"


def _numero(valor) -> float | None:
    if valor is None or valor == FALTANTE:
        return None
    return float(valor)


def _por_ano(cabecalho, prefixo: str) -> dict[int, int]:
    achadas = {}
    for coluna, nome in enumerate(cabecalho):
        if nome and str(nome).startswith(prefixo):
            final = FINAL_DE_ANO.search(str(nome))
            if final:
                achadas[int(final.group(1))] = coluna
    return achadas


def _planilha(caminho):
    with zipfile.ZipFile(caminho) as arquivo:
        dentro = [n for n in arquivo.namelist() if n.endswith(".xlsx")]
        if not dentro:
            raise PlanilhaInesperada(str(caminho))
        return io.BytesIO(arquivo.read(dentro[0]))


def le_ideb(caminho, etapa: str, uf: str = "GO") -> list[Ideb]:
    livro = openpyxl.load_workbook(_planilha(caminho), read_only=True)
    try:
        linhas = livro[livro.sheetnames[0]].iter_rows(values_only=True)
        for _ in range(LINHA_DO_CABECALHO - 1):
            next(linhas)
        cabecalho = list(next(linhas))
        onde = {nome: coluna for coluna, nome in enumerate(cabecalho) if nome}
        if "CO_MUNICIPIO" not in onde:
            raise PlanilhaInesperada(str(caminho))
        observado = _por_ano(cabecalho, "VL_OBSERVADO_")
        meta = _por_ano(cabecalho, "VL_PROJECAO_")
        rendimento = _por_ano(cabecalho, "VL_INDICADOR_REND_")
        nota = _por_ano(cabecalho, "VL_NOTA_MEDIA_")

        achados = []
        for linha in linhas:
            if linha[onde["SG_UF"]] != uf:
                continue
            rede = REDES.get(linha[onde["REDE"]])
            if rede is None:
                continue
            try:
                codigo = para_codigo7(linha[onde["CO_MUNICIPIO"]])
            except (MunicipioDesconhecido, Sentinela):
                continue
            for ano, coluna in observado.items():
                valor = _numero(linha[coluna])
                if valor is None:
                    continue
                achados.append(
                    Ideb(
                        codigo,
                        ano,
                        etapa,
                        rede,
                        valor,
                        _numero(linha[meta[ano]]) if ano in meta else None,
                        _numero(linha[rendimento[ano]]) if ano in rendimento else None,
                        _numero(linha[nota[ano]]) if ano in nota else None,
                    )
                )
        return achados
    finally:
        livro.close()
