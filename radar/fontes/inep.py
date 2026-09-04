"""Matrículas do Censo Escolar do INEP.

O CSV tem 426 colunas e 218 MB descomprimidos dentro de um ZIP de 33 MB, então
é lido em fluxo. Só escola em atividade entra, e as redes ficam separadas: o
gasto do município se divide pelo aluno da rede municipal, não pelo total do
território, senão o município paga pelo aluno que é do estado.
"""

import csv
import io
import zipfile
from collections import Counter
from typing import NamedTuple

from radar.municipios import MunicipioDesconhecido, Sentinela, para_codigo7

BASE = "https://download.inep.gov.br/dados_abertos"
DEPENDENCIA = {"1": "federal", "2": "estadual", "3": "municipal", "4": "privada"}
EM_ATIVIDADE = "1"


class CsvNaoEncontrado(Exception):
    """O ZIP do INEP mudou de estrutura e o arquivo de dados não está onde era."""


class Matricula(NamedTuple):
    codigo_ibge: str
    ano: int
    dependencia: str
    escolas: int
    alunos: int


def url_censo(ano: int) -> str:
    return f"{BASE}/microdados_censo_escolar_{ano}.zip"


def _csv_dentro(zip_censo: zipfile.ZipFile) -> str:
    # o nome da pasta muda de ano para ano, então acha pelo nome do arquivo
    for nome in zip_censo.namelist():
        if "microdados_ed_basica" in nome and nome.endswith(".csv"):
            return nome
    raise CsvNaoEncontrado(zip_censo.filename)


def le_censo(caminho, uf: str = "GO") -> list[Matricula]:
    escolas: Counter = Counter()
    alunos: Counter = Counter()
    with zipfile.ZipFile(caminho) as arquivo, arquivo.open(_csv_dentro(arquivo)) as bruto:
        # latin-1 porque só o cabeçalho é ASCII, o nome do município tem acento
        texto = io.TextIOWrapper(bruto, encoding="latin-1", newline="")
        for linha in csv.DictReader(texto, delimiter=";"):
            if linha["SG_UF"] != uf or linha["TP_SITUACAO_FUNCIONAMENTO"] != EM_ATIVIDADE:
                continue
            if not linha["QT_MAT_BAS"]:
                continue
            try:
                codigo = para_codigo7(linha["CO_MUNICIPIO"])
            except (MunicipioDesconhecido, Sentinela):
                continue
            chave = (codigo, int(linha["NU_ANO_CENSO"]), DEPENDENCIA[linha["TP_DEPENDENCIA"]])
            escolas[chave] += 1
            alunos[chave] += int(linha["QT_MAT_BAS"])
    return [Matricula(*chave, escolas[chave], alunos[chave]) for chave in sorted(escolas)]
