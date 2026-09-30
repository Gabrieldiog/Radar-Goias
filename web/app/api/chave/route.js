// Pedir chave é a única coisa que o navegador manda para a API, e ela é a
// única rota que não exige chave. Passa por aqui pelo mesmo motivo que o
// resto: o navegador nunca fala com a API direto.
const API = process.env.RADAR_API_URL || "http://127.0.0.1:8000";

export async function POST(request) {
  const corpo = await request.text();
  const resposta = await fetch(`${API}/v1/chaves`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: corpo,
    cache: "no-store",
  });
  return new Response(await resposta.text(), {
    status: resposta.status,
    headers: { "content-type": "application/json" },
  });
}
