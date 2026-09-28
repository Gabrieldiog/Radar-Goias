"""Portal de dados abertos de Goiás: SQL de leitura direto no DataStore."""

import re
from typing import NamedTuple
from urllib.parse import quote

import httpx

from radar.consulta import exige_limite
from radar.municipios import MunicipioDesconhecido, Sentinela, para_codigo7

BASE = "https://dadosabertos.go.gov.br/api/3/action/datastore_search_sql"
DENGUE = "0c7c9ff8-cdb2-4cee-892d-c9ef28c0ba9f"
LEITOS = "17b6c28d-02b4-4696-a843-3759c50de0a3"
UBS = "ee0c17bf-e802-49bd-ac7d-5b1c71061bc1"
# a ouvidoria publica um arquivo por ano
MANIFESTACOES = {2026: "b350a63b-aaaa-450d-a377-e5dcc7701fd0"}
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


class Leito(NamedTuple):
    cnes: str
    tipo: str
    implantados: int
    ocupados: int


def sql_datas_leitos(ano: int, limite: int = 500) -> str:
    return exige_limite(
        f'SELECT DISTINCT "Data" AS data FROM "{LEITOS}"'
        f' WHERE "Data" LIKE \'%/{ano}\' LIMIT {limite}'
    )


def sql_leitos(data: str, recurso: str = LEITOS, limite: int = 2000) -> str:
    return exige_limite(
        'SELECT "Unidade de saude" AS unidade, "Tipo de acomodacao" AS tipo,'
        ' "Leitos/Implantados" AS implantados, "Leitos/Ocupados" AS ocupados'
        f' FROM "{recurso}" WHERE "Data" = \'{data}\' LIMIT {limite}'
    )


def le_leitos(payload) -> list[Leito]:
    if not payload.get("success"):
        raise ConsultaRecusada(f"o portal recusou a consulta: {payload.get('error')}")
    leitos = []
    for reg in payload["result"]["records"]:
        # a unidade traz o CNES colado no nome e com os zeros da esquerda comidos
        achado = re.match(r"\s*(\d+)", reg["unidade"] or "")
        if not achado:
            continue
        leitos.append(
            Leito(
                achado.group(1).zfill(7),
                reg["tipo"],
                int(float(reg["implantados"] or 0)),
                int(float(reg["ocupados"] or 0)),
            )
        )
    return leitos


def busca_leitos(cliente, ano: int):
    """Descobre a data mais recente e traz o retrato dela."""
    datas = cliente.json(f"{BASE}?sql={quote(sql_datas_leitos(ano))}", ESPERA_MAXIMA)
    if not datas.payload.get("success"):
        raise ConsultaRecusada(f"o portal recusou a consulta: {datas.payload.get('error')}")
    achadas = [r["data"] for r in datas.payload["result"]["records"]]
    if not achadas:
        raise ConsultaRecusada(f"nenhuma data de leitos em {ano}")
    data = max(achadas, key=lambda s: (s[6:], s[3:5], s[:2]))
    resposta = cliente.json(f"{BASE}?sql={quote(sql_leitos(data))}", ESPERA_MAXIMA)
    return le_leitos(resposta.payload), data, resposta


class Ubs(NamedTuple):
    codigo_ibge: str
    unidades: int


class Manifestacao(NamedTuple):
    ano: int
    orgao: str
    tipo: str
    status: str
    dias: int
    total: int


# A fonte escreve o turno por extenso. Estes dois dizem que a unidade atende
# depois do fim do expediente, que é o recorte do indicador.
#
# O plantão casa por prefixo de propósito: o texto entre parênteses varia na
# pontuação, e escrever "SABADOS,DOMINGOS" sem o espaço que a fonte usa fez as
# 38 unidades de 24 horas serem contadas como diurnas até isso ser pego.
NOTURNO_EXATO = "ATENDIMENTO NOS TURNOS DA MANHA, TARDE E NOITE"
NOTURNO_PREFIXO = "ATENDIMENTO CONTINUO DE 24 HORAS"


def atende_a_noite(turno: str) -> bool:
    turno = (turno or "").strip()
    return turno == NOTURNO_EXATO or turno.startswith(NOTURNO_PREFIXO)
FIM_DE_SEMANA = {"Sábado", "Domingo"}
VAZIOS = {"", "NAO INFORMADO", "NÃO INFORMADO"}


class Unidade(NamedTuple):
    cnes: str
    codigo_ibge: str
    nome: str
    tipo: str
    turno: str
    noite: bool
    sempre_aberto: bool
    fim_de_semana: bool
    dias: int
    latitude: float | None
    longitude: float | None
    regiao_saude: str
    macrorregiao: str


