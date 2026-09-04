"use client";

// Desenha os 246 municípios em SVG a partir do contorno do IBGE, sem biblioteca
// de mapa. Para um estado só, uma projeção linear simples já sai correta.
const RAMPA = ["#e4e9e7", "#b9cfcb", "#7fafaa", "#3f8489", "#14555f"];

function aneis(geometria) {
  return geometria.type === "Polygon" ? geometria.coordinates : geometria.coordinates.flat();
}

function limites(features) {
  let [minX, minY, maxX, maxY] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const f of features)
    for (const anel of aneis(f.geometry))
      for (const [x, y] of anel) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
  return { minX, minY, maxX, maxY };
}

function traco(geometria, box, largura, altura) {
  const escala = Math.min(largura / (box.maxX - box.minX), altura / (box.maxY - box.minY));
  const px = (x) => (x - box.minX) * escala;
  // latitude cresce para cima e a tela cresce para baixo, então y inverte
  const py = (y) => (box.maxY - y) * escala;
  return aneis(geometria)
    .map((a) => "M" + a.map(([x, y]) => `${px(x).toFixed(1)},${py(y).toFixed(1)}`).join("L") + "Z")
    .join(" ");
}

// a raiz quadrada abre a parte de baixo da escala: sem ela, um município muito
// acima da média achata todos os outros numa cor só
function cor(valor, maximo) {
  if (valor == null) return null;
  const posicao = Math.sqrt(valor / maximo);
  return RAMPA[Math.min(RAMPA.length - 1, Math.floor(posicao * RAMPA.length))];
}

function numero(v) {
  return v == null ? "" : v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

export default function Mapa({ malha, valores, nomes, unidade, selecionado, aoSelecionar }) {
  const box = limites(malha.features);
  const largura = 700;
  const altura = Math.round(largura * ((box.maxY - box.minY) / (box.maxX - box.minX)));
  const presentes = Object.values(valores).filter((v) => v != null);
  const maximo = presentes.length ? Math.max(...presentes) : 1;
  const semDado = malha.features.length - presentes.length;

  return (
    <div>
      <svg viewBox={`0 0 ${largura} ${altura}`} className="mapa" role="img"
           aria-label={`Mapa de Goiás colorido por ${unidade}`}>
        <defs>
          <pattern id="hachura" width="5" height="5" patternUnits="userSpaceOnUse"
                   patternTransform="rotate(45)">
            <rect width="5" height="5" fill="#f8fafa" />
            <line x1="0" y1="0" x2="0" y2="5" stroke="#c8d2d3" strokeWidth="1.4" />
          </pattern>
        </defs>
        {malha.features.map((f) => {
          const codigo = f.properties.codarea;
          const valor = valores[codigo];
          const preenchimento = cor(valor, maximo) ?? "url(#hachura)";
          const escolhido = selecionado === codigo;
          return (
            <path
              key={codigo}
              d={traco(f.geometry, box, largura, altura)}
              fill={preenchimento}
              stroke={escolhido ? "#b8860b" : "#eef1f2"}
              strokeWidth={escolhido ? 2.2 : 0.5}
              onClick={() => aoSelecionar(codigo)}
            >
              <title>{`${nomes[codigo] ?? codigo}${valor == null ? ": sem dado" : `: ${numero(valor)}`}`}</title>
            </path>
          );
        })}
      </svg>

      <div className="legenda">
        <div className="escala">
          <span className="extremo">0</span>
          <div className="degraus">
            {RAMPA.map((c) => <span key={c} style={{ background: c }} />)}
          </div>
          <span className="extremo">{numero(maximo)}</span>
          <span>{unidade}</span>
        </div>
        {semDado > 0 && (
          <div className="sem">
            <svg width="18" height="11"><rect width="18" height="11" fill="url(#hachura)" /></svg>
            <span>
              {semDado} {semDado === 1 ? "município sem dado" : "municípios sem dado"} para este
              indicador. Isso é diferente de valor zero, que aparece na cor mais clara.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
