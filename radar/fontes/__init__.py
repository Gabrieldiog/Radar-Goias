
# O coletor grava um apelido curto em cada requisição, e era ele que aparecia
# na tela: "ckan-go", "siconfi", "inpe-fogo". Isso não diz nada a quem lê, e
# desmentia o nome da instituição que a gente fala em voz alta.
#
# O apelido continua sendo a chave, porque é o que está gravado em milhares de
# linhas da tabela de coleta. Aqui mora só a tradução.
# Por extenso, e não pela sigla: quem abre esta página não é obrigado a saber
# o que é INEP, SICONFI ou SINESP.
NOME_DA_FONTE = {
    "ckan-go": "Portal de Dados Abertos de Goiás",
    "ibge": "Instituto Brasileiro de Geografia e Estatística",
    "siconfi": "Tesouro Nacional",
    "sinesp": "Ministério da Justiça e Segurança Pública",
    "inpe-fogo": "Instituto Nacional de Pesquisas Espaciais",
    "inep-ideb": "Instituto Nacional de Estudos e Pesquisas Educacionais, IDEB",
    "inep": "Instituto Nacional de Estudos e Pesquisas Educacionais, censo escolar",
}


def nome_da_fonte(apelido: str) -> str:
    return NOME_DA_FONTE.get(apelido, apelido)
