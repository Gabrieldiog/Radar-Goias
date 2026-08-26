import "./globals.css";

export const metadata = {
  title: "Radar Goiás",
  description: "Indicadores públicos dos 246 municípios de Goiás",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
