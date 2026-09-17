import Link from "next/link";

// Todas as telas abrem com a mesma faixa escura: marca à esquerda, atalhos à
// direita, título e linha de apoio embaixo. Um componente só para o desenho
// não se soltar de uma página para a outra.
export default function Faixa({ titulo, apoio, children }) {
  return (
    <header className="faixa">
      <div className="faixa-dentro">
        <div className="marca">
          <Link href="/" className="nome">Radar Goiás</Link>
          <nav className="atalhos">
            <Link href="/">Mapa do estado</Link>
            <Link href="/comparar">Comparar duas cidades</Link>
            <Link href="/procedencia">De onde veio cada número</Link>
          </nav>
        </div>
        <h1>{titulo}</h1>
        {apoio && <p className="tese">{apoio}</p>}
        {children}
      </div>
    </header>
  );
}
