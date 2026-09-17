"""Confere que o pyproject declara tudo que o código importa.

O Docker instala só o que o pyproject lista. Biblioteca que está no ambiente de
desenvolvimento por acaso, arrastada por outra, não existe dentro da imagem, e a
primeira subida morre com ModuleNotFoundError. Foi o que aconteceu com openpyxl:
ele entrou no dia 11, ninguém reconstruiu a imagem, e o sistema ficou quebrado
para quem fosse rodar em casa.
"""

import ast
import re
import sys
import tomllib
from importlib.metadata import packages_distributions
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CODIGO = RAIZ / "radar"


def importados() -> set[str]:
    achados = set()
    for arquivo in CODIGO.rglob("*.py"):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                achados.update(a.name.split(".")[0] for a in no.names)
            elif isinstance(no, ast.ImportFrom) and no.level == 0 and no.module:
                achados.add(no.module.split(".")[0])
    return {m for m in achados if m != "radar" and m not in sys.stdlib_module_names}


def declaradas() -> set[str]:
    projeto = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    tudo = list(projeto["dependencies"])
    for extras in projeto.get("optional-dependencies", {}).values():
        tudo += list(extras)
    return {re.split(r"[<>=!\[ ]", d)[0].lower().replace("_", "-") for d in tudo}


def test_todo_import_externo_esta_no_pyproject():
    lista = declaradas()
    mapa = packages_distributions()
    faltando = []
    for modulo in sorted(importados()):
        pacotes = {d.lower().replace("_", "-") for d in mapa.get(modulo, [modulo])}
        if not pacotes & lista:
            faltando.append(f"{modulo} (instalaria com: {', '.join(sorted(pacotes))})")
    assert not faltando, "importado mas não declarado no pyproject: " + "; ".join(faltando)


def test_a_busca_de_imports_encontra_alguma_coisa():
    # sem isso, um erro no varredor faria o teste acima passar sempre
    assert {"fastapi", "httpx", "openpyxl", "psycopg"} <= importados()


def test_todo_dado_que_o_codigo_le_esta_versionado():
    """Arquivo que o código abre precisa estar no repositório, não só no disco.

    O certificado do INEP caiu na regra `*.pem` do .gitignore e não foi para o
    clone. Como o cliente HTTP o carrega ao nascer, toda coleta morria na
    máquina de quem baixou o projeto, e não só a do INEP.
    """
    import subprocess

    saida = subprocess.run(
        ["git", "ls-files", "radar/dados"], cwd=RAIZ, capture_output=True, text=True
    )
    rastreados = {linha for linha in saida.stdout.split("\n") if linha}
    no_disco = {
        str(a.relative_to(RAIZ))
        for a in (CODIGO / "dados").iterdir()
        if a.is_file() and a.suffix != ".pyc"
    }
    faltando = sorted(no_disco - rastreados)
    assert not faltando, "no disco mas fora do repositório: " + ", ".join(faltando)
