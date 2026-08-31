"""Conexão e carga. Local no Docker, produção no Supabase, mesmo esquema."""

import os
from pathlib import Path

import psycopg

from radar import municipios

# 5433 porque a 5432 costuma já estar ocupada por outra instalação de Postgres
PADRAO = "postgresql://localhost:5433/radar_goias"


def url() -> str:
    # lido a cada chamada, e não na importação, para os testes poderem apontar
    # para outro banco sem apagar o de verdade
    return os.environ.get("RADAR_BANCO_URL", PADRAO)
ESQUEMA = Path(__file__).parent / "esquema.sql"


def conecta():
    return psycopg.connect(url(), autocommit=True)


def disponivel() -> bool:
    try:
        with psycopg.connect(url(), connect_timeout=2):
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


def grava_coleta(conn, fonte, url, status, tamanho) -> int:
    return conn.execute(
        "insert into coleta (fonte, url, status_http, bytes) values (%s, %s, %s, %s)"
        " returning id",
        (fonte, url, status, tamanho),
    ).fetchone()[0]


def grava_populacao(conn, linhas, coleta_id=None) -> int:
    linhas = [(*l, coleta_id) for l in linhas]
    conn.cursor().executemany(
        "insert into populacao (codigo_ibge, ano, habitantes, base, coleta_id)"
        " values (%s, %s, %s, %s, %s)"
        " on conflict (codigo_ibge, ano, base) do update set"
        " habitantes = excluded.habitantes, coleta_id = excluded.coleta_id",
        linhas,
    )
    return len(linhas)


def grava_casos_dengue(conn, casos, coleta_id=None) -> int:
    linhas = [(*c, coleta_id) for c in casos]
    conn.cursor().executemany(
        "insert into caso_dengue (codigo_ibge, ano, casos, coleta_id)"
        " values (%s, %s, %s, %s)"
        " on conflict (codigo_ibge, ano) do update set"
        " casos = excluded.casos, coleta_id = excluded.coleta_id",
        linhas,
    )
    return len(linhas)


def grava_leitos(conn, linhas, coleta_id=None) -> int:
    linhas = [(*l, coleta_id) for l in linhas]
    conn.cursor().executemany(
        "insert into leito (codigo_ibge, cnes, tipo, data, implantados, ocupados, coleta_id)"
        " values (%s, %s, %s, %s, %s, %s, %s)"
        " on conflict (cnes, tipo, data) do update set"
        " implantados = excluded.implantados, ocupados = excluded.ocupados,"
        " codigo_ibge = excluded.codigo_ibge, coleta_id = excluded.coleta_id",
        linhas,
    )
    return len(linhas)


def grava_ubs(conn, linhas, coleta_id=None) -> int:
    linhas = [(*l, coleta_id) for l in linhas]
    conn.cursor().executemany(
        "insert into ubs (codigo_ibge, unidades, coleta_id) values (%s, %s, %s)"
        " on conflict (codigo_ibge) do update set"
        " unidades = excluded.unidades, coleta_id = excluded.coleta_id",
        linhas,
    )
    return len(linhas)


def grava_manifestacoes(conn, linhas, coleta_id=None) -> int:
    linhas = [(*l, coleta_id) for l in linhas]
    conn.cursor().executemany(
        "insert into manifestacao (ano, orgao, tipo, status, dias, total, coleta_id)"
        " values (%s, %s, %s, %s, %s, %s, %s)"
        " on conflict (ano, orgao, tipo, status, dias) do update set"
        " total = excluded.total, coleta_id = excluded.coleta_id",
        linhas,
    )
    return len(linhas)
