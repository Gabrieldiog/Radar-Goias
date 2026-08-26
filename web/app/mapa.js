"use client";

// Desenha os 246 municípios em SVG a partir do GeoJSON do IBGE, sem biblioteca
// de mapa. Para um estado só, uma projeção linear simples já fica correta.
const CORES = ["#e8eef2", "#cfe0d8", "#a8cbb4", "#6fae8b", "#2f8f5b"];

function limites(features) {
  let [minX, minY, maxX, maxY] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const f of features) {
    for (const anel of aneis(f.geometry)) {
      for (const [x, y] of anel) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  return { minX, minY, maxX, maxY };
}

function aneis(geometria) {
  return geometria.type === "Polygon"
    ? geometria.coordinates
    : geometria.coordinates.flat();
}

function traco(geometria, box, largura, altura) {
  const escala = Math.min(
    largura / (box.maxX - box.minX),
    altura / (box.maxY - box.minY)
  );
  const px = (x) => (x - box.minX) * escala;
  // y é invertido porque latitude cresce para cima e a tela cresce para baixo
  const py = (y) => (box.maxY - y) * escala;
  return aneis(geometria)
    .map((anel) => "M" + anel.map(([x, y]) => `${px(x).toFixed(1)},${py(y).toFixed(1)}`).join("L") + "Z")
    .join(" ");
}

function faixa(valor, maximo) {
  if (valor == null) return CORES[0];
  const posicao = Math.sqrt(valor / maximo);
  return CORES[Math.min(CORES.length - 1, Math.floor(posicao * CORES.length))];
}

export default function Mapa({ malha, valores, selecionado, aoSelecionar }) {
  const box = limites(malha.features);
  const largura = 760;
  const altura = Math.round(largura * ((box.maxY - box.minY) / (box.maxX - box.minX)));
  const maximo = Math.max(...Object.values(valores), 1);

  return (
    <svg viewBox={`0 0 ${largura} ${altura}`} className="mapa" role="img">
      {malha.features.map((f) => {
        const codigo = f.properties.codarea;
        return (
          <path
            key={codigo}
            d={traco(f.geometry, box, largura, altura)}
            fill={faixa(valores[codigo], maximo)}
            stroke={selecionado === codigo ? "#111" : "#fff"}
            strokeWidth={selecionado === codigo ? 1.6 : 0.4}
            onClick={() => aoSelecionar(codigo)}
          />
        );
      })}
    </svg>
  );
}
