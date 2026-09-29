"use client";

import { fmt } from "./indicadores";

// Quatro números que situam o indicador antes de qualquer gráfico: os dois
// extremos, o meio e quantos ficaram de fora.
//
// A mediana, e não a média: um município de dois mil habitantes com valor fora
// da curva desloca a média do estado inteiro, e o painel inteiro já trata isso
// assim nos cruzamentos.

function mediana(valores) {
  const meio = Math.floor(valores.length / 2);
  return valores.length % 2 ? valores[meio] : (valores[meio - 1] + valores[meio]) / 2;
}

export default function Resumo({ linhas, municipios, campo, unidade }) {
  const com = linhas.filter((l) => l[campo] != null);
  if (com.length < 3) return null;

  const ordenados = [...com].sort((a, b) => b[campo] - a[campo]);
  const alto = ordenados[0];
  const baixo = ordenados[ordenados.length - 1];
  const meio = mediana([...com.map((l) => l[campo])].sort((a, b) => a - b));
  const total = municipios.length || com.length;
  const sem = total - com.length;

  const fichas = [
    { rotulo: "Maior", valor: fmt(alto[campo]), apoio: alto.nome },
    { rotulo: "Mediana", valor: fmt(meio), apoio: `${com.length} municípios com dado` },
    { rotulo: "Menor", valor: fmt(baixo[campo]), apoio: baixo.nome },
    {
      rotulo: "Sem o dado",
      valor: sem ? String(sem) : "nenhum",
      apoio: sem ? `de ${total} municípios` : `os ${total} publicaram`,
      apagada: sem === 0,
    },
  ];

  return (
    <div className="tiles">
      {fichas.map((f, i) => (
        <div key={f.rotulo} className={`tile${f.apagada ? " calma" : ""}`} style={{ "--i": i }}>
          <span className="tile-rotulo">{f.rotulo}</span>
          <strong className="tile-valor">{f.valor}</strong>
          <span className="tile-apoio">{f.apoio}</span>
        </div>
      ))}
      <p className="tiles-unidade">Valores em {unidade}.</p>
    </div>
  );
}
