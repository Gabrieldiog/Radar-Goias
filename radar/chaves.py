"""Chaves de acesso à API: pedido, conferência e registro de uso.

Antes a chave era uma variável de ambiente. Para dar acesso a alguém era
preciso editar um arquivo no servidor e reiniciar a API, o que não é um
sistema, é um bilhete. Aqui a chave vira linha de tabela, com o nome de quem
pediu e a conta de quantas vezes ela foi usada.

As chaves do ambiente continuam valendo em paralelo: são a do painel e as de
quem já recebeu a sua, e tirá-las derrubaria o que está no ar.
"""

import secrets
from typing import NamedTuple

from psycopg.rows import dict_row

TAMANHO = 32
LIMITE_NOME = 120
LIMITE_MOTIVO = 300


class Chave(NamedTuple):
    chave: str
    nome: str
    motivo: str


def gera() -> str:
    # token_hex dá alfabeto [0-9a-f], que atravessa URL, cabeçalho e planilha
    # sem nada para escapar
    return secrets.token_hex(TAMANHO // 2)


def emite(conn, nome: str | None, motivo: str | None = "") -> Chave:
    nome = (nome or "").strip()
    motivo = (motivo or "").strip()
    if not nome:
        raise ValueError("diga quem está pedindo a chave")
    if len(nome) > LIMITE_NOME:
        raise ValueError(f"nome acima de {LIMITE_NOME} caracteres")
    motivo = motivo[:LIMITE_MOTIVO]
    nova = gera()
    conn.execute(
        "insert into chave_api (chave, nome, motivo) values (%s, %s, %s)",
        (nova, nome, motivo),
    )
    return Chave(chave=nova, nome=nome, motivo=motivo)


def confere(conn, chave) -> bool:
    if not isinstance(chave, str) or not chave.strip():
        return False
    # a mesma instrução confere e registra: sem ida e volta a mais, e sem
    # janela entre conferir e contar
    achou = conn.execute(
        "update chave_api set chamadas = chamadas + 1, ultimo_uso = now()"
        " where chave = %s returning chave",
        (chave.strip(),),
    ).fetchone()
    return achou is not None


def busca(conn, chave: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "select chave, nome, motivo, criada_em, ultimo_uso, chamadas"
            " from chave_api where chave = %s",
            (chave,),
        ).fetchone()
