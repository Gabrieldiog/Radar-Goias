"""Testa a leitura das matrículas do Censo Escolar do INEP.

O arquivo real tem 218 MB descomprimidos dentro de um ZIP de 33 MB, então os
testes montam um pequeno com a mesma estrutura.
"""

import zipfile

import pytest

from radar.fontes.inep import DEPENDENCIA, le_censo, url_censo

COLUNAS = [
    "NU_ANO_CENSO", "NO_MUNICIPIO", "CO_MUNICIPIO", "SG_UF",
    "TP_DEPENDENCIA", "TP_SITUACAO_FUNCIONAMENTO", "QT_MAT_BAS",
]


def zip_censo(tmp_path, linhas, ano=2024):
    corpo = ";".join(COLUNAS) + "\r\n"
    for l in linhas:
        corpo += ";".join("" if c is None else str(c) for c in l) + "\r\n"
    caminho = tmp_path / f"censo{ano}.zip"
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"censo_{ano}/leia-me/Leia-me.pdf", b"%PDF")
        z.writestr(f"censo_{ano}/dados/microdados_ed_basica_{ano}.csv", corpo.encode("latin-1"))
    return caminho


def linha(uf="GO", codigo="5208707", nome="GOIÂNIA", dependencia=3,
          situacao=1, alunos=500, ano=2024):
    return [ano, nome, codigo, uf, dependencia, situacao, alunos]


# Verifica que só as escolas do estado pedido entram.
def test_le_apenas_o_estado_pedido(tmp_path):
    caminho = zip_censo(tmp_path, [linha(), linha(uf="SP", codigo="3550308", nome="SAO PAULO")])
    linhas = le_censo(caminho, "GO")
    assert len(linhas) == 1
    assert linhas[0].codigo_ibge == "5208707"


# Verifica que o arquivo é lido em LATIN-1. Em UTF-8 o acento do nome do
# município levanta erro de decodificação, e só o cabeçalho é ASCII puro.
def test_le_o_arquivo_em_latin1(tmp_path):
    caminho = zip_censo(tmp_path, [linha(nome="ANÁPOLIS", codigo="5201108")])
    assert le_censo(caminho, "GO")[0].alunos == 500


# Verifica que escola paralisada ou extinta fica de fora. Só a situação 1 conta,
# senão o denominador inclui escola que não recebe aluno.
@pytest.mark.parametrize("situacao", [2, 3])
def test_escola_fora_de_atividade_nao_conta(tmp_path, situacao):
    caminho = zip_censo(tmp_path, [linha(situacao=situacao)])
    assert le_censo(caminho, "GO") == []


# Verifica que escola ativa sem matrícula informada não vira linha nem quebra a
# leitura. São 28 escolas em Goiás no censo de 2024.
def test_escola_ativa_sem_matricula_e_ignorada(tmp_path):
    caminho = zip_censo(tmp_path, [linha(alunos=None), linha()])
    assert len(le_censo(caminho, "GO")) == 1


# Verifica que as escolas do mesmo município e da mesma rede são somadas.
def test_agrega_escolas_do_mesmo_municipio_e_rede(tmp_path):
    caminho = zip_censo(tmp_path, [linha(alunos=300), linha(alunos=200)])
    m = le_censo(caminho, "GO")[0]
    assert (m.escolas, m.alunos) == (2, 500)


# Verifica que redes diferentes do mesmo município não se misturam. É o que
# separa o aluno da rede municipal, que é o denominador do gasto do município.
def test_separa_as_redes_do_mesmo_municipio(tmp_path):
    caminho = zip_censo(tmp_path, [linha(dependencia=3, alunos=700), linha(dependencia=2, alunos=540)])
    por_rede = {m.dependencia: m.alunos for m in le_censo(caminho, "GO")}
    assert por_rede == {"municipal": 700, "estadual": 540}


# Verifica que o código numérico da rede vira nome legível.
def test_traduz_o_codigo_da_rede(tmp_path):
    assert DEPENDENCIA == {"1": "federal", "2": "estadual", "3": "municipal", "4": "privada"}
    caminho = zip_censo(tmp_path, [linha(dependencia=4)])
    assert le_censo(caminho, "GO")[0].dependencia == "privada"


# Verifica que o ano vem da coluna do censo, e não do nome do arquivo.
def test_ano_vem_da_coluna_do_censo(tmp_path):
    caminho = zip_censo(tmp_path, [linha(ano=2023)])
    assert le_censo(caminho, "GO")[0].ano == 2023


# Verifica que município fora dos 246 não derruba a carga inteira.
def test_municipio_desconhecido_nao_quebra_a_leitura(tmp_path):
    caminho = zip_censo(tmp_path, [linha(codigo="9999999"), linha()])
    assert len(le_censo(caminho, "GO")) == 1


# Verifica que o CSV é achado dentro do ZIP mesmo com outros arquivos junto,
# porque o nome da pasta muda de um ano para o outro.
def test_acha_o_csv_entre_os_anexos(tmp_path):
    caminho = zip_censo(tmp_path, [linha()])
    with zipfile.ZipFile(caminho, "a") as z:
        z.writestr("censo_2024/Anexos/dicionario.xlsx", b"xx")
    assert len(le_censo(caminho, "GO")) == 1


# Verifica o endereço do arquivo do INEP.
def test_url_do_censo():
    assert url_censo(2024).endswith("/microdados_censo_escolar_2024.zip")
