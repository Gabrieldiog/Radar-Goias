import sys

from radar import banco, carga
from radar.http import Cliente


def main() -> int:
    with banco.conecta() as conn:
        resumo = carga.executa(conn, Cliente())
    print(f"municipios: {resumo['municipios']}  populacao: {resumo['populacao']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
