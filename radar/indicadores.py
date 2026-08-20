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


# só a rede estadual entra aqui; o arquivo do estado não cobre hospital
# municipal nem privado, e o rótulo precisa dizer isso
LEITOS_POR_100MIL = """
with pop as (
    select distinct on (codigo_ibge) codigo_ibge, ano, habitantes, base
    from populacao where base = %s order by codigo_ibge, ano desc
),
rede as (
    select codigo_ibge, sum(implantados) as leitos, sum(ocupados) as ocupados,
           count(distinct cnes) as unidades, max(data) as data
    from leito where data = (select max(data) from leito) group by codigo_ibge
)
select r.codigo_ibge, m.nome, r.leitos, r.ocupados, r.unidades, r.data,
       p.habitantes, p.ano as ano_populacao, p.base as base_populacional,
       round(r.leitos * 100000.0 / p.habitantes, 1)::float8 as por_100mil,
       round(r.ocupados * 100.0 / nullif(r.leitos, 0), 1)::float8 as ocupacao_pct
from rede r
join municipio m using (codigo_ibge)
join pop p using (codigo_ibge)
order by por_100mil desc
"""


def leitos_por_100mil(conn, base: str = "estimativa") -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(LEITOS_POR_100MIL, (base,)).fetchall()
