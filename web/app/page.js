"use client";

import { useEffect, useState } from "react";
import Mapa from "./mapa";
import Tabela from "./tabela";
import Evolucao from "./evolucao";
import Cruzamento from "./cruzamento";
import { EIXOS, INDICADORES, fmt } from "./indicadores";

const MAPEAVEIS = Object.entries(INDICADORES).filter(([, v]) => v.eixo !== "Atendimento ao cidadão");

async function busca(caminho) {
  const r = await fetch(`/api/radar${caminho}`);
  if (!r.ok) throw new Error(`a API respondeu ${r.status}`);
  return r.json();
}

export default function Painel() {
  const [aba, setAba] = useState("mapa");
  const [malha, setMalha] = useState(null);
  const [municipios, setMunicipios] = useState([]);
  const [serie, setSerie] = useState(null);
  const [ondeSerie, setOndeSerie] = useState("");
  const [escolhido, setEscolhido] = useState("leitos-rede-estadual");
  const [resposta, setResposta] = useState(null);
  const [selecionado, setSelecionado] = useState(null);
  const [eixoX, setEixoX] = useState("gasto-saude-por-habitante");
  const [eixoY, setEixoY] = useState("incidencia-dengue");
  const [cruzados, setCruzados] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    busca("/v1/malha").then(setMalha).catch((e) => setErro(e.message));
    busca("/v1/municipios").then((d) => setMunicipios(d.dados)).catch((e) => setErro(e.message));
  }, []);

  useEffect(() => {
    if (aba !== "evolucao") return;
    setSerie(null);
    const filtro = ondeSerie ? `?municipio=${ondeSerie}` : "";
    busca(`/v1/series/dengue${filtro}`)
      .then((d) => setSerie(d.dados))
      .catch((e) => setErro(e.message));
  }, [aba, ondeSerie]);

  useEffect(() => {
    setResposta(null);
    setSelecionado(null);
    busca(`/v1/indicadores/${escolhido}`).then(setResposta).catch((e) => setErro(e.message));
  }, [escolhido]);

  useEffect(() => {
    if (aba !== "cruzamento") return;
    setCruzados(null);
    Promise.all([busca(`/v1/indicadores/${eixoX}`), busca(`/v1/indicadores/${eixoY}`)])
      .then(([x, y]) => {
        const outro = Object.fromEntries(
          y.dados.map((l) => [l.codigo_ibge, l[INDICADORES[eixoY].campo]])
        );
        setCruzados(
          x.dados
            .filter((l) => outro[l.codigo_ibge] != null)
            .map((l) => ({
              codigo: l.codigo_ibge,
              nome: l.nome,
              x: l[INDICADORES[eixoX].campo],
              y: outro[l.codigo_ibge],
            }))
        );
      })
      .catch((e) => setErro(e.message));
  }, [aba, eixoX, eixoY]);

  const meta = INDICADORES[escolhido];
  const linhas = resposta?.dados ?? [];
  const porOrgao = resposta?.meta?.dimensao === "orgao";
  const valores = Object.fromEntries(linhas.map((l) => [l.codigo_ibge, l[meta.campo]]));
  const nomes = Object.fromEntries(linhas.map((l) => [l.codigo_ibge, l.nome]));
  const ondeNome =
    municipios.find((m) => m.codigo_ibge === ondeSerie)?.nome ?? "Goiás inteiro";
  const posicao = linhas.findIndex((l) => l.codigo_ibge === selecionado);
  const detalhe = posicao >= 0 ? linhas[posicao] : null;

  return (
    <main className="painel">
      <header className="capa">
        <h1>Radar Goiás</h1>
        <p className="tese">
          Sete indicadores dos 246 municípios, calculados cruzando seis fontes públicas que não
          conversam entre si.
        </p>
      </header>

      <nav className="abas" aria-label="Escolha da visão">
        {[
          ["mapa", "Onde está"],
          ["cruzamento", "Uma coisa explica a outra?"],
          ["evolucao", "Como mudou"],
        ].map(([id, rotulo]) => (
          <button key={id} onClick={() => setAba(id)} aria-pressed={id === aba}>
            {rotulo}
          </button>
        ))}
      </nav>

      {erro && <p className="erro">Não consegui falar com a API: {erro}. Confira se ela está no ar.</p>}

      {!erro && aba === "evolucao" && (
        <section className="vista">
          <h2>Casos de dengue, ano a ano</h2>
          <p className="apoio">
            Dezessete anos da mesma base, para ver se um ano ruim foi fora do comum ou rotina.
          </p>
          <div className="eixos">
            <label>
              Onde
              <select value={ondeSerie} onChange={(e) => setOndeSerie(e.target.value)}>
                <option value="">Goiás inteiro, somando os 246 municípios</option>
                {municipios.map((m) => (
                  <option key={m.codigo_ibge} value={m.codigo_ibge}>{m.nome}</option>
                ))}
              </select>
            </label>
          </div>
          {serie ? (
            <Evolucao serie={serie} onde={ondeNome} />
          ) : (
            <p className="aviso">Carregando a série.</p>
          )}
        </section>
      )}

      {!erro && aba === "cruzamento" && (
        <section className="vista">
          <h2>Uma coisa explica a outra?</h2>
          <p className="apoio">
            Escolha dois indicadores. Os municípios entram em cinco grupos pelo primeiro, e as
            barras mostram quanto cada grupo tem do segundo.
          </p>
          <div className="eixos">
            <label>
              Agrupar os municípios por
              <select value={eixoX} onChange={(e) => setEixoX(e.target.value)}>
                {MAPEAVEIS.map(([id, v]) => <option key={id} value={id}>{v.rotulo}</option>)}
              </select>
            </label>
            <label>
              E comparar com
              <select value={eixoY} onChange={(e) => setEixoY(e.target.value)}>
                {MAPEAVEIS.map(([id, v]) => <option key={id} value={id}>{v.rotulo}</option>)}
              </select>
            </label>
          </div>
          {cruzados ? (
            <Cruzamento
              pontos={cruzados}
              x={INDICADORES[eixoX]}
              y={INDICADORES[eixoY]}
              selecionado={selecionado}
            />
          ) : (
            <p className="aviso">Cruzando os dois indicadores.</p>
          )}
        </section>
      )}

      {!erro && aba === "mapa" && (
        <section className="vista">
          <nav className="seletor" aria-label="Escolha do indicador">
            {EIXOS.map((eixo) => (
              <div key={eixo} className="grupo">
                <span className="grupo-nome">{eixo}</span>
                <div className="grupo-botoes">
                  {Object.entries(INDICADORES)
                    .filter(([, v]) => v.eixo === eixo)
                    .map(([id, v]) => (
                      <button key={id} onClick={() => setEscolhido(id)} aria-pressed={id === escolhido}>
                        {v.rotulo}
                      </button>
                    ))}
                </div>
              </div>
            ))}
          </nav>

          {!resposta ? (
            <p className="aviso">Carregando o indicador.</p>
          ) : (
            <>
              <p className="destaque">{meta.destaque(linhas, 246)}</p>

              {porOrgao ? (
                <Tabela linhas={linhas} />
              ) : !malha ? (
                <p className="aviso">Carregando o mapa.</p>
              ) : (
                <div className="quadro">
                  <Mapa
                    malha={malha}
                    valores={valores}
                    nomes={nomes}
                    unidade={meta.unidade}
                    selecionado={selecionado}
                    aoSelecionar={setSelecionado}
                  />
                  <section className="ranking">
                    <h3>Do maior para o menor</h3>
                    <ol>
                      {linhas.map((l, i) => (
                        <li
                          key={l.codigo_ibge}
                          onClick={() => setSelecionado(l.codigo_ibge)}
                          aria-current={l.codigo_ibge === selecionado}
                        >
                          <span className="pos">{i + 1}</span>
                          <span>{l.nome}</span>
                          <span className="valor">{fmt(l[meta.campo])}</span>
                        </li>
                      ))}
                    </ol>
                  </section>
                </div>
              )}

              {!porOrgao && (
                <div className="ficha">
                  {detalhe ? (
                    <>
                      <p>
                        <strong>{detalhe.nome}</strong> aparece em{" "}
                        <strong>{posicao + 1}º de {linhas.length}</strong>, com{" "}
                        {fmt(detalhe[meta.campo])} {meta.unidade}, entre{" "}
                        {detalhe.habitantes.toLocaleString("pt-BR")} moradores.
                      </p>
                      <p className="apoio">
                        População estimada pelo IBGE em {detalhe.ano_populacao}. Fontes:{" "}
                        {resposta.meta.fontes.join(", ")}.
                      </p>
                    </>
                  ) : (
                    <p className="apoio">
                      Clique num município, no mapa ou na lista, para ver a posição dele.
                    </p>
                  )}
                </div>
              )}
            </>
          )}
        </section>
      )}

      <footer className="rodape">
        Números calculados a partir de fontes públicas, com a data de cada coleta registrada.
        Município pequeno oscila muito: poucos casos numa cidade de dois mil habitantes viram
        uma taxa alta que não se repete no ano seguinte.
      </footer>
    </main>
  );
}
