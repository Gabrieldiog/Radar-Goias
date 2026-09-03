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


UBS_POR_10MIL = """
with pop as (
    select distinct on (codigo_ibge) codigo_ibge, ano, habitantes, base
    from populacao where base = %s order by codigo_ibge, ano desc
)
select u.codigo_ibge, m.nome, u.unidades,
       p.habitantes, p.ano as ano_populacao, p.base as base_populacional,
       round(u.unidades * 10000.0 / p.habitantes, 2)::float8 as por_10mil
from ubs u
join municipio m using (codigo_ibge)
join pop p using (codigo_ibge)
order by por_10mil desc
"""

# o histograma guarda quantas manifestações levaram cada número de dias, então
# a média sai ponderada pela quantidade, e não como média de médias
OUVIDORIA_POR_ORGAO = """
select orgao,
       sum(total)::int as total,
       coalesce(sum(total) filter (where status <> 'Aberta'), 0)::int as finalizadas,
       coalesce(sum(total) filter (where status <> 'Aberta' and dias <= %s), 0)::int as no_prazo,
       round(
           100.0 * sum(total) filter (where status <> 'Aberta') / sum(total), 1
       )::float8 as taxa_finalizacao,
       round(
           100.0 * sum(total) filter (where status <> 'Aberta' and dias <= %s)
           / nullif(sum(total) filter (where status <> 'Aberta' and dias is not null), 0), 1
       )::float8 as taxa_no_prazo,
       round(
           sum(dias * total) filter (where status <> 'Aberta' and dias is not null)::numeric
           / nullif(sum(total) filter (where status <> 'Aberta' and dias is not null), 0), 1
       )::float8 as tempo_medio
from manifestacao
where ano = %s
group by orgao
order by total desc
"""


def ubs_por_10mil(conn, base: str = "estimativa") -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(UBS_POR_10MIL, (base,)).fetchall()


def ouvidoria_por_orgao(conn, ano: int | None = None, prazo: int = 30) -> list[dict]:
    if ano is None:
        ano = conn.execute("select max(ano) from manifestacao").fetchone()[0]
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(OUVIDORIA_POR_ORGAO, (prazo, prazo, ano)).fetchall()


DESPESA_PER_CAPITA = """
with pop as (
    select distinct on (codigo_ibge) codigo_ibge, ano, habitantes, base
    from populacao where base = %s order by codigo_ibge, ano desc
)
select d.codigo_ibge, m.nome, d.exercicio, d.funcao, d.empenhado, d.pago,
       p.habitantes, p.ano as ano_populacao, p.base as base_populacional,
       round(d.empenhado / p.habitantes, 2)::float8 as por_habitante
from despesa_funcao d
join municipio m using (codigo_ibge)
join pop p using (codigo_ibge)
where d.funcao = %s and d.exercicio = %s
order by por_habitante desc
"""


def despesa_per_capita(
    conn, funcao: str, exercicio: int | None = None, base: str = "estimativa"
) -> list[dict]:
    if exercicio is None:
        exercicio = conn.execute(
            "select max(exercicio) from despesa_funcao where funcao = %s", (funcao,)
        ).fetchone()[0]
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(DESPESA_PER_CAPITA, (base, funcao, exercicio)).fetchall()


# a abrangência entra no agrupamento porque o mesmo evento aparece medido por
# forças diferentes, e somar as duas contaria a mesma morte duas vezes
OCORRENCIAS_POR_100MIL = """
with pop as (
    select distinct on (codigo_ibge) codigo_ibge, ano, habitantes, base
    from populacao where base = %s order by codigo_ibge, ano desc
)
select o.codigo_ibge, m.nome, o.evento, o.abrangencia, o.ano,
       sum(o.vitimas)::int as vitimas,
       p.habitantes, p.ano as ano_populacao, p.base as base_populacional,
       round(sum(o.vitimas) * 100000.0 / p.habitantes, 2)::float8 as por_100mil
from ocorrencia o
join municipio m using (codigo_ibge)
join pop p using (codigo_ibge)
where o.evento = %s and o.ano = %s
group by o.codigo_ibge, m.nome, o.evento, o.abrangencia, o.ano,
         p.habitantes, p.ano, p.base
order by por_100mil desc
"""


def ocorrencias_por_100mil(
    conn, evento: str, ano: int | None = None, base: str = "estimativa"
) -> list[dict]:
    if ano is None:
        ano = conn.execute(
            "select max(ano) from ocorrencia where evento = %s", (evento,)
        ).fetchone()[0]
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(OCORRENCIAS_POR_100MIL, (base, evento, ano)).fetchall()
