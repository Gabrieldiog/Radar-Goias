"""Os 246 municípios de Goiás. Toda fonte converge para o código IBGE de 7 dígitos."""

import json
import unicodedata
from functools import cache
from pathlib import Path

ARQUIVO = Path(__file__).parent / "dados" / "municipios_go.json"

# ocupam a coluna de município nas fontes, mas não são município
SENTINELAS_CODIGO = {"520000"}
SENTINELAS_NOME = {"NAO INFORMADO", "MUNICIPIO IGNORADO - GO", "MUNICIPIO IGNORADO"}


class MunicipioDesconhecido(Exception):
    def __init__(self, valor):
        super().__init__(f"{valor!r} não é município de Goiás")
        self.valor = valor


class Sentinela(Exception):
    def __init__(self, valor):
        super().__init__(f"{valor!r} é sentinela da fonte; filtre antes de agregar")
        self.valor = valor


@cache
def todos() -> dict[str, str]:
    return json.loads(ARQUIVO.read_text(encoding="utf-8"))


@cache
def _por_codigo6() -> dict[str, str]:
    return {codigo[:6]: codigo for codigo in todos()}


@cache
def _por_nome() -> dict[str, str]:
    return {normaliza_nome(nome): codigo for codigo, nome in todos().items()}


def normaliza_nome(valor: str) -> str:
    # o apóstrofo sai porque o IBGE escreve "São João d'Aliança" e o FNDE "SAO JOAO DALIANCA"
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", str(valor)) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sem_acento.replace("'", "").replace("’", "").split()).upper()


def para_codigo7(valor: str | int) -> str:
    codigo = str(valor).strip()
    if codigo in SENTINELAS_CODIGO:
        raise Sentinela(codigo)
    if codigo in todos():
        return codigo
    achado = _por_codigo6().get(codigo)
    if achado is None:
        raise MunicipioDesconhecido(codigo)
    return achado


def por_nome(nome: str) -> str:
    # o nome só é único dentro de Goiás; filtre a UF antes
    normalizado = normaliza_nome(nome)
    if normalizado in SENTINELAS_NOME:
        raise Sentinela(nome)
    achado = _por_nome().get(normalizado)
    if achado is None:
        raise MunicipioDesconhecido(nome)
    return achado
