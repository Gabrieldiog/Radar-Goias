"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Faixa from "../faixa";

async function busca(caminho) {
  const r = await fetch(`/api/radar${caminho}`);
  if (!r.ok) throw new Error(`a API respondeu ${r.status}`);
  return r.json();
}

const NUM = (v) => (v == null ? "" : v.toLocaleString("pt-BR"));

// A página tinha duas tabelas e mais nada. Ler que um conjunto tem 50.320
// linhas e outro tem 246 não diz de relance quem carrega o peso da coleta: a
// barra atrás do número diz. A raiz abre a parte de baixo da escala, senão os
// conjuntos pequenos somem atrás do maior.
function Peso({ valor, maximo }) {
  const fracao = maximo > 0 ? Math.sqrt(valor / maximo) : 0;
  return <span className="peso" style={{ "--fracao": `${(fracao * 100).toFixed(1)}%` }} />;
}

function tamanho(bytes) {
  if (!bytes) return "sem corpo";
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1).replace(".", ",")} MB`;
  if (bytes >= 1e3) return `${Math.round(bytes / 1e3)} KB`;
  return `${bytes} B`;
}

function quando(iso) {
  if (!iso) return "sem registro";
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
}

// endereço de API é longo e cheio de parâmetro; o domínio é o que responde a
// pergunta "de quem veio", e o resto fica no title para quem quiser conferir
function dominio(url) {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

export default function Procedencia() {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    busca("/v1/procedencia").then(setDados).catch((e) => setErro(e.message));
  }, []);

  if (erro) return <main className="painel"><p className="erro">Não consegui carregar: {erro}</p></main>;
  if (!dados) return <main className="painel"><p className="aviso carregando">Carregando o registro.</p></main>;

  const linhas = dados.conjuntos.reduce((s, c) => s + c.linhas, 0);
  const recusadas = dados.fontes.reduce((s, f) => s + f.recusadas, 0);
  const coletas = dados.fontes.reduce((s, f) => s + f.coletas, 0);
  const maiorConjunto = Math.max(...dados.conjuntos.map((c) => c.linhas), 1);
  const maiorFonte = Math.max(...dados.fontes.map((f) => f.coletas), 1);

  return (
    <>
      <Faixa
        titulo="De onde veio cada número"
        apoio="Toda requisição feita a um servidor público fica gravada com data, endereço, status e tamanho da resposta. Nenhum número deste painel existe sem essa linha."
      />

      <main className="painel">
      <p className="manchete">
        {NUM(linhas)} linhas de dado, trazidas por {NUM(coletas)} requisições a{" "}
        {dados.fontes.length} fontes públicas.
        {recusadas > 0
          ? ` ${NUM(recusadas)} foram recusadas pelo servidor e ficaram registradas como recusa, em vez de sumirem.`
          : " Nenhuma foi recusada."}
      </p>

      <div className="tiles">
        {[
          { rotulo: "Linhas guardadas", valor: NUM(linhas), apoio: `em ${dados.conjuntos.length} conjuntos` },
          { rotulo: "Requisições feitas", valor: NUM(coletas), apoio: "uma por segundo, no máximo" },
          { rotulo: "Fontes públicas", valor: String(dados.fontes.length), apoio: "nenhuma conversa com a outra" },
          {
            rotulo: "Recusadas",
            valor: recusadas ? NUM(recusadas) : "nenhuma",
            apoio: recusadas ? "ficaram registradas" : "todas responderam",
            calma: recusadas === 0,
          },
        ].map((f, i) => (
          <div key={f.rotulo} className={`tile${f.calma ? " calma" : ""}`} style={{ "--i": i }}>
            <span className="tile-rotulo">{f.rotulo}</span>
            <strong className="tile-valor">{f.valor}</strong>
            <span className="tile-apoio">{f.apoio}</span>
          </div>
        ))}
      </div>

      <section className="vista bloco-eixo">
        <h2>O que está guardado, e de quando</h2>
        <div className="rolagem">
          <table className="tabela registro">
            <thead>
              <tr>
                <th>Conjunto</th>
                <th className="num">Linhas</th>
                <th>Veio de</th>
                <th className="num">Resposta</th>
                <th className="num">Tamanho</th>
                <th>Coletado em</th>
              </tr>
            </thead>
            <tbody>
              {dados.conjuntos.map((c) => (
                <tr key={c.tabela}>
                  <td>{c.tabela}</td>
                  <td className="num com-peso">
                    <Peso valor={c.linhas} maximo={maiorConjunto} />
                    {NUM(c.linhas)}
                  </td>
                  <td title={c.url || ""}>{c.url ? dominio(c.url) : "carga anterior"}</td>
                  <td className={c.status_http >= 400 ? "num recusa" : "num"}>
                    {c.status_http ?? "sem registro"}
                  </td>
                  <td className="num">{tamanho(c.bytes)}</td>
                  <td>{quando(c.executada_em)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="vista bloco-eixo">
        <h2>Quantas vezes batemos em cada porta</h2>
        <div className="rolagem">
          <table className="tabela registro">
            <thead>
              <tr>
                <th>Fonte</th>
                <th className="num">Requisições</th>
                <th className="num">Recusadas</th>
                <th className="num">Baixado</th>
                <th>Última vez</th>
              </tr>
            </thead>
            <tbody>
              {dados.fontes.map((f) => (
                <tr key={f.fonte}>
                  <td>{f.fonte}</td>
                  <td className="num com-peso">
                    <Peso valor={f.coletas} maximo={maiorFonte} />
                    {NUM(f.coletas)}
                  </td>
                  <td className={f.recusadas ? "num recusa" : "num"}>{NUM(f.recusadas)}</td>
                  <td className="num">{tamanho(f.bytes)}</td>
                  <td>{quando(f.ultima)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <footer className="rodape">
        O sistema pede no máximo uma requisição por segundo por domínio e se identifica em toda
        chamada, porque são servidores de governo e derrubar um deles não é parte do trabalho.
        Fonte que responde incompleta não grava nada pela metade.{" "}
        <Link href="/">Voltar ao mapa</Link>.
      </footer>
      </main>
    </>
  );
}
