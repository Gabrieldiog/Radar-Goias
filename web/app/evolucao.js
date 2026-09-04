"use client";

// Barra com o número escrito em cima. Numa linha, o leitor tem que medir a
// altura contra o eixo para saber quanto foi; aqui ele lê.
const TEAL = "#3f8489";
const OURO = "#a9760a";
const CLARO = "#a9c4c4";

export default function Evolucao({ serie, onde }) {
  if (!serie.length) return <p className="aviso">Não há caso registrado em {onde}.</p>;

  const largura = 940;
  const altura = 330;
  const margem = { cima: 42, baixo: 52, esquerda: 10, direita: 10 };
  const util = {
    largura: largura - margem.esquerda - margem.direita,
    altura: altura - margem.cima - margem.baixo,
  };
  const maximo = Math.max(...serie.map((p) => p.casos));
  const fatia = util.largura / serie.length;
  const barra = Math.min(fatia * 0.66, 56);
  const base = margem.cima + util.altura;
  const cx = (i) => margem.esquerda + fatia * i + fatia / 2;

  // com dezessete barras não cabe "437 mil" em cima de cada uma sem encostar na
  // vizinha, então a unidade é dita uma vez no topo e a barra fica só com o número
  const escala = maximo >= 20000 ? 1000 : 1;
  const curto = (v) => {
    const n = v / escala;
    return n < 10 && escala > 1
      ? n.toFixed(1).replace(".", ",")
      : Math.round(n).toLocaleString("pt-BR");
  };

  const pico = serie.reduce((a, b) => (b.casos > a.casos ? b : a));
  const brando = serie.reduce((a, b) => (b.casos < a.casos ? b : a));
  const corrente = new Date().getFullYear();
  const temParcial = serie.some((p) => p.ano === corrente);
  const vezes = (pico.casos / Math.max(brando.casos, 1)).toFixed(1).replace(".", ",");

  return (
    <div>
      <svg viewBox={`0 0 ${largura} ${altura}`} className="grafico" role="img"
           aria-label={`Casos de dengue por ano em ${onde}`}>
        <text x={margem.esquerda} y={16} className="eixo-titulo">
          Casos notificados{escala > 1 ? ", em milhares" : ""}
        </text>
        <line x1={margem.esquerda} x2={largura - margem.direita} y1={base} y2={base}
              stroke="#b6c2c4" />
        {serie.map((p, i) => {
          const h = Math.max(2, (p.casos / maximo) * util.altura);
          const parcial = p.ano === corrente;
          return (
            <g key={p.ano}>
              <rect x={cx(i) - barra / 2} y={base - h} width={barra} height={h}
                    fill={p.ano === pico.ano ? OURO : parcial ? CLARO : TEAL}>
                <title>{`${p.ano}: ${p.casos.toLocaleString("pt-BR")} casos em ${p.municipios} municípios`}</title>
              </rect>
              <text x={cx(i)} y={base - h - 9} textAnchor="middle" className="valor-barra">
                {curto(p.casos)}
              </text>
              <text x={cx(i)} y={base + 19} textAnchor="middle" className="eixo">{p.ano}</text>
              {parcial && (
                <text x={cx(i)} y={base + 34} textAnchor="middle" className="eixo-nota">
                  parcial
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div className="legenda-cores">
        <span><i style={{ background: OURO }} /> pior ano da série</span>
        <span><i style={{ background: TEAL }} /> ano fechado</span>
        {temParcial && <span><i style={{ background: CLARO }} /> ano ainda em andamento</span>}
      </div>

      <p className="aviso">
        Casos de dengue notificados em {onde}, somando os doze meses de cada ano. {pico.ano} teve{" "}
        {vezes} vezes mais casos que {brando.ano}, o ano mais brando dos {serie.length} da série.
        {temParcial && ` O ano de ${corrente} ainda não terminou, então a última barra vai crescer.`}
      </p>
    </div>
  );
}