def sql_unidades(recurso: str = UBS, limite: int = 9000) -> str:
    return exige_limite(
        'SELECT "codigo_cnes" AS cnes,'
        ' "codigo_ibge_municipio_gestor" AS ibge,'
        ' "nome_fantasia" AS nome,'
        ' "tipo_unidade" AS tipo,'
        ' "turno_atendimento" AS turno,'
        ' "estabelecimento_sempre_aberto" AS sempre_aberto,'
        ' "dia_da_semana" AS dia,'
        ' "latitude" AS latitude,'
        ' "longitude" AS longitude,'
        ' "regiao_saude" AS regiao,'
        ' "macrorregiao" AS macrorregiao'
        f' FROM "{recurso}" LIMIT {limite}'
    )


def _coordenada(valor) -> float | None:
    if valor is None or str(valor).strip() in VAZIOS:
        return None
    try:
        return float(valor)
    except ValueError:
        return None


def le_unidades(payload) -> list[Unidade]:
    """Junta as linhas de dia da semana numa linha por unidade.

    Unidade sempre aberta não gera linha de dia nenhum na fonte, então ler a
    ausência como "não abre" inverteria o sentido: ela abre todo dia.
    """
    juntas: dict[str, dict] = {}
    for reg in _registros(payload):
        try:
            codigo = para_codigo7(reg["ibge"])
        except (Sentinela, MunicipioDesconhecido):
            continue
        atual = juntas.setdefault(
            reg["cnes"], {"registro": reg, "dias": set()}
        )
        dia = (reg.get("dia") or "").strip()
        if dia:
            atual["dias"].add(dia)
        atual["codigo_ibge"] = codigo

    unidades = []
    for cnes, junta in juntas.items():
        reg, dias = junta["registro"], junta["dias"]
        sempre = str(reg.get("sempre_aberto", "")).strip().upper() == "S"
        turno = (reg.get("turno") or "").strip()
        unidades.append(
            Unidade(
                cnes=cnes,
                codigo_ibge=junta["codigo_ibge"],
                nome=(reg.get("nome") or "").strip(),
                tipo=(reg.get("tipo") or "").strip(),
                turno=turno,
                noite=atende_a_noite(turno),
                sempre_aberto=sempre,
                fim_de_semana=sempre or bool(dias & FIM_DE_SEMANA),
                dias=7 if sempre else len(dias),
                latitude=_coordenada(reg.get("latitude")),
                longitude=_coordenada(reg.get("longitude")),
                regiao_saude=(reg.get("regiao") or "").strip(),
                macrorregiao=(reg.get("macrorregiao") or "").strip(),
            )
        )
    return unidades


def sql_ubs(recurso: str = UBS, limite: int = 300) -> str:
    return exige_limite(
        'SELECT "codigo_ibge_municipio_gestor" AS ibge,'
        ' COUNT(DISTINCT "codigo_cnes") AS ubs'
        f' FROM "{recurso}" GROUP BY "codigo_ibge_municipio_gestor" LIMIT {limite}'
    )


def sql_manifestacoes(ano: int, limite: int = 9000) -> str:
    return exige_limite(
        'SELECT "sigla" AS orgao, "tipo_manifestacao" AS tipo, "ds_status" AS status,'
        ' "dias_vida" AS dias, COUNT(*) AS total'
        f' FROM "{MANIFESTACOES[ano]}"'
        ' GROUP BY "sigla", "tipo_manifestacao", "ds_status", "dias_vida"'
        f' LIMIT {limite}'
    )


def _registros(payload):
    if not payload.get("success"):
        raise ConsultaRecusada(f"o portal recusou a consulta: {payload.get('error')}")
    return payload["result"]["records"]


def le_ubs(payload) -> list[Ubs]:
    unidades = []
    for reg in _registros(payload):
        try:
            codigo = para_codigo7(reg["ibge"])
        except Sentinela:
            continue
        unidades.append(Ubs(codigo, int(reg["ubs"])))
    return unidades


def le_manifestacoes(payload, ano: int) -> list[Manifestacao]:
    return [
        Manifestacao(
            ano,
            reg["orgao"],
            reg["tipo"],
            reg["status"],
            # a fonte escreve "34.0", e deixa vazio quando não registrou o prazo
            None if reg["dias"] is None else int(float(reg["dias"])),
            int(reg["total"]),
        )
        for reg in _registros(payload)
    ]
