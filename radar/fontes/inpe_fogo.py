"""Focos de calor do INPE, do Programa Queimadas.

É a primeira fonte do projeto que muda ao longo do dia. As outras publicam uma
vez por ano ou por mês; esta publica um CSV por dia e vai enchendo ele conforme
os satélites passam. Por isso o foco tem identificador próprio do INPE, e
recarregar o mesmo dia atualiza em vez de duplicar.

Duas coisas precisam ficar ditas em qualquer número que sair daqui.

Um foco é uma detecção de satélite, não um incêndio. Doze satélites cobrem o
Brasil e vários veem o mesmo fogo na mesma passagem, então somar tudo conta a
mesma queimada mais de uma vez. Para comparar ao longo do tempo o INPE usa um
satélite de referência, porque a constelação mudou ao longo dos anos.

E três colunas do arquivo vêm vazias hoje: risco de fogo, dias sem chuva e
precipitação. Não construa indicador em cima delas sem conferir de novo.
"""

import csv
import io
from datetime import date, datetime
from typing import NamedTuple

from radar.municipios import MunicipioDesconhecido, Sentinela, para_codigo7

BASE = "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil"

# o INPE usa este para a série histórica; os outros entram na contagem do dia
SATELITE_DE_REFERENCIA = "AQUA_M-T"


class Foco(NamedTuple):
    id: str
    codigo_ibge: str
    detectado_em: datetime
    satelite: str
    bioma: str
    latitude: float
    longitude: float
    frp: float | None


def url_focos(dia: date) -> str:
    return f"{BASE}/focos_diario_br_{dia:%Y%m%d}.csv"


def _numero(valor) -> float | None:
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        return None


def le_focos(texto: str, estado: str = "GOIÁS") -> list[Foco]:
    achados: dict[str, Foco] = {}
    for linha in csv.DictReader(io.StringIO(texto)):
        if (linha.get("estado") or "").strip().upper() != estado.upper():
            continue
        latitude = _numero(linha.get("lat"))
        longitude = _numero(linha.get("lon"))
        if latitude is None or longitude is None:
            continue
        try:
            codigo = para_codigo7((linha.get("municipio_id") or "").strip())
        except (MunicipioDesconhecido, Sentinela):
            continue
        identificador = (linha.get("id") or "").strip()
        achados[identificador] = Foco(
            id=identificador,
            codigo_ibge=codigo,
            detectado_em=datetime.strptime(
                (linha.get("data_hora_gmt") or "").strip(), "%Y-%m-%d %H:%M:%S"
            ),
            satelite=(linha.get("satelite") or "").strip(),
            bioma=(linha.get("bioma") or "").strip(),
            latitude=latitude,
            longitude=longitude,
            frp=_numero(linha.get("frp")),
        )
    return list(achados.values())
