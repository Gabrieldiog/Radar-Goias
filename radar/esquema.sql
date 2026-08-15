create table if not exists municipio (
    codigo_ibge      text primary key check (length(codigo_ibge) = 7),
    nome             text not null,
    nome_normalizado text not null unique
);

-- procedência: toda linha de dado aponta para a requisição que a trouxe
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
    -- estimativa e censo divergem 5% em Goiás; o indicador declara qual usou
    base        text    not null check (base in ('estimativa', 'censo')),
    coleta_id   bigint  references coleta,
    primary key (codigo_ibge, ano, base)
);
