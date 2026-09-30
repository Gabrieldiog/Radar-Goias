/** @type {import('next').NextConfig} */
const nextConfig = {
  // empacota o servidor e só o que ele usa, para a imagem do Docker não
  // carregar node_modules inteiro
  output: "standalone",

  // dizer a versão do framework só ajuda quem procura uma falha conhecida
  poweredByHeader: false,

  // Um teste dinâmico mostrou que o painel entrava em iframe de qualquer site.
  // Num painel de dado público isso é sequestro de clique: outro site embute a
  // tela, deixa ela transparente e colhe o clique de quem pensa estar clicando
  // na página dele.
  async headers() {
    return [
      {
        source: "/:caminho*",
        headers: [
          { key: "Content-Security-Policy", value: "frame-ancestors 'none'" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
