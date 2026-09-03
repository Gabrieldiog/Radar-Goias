"use client";

// A ouvidoria é medida por órgão, não por município, então ela não cabe no mapa.
export default function Tabela({ linhas }) {
  const comVolume = linhas.filter((l) => l.total >= 100);
  return (
    <table className="tabela">
      <thead>
        <tr>
          <th>Órgão</th>
          <th>Manifestações</th>
          <th>Finalizadas</th>
          <th>Tempo médio</th>
        </tr>
      </thead>
      <tbody>
        {comVolume.map((l) => (
          <tr key={l.orgao}>
            <td>{l.orgao}</td>
            <td className="num">{l.total.toLocaleString("pt-BR")}</td>
            <td className="num">{l.taxa_finalizacao}%</td>
            <td className="num">{l.tempo_medio == null ? "sem dado" : `${l.tempo_medio} dias`}</td>
          </tr>
        ))}
      </tbody>
      <caption>
        Órgãos com pelo menos 100 manifestações em 2026. O prazo legal é de 30 dias e quase todos
        cumprem, então o que separa um órgão do outro é o tempo médio de resposta.
      </caption>
    </table>
  );
}
