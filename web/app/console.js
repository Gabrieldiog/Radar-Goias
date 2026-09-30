"use client";

import { useState } from "react";

// O pedido de chave e o teste dela, na mesma tela. Antes a documentação dizia
// "peça uma chave" sem dizer a quem, porque não havia a quem pedir: a chave
// era uma variável de ambiente que alguém editava no servidor à mão.

const ROTAS = [
  ["/v1/municipios", "Os 246 municípios, com código e nome"],
  ["/v1/indicadores", "O catálogo dos indicadores"],
  ["/v1/indicadores/incidencia-dengue", "Dengue por 100 mil, nos 246 municípios"],
  ["/v1/municipios/5208707", "A ficha de Goiânia, com todos os indicadores"],
  ["/v1/procedencia", "De onde veio cada número"],
  ["/v1/chaves/minha", "Conferir a minha própria chave"],
];

export default function Console({ endereco }) {
  const [nome, setNome] = useState("");
  const [motivo, setMotivo] = useState("");
  const [pedindo, setPedindo] = useState(false);
  const [emitida, setEmitida] = useState(null);
  const [erroPedido, setErroPedido] = useState(null);

  const [chave, setChave] = useState("");
  const [rota, setRota] = useState(ROTAS[0][0]);
  const [chamando, setChamando] = useState(false);
  const [saida, setSaida] = useState(null);
  const [copiado, setCopiado] = useState(false);

  async function pedir(e) {
    e.preventDefault();
    setPedindo(true);
    setErroPedido(null);
    try {
      const r = await fetch("/api/chave", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ nome, motivo }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || `a API respondeu ${r.status}`);
      setEmitida(d);
      setChave(d.chave);
    } catch (erro) {
      setErroPedido(erro.message);
    } finally {
      setPedindo(false);
    }
  }

  async function chamar(e) {
    e.preventDefault();
    setChamando(true);
    setSaida(null);
    const q = new URLSearchParams({ caminho: rota, chave });
    try {
      const r = await fetch(`/api/testar?${q}`);
      setSaida(await r.json());
    } catch (erro) {
      setSaida({ erro: erro.message });
    } finally {
      setChamando(false);
    }
  }

  function copiar() {
    navigator.clipboard?.writeText(emitida.chave).then(
      () => {
        setCopiado(true);
        setTimeout(() => setCopiado(false), 2000);
      },
      () => setCopiado(false)
    );
  }

  const curl = `curl -H "x-api-key: ${chave || "SUA_CHAVE"}" \\\n  "${endereco}${rota}"`;

  return (
    <div className="console">
      <section className="cartela console-pedido">
        <h3>Peça sua chave</h3>
        <p className="apoio">
          Sai na hora, não custa nada e vale para todas as rotas. Ela serve para sabermos quem
          está consumindo e para o limite de requisições ser seu, e não compartilhado.
        </p>

        <form onSubmit={pedir}>
          <label>
            Quem está pedindo
            <input
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="seu nome, ou o da instituição"
              maxLength={120}
              required
            />
          </label>
          <label>
            Para quê, se quiser dizer
            <input
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="trabalho da faculdade, painel interno, reportagem"
              maxLength={300}
            />
          </label>
          <button type="submit" className="principal" disabled={pedindo || !nome.trim()}>
            {pedindo ? "Emitindo" : "Quero minha chave"}
          </button>
        </form>

        {erroPedido && <p className="erro-inline">{erroPedido}</p>}

        {emitida && (
          <div className="chave-emitida">
            <span className="rotulo-chave">Sua chave, de {emitida.nome}</span>
            <code>{emitida.chave}</code>
            <button type="button" onClick={copiar}>{copiado ? "copiada" : "copiar"}</button>
            <p className="apoio">{emitida.limite}. Ela já está valendo: teste aqui embaixo.</p>
          </div>
        )}
      </section>

      <section className="cartela console-teste">
        <h3>Teste agora</h3>
        <p className="apoio">
          A chamada sai daqui com a chave que estiver no campo. Chave errada volta 401 de
          verdade, porque quem responde é a API e não esta página.
        </p>

        <form onSubmit={chamar}>
          <label>
            Chave
            <input
              value={chave}
              onChange={(e) => setChave(e.target.value)}
              placeholder="cole aqui, ou peça uma acima"
              spellCheck={false}
            />
          </label>
          <label>
            O que pedir
            <select value={rota} onChange={(e) => setRota(e.target.value)}>
              {ROTAS.map(([c, r]) => <option key={c} value={c}>{r}</option>)}
            </select>
          </label>
          <button type="submit" className="principal" disabled={chamando}>
            {chamando ? "Chamando" : "Chamar a API"}
          </button>
        </form>

        <p className="apoio equivalente">O mesmo pedido, no seu terminal:</p>
        <pre className="codigo"><code>{curl}</code></pre>

        {saida && (
          <div className="saida">
            {saida.erro ? (
              <p className="erro-inline">{saida.erro}</p>
            ) : (
              <>
                <p className="placar">
                  <span className={saida.status < 300 ? "selo-ok" : "selo-ruim"}>{saida.status}</span>
                  <span>{saida.ms} ms</span>
                  {saida.limite != null && <span>restam {saida.limite} no minuto</span>}
                </p>
                <pre className="codigo"><code>{saida.corpo}{saida.cortado ? "\n… resposta cortada nesta tela" : ""}</code></pre>
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
