// Cada indicador declara a que eixo pertence, como se lê o número e qual frase
// resume o que o mapa está mostrando. A frase é calculada do próprio dado.
export const INDICADORES = {
  "leitos-rede-estadual": {
    curto: "leitos por habitante",
    eixo: "Saúde",
    campo: "por_100mil",
    rotulo: "Leitos",
    unidade: "leitos por 100 mil hab",
    destaque: (linhas, total) =>
      `${total - linhas.length} dos ${total} municípios não têm nenhum leito da rede estadual.`,
  },
  "ubs-por-habitante": {
    curto: "unidades de saúde por habitante",
    eixo: "Saúde",
    campo: "por_10mil",
    rotulo: "Unidades de saúde",
    unidade: "unidades por 10 mil hab",
    destaque: (linhas) =>
      `${linhas[linhas.length - 1].nome} tem a menor cobertura do estado, com ${fmt(
        linhas[linhas.length - 1].por_10mil
      )} unidade por 10 mil moradores.`,
  },
  "incidencia-dengue": {
    curto: "incidência de dengue",
    eixo: "Saúde",
    campo: "por_100k",
    rotulo: "Dengue",
    unidade: "casos por 100 mil hab",
    destaque: (linhas) =>
      `${linhas[0].nome} teve ${fmt(linhas[0].por_100k)} casos por 100 mil moradores, ${(
        linhas[0].por_100k / mediana(linhas, "por_100k")
      ).toFixed(1)} vezes a mediana do estado.`,
  },
  "homicidio-por-100mil": {
    curto: "taxa de homicídio",
    eixo: "Segurança",
    campo: "por_100mil",
    rotulo: "Homicídio",
    unidade: "vítimas por 100 mil hab",
    destaque: (linhas) =>
      `${linhas.filter((l) => l.vitimas === 0).length} dos ${
        linhas.length
      } municípios não registraram nenhum homicídio no período.`,
  },
  "gasto-saude-por-habitante": {
    curto: "gasto em saúde por morador",
    eixo: "Dinheiro público",
    campo: "por_habitante",
    rotulo: "Gasto em saúde",
    unidade: "reais por habitante",
    destaque: (linhas) =>
      `${linhas[0].nome} gasta ${(
        linhas[0].por_habitante / linhas[linhas.length - 1].por_habitante
      ).toFixed(0)} vezes mais por morador que ${linhas[linhas.length - 1].nome}.`,
  },
  "gasto-educacao-por-habitante": {
    curto: "gasto em educação por morador",
    eixo: "Dinheiro público",
    campo: "por_habitante",
    rotulo: "Gasto em educação",
    unidade: "reais por habitante",
    destaque: (linhas) =>
      `${linhas[0].nome} gasta ${(
        linhas[0].por_habitante / linhas[linhas.length - 1].por_habitante
      ).toFixed(0)} vezes mais por morador que ${linhas[linhas.length - 1].nome}.`,
  },
  "ouvidoria-por-orgao": {
    curto: "tempo de resposta da ouvidoria",
    eixo: "Atendimento ao cidadão",
    campo: "tempo_medio",
    rotulo: "Ouvidoria",
    unidade: "dias até responder",
    destaque: (linhas) => {
      const com = linhas.filter((l) => l.tempo_medio != null && l.total >= 100);
      const pior = com.reduce((a, b) => (b.tempo_medio > a.tempo_medio ? b : a));
      const melhor = com.reduce((a, b) => (b.tempo_medio < a.tempo_medio ? b : a));
      return `A ${melhor.orgao} responde em ${melhor.tempo_medio} dias e a ${pior.orgao} leva ${pior.tempo_medio}.`;
    },
  },
};

export const EIXOS = ["Saúde", "Segurança", "Dinheiro público", "Atendimento ao cidadão"];

export function fmt(v) {
  return v == null ? "sem dado" : v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

function mediana(linhas, campo) {
  const v = linhas.map((l) => l[campo]).filter((x) => x != null).sort((a, b) => a - b);
  return v[Math.floor(v.length / 2)] || 1;
}
