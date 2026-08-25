"""Contorno geográfico dos 246 municípios, do IBGE, para o painel desenhar o mapa."""

import json
from functools import cache
from pathlib import Path

ARQUIVO = Path(__file__).parent / "dados" / "malha_go.json"


@cache
def geojson() -> dict:
    return json.loads(ARQUIVO.read_text(encoding="utf-8"))
