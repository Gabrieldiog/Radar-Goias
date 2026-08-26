// O navegador nunca fala com a API direto: ele chama esta rota, que repassa o
// pedido por trás com a chave. Assim não há CORS e a chave não vaza no cliente.
const API = process.env.RADAR_API_URL || "http://127.0.0.1:8000";
const CHAVE = process.env.RADAR_CHAVE || "demo";

export async function GET(request, { params }) {
  const { caminho } = await params;
  const busca = new URL(request.url).search;
  const resposta = await fetch(`${API}/${caminho.join("/")}${busca}`, {
    headers: { "x-api-key": CHAVE },
    cache: "no-store",
  });
  return new Response(await resposta.text(), {
    status: resposta.status,
    headers: {
      "content-type": resposta.headers.get("content-type") || "application/json",
    },
  });
}
