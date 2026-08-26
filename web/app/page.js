"use client";

import { useEffect, useState } from "react";
import Mapa from "./mapa";

const INDICADORES = {
  "leitos-rede-estadual": { campo: "por_100mil", rotulo: "Leitos da rede estadual por 100 mil hab" },
  "incidencia-dengue": { campo: "por_100k", rotulo: "Casos de dengue por 100 mil hab" },
};

async function busca(caminho) {
  const r = await fetch(`/api/radar${caminho}`);
  if (!r.ok) throw new Error(`a API respondeu ${r.status}`);
  return r.json();
}

export default function Painel() {
  const [malha, setMalha] = useState(null);
  const [escolhido, setEscolhido] = useState("leitos-rede-estadual");
  const [linhas, setLinhas] = useState([]);
  const [selecionado, setSelecionado] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    busca("/v1/malha").then(setMalha).catch((e) => setErro(e.message));
  }, []);

  useEffect(() => {
    setLinhas([]);
    busca(`/v1/indicadores/${escolhido}`)
      .then((d) => setLinhas(d.dados))
      .catch((e) => setErro(e.message));
  }, [escolhido]);

  if (erro) return <main className="painel"><p className="erro">Não consegui falar com a API: {erro}</p></main>;
  if (!malha) return <main className="painel"><p>Carregando o mapa...</p></main>;

  const campo = INDICADORES[escolhido].campo;
  const valores = Object.fromEntries(linhas.map((l) => [l.codigo_ibge, l[campo]]));
  const detalhe = linhas.find((l) => l.codigo_ibge === selecionado);

  return (
    <main className="painel">
      <h1>Radar Goiás</h1>
      <p className="sub">Indicadores públicos dos 246 municípios, cruzando fontes que não conversam entre si.</p>

      <div className="controles">
        {Object.entries(INDICADORES).map(([id, { rotulo }]) => (
          <button key={id} onClick={() => setEscolhido(id)} className={id === escolhido ? "ativo" : ""}>
            {rotulo}
          </button>
        ))}
      </div>

      <Mapa malha={malha} valores={valores} selecionado={selecionado} aoSelecionar={setSelecionado} />

      {detalhe ? (
        <p className="detalhe">
          <strong>{detalhe.nome}</strong>: {detalhe[campo]} {escolhido === "leitos-rede-estadual" ? "leitos" : "casos"} por 100 mil habitantes,
          em {detalhe.habitantes.toLocaleString("pt-BR")} moradores.
        </p>
      ) : (
        <p className="detalhe">Clique num município para ver o número dele. Municípios em cinza não têm dado para este indicador.</p>
      )}

      <p className="rodape">{linhas.length} municípios com dado. Fonte: portal de dados abertos de Goiás, Ministério da Saúde e IBGE.</p>
    </main>
  );
}
