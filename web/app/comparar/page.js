"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { EIXOS, INDICADORES, fmt } from "../indicadores";

const PADRAO_A = "5208707";
const PADRAO_B = "5201405";

async function busca(caminho) {
  const r = await fetch(`/api/radar${caminho}`);
  if (!r.ok) throw new Error(`a API respondeu ${r.status}`);
  return r.json();
}

// quem está melhor só faz sentido onde existe um lado melhor. Gastar mais por
// morador não é melhor nem pior, e fingir que é seria a pior leitura possível
// deste painel, já que a tese dele é justamente que gasto não prevê resultado.
function melhor(sentido, a, b) {
  if (sentido === "neutro" || a == null || b == null || a === b) return null;
  const maiorVence = sentido === "maior";
  return (a > b) === maiorVence ? "a" : "b";
}

function Linha({ id, a, b }) {
  const meta = INDICADORES[id];
  const va = a.indicadores[id];
  const vb = b.indicadores[id];
  const teto = Math.max(va ?? 0, vb ?? 0) || 1;
  const vence = melhor(meta.sentido, va, vb);

  return (
    <tr>
      <th scope="row">
        <span className="rotulo">{meta.rotulo}</span>
        <span className="unidade">{meta.unidade}</span>
      </th>
      {[
        ["a", va, a],
        ["b", vb, b],
      ].map(([lado, valor, ficha]) => (
        <td key={lado} className={vence === lado ? "lado vence" : "lado"}>
          <span className="valor">{valor == null ? "sem dado" : fmt(valor)}</span>
          <span className="barra" aria-hidden="true">
            <i style={{ width: `${((valor ?? 0) / teto) * 100}%` }} />
          </span>
          <span className="lugar">
            {ficha.posicoes[id] ? `${ficha.posicoes[id].posicao}º de ${ficha.posicoes[id].de}` : "sem dado"}
          </span>
        </td>
      ))}
    </tr>
  );
}

export default function Comparar() {
  const [municipios, setMunicipios] = useState([]);
  const [a, setA] = useState(PADRAO_A);
  const [b, setB] = useState(PADRAO_B);
  const [par, setPar] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    busca("/v1/municipios").then((d) => setMunicipios(d.dados)).catch((e) => setErro(e.message));
  }, []);

  useEffect(() => {
    if (a === b) return;
    setPar(null);
    setErro(null);
    busca(`/v1/comparar?a=${a}&b=${b}`).then((d) => setPar(d.dados)).catch((e) => setErro(e.message));
  }, [a, b]);

  const mapeaveis = Object.keys(INDICADORES).filter(
    (id) => INDICADORES[id].eixo !== "Atendimento ao cidadão"
  );

  return (
    <main className="painel">
      <header className="capa">
        <Link href="/" className="voltar">Radar Goiás</Link>
        <h1>Duas cidades, lado a lado</h1>
        <p className="tese">
          Os mesmos {mapeaveis.length} indicadores, calculados do mesmo jeito para as duas, com a
          posição de cada uma entre os 246 municípios.
        </p>
      </header>

      <div className="eixos">
        <label>
          De um lado
          <select value={a} onChange={(e) => setA(e.target.value)}>
            {municipios.map((m) => (
              <option key={m.codigo_ibge} value={m.codigo_ibge}>{m.nome}</option>
            ))}
          </select>
        </label>
        <label>
          Do outro
          <select value={b} onChange={(e) => setB(e.target.value)}>
            {municipios.map((m) => (
              <option key={m.codigo_ibge} value={m.codigo_ibge}>{m.nome}</option>
            ))}
          </select>
        </label>
      </div>

      {a === b && <p className="aviso">Escolha duas cidades diferentes para comparar.</p>}
      {erro && <p className="erro">Não consegui comparar: {erro}.</p>}

      {par && (
        <>
          <p className="veredito">
            {par[0].nome} tem {par[0].habitantes.toLocaleString("pt-BR")} moradores e {par[1].nome}{" "}
            tem {par[1].habitantes.toLocaleString("pt-BR")}, pela estimativa do IBGE de{" "}
            {par[0].ano_populacao}.
          </p>

          {EIXOS.filter((e) => e !== "Atendimento ao cidadão").map((eixo) => {
            const ids = mapeaveis.filter((id) => INDICADORES[id].eixo === eixo);
            if (!ids.length) return null;
            return (
              <section key={eixo} className="vista bloco-eixo">
                <h2>{eixo}</h2>
                <div className="rolagem">
                  <table className="duelo">
                    <thead>
                      <tr>
                        <th scope="col">Indicador</th>
                        <th scope="col">
                          <Link href={`/municipio/${par[0].codigo_ibge}`}>{par[0].nome}</Link>
                        </th>
                        <th scope="col">
                          <Link href={`/municipio/${par[1].codigo_ibge}`}>{par[1].nome}</Link>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {ids.map((id) => <Linha key={id} id={id} a={par[0]} b={par[1]} />)}
                    </tbody>
                  </table>
                </div>
              </section>
            );
          })}

          <p className="aviso">
            A barra de cada linha compara só aquela linha: ela enche até o maior dos dois valores, e
            não entre indicadores diferentes. O traço dourado marca quem está melhor, e ele não
            aparece nos indicadores de gasto, porque gastar mais por morador não é melhor nem pior.
            É justamente isso que este painel vem mostrando: dinheiro não prevê resultado.
          </p>
        </>
      )}

      <footer className="rodape">
        Município pequeno oscila muito, então diferença pequena entre duas cidades de poucos
        milhares de moradores pode sumir no ano seguinte. <Link href="/">Voltar ao mapa</Link>.
      </footer>
    </main>
  );
}
