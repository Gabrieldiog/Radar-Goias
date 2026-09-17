"use client";

// O IDEB é o produto de duas coisas que a fonte publica separadas: quanto se
// aprova e quanto se aprende. Mostrar só a nota final esconde qual das duas
// mexeu, e é justamente aí que está a leitura que ninguém publica.
const TEAL = "#3f8489";
const OURO = "#a9760a";
const VINHO = "#8c2f18";

const n1 = (v) => (v == null ? "" : v.toFixed(1).replace(".", ","));
const pct = (v) => (v == null ? "" : `${Math.round(v * 100)}%`);

function diagnostico(serie) {
  // procura a maior queda de um ponto para o outro, que é onde a decomposição
  // tem algo a dizer; se nunca caiu, fala do trecho inteiro
  let queda = null;
  for (let i = 1; i < serie.length; i++) {
    const delta = serie[i].ideb - serie[i - 1].ideb;
    if (delta < 0 && (queda === null || delta < queda.delta)) {
      queda = { delta, de: serie[i - 1], para: serie[i] };
    }
  }
  const primeiro = serie[0];
  const ultimo = serie[serie.length - 1];
  if (queda) {
    const fluxoSubiu = queda.para.rendimento >= queda.de.rendimento;
    return fluxoSubiu
      ? `De ${queda.de.ano} para ${queda.para.ano} a nota caiu de ${n1(queda.de.ideb)} para ${n1(
          queda.para.ideb
        )}, mas a aprovação subiu. A queda veio da aprendizagem, não da reprovação.`
      : `De ${queda.de.ano} para ${queda.para.ano} a nota caiu de ${n1(queda.de.ideb)} para ${n1(
          queda.para.ideb
        )}, e a aprovação caiu junto.`;
  }
  return `A nota saiu de ${n1(primeiro.ideb)} em ${primeiro.ano} para ${n1(ultimo.ideb)} em ${
    ultimo.ano
  }, com a aprovação indo de ${pct(primeiro.rendimento)} a ${pct(ultimo.rendimento)}.`;
}

export default function Aprendizagem({ serie, onde }) {
  if (!serie.length) return <p className="aviso">Não há IDEB publicado para {onde}.</p>;

  const largura = 940;
  const altura = 300;
  const margem = { cima: 42, baixo: 42, esquerda: 10, direita: 10 };
  const util = {
    largura: largura - margem.esquerda - margem.direita,
    altura: altura - margem.cima - margem.baixo,
  };
  // a escala vai até 10 porque é o teto do IDEB, e não até o maior valor visto:
  // assim a altura da barra significa a mesma coisa em qualquer município
  const TETO = 10;
  const fatia = util.largura / serie.length;
  const barra = Math.min(fatia * 0.62, 52);
  const base = margem.cima + util.altura;
  const cx = (i) => margem.esquerda + fatia * i + fatia / 2;

  const ultimo = serie[serie.length - 1];
  const teto = serie.reduce((a, b) => (b.ideb > a.ideb ? b : a));

  return (
    <div>
      <p className="veredito">{diagnostico(serie)}</p>

      <svg viewBox={`0 0 ${largura} ${altura}`} className="grafico" role="img"
           aria-label={`IDEB por ano em ${onde}`}>
        <text x={margem.esquerda} y={16} className="eixo-titulo">
          IDEB, numa escala que vai até 10
        </text>
        <line x1={margem.esquerda} x2={largura - margem.direita} y1={base} y2={base}
              stroke="#b6c2c4" />
        {serie.map((p, i) => {
          const h = Math.max(2, (p.ideb / TETO) * util.altura);
          return (
            <g key={p.ano}>
              <rect x={cx(i) - barra / 2} y={base - h} width={barra} height={h}
                    fill={p.ano === teto.ano ? OURO : TEAL}>
                <title>
                  {`${p.ano}: IDEB ${n1(p.ideb)}, aprovação ${pct(p.rendimento)}, aprendizagem ${n1(p.nota)}`}
                </title>
              </rect>
              <text x={cx(i)} y={base - h - 9} textAnchor="middle" className="valor-barra">
                {n1(p.ideb)}
              </text>
              <text x={cx(i)} y={base + 19} textAnchor="middle" className="eixo">{p.ano}</text>
            </g>
          );
        })}
      </svg>

      <div className="decomposicao">
        <table className="tabela">
          <caption>
            As duas metades que formam a nota. A aprovação já está perto do teto, então daqui em
            diante quase todo ganho tem que vir da aprendizagem.
          </caption>
          <thead>
            <tr>
              <th>Ano</th>
              {serie.map((p) => <th key={p.ano} className="num">{p.ano}</th>)}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Aprovação</td>
              {serie.map((p) => <td key={p.ano} className="num">{pct(p.rendimento)}</td>)}
            </tr>
            <tr>
              <td>Aprendizagem</td>
              {serie.map((p) => <td key={p.ano} className="num">{n1(p.nota)}</td>)}
            </tr>
          </tbody>
        </table>
      </div>

      <p className="aviso">
        Anos iniciais do ensino fundamental, rede municipal, que é a etapa que o município de fato
        comanda: 241 dos 246 têm rede própria aqui, contra 3 no ensino médio, que é do estado.
        {ultimo.municipios != null &&
          ` O último ano reúne ${ultimo.municipios} municípios com nota publicada.`}
      </p>
    </div>
  );
}
