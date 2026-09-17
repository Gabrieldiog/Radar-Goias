import { Bricolage_Grotesque, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

// três vozes: a de display carrega a personalidade, a de texto carrega a
// leitura, e a monoespaçada carrega número e rótulo, que é o registro certo
// para um projeto que fala de código IBGE e status HTTP
const display = Bricolage_Grotesque({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--display",
});

const texto = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--fonte",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--mono",
});

export const metadata = {
  title: "Radar Goiás",
  description: "Indicadores públicos dos 246 municípios de Goiás",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR" className={`${display.variable} ${texto.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
