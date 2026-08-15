"""Conexão e carga. Local no Docker, produção no Supabase, mesmo esquema."""

import os
from pathlib import Path

import psycopg

from radar import municipios

# 5433 porque a 5432 costuma já estar ocupada por outra instalação de Postgres
URL = os.environ.get("RADAR_BANCO_URL", "postgresql://localhost:5433/radar_goias")
ESQUEMA = Path(__file__).parent / "esquema.sql"


def conecta():
    return psycopg.connect(URL, autocommit=True)


def disponivel() -> bool:
    try:
        with psycopg.connect(URL, connect_timeout=2):
            return True
    except psycopg.Error:
        return False


def aplica_esquema(conn) -> None:
    conn.execute(ESQUEMA.read_text(encoding="utf-8"))


def carrega_municipios(conn) -> int:
    linhas = [
        (codigo, nome, municipios.normaliza_nome(nome))
        for codigo, nome in municipios.todos().items()
    ]
    conn.cursor().executemany(
        "insert into municipio values (%s, %s, %s) on conflict (codigo_ibge) do nothing",
        linhas,
    )
    return len(linhas)


def grava_populacao(conn, linhas) -> int:
    linhas = list(linhas)
    conn.cursor().executemany(
        "insert into populacao (codigo_ibge, ano, habitantes, base) values (%s, %s, %s, %s) "
        "on conflict (codigo_ibge, ano, base) do update set habitantes = excluded.habitantes",
        linhas,
    )
    return len(linhas)
