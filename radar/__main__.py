import sys

from radar import banco, carga
from radar.http import Cliente


def main() -> int:
    # "financas" fica separado porque são 246 requisições ao Tesouro, uma por
    # segundo, e não faz sentido pagar esses minutos na carga de todo dia
    if len(sys.argv) > 1 and sys.argv[1] == "seguranca":
        with banco.conecta() as conn:
            resumo = carga.executa_seguranca(conn, Cliente())
        for chave, valor in resumo.items():
            print(f"{chave}: {valor}")
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "financas":
        with banco.conecta() as conn:
            resumo = carga.executa_financas(conn, Cliente())
        for chave, valor in resumo.items():
            print(f"{chave}: {valor}")
        return 0
    with banco.conecta() as conn:
        cliente = Cliente()
        resumo = (
            carga.executa(conn, cliente)
            | carga.executa_dengue(conn, cliente)
            | carga.executa_leitos(conn, cliente)
            | carga.executa_ubs(conn, cliente)
            | carga.executa_ouvidoria(conn, cliente)
        )
    for chave, valor in resumo.items():
        print(f"{chave}: {valor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
