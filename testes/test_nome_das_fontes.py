"""Testa o nome que a página mostra para cada fonte.

A tela listava o apelido que o coletor usa por dentro: "ckan-go", "siconfi",
"inpe-fogo". Isso não diz nada a quem está lendo, e desmentia o que a gente
fala em voz alta, que é o nome da instituição. O apelido continua existindo
porque é a chave que o coletor grava, mas agora ele vem acompanhado do nome.
"""

import pytest

from radar.fontes import NOME_DA_FONTE, nome_da_fonte


# Verifica que todo apelido que o coletor usa tem nome de gente.
@pytest.mark.parametrize(
    "apelido", ["ckan-go", "ibge", "siconfi", "sinesp", "inpe-fogo", "inep-ideb", "inep"]
)
def test_todo_apelido_tem_nome(apelido):
    assert apelido in NOME_DA_FONTE
    assert nome_da_fonte(apelido) != apelido


# Verifica os nomes que a gente fala na apresentação, um por um.
@pytest.mark.parametrize(
    "apelido,esperado",
    [
        ("ckan-go", "Portal de Dados Abertos de Goiás"),
        ("ibge", "Instituto Brasileiro de Geografia e Estatística"),
        ("siconfi", "Tesouro Nacional"),
        ("sinesp", "Ministério da Justiça e Segurança Pública"),
        ("inpe-fogo", "Instituto Nacional de Pesquisas Espaciais"),
    ],
)
def test_o_nome_e_o_da_instituicao(apelido, esperado):
    assert nome_da_fonte(apelido).startswith(esperado)


# Verifica que as duas entradas do INEP não viram a mesma linha na tela. São a
# mesma instituição, mas arquivos diferentes, e duas linhas iguais pareceriam
# defeito.
def test_as_duas_do_inep_se_distinguem():
    a, b = nome_da_fonte("inep-ideb"), nome_da_fonte("inep")
    assert a != b
    assert a.startswith("Instituto Nacional de Estudos")
    assert b.startswith("Instituto Nacional de Estudos")


# Verifica que apelido desconhecido devolve ele mesmo, em vez de quebrar. Fonte
# nova entra no coletor antes de alguém lembrar de batizar.
def test_apelido_desconhecido_devolve_ele_mesmo():
    assert nome_da_fonte("fonte-que-ainda-nao-existe") == "fonte-que-ainda-nao-existe"


# Verifica que nenhum nome vem vazio ou só com espaço.
def test_nenhum_nome_vazio():
    assert all(n.strip() for n in NOME_DA_FONTE.values())


# Verifica que nenhum nome é só uma sigla. Quem abre a página não é obrigado a
# saber o que significa INEP, SICONFI ou SINESP.
@pytest.mark.parametrize("sigla", ["IBGE", "INEP", "INPE", "SICONFI", "SINESP"])
def test_nenhum_nome_e_so_sigla(sigla):
    assert sigla not in NOME_DA_FONTE.values()
