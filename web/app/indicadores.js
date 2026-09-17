// Cada indicador declara a que eixo pertence, como se lê o número e qual frase
// resume o que o mapa está mostrando. A frase é calculada do próprio dado.
//
// Toda frase precisa aguentar receber linha a menos do que espera. Ela é gerada
// no meio do desenho da tela, então um erro aqui não deixa um campo vazio: leva
// a página inteira junto.
const SEM_RESUMO = "Ainda não há dado suficiente para resumir este indicador.";
export const INDICADORES = {
  "leitos-rede-estadual": {
    sentido: "maior",
    curto: "leitos por habitante",
    eixo: "Saúde",
    campo: "por_100mil",
    rotulo: "Leitos",
    unidade: "leitos por 100 mil hab",
    destaque: (linhas, total) =>
      `${total - linhas.length} dos ${total} municípios não têm nenhum leito da rede estadual.`,
  },
  "ubs-por-habitante": {
    sentido: "maior",
    curto: "unidades de saúde por habitante",
    eixo: "Saúde",
    campo: "por_10mil",
    rotulo: "Unidades de saúde",
    unidade: "unidades por 10 mil hab",
    destaque: (linhas) => {
      const menor = linhas[linhas.length - 1];
      if (menor?.por_10mil == null) return SEM_RESUMO;
      return `${menor.nome} tem a menor cobertura do estado, com ${fmt(
        menor.por_10mil
      )} unidade por 10 mil moradores.`;
    },
  },
  "incidencia-dengue": {
    sentido: "menor",
    curto: "incidência de dengue",
    eixo: "Saúde",
    campo: "por_100k",
    rotulo: "Dengue",
    unidade: "casos por 100 mil hab",
    destaque: (linhas) => {
      const topo = linhas[0];
      if (topo?.por_100k == null) return SEM_RESUMO;
      return `${topo.nome} teve ${fmt(topo.por_100k)} casos por 100 mil moradores, ${(
        topo.por_100k / mediana(linhas, "por_100k")
      )
        .toFixed(1)
        .replace(".", ",")} vezes a mediana do estado.`;
    },
  },
  "homicidio-por-100mil": {
    sentido: "menor",
    curto: "taxa de homicídio",
    eixo: "Segurança",
    campo: "por_100mil",
    rotulo: "Homicídio",
    unidade: "vítimas por 100 mil hab",
    destaque: (linhas) => {
      const zerados = linhas.filter((l) => l.vitimas === 0).length;
      if (!linhas.length) return SEM_RESUMO;
      return `${zerados} dos ${linhas.length} municípios não registraram nenhum homicídio no período.`;
    },
  },
  "gasto-saude-por-habitante": {
    sentido: "neutro",
    curto: "gasto em saúde por morador",
    eixo: "Dinheiro público",
    campo: "por_habitante",
    rotulo: "Gasto em saúde",
    unidade: "reais por habitante",
    destaque: (linhas) => razaoDeGasto(linhas, "por_habitante", "por morador"),
  },
  "gasto-educacao-por-habitante": {
    sentido: "neutro",
    curto: "gasto em educação por morador",
    eixo: "Dinheiro público",
    campo: "por_habitante",
    rotulo: "Gasto em educação",
    unidade: "reais por habitante",
    destaque: (linhas) => razaoDeGasto(linhas, "por_habitante", "por morador"),
  },
  "gasto-educacao-por-aluno": {
    sentido: "neutro",
    curto: "gasto em educação por aluno",
    eixo: "Educação",
    campo: "por_aluno",
    rotulo: "Gasto por aluno",
    unidade: "reais por aluno no ano",
    destaque: (linhas) => {
      const alto = linhas[0];
      const baixo = linhas[linhas.length - 1];
      if (!alto?.por_aluno || !baixo?.por_aluno) return SEM_RESUMO;
      return `${alto.nome} gasta ${fmt(
        Math.round(alto.por_aluno)
      )} reais por aluno da rede municipal, ${(alto.por_aluno / baixo.por_aluno)
        .toFixed(1)
        .replace(".", ",")} vezes o que ${baixo.nome} gasta.`;
    },
  },
  "ideb-anos-iniciais": {
    sentido: "maior",
    curto: "IDEB dos anos iniciais",
    eixo: "Educação",
    campo: "ideb",
    rotulo: "IDEB",
    unidade: "nota de 0 a 10",
    destaque: (linhas) => {
      const alto = linhas[0];
      const baixo = linhas[linhas.length - 1];
      if (alto?.ideb == null || baixo?.ideb == null) return SEM_RESUMO;
      return `${alto.nome} tem nota ${fmt(alto.ideb)} e ${baixo.nome} tem ${fmt(
        baixo.ideb
      )}, nos mesmos anos iniciais da rede municipal.`;
    },
  },
  "ouvidoria-por-orgao": {
    sentido: "menor",
    curto: "tempo de resposta da ouvidoria",
    eixo: "Atendimento ao cidadão",
    campo: "tempo_medio",
    rotulo: "Ouvidoria",
    unidade: "dias até responder",
    destaque: (linhas) => {
      // órgão com menos de cem manifestações vira campeão ou lanterna por acaso
      const com = linhas.filter((l) => l.tempo_medio != null && l.total >= 100);
      if (!com.length) return SEM_RESUMO;
      const pior = com.reduce((a, b) => (b.tempo_medio > a.tempo_medio ? b : a));
      const melhor = com.reduce((a, b) => (b.tempo_medio < a.tempo_medio ? b : a));
      return `A ${melhor.orgao} responde em ${fmt(melhor.tempo_medio)} dias e a ${
        pior.orgao
      } leva ${fmt(pior.tempo_medio)}.`;
    },
  },
};

export const EIXOS = ["Saúde", "Educação", "Segurança", "Dinheiro público", "Atendimento ao cidadão"];

export function fmt(v) {
  return v == null ? "sem dado" : v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

function razaoDeGasto(linhas, campo, quem) {
  const alto = linhas[0];
  const baixo = linhas[linhas.length - 1];
  if (!alto?.[campo] || !baixo?.[campo]) return SEM_RESUMO;
  return `${alto.nome} gasta ${(alto[campo] / baixo[campo]).toFixed(
    0
  )} vezes mais ${quem} que ${baixo.nome}.`;
}

function mediana(linhas, campo) {
  const v = linhas.map((l) => l[campo]).filter((x) => x != null).sort((a, b) => a - b);
  return v[Math.floor(v.length / 2)] || 1;
}
