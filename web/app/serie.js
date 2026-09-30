"use client";

import { RAMPA } from "./rampa";

// Um gráfico de série para as quatro coisas que o Radar sabe contar ao longo
// do tempo: dengue por ano, homicídio por mês, foco de queimada por dia e a
// nota do IDEB. Antes era uma barra chapada com o número em cima e mais nada:
// sem eixo de valor, quem olhava não sabia se a segunda barra era metade ou
// dois terços da primeira.
//
// A linha da mediana é o que separa "esse ano foi fora do comum" de "esse ano
// foi como sempre", e é a pergunta que a aba inteira faz.

const OURO = "#a9760a";
const TRACO = "#c3cfd0";

// O eixo precisa de número redondo nas quatro divisões, e não só no topo: com
// teto 75 as marcas caíam em 18,8 e 56,3, que ninguém lê. Escolhe-se primeiro
// o passo bonito, e o teto é quatro passos.
const PASSOS = [1, 2, 2.5, 5, 10];

export function escada(maximo) {
  if (maximo <= 0) return { alto: 1, passo: 0.25 };
  const cru = maximo / 4;
  const ordem = 10 ** Math.floor(Math.log10(cru));
  const passo = (PASSOS.find((p) => p * ordem >= cru) ?? 10) * ordem;
  return { alto: passo * 4, passo };
}

export function curto(v) {
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(1).replace(".", ",")} mi`;
  if (Math.abs(v) >= 10000) return `${Math.round(v / 1000)} mil`;
  return v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

function mediana(valores) {
  const ordenado = [...valores].sort((a, b) => a - b);
  const meio = Math.floor(ordenado.length / 2);
  return ordenado.length % 2 ? ordenado[meio] : (ordenado[meio - 1] + ordenado[meio]) / 2;
}

export default function Serie({ pontos, titulo, descricao }) {
  if (!pontos.length) return <p className="aviso">Não há dado para o que você pediu.</p>;

  const largura = 940;
  const altura = 340;
  const margem = { cima: 34, baixo: 54, esquerda: 56, direita: 14 };
  const util = {
    largura: largura - margem.esquerda - margem.direita,
    altura: altura - margem.cima - margem.baixo,
  };

  const valores = pontos.map((p) => p.valor);
  const { alto, passo } = escada(Math.max(...valores));
  const meio = mediana(valores);
  const base = margem.cima + util.altura;
  const fatia = util.largura / pontos.length;
  const barra = Math.min(fatia * 0.62, 54);
  const cx = (i) => margem.esquerda + fatia * i + fatia / 2;
  const y = (v) => base - (v / alto) * util.altura;

  const maior = pontos.reduce((a, b) => (b.valor > a.valor ? b : a));
  // com muitos pontos o rótulo de cada barra vira mancha; então só os extremos
  const rotulaTodos = pontos.length <= 12;
  const menor = pontos.reduce((a, b) => (b.valor < a.valor ? b : a));

  const linhas = [0, 1, 2, 3, 4].map((n) => passo * n);

  return (
    <div className="serie">
      <div className="grafico-caixa">
        <svg viewBox={`0 0 ${largura} ${altura}`} className="grafico" role="img"
             aria-label={descricao}>
          <text x={0} y={14} className="eixo-titulo">{titulo}</text>

          {linhas.map((v) => (
            <g key={v}>
              <line x1={margem.esquerda} x2={largura - margem.direita} y1={y(v)} y2={y(v)}
                    stroke={v === 0 ? "#9aa9ab" : "#e4eaea"} />
              <text x={margem.esquerda - 10} y={y(v) + 4} textAnchor="end" className="eixo">
                {curto(v)}
              </text>
            </g>
          ))}

          {/* a mediana é a régua contra a qual cada barra se explica */}
          <line x1={margem.esquerda} x2={largura - margem.direita} y1={y(meio)} y2={y(meio)}
                stroke={OURO} strokeWidth="1.2" strokeDasharray="5 4" opacity="0.75" />
          {/* à esquerda e colado no eixo: na direita ele batia no número da
              última barra sempre que a série terminava alta */}
          <text x={margem.esquerda + 6} y={y(meio) - 7} className="eixo-nota" fill={OURO}>
            mediana {curto(meio)}
          </text>

          {pontos.map((p, i) => {
            const h = Math.max(2, base - y(p.valor));
            const destaque = p.rotulo === maior.rotulo;
            return (
              <g key={p.rotulo} className="ponto">
                <rect x={cx(i) - barra / 2} y={base - h} width={barra} height={h} rx="3"
                      fill={p.parcial ? RAMPA[2] : destaque ? OURO : RAMPA[4]}>
                  <title>{`${p.rotulo}: ${p.valor.toLocaleString("pt-BR")}${p.detalhe ? ` (${p.detalhe})` : ""}`}</title>
                </rect>
                {(rotulaTodos || destaque || p.rotulo === menor.rotulo) && (
                  <text x={cx(i)} y={base - h - 8} textAnchor="middle" className="valor-barra">
                    {curto(p.valor)}
                  </text>
                )}
                <text x={cx(i)} y={base + 19} textAnchor="middle" className="eixo">{p.rotulo}</text>
                {p.parcial && (
                  <text x={cx(i)} y={base + 33} textAnchor="middle" className="eixo-nota">
                    parcial
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="legenda-cores">
        <span><i style={{ background: OURO }} /> o maior da série</span>
        <span><i style={{ background: RAMPA[4] }} /> período fechado</span>
        {pontos.some((p) => p.parcial) && (
          <span><i style={{ background: RAMPA[2] }} /> ainda em andamento</span>
        )}
        <span><i className="risco" /> mediana da série</span>
      </div>
    </div>
  );
}
