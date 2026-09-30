// O console de teste manda a chave que a pessoa digitou, e não a do servidor.
// É o que faz o teste valer: chave errada tem que voltar 401 de verdade.
const API = process.env.RADAR_API_URL || "http://127.0.0.1:8000";

// só o que a documentação ensina, para esta rota não virar um proxy de tudo
const PERMITIDOS = [
  "/v1/municipios",
  "/v1/indicadores",
  "/v1/procedencia",
  "/v1/chaves/minha",
];
const COM_PARAMETRO = ["/v1/municipios/", "/v1/indicadores/"];

function liberado(caminho) {
  return (
    PERMITIDOS.includes(caminho) ||
    COM_PARAMETRO.some((p) => caminho.startsWith(p) && /^[\w-]+$/.test(caminho.slice(p.length)))
  );
}

export async function GET(request) {
  const url = new URL(request.url);
  const caminho = url.searchParams.get("caminho") || "";
  const chave = url.searchParams.get("chave") || "";

  if (!liberado(caminho)) {
    return Response.json({ erro: "caminho fora da lista do console" }, { status: 400 });
  }

  const comecou = Date.now();
  try {
    const resposta = await fetch(`${API}${caminho}`, {
      headers: { "x-api-key": chave },
      cache: "no-store",
    });
    const texto = await resposta.text();
    return Response.json({
      status: resposta.status,
      ms: Date.now() - comecou,
      limite: resposta.headers.get("x-ratelimit-remaining"),
      corpo: texto.slice(0, 4000),
      cortado: texto.length > 4000,
    });
  } catch (e) {
    return Response.json({ erro: `não consegui falar com a API: ${e.message}` }, { status: 502 });
  }
}
