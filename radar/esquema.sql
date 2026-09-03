create table if not exists municipio (
    codigo_ibge      text primary key check (length(codigo_ibge) = 7),
    nome             text not null,
    nome_normalizado text not null unique
);

create table if not exists coleta (
    id           bigserial primary key,
    fonte        text        not null,
    url          text        not null,
    status_http  integer,
    bytes        integer,
    executada_em timestamptz not null default now()
);

create table if not exists populacao (
    codigo_ibge text    not null references municipio,
    ano         integer not null,
    habitantes  integer not null check (habitantes > 0),
    base        text    not null check (base in ('estimativa', 'censo')),
    coleta_id   bigint  references coleta,
    primary key (codigo_ibge, ano, base)
);

create table if not exists caso_dengue (
    codigo_ibge text    not null references municipio,
    ano         integer not null,
    casos       integer not null check (casos >= 0),
    coleta_id   bigint  references coleta,
    primary key (codigo_ibge, ano)
);

create table if not exists leito (
    codigo_ibge text    not null references municipio,
    cnes        text    not null,
    tipo        text    not null,
    data        date    not null,
    implantados integer not null check (implantados >= 0),
    ocupados    integer not null check (ocupados >= 0),
    coleta_id   bigint  references coleta,
    primary key (cnes, tipo, data)
);

create table if not exists ubs (
    codigo_ibge text    not null references municipio,
    unidades    integer not null check (unidades >= 0),
    coleta_id   bigint  references coleta,
    primary key (codigo_ibge)
);

create table if not exists manifestacao (
    id        bigserial primary key,
    ano       integer not null,
    orgao     text    not null,
    tipo      text    not null,
    status    text    not null,
    dias      integer check (dias >= 0),
    total     integer not null check (total > 0),
    coleta_id bigint  references coleta,
    unique nulls not distinct (ano, orgao, tipo, status, dias)
);

create table if not exists despesa_funcao (
    codigo_ibge text    not null references municipio,
    exercicio   integer not null,
    funcao      text    not null check (funcao in ('saude', 'educacao', 'seguranca')),
    empenhado   numeric not null check (empenhado >= 0),
    pago        numeric not null check (pago >= 0),
    coleta_id   bigint  references coleta,
    primary key (codigo_ibge, exercicio, funcao)
);

create table if not exists ocorrencia (
    codigo_ibge text    not null references municipio,
    ano         integer not null,
    mes         integer not null check (mes between 1 and 12),
    evento      text    not null,
    abrangencia text    not null,
    vitimas     integer not null check (vitimas >= 0),
    coleta_id   bigint  references coleta,
    primary key (codigo_ibge, ano, mes, evento, abrangencia)
);
