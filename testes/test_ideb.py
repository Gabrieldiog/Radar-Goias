"""Testa a leitura do IDEB do INEP.

A planilha real tem 133 colunas e 12 MB, então os testes montam uma pequena com
a mesma forma: nove linhas de cabeçalho humano antes do cabeçalho de máquina, e
uma coluna por ano em vez de uma coluna de ano.
"""

import zipfile

import openpyxl
import pytest

from radar.fontes.ideb import ETAPAS, REDES, Ideb, le_ideb, url_ideb

ANOS = [2005, 2021, 2025]
CABECALHO = (
    ["SG_UF", "CO_MUNICIPIO", "NO_MUNICIPIO", "REDE"]
    + [f"VL_APROVACAO_{a}_SI_4" for a in ANOS]
    + [f"VL_INDICADOR_REND_{a}" for a in ANOS]
    + [f"VL_NOTA_MATEMATICA_{a}" for a in ANOS]
    + [f"VL_NOTA_MEDIA_{a}" for a in ANOS]
    + [f"VL_OBSERVADO_{a}" for a in ANOS]
    + [f"VL_PROJECAO_{a}" for a in ANOS[:2]]
)


def planilha(tmp_path, linhas, etapa="anos_iniciais", ano=2025):
    livro = openpyxl.Workbook()
    pagina = livro.active
    pagina.title = "IDEB_AI_MUNICÍPIOS"
    for _ in range(9):
        pagina.append(["Ministério da Educação"])
    pagina.append(CABECALHO)
    for l in linhas:
        pagina.append(l)
    xlsx = tmp_path / "planilha.xlsx"
    livro.save(xlsx)
    caminho = tmp_path / f"{ETAPAS[etapa]}_{ano}.zip"
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pasta/md5.txt", b"abc")
        z.writestr(f"pasta/{ETAPAS[etapa]}_{ano}.xlsx", xlsx.read_bytes())
    return caminho


def linha(uf="GO", codigo=5208707, nome="Goiânia", rede="Municipal",
          ideb=(3.9, 6.1, 6.6), meta=(None, 6.1), rendimento=(0.9, 0.95, 0.99),
          nota=(4.3, 6.4, 6.66)):
    def tres(v):
        return list(v) + ["-"] * (3 - len(v))

    return (
        [uf, codigo, nome, rede]
        + tres(["-", "-", "-"])
        + tres([x if x is not None else "-" for x in rendimento])
        + tres(["-", "-", "-"])
        + tres([x if x is not None else "-" for x in nota])
        + tres([x if x is not None else "-" for x in ideb])
        + [x if x is not None else "-" for x in meta]
    )


# Verifica que o cabeçalho de máquina é achado na linha 10, e não na 1. As nove
# primeiras linhas são título e legenda escritos para gente ler.
def test_acha_o_cabecalho_na_linha_dez(tmp_path):
    caminho = planilha(tmp_path, [linha()])
    assert len(le_ideb(caminho, "anos_iniciais")) == 3


# Verifica que só as linhas do estado pedido entram.
def test_le_apenas_o_estado_pedido(tmp_path):
    caminho = planilha(tmp_path, [linha(), linha(uf="SP", codigo=3550308, nome="São Paulo")])
    assert {l.codigo_ibge for l in le_ideb(caminho, "anos_iniciais")} == {"5208707"}


# Verifica que uma coluna por ano vira uma linha por ano.
def test_transforma_coluna_de_ano_em_linha(tmp_path):
    caminho = planilha(tmp_path, [linha()])
    por_ano = {l.ano: l.ideb for l in le_ideb(caminho, "anos_iniciais")}
    assert por_ano == {2005: 3.9, 2021: 6.1, 2025: 6.6}


# Verifica que o traço, que é como a fonte escreve ausência de medida, não vira
# zero. Zero seria o pior IDEB possível, e ausência não é isso.
def test_traco_nao_vira_zero(tmp_path):
    caminho = planilha(tmp_path, [linha(ideb=(3.9, None, 6.6))])
    anos = {l.ano for l in le_ideb(caminho, "anos_iniciais")}
    assert anos == {2005, 2025}


