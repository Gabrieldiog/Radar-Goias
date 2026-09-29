"use client";

import { useState } from "react";
import { RAMPA, altura, degrau } from "./rampa";

// Uma barra por município, do maior para o menor, e as sem dado no fim. É a
// única vista que mostra os 246 de uma vez, e responde de relance a pergunta
// que mais se repete neste projeto: quantos ficaram de fora?
//
// Antes eram quadradinhos com três letras do nome. Três letras não separam
// Goiânia de Goianira, e em 4px nenhuma delas se lia. A altura diz mais e não
// precisa ser lida.
//
// As barras não entram na ordem do Tab: 246 paradas seriam uma armadilha para
// quem navega no teclado. A lista logo abaixo faz a mesma seleção, com botões
// de verdade, e é por ela que o teclado passa.

const fmt = (v) => v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });

export default function Cobertura({ linhas, municipios, campo, unidade, selecionado, aoSelecionar }) {
  const [sobre, setSobre] = useState(null);

  const com = linhas.filter((l) => l[campo] != null);
  if (!com.length) return null;

  const maximo = Math.max(...com.map((l) => l[campo])) || 1;
  const temDado = new Set(com.map((l) => l.codigo_ibge));
  const sem = municipios.filter((m) => !temDado.has(m.codigo_ibge));
  const total = municipios.length || com.length;

  const apontado =
    sobre ?? com.find((l) => l.codigo_ibge === selecionado) ??
    sem.find((m) => m.codigo_ibge === selecionado) ?? null;

  return (
    <figure className="faixa-246">
      <figcaption>
        <span>Os {total} municípios, do maior para o menor</span>
        <strong aria-live="polite">
          {apontado
            ? apontado[campo] != null
              ? `${apontado.nome}: ${fmt(apontado[campo])} ${unidade}`
              : `${apontado.nome}: sem este dado`
            : "Aponte uma barra para ver o nome"}
        </strong>
      </figcaption>

      <div
        className="torres"
        role="img"
        aria-label={`Distribuição de ${unidade} entre os ${total} municípios, do maior para o menor. ${sem.length} sem dado publicado.`}
        onMouseLeave={() => setSobre(null)}
      >
        <div className="bloco" style={{ flex: com.length }}>
          {com.map((l, i) => (
            <span
              key={l.codigo_ibge}
              className={`torre${l.codigo_ibge === selecionado ? " escolhida" : ""}`}
              style={{
                "--i": i,
                height: `${altura(l[campo], maximo)}%`,
                background: RAMPA[degrau(l[campo], maximo)],
              }}
              onMouseEnter={() => setSobre(l)}
              onClick={() => aoSelecionar(l.codigo_ibge)}
            />
          ))}
        </div>
        {sem.length > 0 && (
          <div className="bloco ausente" style={{ flex: sem.length }}>
            {sem.map((m, i) => (
              <span
                key={m.codigo_ibge}
                className={`torre vazia${m.codigo_ibge === selecionado ? " escolhida" : ""}`}
                style={{ "--i": com.length + i }}
                onMouseEnter={() => setSobre(m)}
                onClick={() => aoSelecionar(m.codigo_ibge)}
              />
            ))}
          </div>
        )}
      </div>

      {/* onde a faixa deixa de ter altura é a informação, e não um defeito do
          desenho: sem a divisa e os dois rótulos, um indicador com 23 dados em
          246 municípios parece um gráfico quebrado */}
      <div className="torres-eixo">
        <span>{com.length} com dado</span>
        {sem.length > 0 && <span>{sem.length} sem dado</span>}
      </div>

      <p className="faixa-nota">
        Cada barra é um município e a altura é o valor dele.{" "}
        {sem.length > 0
          ? `As ${sem.length} do fim, sem altura, não têm este dado publicado, o que é diferente de ter valor zero.`
          : `Todos os ${total} têm este dado publicado.`}
      </p>
    </figure>
  );
}
