"use client";

// Um quadrinho por município, do maior para o menor, com os sem dado no fim.
// É a única tela que mostra os 246 de uma vez, e ela responde de relance a
// pergunta que mais se repete neste projeto: quantos ficaram de fora?
const RAMPA = ["#e4e9e7", "#b9cfcb", "#7fafaa", "#3f8489", "#14555f"];

function cor(valor, maximo) {
  const posicao = Math.sqrt(valor / maximo);
  return RAMPA[Math.min(RAMPA.length - 1, Math.floor(posicao * RAMPA.length))];
}

const fmt = (v) => v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });

export default function Cobertura({ linhas, campo, unidade, total, selecionado, aoSelecionar }) {
  const com = linhas.filter((l) => l[campo] != null);
  if (!com.length) return null;
  const maximo = Math.max(...com.map((l) => l[campo])) || 1;
  const sem = total - com.length;

  return (
    <div className="cobertura">
      <div className="celulas">
        {com.map((l) => (
          <button
            key={l.codigo_ibge}
            className={l.codigo_ibge === selecionado ? "celula escolhida" : "celula"}
            style={{ background: cor(l[campo], maximo) }}
            onClick={() => aoSelecionar(l.codigo_ibge)}
            title={`${l.nome}: ${fmt(l[campo])} ${unidade}`}
            aria-label={`${l.nome}, ${fmt(l[campo])} ${unidade}`}
          />
        ))}
        {Array.from({ length: sem }, (_, i) => (
          <span key={`sem${i}`} className="celula sem" title="município sem este dado" />
        ))}
      </div>
      <p className="cobertura-nota">
        Cada quadrinho é um dos {total} municípios, do maior para o menor.{" "}
        {sem > 0 ? (
          <>
            Os {sem} vazios no fim não têm este dado publicado, o que é diferente de ter valor
            zero.
          </>
        ) : (
          <>Todos os {total} têm este dado publicado.</>
        )}
      </p>
    </div>
  );
}