# Verifica que a meta é lida junto, e que ano sem meta publicada fica nulo. A
# fonte projeta metas só até 2021.
def test_le_a_meta_e_aceita_ano_sem_meta(tmp_path):
    caminho = planilha(tmp_path, [linha()])
    por_ano = {l.ano: l.meta for l in le_ideb(caminho, "anos_iniciais")}
    assert por_ano[2021] == 6.1
    assert por_ano[2025] is None


# Verifica que as duas metades do IDEB são guardadas separadas. É o que permite
# dizer se o município melhorou por aprovar mais ou por aprender mais.
def test_guarda_fluxo_e_aprendizagem_separados(tmp_path):
    caminho = planilha(tmp_path, [linha()])
    l = [x for x in le_ideb(caminho, "anos_iniciais") if x.ano == 2025][0]
    assert (l.rendimento, l.nota) == (0.99, 6.66)


# Verifica que a rede vira nome em minúscula, e que existem quatro, não três. A
# planilha traz uma linha Federal em Goiás que a pesquisa não tinha visto.
def test_traduz_as_quatro_redes(tmp_path):
    assert REDES == {
        "Estadual": "estadual",
        "Municipal": "municipal",
        "Federal": "federal",
        "Pública": "publica",
    }
    caminho = planilha(tmp_path, [linha(rede="Federal")])
    assert le_ideb(caminho, "anos_iniciais")[0].rede == "federal"


# Verifica que a rede Pública é lida como rede própria. Ela é o agregado das
# outras, então nunca pode ser somada junto, e o nome separado deixa isso claro.
def test_publica_e_uma_rede_a_parte(tmp_path):
    caminho = planilha(tmp_path, [linha(rede="Municipal"), linha(rede="Pública")])
    redes = {l.rede for l in le_ideb(caminho, "anos_iniciais")}
    assert redes == {"municipal", "publica"}


# Verifica que rede desconhecida é ignorada em vez de derrubar a carga.
def test_rede_desconhecida_e_ignorada(tmp_path):
    caminho = planilha(tmp_path, [linha(rede="Conveniada"), linha()])
    assert {l.rede for l in le_ideb(caminho, "anos_iniciais")} == {"municipal"}


# Verifica que a etapa vem de fora, porque a planilha não diz qual é.
def test_etapa_vem_do_chamador(tmp_path):
    caminho = planilha(tmp_path, [linha()], etapa="ensino_medio")
    assert {l.etapa for l in le_ideb(caminho, "ensino_medio")} == {"ensino_medio"}


# Verifica que município fora dos 246 não derruba a carga inteira.
def test_municipio_desconhecido_nao_quebra_a_leitura(tmp_path):
    caminho = planilha(tmp_path, [linha(codigo=9999999), linha()])
    assert {l.codigo_ibge for l in le_ideb(caminho, "anos_iniciais")} == {"5208707"}


# Verifica que o valor inteiro da planilha vira float, porque o openpyxl devolve
# 4 em vez de 4.0 quando a célula não tem casa decimal.
def test_inteiro_da_planilha_vira_float(tmp_path):
    caminho = planilha(tmp_path, [linha(ideb=(4, 6.1, 6.6))])
    l = [x for x in le_ideb(caminho, "anos_iniciais") if x.ano == 2005][0]
    assert l.ideb == 4.0 and isinstance(l.ideb, float)


# Verifica o endereço dos três arquivos do INEP.
@pytest.mark.parametrize(
    "etapa,pedaco",
    [
        ("anos_iniciais", "divulgacao_anos_iniciais_municipios_2025.zip"),
        ("anos_finais", "divulgacao_anos_finais_municipios_2025.zip"),
        ("ensino_medio", "divulgacao_ensino_medio_municipios_2025.zip"),
    ],
)
def test_url_de_cada_etapa(etapa, pedaco):
    assert url_ideb(etapa, 2025).endswith(f"/ideb/resultados/{pedaco}")


# Verifica que a tupla carrega tudo que o indicador vai precisar.
def test_forma_da_tupla():
    assert Ideb._fields == (
        "codigo_ibge", "ano", "etapa", "rede", "ideb", "meta", "rendimento", "nota",
    )
