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
