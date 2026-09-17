"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Mapa from "./mapa";
import Tabela from "./tabela";
import Evolucao from "./evolucao";
import Cruzamento from "./cruzamento";
import Aprendizagem from "./aprendizagem";
import Cobertura from "./cobertura";
import { EIXOS, INDICADORES, fmt } from "./indicadores";

const MAPEAVEIS = Object.entries(INDICADORES).filter(([, v]) => v.eixo !== "Atendimento ao cidadão");

const ABAS = [
  ["mapa", "Onde está"],
  ["cruzamento", "Uma coisa explica a outra?"],
  ["evolucao", "Como mudou"],
];

// "goiania" precisa achar "Goiânia": quem digita rápido não põe acento, e o
// backend já normaliza do mesmo jeito para cruzar as fontes
const semAcento = (t) =>
  t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();

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
  const [assunto, setAssunto] = useState("dengue");
  const [escolhido, setEscolhido] = useState("leitos-rede-estadual");
  const [resposta, setResposta] = useState(null);
  const [selecionado, setSelecionado] = useState(null);
  const [filtro, setFiltro] = useState("");
  const lista = useRef(null);
  const escolhida = useRef(null);
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
    busca(`/v1/series/${assunto}${filtro}`)
      .then((d) => setSerie(d.dados))
      .catch((e) => setErro(e.message));
  }, [aba, assunto, ondeSerie]);

  useEffect(() => {
    setResposta(null);
    setSelecionado(null);
    busca(`/v1/indicadores/${escolhido}`)
      .then((d) => setResposta({ ...d, id: escolhido }))
      .catch((e) => setErro(e.message));
  }, [escolhido]);

  useEffect(() => {
    if (aba !== "cruzamento") return;
    setCruzados(null);
    Promise.all([busca(`/v1/indicadores/${eixoX}`), busca(`/v1/indicadores/${eixoY}`)])
      .then(([x, y]) => {
        const outro = Object.fromEntries(
          y.dados.map((l) => [l.codigo_ibge, l[INDICADORES[eixoY].campo]])
        );
        setCruzados({
          id: `${eixoX}|${eixoY}`,
          pontos: x.dados
            .filter((l) => outro[l.codigo_ibge] != null)
            .map((l) => ({
              codigo: l.codigo_ibge,
              nome: l.nome,
              x: l[INDICADORES[eixoX].campo],
              y: outro[l.codigo_ibge],
            })),
        });
      })
      .catch((e) => setErro(e.message));
  }, [aba, eixoX, eixoY]);

  // clicar no mapa ou no quadrinho leva a lista até o município, em vez de
  // deixar o usuário procurar à mão numa lista de 246
  useEffect(() => {
    const alvo = escolhida.current;
    const caixa = lista.current;
    if (!alvo || !caixa) return;
    const meio = alvo.offsetTop - caixa.clientHeight / 2 + alvo.clientHeight / 2;
    const suave = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    caixa.scrollTo({ top: Math.max(0, meio), behavior: suave ? "smooth" : "auto" });
  }, [selecionado, escolhido]);

  // vir do mapa com um filtro ligado esconderia justamente quem foi clicado
  const seleciona = (codigo) => {
    setFiltro("");
    setSelecionado(codigo);
  };

  const meta = INDICADORES[escolhido];
  const pronto = resposta?.id === escolhido;
  const linhas = pronto ? resposta.dados : [];
  const porOrgao = pronto && resposta.meta?.dimensao === "orgao";
  const valores = Object.fromEntries(linhas.map((l) => [l.codigo_ibge, l[meta.campo]]));
  const nomes = Object.fromEntries(linhas.map((l) => [l.codigo_ibge, l.nome]));
  const maiorValor = Math.max(...linhas.map((l) => l[meta.campo] ?? 0), 1);
  const ondeNome = municipios.find((m) => m.codigo_ibge === ondeSerie)?.nome ?? "Goiás inteiro";
  // a posição vem da lista inteira, para filtrar não renumerar o ranking
  const comPosicao = linhas.map((l, i) => ({ ...l, posicao: i + 1 }));
  const procurado = semAcento(filtro);
  const listados = procurado
    ? comPosicao.filter((l) => semAcento(l.nome).includes(procurado))
    : comPosicao;
  const posicao = linhas.findIndex((l) => l.codigo_ibge === selecionado);
  const detalhe = posicao >= 0 ? linhas[posicao] : null;

  return (
    <>
      <header className="faixa">
        <div className="faixa-dentro">
          <div className="marca">
            <Link href="/" className="nome">Radar Goiás</Link>
            <nav className="atalhos">
              <Link href="/comparar">Comparar duas cidades</Link>
              <Link href="/procedencia">De onde veio cada número</Link>
            </nav>
          </div>

          <h1>Os 246 municípios de Goiás, no mesmo lugar</h1>
          <p className="tese">
            <strong>{Object.keys(INDICADORES).length} indicadores</strong> calculados por nós,
            cruzando seis fontes públicas que não conversam entre si. Cada número traz junto de
            onde veio.
          </p>

          <nav className="abas" aria-label="Escolha da visão">
            {ABAS.map(([id, rotulo]) => (
              <button key={id} onClick={() => setAba(id)} aria-pressed={id === aba}>
                {rotulo}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="painel">
        {erro && (
          <p className="erro">Não consegui falar com a API: {erro}. Confira se ela está no ar.</p>
        )}

        {!erro && aba === "evolucao" && (
          <section className="vista">
            <h2>{assunto === "dengue" ? "Casos de dengue, ano a ano" : "IDEB, ano a ano"}</h2>
            <p className="apoio">
              {assunto === "dengue"
                ? "Dezessete anos da mesma base, para ver se um ano ruim foi fora do comum ou rotina."
                : "Vinte anos de nota, com as duas metades que a formam separadas."}
            </p>
            <div className="eixos">
              <label>
                O que
                <select value={assunto} onChange={(e) => setAssunto(e.target.value)}>
                  <option value="dengue">Casos de dengue</option>
                  <option value="ideb">IDEB dos anos iniciais</option>
                </select>
              </label>
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
            {!serie ? (
              <p className="aviso">Carregando a série.</p>
            ) : assunto === "dengue" ? (
              <Evolucao serie={serie} onde={ondeNome} />
            ) : (
              <Aprendizagem serie={serie} onde={ondeNome} />
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
            {cruzados?.id === `${eixoX}|${eixoY}` ? (
              <Cruzamento
                pontos={cruzados.pontos}
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
                        <button
                          key={id}
                          onClick={() => setEscolhido(id)}
                          aria-pressed={id === escolhido}
                        >
                          {v.rotulo}
                        </button>
                      ))}
                  </div>
                </div>
              ))}
            </nav>

            {!pronto ? (
              <p className="aviso">Carregando o indicador.</p>
            ) : (
              <>
                <p className="manchete">{meta.destaque(linhas, 246)}</p>

                {porOrgao ? (
                  <Tabela linhas={linhas} />
                ) : (
                  <>
                    <Cobertura
                      linhas={linhas}
                      municipios={municipios}
                      campo={meta.campo}
                      unidade={meta.unidade}
                      selecionado={selecionado}
                      aoSelecionar={seleciona}
                    />

                    {!malha ? (
                      <p className="aviso">Carregando o mapa.</p>
                    ) : (
                      <div className="quadro">
                        <Mapa
                          malha={malha}
                          valores={valores}
                          nomes={nomes}
                          unidade={meta.unidade}
                          selecionado={selecionado}
                          aoSelecionar={seleciona}
                        />
                        <section className="ranking">
                          <div className="ranking-topo">
                            <h3>Do maior para o menor</h3>
                            <input
                              type="search"
                              value={filtro}
                              onChange={(e) => setFiltro(e.target.value)}
                              placeholder="Procurar município"
                              aria-label="Procurar município na lista"
                            />
                          </div>
                          {procurado && (
                            <p className="ranking-conta">
                              {listados.length === 0
                                ? `Nenhum município com "${filtro}" tem este dado.`
                                : `${listados.length} de ${linhas.length} municípios.`}
                            </p>
                          )}
                          <ol ref={lista}>
                            {listados.map((l) => (
                              <li
                                key={l.codigo_ibge}
                                ref={l.codigo_ibge === selecionado ? escolhida : null}
                                onClick={() => setSelecionado(l.codigo_ibge)}
                                aria-current={l.codigo_ibge === selecionado}
                              >
                                <span
                                  className="fundo"
                                  style={{
                                    width: `calc(${((l[meta.campo] ?? 0) / maiorValor) * 100}% - 42px)`,
                                  }}
                                />
                                <span className="pos">{l.posicao}</span>
                                <span>{l.nome}</span>
                                <span className="valor">{fmt(l[meta.campo])}</span>
                              </li>
                            ))}
                          </ol>
                        </section>
                      </div>
                    )}
                  </>
                )}

                {!porOrgao && (
                  <div className="ficha">
                    {detalhe ? (
                      <>
                        <p>
                          <strong>{detalhe.nome}</strong> aparece em{" "}
                          <strong>{posicao + 1}º de {linhas.length}</strong>, com{" "}
                          {fmt(detalhe[meta.campo])} {meta.unidade}
                          {detalhe.habitantes
                            ? `, entre ${detalhe.habitantes.toLocaleString("pt-BR")} moradores.`
                            : "."}
                        </p>
                        <p className="apoio">
                          {detalhe.ano_populacao
                            ? `População estimada pelo IBGE em ${detalhe.ano_populacao}. `
                            : ""}
                          Fontes: {resposta.meta.fontes.join(", ")}.
                        </p>
                        <p>
                          <Link href={`/municipio/${detalhe.codigo_ibge}`} className="voltar">
                            Ver os {Object.keys(INDICADORES).length - 1} indicadores de{" "}
                            {detalhe.nome}
                          </Link>
                        </p>
                      </>
                    ) : selecionado ? (
                      <p className="apoio">
                        {municipios.find((m) => m.codigo_ibge === selecionado)?.nome ??
                          "Este município"}{" "}
                        não tem {meta.curto} publicado. Isso é diferente de ter valor zero.
                      </p>
                    ) : (
                      <p className="apoio">
                        Clique num município, no quadrinho, no mapa ou na lista, para ver a posição
                        dele.
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
          Município pequeno oscila muito: poucos casos numa cidade de dois mil habitantes viram uma
          taxa alta que não se repete no ano seguinte.
        </footer>
      </main>
    </>
  );
}
