"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Faixa from "../faixa";

// o endereço entra na imagem no momento do build, porque o painel e a API
// respondem em portas diferentes e o navegador precisa do endereço de fora
const API = process.env.NEXT_PUBLIC_API_PUBLICA || "http://127.0.0.1:8000";

function Codigo({ children }) {
  return <pre className="codigo"><code>{children}</code></pre>;
}

export default function UsarApi() {
  const [catalogo, setCatalogo] = useState([]);

  useEffect(() => {
    fetch("/api/radar/v1/indicadores")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setCatalogo(d?.dados || []))
      .catch(() => setCatalogo([]));
  }, []);

  return (
    <>
      <Faixa
        titulo="Puxar os dados pela API"
        apoio="Os mesmos números deste painel saem em JSON, com a fonte de cada um junto. Qualquer linguagem que fale HTTP consegue consumir."
      />

      <main className="painel">
        <p className="manchete">
          A API responde em <code className="endereco">{API}</code>. Você precisa de uma chave e
          do código IBGE de 7 dígitos do município. Nada mais.
        </p>

        <section className="vista bloco-eixo">
          <h2>Em três passos</h2>

          <ol className="passos">
            <li>
              <h3>Peça uma chave</h3>
              <p>
                Ela é um texto que identifica quem está chamando. Sem chave a resposta é 401, e
                com chave inválida também.
              </p>
            </li>
            <li>
              <h3>Mande a chave no cabeçalho</h3>
              <p>
                O cabeçalho <code>x-api-key</code> é a forma recomendada. Também vale
                <code>?chave=</code> na URL, mas aí ela fica gravada no log do servidor.
              </p>
              <Codigo>{`curl -H "x-api-key: SUA_CHAVE" \\\n  "${API}/v1/indicadores/incidencia-dengue"`}</Codigo>
            </li>
            <li>
              <h3>Filtre pelo município</h3>
              <p>
                A chave de junção é o código IBGE de 7 dígitos, o mesmo do mapa do IBGE. Não use
                nome: as fontes escrevem acento e apóstrofo de jeitos diferentes.
              </p>
              <Codigo>{`curl -H "x-api-key: SUA_CHAVE" \\\n  "${API}/v1/municipios"\n\ncurl -H "x-api-key: SUA_CHAVE" \\\n  "${API}/v1/indicadores/incidencia-dengue?municipio=5208707"`}</Codigo>
            </li>
          </ol>
        </section>

        <section className="vista bloco-eixo">
          <h2>O que volta</h2>
          <p className="apoio">
            Os números em <code>dados</code>, a contagem em <code>total</code>, e em
            <code>meta</code> de onde aquilo veio. Indicador por habitante traz o denominador em
            cada linha, para você conferir a conta.
          </p>
          <Codigo>{`{
  "dados": [
    {
      "codigo_ibge": "5208707",
      "nome": "Goiânia",
      "casos": 38232,
      "habitantes": 1503256,
      "ano_populacao": 2025,
      "por_100k": 2543.3
    }
  ],
  "total": 1,
  "meta": {
    "indicador": "incidencia-dengue",
    "dimensao": "municipio",
    "fontes": ["dadosabertos.go.gov.br", "servicodados.ibge.gov.br"]
  }
}`}</Codigo>
        </section>

        <section className="vista bloco-eixo">
          <h2>O catálogo, como a própria API devolve</h2>
          <p className="apoio">
            Esta tabela é o retorno de <code>GET /v1/indicadores</code> lido ao vivo. Se um
            indicador entrar amanhã, ele aparece aqui sozinho.
          </p>
          <div className="rolagem">
            <table className="tabela registro">
              <thead>
                <tr>
                  <th>Identificador</th>
                  <th>O que mede</th>
                  <th>A conta</th>
                </tr>
              </thead>
              <tbody>
                {catalogo.map((i) => (
                  <tr key={i.id}>
                    <td><code>{i.id}</code></td>
                    <td>{i.nome}</td>
                    <td className="conta">{i.formula}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {catalogo.length === 0 && <p className="aviso carregando">Carregando o catálogo.</p>}
        </section>

        <section className="vista bloco-eixo">
          <h2>As regras</h2>
          <dl className="regras">
            <dt>60 requisições por minuto</dt>
            <dd>
              Contadas por chave e não por IP. Numa faculdade todo mundo sai pelo mesmo IP, e um
              balde compartilhado faria um usuário derrubar os colegas. Ao estourar, a resposta é
              429, e os cabeçalhos <code>X-RateLimit-*</code> dizem quando reabre.
            </dd>
            <dt>Toda resposta declara a fonte</dt>
            <dd>
              E <code>GET /v1/procedencia</code> devolve o endereço, o status e a data de cada
              coleta. Nenhum número daqui existe sem essa linha.
            </dd>
            <dt>Município pequeno oscila</dt>
            <dd>
              Poucos casos numa cidade de dois mil habitantes viram uma taxa alta que não se
              repete no ano seguinte. Vale para todo indicador por habitante.
            </dd>
          </dl>
        </section>

        <footer className="rodape">
          A referência gerada pelo próprio código, com todos os parâmetros e um botão para testar
          na hora, fica em <a href={`${API}/docs`}>{API}/docs</a>. O contrato em OpenAPI está em{" "}
          <a href={`${API}/openapi.json`}>openapi.json</a>, e serve para gerar cliente
          automaticamente. <Link href="/">Voltar ao mapa</Link>.
        </footer>
      </main>
    </>
  );
}
