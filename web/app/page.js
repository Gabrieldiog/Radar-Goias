"use client";

import { useEffect, useState } from "react";
import Mapa from "./mapa";
import Tabela from "./tabela";

const INDICADORES = {
  "leitos-rede-estadual": { campo: "por_100mil", rotulo: "Leitos por 100 mil hab", sufixo: "leitos por 100 mil habitantes" },
  "ubs-por-habitante": { campo: "por_10mil", rotulo: "UBS por 10 mil hab", sufixo: "unidades por 10 mil habitantes" },
  "incidencia-dengue": { campo: "por_100k", rotulo: "Dengue por 100 mil hab", sufixo: "casos por 100 mil habitantes" },
  "ouvidoria-por-orgao": { campo: "tempo_medio", rotulo: "Ouvidoria por órgão", sufixo: "dias até responder" },
};

async function busca(caminho) {
  const r = await fetch(`/api/radar${caminho}`);
  if (!r.ok) throw new Error(`a API respondeu ${r.status}`);
  return r.json();
}

export default function Painel() {
  const [malha, setMalha] = useState(null);
  const [escolhido, setEscolhido] = useState("leitos-rede-estadual");
  const [resposta, setResposta] = useState(null);
  const [selecionado, setSelecionado] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    busca("/v1/malha").then(setMalha).catch((e) => setErro(e.message));
  }, []);

  useEffect(() => {
    setResposta(null);
    setSelecionado(null);
    busca(`/v1/indicadores/${escolhido}`).then(setResposta).catch((e) => setErro(e.message));
  }, [escolhido]);

  if (erro) return <main className="painel"><p className="erro">Não consegui falar com a API: {erro}</p></main>;

  const { campo, sufixo } = INDICADORES[escolhido];
  const linhas = resposta?.dados ?? [];
  const porOrgao = resposta?.meta?.dimensao === "orgao";
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

      {!resposta ? (
        <p>Carregando...</p>
      ) : porOrgao ? (
        <Tabela linhas={linhas} />
      ) : !malha ? (
        <p>Carregando o mapa...</p>
      ) : (
        <>
          <Mapa malha={malha} valores={valores} selecionado={selecionado} aoSelecionar={setSelecionado} />
          <p className="detalhe">
            {detalhe ? (
              <>
                <strong>{detalhe.nome}</strong>: {detalhe[campo]} {sufixo}, em{" "}
                {detalhe.habitantes.toLocaleString("pt-BR")} moradores.
              </>
            ) : (
              "Clique num município para ver o número dele. Municípios em cinza não têm dado para este indicador."
            )}
          </p>
        </>
      )}

      <p className="rodape">
        {linhas.length} {porOrgao ? "órgãos" : "municípios"} com dado.
        {resposta && ` Fonte: ${resposta.meta.fontes.join(", ")}.`}
      </p>
    </main>
  );
}
