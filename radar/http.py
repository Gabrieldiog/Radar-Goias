"""Cliente HTTP das fontes públicas: no máximo uma requisição por segundo por domínio."""

import time
from typing import Any, NamedTuple

import httpx

UA = "RadarGoias/0.1 (+projeto academico UFG; contato rniedson@gmail.com)"


class Resposta(NamedTuple):
    payload: Any
    status: int
    bytes: int
    url: str


class Cliente:
    def __init__(self, transport=None, espera=1.0, relogio=time.monotonic, dorme=time.sleep):
        self._http = httpx.Client(transport=transport, headers={"user-agent": UA}, timeout=30)
        self._espera = espera
        self._relogio = relogio
        self._dorme = dorme
        self._ultimo: dict[str, float] = {}

    def json(self, url: str, timeout: float | None = None) -> Resposta:
        self._aguarda(httpx.URL(url).host)
        r = self._http.get(url, timeout=timeout or self._http.timeout)
        r.raise_for_status()
        return Resposta(r.json(), r.status_code, len(r.content), str(r.url))

    def _aguarda(self, host: str) -> None:
        anterior = self._ultimo.get(host)
        if anterior is not None:
            falta = self._espera - (self._relogio() - anterior)
            if falta > 0:
                self._dorme(falta)
        self._ultimo[host] = self._relogio()
