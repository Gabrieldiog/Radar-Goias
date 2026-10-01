
# O coletor grava um apelido curto em cada requisição, e era ele que aparecia
# na tela: "ckan-go", "siconfi", "inpe-fogo". Isso não diz nada a quem lê, e
# desmentia o nome da instituição que a gente fala em voz alta.
#
# O apelido continua sendo a chave, porque é o que está gravado em milhares de
# linhas da tabela de coleta. Aqui mora só a tradução.
NOME_DA_FONTE = {
    "ckan-go": "Portal de Dados Abertos de Goiás",
    "ibge": "IBGE",
    "siconfi": "Tesouro Nacional, SICONFI",
    "sinesp": "Ministério da Justiça, SINESP",
    "inpe-fogo": "INPE, Programa Queimadas",
    "inep-ideb": "INEP, IDEB",
    "inep": "INEP, Censo Escolar",
}


def nome_da_fonte(apelido: str) -> str:
    return NOME_DA_FONTE.get(apelido, apelido)
