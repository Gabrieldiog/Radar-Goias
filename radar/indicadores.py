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


SERIE_DENGUE = """
select ano, sum(casos)::int as casos, count(*)::int as municipios
from caso_dengue
where (%s::text is null or codigo_ibge = %s::text)
group by ano
order by ano
"""


def serie_dengue(conn, codigo_ibge: str | None = None) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(SERIE_DENGUE, (codigo_ibge, codigo_ibge)).fetchall()


# o denominador é o aluno da rede municipal, não o total do território: o gasto
# declarado ao Tesouro é do município, e dividir pelo total daria a ele a conta
# do aluno que é do estado, do governo federal ou da escola particular
GASTO_POR_ALUNO = """
with pop as (
    select distinct on (codigo_ibge) codigo_ibge, ano, habitantes, base
    from populacao where base = %s order by codigo_ibge, ano desc
)
select d.codigo_ibge, m.nome, d.exercicio, d.empenhado,
       t.ano as ano_censo, t.alunos, t.escolas,
       p.habitantes, p.ano as ano_populacao, p.base as base_populacional,
       round(d.empenhado / t.alunos, 2)::float8 as por_aluno
from despesa_funcao d
join matricula t using (codigo_ibge)
join municipio m using (codigo_ibge)
join pop p using (codigo_ibge)
where d.funcao = 'educacao' and d.exercicio = %s
  and t.dependencia = 'municipal' and t.ano = %s
order by por_aluno desc
"""


def gasto_por_aluno(
    conn, exercicio: int | None = None, ano_censo: int | None = None, base: str = "estimativa"
) -> list[dict]:
    if exercicio is None:
        exercicio = conn.execute(
            "select max(exercicio) from despesa_funcao where funcao = 'educacao'"
        ).fetchone()[0]
    if ano_censo is None:
        ano_censo = conn.execute("select max(ano) from matricula").fetchone()[0]
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(GASTO_POR_ALUNO, (base, exercicio, ano_censo)).fetchall()


# anos iniciais na rede municipal é o recorte que o município de fato comanda:
# 241 dos 246 têm rede municipal aqui, contra 3 no ensino médio, que é do estado
IDEB_POR_MUNICIPIO = """
with pop as (
    select distinct on (codigo_ibge) codigo_ibge, ano, habitantes, base
    from populacao where base = %s order by codigo_ibge, ano desc
)
select i.codigo_ibge, m.nome, i.ano, i.etapa, i.rede,
       i.ideb::float8, i.meta::float8, i.rendimento::float8, i.nota::float8,
       case when i.meta is null then null else i.ideb >= i.meta end as bateu_meta,
       p.habitantes, p.ano as ano_populacao, p.base as base_populacional
from ideb i
join municipio m using (codigo_ibge)
left join pop p using (codigo_ibge)
where i.etapa = %s and i.rede = %s and i.ano = %s
order by i.ideb desc
"""


def ideb_por_municipio(
    conn,
    etapa: str = "anos_iniciais",
    rede: str = "municipal",
    ano: int | None = None,
    base: str = "estimativa",
) -> list[dict]:
    if ano is None:
        ano = conn.execute(
            "select max(ano) from ideb where etapa = %s and rede = %s", (etapa, rede)
        ).fetchone()[0]
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(IDEB_POR_MUNICIPIO, (base, etapa, rede, ano)).fetchall()


# o IDEB é o produto de duas coisas, e a fonte publica as duas separadas: o
# rendimento diz quanto se aprova e a nota diz quanto se aprende, então dá para
# ver se o município subiu porque reprova menos ou porque ensina mais
SERIE_IDEB = """
select ano, etapa, rede,
       round(avg(ideb), 2)::float8 as ideb,
       round(avg(meta), 2)::float8 as meta,
       round(avg(rendimento), 4)::float8 as rendimento,
       round(avg(nota), 2)::float8 as nota,
       count(*)::int as municipios
from ideb
where etapa = %s and rede = %s and (%s::text is null or codigo_ibge = %s::text)
group by ano, etapa, rede
order by ano
"""


def serie_ideb(
    conn,
    codigo_ibge: str | None = None,
    etapa: str = "anos_iniciais",
    rede: str = "municipal",
) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(SERIE_IDEB, (etapa, rede, codigo_ibge, codigo_ibge)).fetchall()


# cada conjunto de dados aponta para a requisição que o trouxe, então dá para
# dizer de onde veio, quando e com que resposta o servidor atendeu
FRESCOR = """
select t.tabela, t.linhas, c.fonte, c.url, c.status_http, c.bytes, c.executada_em
from (
    select 'Casos de dengue' as tabela, count(*)::int as linhas, max(coleta_id) as coleta
    from caso_dengue
    union all select 'Leitos da rede estadual', count(*)::int, max(coleta_id) from leito
    union all select 'Unidades básicas de saúde', count(*)::int, max(coleta_id) from ubs
    union all select 'Manifestações da ouvidoria', count(*)::int, max(coleta_id) from manifestacao
    union all select 'Despesa por função', count(*)::int, max(coleta_id) from despesa_funcao
    union all select 'Ocorrências criminais', count(*)::int, max(coleta_id) from ocorrencia
    union all select 'Matrículas do censo escolar', count(*)::int, max(coleta_id) from matricula
    union all select 'IDEB', count(*)::int, max(coleta_id) from ideb
    union all select 'População', count(*)::int, max(coleta_id) from populacao
) t
left join coleta c on c.id = t.coleta
where t.linhas > 0
order by c.executada_em desc nulls last
"""


def frescor(conn) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(FRESCOR).fetchall()


POR_FONTE = """
select fonte,
       count(*)::int as coletas,
       max(executada_em) as ultima,
       coalesce(sum(bytes), 0)::bigint as bytes,
       count(*) filter (where status_http >= 400)::int as recusadas
from coleta
group by fonte
order by max(executada_em) desc
"""


def por_fonte(conn) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(POR_FONTE).fetchall()

