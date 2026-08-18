import sys

from radar import banco, carga
from radar.http import Cliente


def main() -> int:
    with banco.conecta() as conn:
        cliente = Cliente()
        resumo = carga.executa(conn, cliente) | carga.executa_dengue(conn, cliente)
    for chave, valor in resumo.items():
        print(f"{chave}: {valor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
