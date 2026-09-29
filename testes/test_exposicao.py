"""Guarda as portas que o docker compose publica.

Em 28 de setembro de 2026 o banco subiu publicado em 0.0.0.0:5434 e com
autenticação confiada, ou seja, aberto para a internet inteira sem senha. Um
minerador entrou pela porta, trancou o usuário do Postgres e ficou 27 horas
consumindo a máquina. O painel caiu junto, com erro 500.

O Docker escreve as próprias regras de iptables e passa por cima de firewall,
então quem decide se a porta é pública é esta linha do compose e mais nada.
"""

import re
from pathlib import Path

COMPOSE = Path(__file__).parent.parent / "docker-compose.yml"

# quem pode ficar de frente para a internet, e por quê
PUBLICAS = {"8000": "a API é para ser consumida de fora", "3000": "o painel é a tela"}


def mapeamentos() -> list[str]:
    texto = COMPOSE.read_text()
    return re.findall(r'^\s*-\s*"([^"]+:\d+)"', texto, re.MULTILINE)


# Verifica que só a API e o painel ficam expostos, e que todo o resto publica
# preso ao próprio host.
def test_so_api_e_painel_ficam_publicos():
    for mapa in mapeamentos():
        interna = mapa.rsplit(":", 1)[1]
        if interna in PUBLICAS:
            continue
        assert mapa.startswith("127.0.0.1:"), (
            f"{mapa} publica a porta {interna} para qualquer endereço."
            " Prenda em 127.0.0.1 ou explique em PUBLICAS por que ela é pública."
        )


# Verifica que o banco não está entre as portas públicas, dito pelo nome, para
# o teste continuar valendo se alguém trocar o número da porta.
def test_o_banco_nao_e_publicado_para_fora():
    texto = COMPOSE.read_text()
    banco = texto.split("banco:", 1)[1].split("\n  api:", 1)[0]
    for mapa in re.findall(r'^\s*-\s*"([^"]+)"', banco, re.MULTILINE):
        assert mapa.startswith("127.0.0.1:"), f"o banco publicou {mapa} para fora"
