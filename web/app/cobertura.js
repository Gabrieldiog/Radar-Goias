"use client";

// Um quadrinho por município, do maior para o menor, com os sem dado no fim.
// É a única tela que mostra os 246 de uma vez, e ela responde de relance a
// pergunta que mais se repete neste projeto: quantos ficaram de fora?
const RAMPA = ["#d5e2de", "#b9cfcb", "#7fafaa", "#3f8489", "#14555f"];
const LIGACOES = new Set(["de", "do", "da", "dos", "das", "e"]);

function degrau(valor, maximo) {
  const posicao = Math.sqrt(valor / maximo);
  return Math.min(RAMPA.length - 1, Math.floor(posicao * RAMPA.length));
}

// "Aparecida de Goiânia" vira AG e "Uruaçu" vira URU. Não é identificador, é
// pista: três letras não separam Goiânia de Goianira, e o nome inteiro está no
// tooltip de quem precisar ter certeza.
function iniciais(nome) {
  const palavras = nome.split(/\s+/).filter((p) => !LIGACOES.has(p.toLowerCase()));
  if (palavras.length > 1) {
    return palavras.slice(0, 3).map((p) => p[0]).join("").toUpperCase();
  }
  return nome.slice(0, 3).toUpperCase();
}

const fmt = (v) => v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });

export default function Cobertura({ linhas, municipios, campo, unidade, selecionado, aoSelecionar }) {
  const com = linhas.filter((l) => l[campo] != null);
  if (!com.length) return null;

  const maximo = Math.max(...com.map((l) => l[campo])) || 1;
  const temDado = new Set(com.map((l) => l.codigo_ibge));
  const sem = municipios.filter((m) => !temDado.has(m.codigo_ibge));
  const total = municipios.length || com.length;

  return (
    <div className="cobertura">
      <div className="celulas">
        {com.map((l) => {
          const nivel = degrau(l[campo], maximo);
          return (
            <button
              key={l.codigo_ibge}
              className={`celula n${nivel}${l.codigo_ibge === selecionado ? " escolhida" : ""}`}
              style={{ background: RAMPA[nivel] }}
              onClick={() => aoSelecionar(l.codigo_ibge)}
              title={`${l.nome}: ${fmt(l[campo])} ${unidade}`}
            >
              <span aria-hidden="true">{iniciais(l.nome)}</span>
              <span className="oculto">{`${l.nome}, ${fmt(l[campo])} ${unidade}`}</span>
            </button>
          );
        })}
        {sem.map((m) => (
          <button
            key={m.codigo_ibge}
            className={`celula sem${m.codigo_ibge === selecionado ? " escolhida" : ""}`}
            onClick={() => aoSelecionar(m.codigo_ibge)}
            title={`${m.nome}: sem este dado publicado`}
          >
            <span aria-hidden="true">{iniciais(m.nome)}</span>
            <span className="oculto">{`${m.nome}, sem este dado`}</span>
          </button>
        ))}
      </div>
      <p className="cobertura-nota">
        Cada quadrinho é um dos {total} municípios, do maior para o menor, com as iniciais do nome.
        Clique em um para achá-lo na lista.{" "}
        {sem.length > 0
          ? `Os ${sem.length} hachurados no fim não têm este dado publicado, o que é diferente de ter valor zero.`
          : `Todos os ${total} têm este dado publicado.`}
      </p>
    </div>
  );
}
