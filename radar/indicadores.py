from psycopg.rows import dict_row

# a população mais recente vale como denominador de qualquer ano, e o resultado
# diz qual ano foi usado para o leitor julgar
INCIDENCIA_DENGUE = """
with pop as (
    select distinct on (codigo_ibge) codigo_ibge, ano, habitantes, base
    from populacao where base = %s order by codigo_ibge, ano desc
)
select c.codigo_ibge, m.nome, c.ano, c.casos,
       p.habitantes, p.ano as ano_populacao, p.base as base_populacional,
       round(c.casos * 100000.0 / p.habitantes, 2)::float8 as por_100k
from caso_dengue c
join municipio m using (codigo_ibge)
join pop p using (codigo_ibge)
where c.ano = %s
order by por_100k desc
"""


def incidencia_dengue(conn, ano: int, base: str = "estimativa") -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(INCIDENCIA_DENGUE, (base, ano)).fetchall()
