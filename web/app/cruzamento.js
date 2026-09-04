"use client";

// Nuvem de 246 pontos não responde nada a quem olha. Aqui os municípios entram
// em cinco grupos, do menor para o maior no indicador de baixo, e cada barra
// mostra quanto o grupo tem do outro indicador. Se as barras sobem, uma coisa
// acompanha a outra.

// mesma direção da rampa do mapa, sem o tom mais claro, que some no fundo
const RAMPA = ["#cbdedb", "#9fc4c0", "#6fa8a6", "#3f8489", "#14555f"];
const GRUPOS = 5;

// centavos e décimos em número de quatro dígitos só atrapalham a leitura
const num = (v) => v.toLocaleString("pt-BR", { maximumFractionDigits: v >= 100 ? 0 : 1 });

function meio(valores) {
  const v = [...valores].sort((a, b) => a - b);
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

export default function Cruzamento({ pontos, x, y, selecionado }) {
  if (pontos.length < GRUPOS * 2)
    return <p className="aviso">Só {pontos.length} municípios têm os dois indicadores, pouco para agrupar.</p>;

  const ordenados = [...pontos].sort((a, b) => a.x - b.x);
  const grupos = Array.from({ length: GRUPOS }, (_, i) => {
    const fatia = ordenados.slice(
      Math.floor((i * ordenados.length) / GRUPOS),
      Math.floor(((i + 1) * ordenados.length) / GRUPOS)
    );
    return {
      quantos: fatia.length,
      valor: meio(fatia.map((p) => p.y)),
      de: fatia[0].x,
      ate: fatia[fatia.length - 1].x,
      tem: fatia.some((p) => p.codigo === selecionado),
    };
  });

  const largura = 940;
  const altura = 330;
  const margem = { cima: 44, baixo: 96, esquerda: 10, direita: 10 };
  const util = {
    largura: largura - margem.esquerda - margem.direita,
    altura: altura - margem.cima - margem.baixo,
  };
  const maximo = Math.max(...grupos.map((g) => g.valor)) || 1;
  const fatia = util.largura / GRUPOS;
  const barra = Math.min(fatia * 0.56, 108);
  const base = margem.cima + util.altura;
  const cx = (i) => margem.esquerda + fatia * i + fatia / 2;

  const primeiro = grupos[0];
  const ultimo = grupos[GRUPOS - 1];
  const razao = primeiro.valor > 0 ? ultimo.valor / primeiro.valor : ultimo.valor > 0 ? 9 : 1;
  // só vale dizer que acompanha se as barras andarem na mesma direção; ponta
  // contra ponta esconde um meio que sobe e desce
  const subidas = grupos.filter((g, i) => i > 0 && g.valor > grupos[i - 1].valor).length;
  const veredito =
    pontos.length < 50
      ? `Só ${pontos.length} municípios têm os dois indicadores, então cada grupo fica com` +
        ` ${primeiro.quantos} ou ${ultimo.quantos} cidades e o desenho muda com pouca coisa.`
      : razao >= 1.3 && subidas >= 3
        ? "Uma coisa acompanha a outra."
        : razao <= 0.77 && subidas <= 1
          ? "Uma coisa anda ao contrário da outra."
          : razao > 0.77 && razao < 1.3
            ? "A diferença entre as pontas é pequena, então uma coisa não explica a outra."
            : "As barras sobem e descem sem ordem, então não dá para dizer que uma explica a outra.";
  const alvo = pontos.find((p) => p.codigo === selecionado);

  return (
    <div>
      <p className="veredito">
        Os {ultimo.quantos} municípios com maior {x.curto} têm {num(ultimo.valor)} {y.unidade}.
        Nos {primeiro.quantos} com menor, são {num(primeiro.valor)}. {veredito}
      </p>

      <svg viewBox={`0 0 ${largura} ${altura}`} className="grafico" role="img"
           aria-label={`${y.rotulo} de cada grupo de municípios, agrupados por ${x.curto}`}>
        <text x={margem.esquerda} y={16} className="eixo-titulo">
          {y.rotulo}, em {y.unidade}
        </text>
        <line x1={margem.esquerda} x2={largura - margem.direita} y1={base} y2={base}
              stroke="#b6c2c4" />
        {grupos.map((g, i) => {
          const h = Math.max(2, (g.valor / maximo) * util.altura);
          return (
            <g key={i}>
              <rect x={cx(i) - barra / 2} y={base - h} width={barra} height={h}
                    fill={RAMPA[i]} stroke={g.tem ? "#a9760a" : "#b6c2c4"}
                    strokeWidth={g.tem ? 2.5 : 0.8}>
                <title>{`${g.quantos} municípios, de ${num(g.de)} a ${num(g.ate)} em ${x.curto}`}</title>
              </rect>
              <text x={cx(i)} y={base - h - 10} textAnchor="middle" className="valor-barra">
                {num(g.valor)}
              </text>
              <text x={cx(i)} y={base + 20} textAnchor="middle" className="eixo">
                {num(g.de)} a {num(g.ate)}
              </text>
              <text x={cx(i)} y={base + 36} textAnchor="middle" className="eixo-nota">
                {g.quantos} municípios
              </text>
            </g>
          );
        })}
        <line x1={margem.esquerda + 20} x2={largura - margem.direita - 20} y1={base + 58}
              y2={base + 58} stroke="#b6c2c4" />
        <text x={margem.esquerda + 20} y={base + 76} className="eixo">menor {x.curto}</text>
        <text x={largura - margem.direita - 20} y={base + 76} textAnchor="end" className="eixo">
          maior {x.curto}
        </text>
      </svg>

      <p className="aviso">
        A altura é o valor do meio do grupo, a mediana, e não a média: uma cidade de dois mil
        habitantes com número fora da curva não desloca o grupo inteiro. Barra que sobe não quer
        dizer causa, porque município pequeno costuma cair na mesma ponta dos dois indicadores.
        {alvo && ` A barra contornada em ouro é o grupo onde está ${alvo.nome}.`}
      </p>
    </div>
  );
}
