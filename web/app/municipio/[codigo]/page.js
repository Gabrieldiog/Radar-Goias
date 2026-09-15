"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import Aprendizagem from "../../aprendizagem";
import { EIXOS, INDICADORES, fmt } from "../../indicadores";

async function busca(caminho) {
  const r = await fetch(`/api/radar${caminho}`);
  if (!r.ok) throw new Error(`a API respondeu ${r.status}`);
  return r.json();
}

// posição 1 quer dizer coisa diferente em cada indicador: estar no topo de
// leitos é bom e estar no topo de dengue é ruim, então o texto não julga, só
// diz onde o município está
function posicao(p) {
  if (!p) return "sem dado publicado";
  if (p.posicao === 1) return `o maior dos ${p.de} que têm esse dado`;
  if (p.posicao === p.de) return `o menor dos ${p.de} que têm esse dado`;
  return `${p.posicao}º de ${p.de}`;
}

export default function Municipio({ params }) {
  const { codigo } = use(params);
  const [ficha, setFicha] = useState(null);
  const [serie, setSerie] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    busca(`/v1/municipios/${codigo}`).then(setFicha).catch((e) => setErro(e.message));
    busca(`/v1/series/ideb?municipio=${codigo}`)
      .then((d) => setSerie(d.dados))
      .catch(() => setSerie([]));
  }, [codigo]);

  if (erro) return <main className="painel"><p className="erro">Não consegui carregar: {erro}</p></main>;
  if (!ficha) return <main className="painel"><p className="aviso">Carregando a ficha.</p></main>;

  const comDado = Object.keys(INDICADORES).filter(
    (id) => INDICADORES[id].eixo !== "Atendimento ao cidadão"
  );
  const cobertos = comDado.filter((id) => ficha.indicadores[id] != null).length;

  return (
    <main className="painel">
      <header className="capa">
        <Link href="/" className="voltar">Radar Goiás</Link>
        <h1>{ficha.nome}</h1>
        <p className="tese">
          {ficha.habitantes.toLocaleString("pt-BR")} moradores, pela estimativa do IBGE de{" "}
          {ficha.ano_populacao}. {cobertos} dos {comDado.length} indicadores têm dado publicado
          para este município.
        </p>
      </header>

      {EIXOS.filter((e) => e !== "Atendimento ao cidadão").map((eixo) => {
        const ids = comDado.filter((id) => INDICADORES[id].eixo === eixo);
        return (
          <section key={eixo} className="vista bloco-eixo">
            <h2>{eixo}</h2>
            <dl className="fichas">
              {ids.map((id) => {
                const meta = INDICADORES[id];
                const valor = ficha.indicadores[id];
                return (
                  <div key={id} className={valor == null ? "cartao vazio" : "cartao"}>
                    <dt>{meta.rotulo}</dt>
                    <dd className="numero">{valor == null ? "sem dado" : fmt(valor)}</dd>
                    <dd className="unidade">{meta.unidade}</dd>
                    <dd className="lugar">{posicao(ficha.posicoes?.[id])}</dd>
                  </div>
                );
              })}
            </dl>
          </section>
        );
      })}

      {serie && serie.length > 0 && (
        <section className="vista">
          <h2>Como a nota mudou aqui</h2>
          <Aprendizagem serie={serie} onde={ficha.nome} />
        </section>
      )}

      <footer className="rodape">
        Cada número vem de uma fonte pública diferente, com a data e o endereço da coleta
        registrados. Município pequeno oscila muito: poucos casos numa cidade de dois mil
        habitantes viram uma taxa alta que não se repete no ano seguinte.{" "}
        <Link href="/">Voltar ao mapa do estado</Link>.
      </footer>
    </main>
  );
}
