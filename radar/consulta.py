"""SQL do DataStore de Goiás. O firewall do Estado responde 403 sem LIMIT."""

import re

LIMITE = re.compile(r"\blimit\s+(\d+)\s*;?\s*$", re.IGNORECASE)


class SqlSemLimite(Exception):
    def __init__(self, sql):
        super().__init__(
            f"consulta sem LIMIT no fim: o firewall do portal responde 403. sql: {sql!r}"
        )
        self.sql = sql


def exige_limite(sql: str) -> str:
    achado = LIMITE.search(sql or "")
    if not achado or int(achado.group(1)) < 1:
        raise SqlSemLimite(sql)
    return sql
