import { IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--fonte",
});

export const metadata = {
  title: "Radar Goiás",
  description: "Indicadores públicos dos 246 municípios de Goiás",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR" className={plex.variable}>
      <body>{children}</body>
    </html>
  );
}
