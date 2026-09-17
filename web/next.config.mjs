/** @type {import('next').NextConfig} */
const nextConfig = {
  // empacota o servidor e só o que ele usa, para a imagem do Docker não
  // carregar node_modules inteiro
  output: "standalone",
};

export default nextConfig;
