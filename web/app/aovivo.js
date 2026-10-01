"use client";

import { useEffect, useRef, useState } from "react";

// A tela ao vivo das queimadas. Ela existe porque esta é a única fonte do
// projeto que muda ao longo do dia: o INPE vai enchendo o arquivo do dia
// conforme os satélites passam, e dezesseis das vinte e quatro horas de um dia
// têm detecção.
//
// A página se atualiza de trinta em trinta segundos, mas o número só muda
// quando um satélite passa. Isso está escrito na tela de propósito: um
// contador que finge movimento a cada segundo seria teatro, e o que o relógio
// mostra de verdade é o tempo desde a última detecção, que sobe sozinho.

const PASSO = 30000;

function faz(segundos) {
  if (segundos < 60) return `${Math.floor(segundos)} s`;
  if (segundos < 3600) return `${Math.floor(segundos / 60)} min`;
  const h = Math.floor(segundos / 3600);
  return h < 24 ? `${h} h` : `${Math.floor(h / 24)} d`;
}

const hora = (iso) =>
  new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

export default function AoVivo() {
  const [focos, setFocos] = useState(null);
  const [erro, setErro] = useState(null);
  const [buscando, setBuscando] = useState(false);
  const [chegaram, setChegaram] = useState(0);
  const [agora, setAgora] = useState(() => Date.now());
  const vistos = useRef(new Set());
  const primeira = useRef(true);

  useEffect(() => {
    let vivo = true;

    async function busca() {
      setBuscando(true);
      try {
        const r = await fetch("/api/radar/v1/fogo/recentes?limite=10");
        if (!r.ok) throw new Error(`a API respondeu ${r.status}`);
        const d = await r.json();
        if (!vivo) return;
        const novos = d.dados.filter((f) => !vistos.current.has(f.id));
        d.dados.forEach((f) => vistos.current.add(f.id));
        // na primeira carga tudo é novo, e anunciar isso seria mentira
        if (!primeira.current && novos.length) setChegaram(novos.length);
        primeira.current = false;
        setFocos(d.dados);
        setErro(null);
      } catch (e) {
        if (vivo) setErro(e.message);
      } finally {
        if (vivo) setBuscando(false);
      }
    }

    busca();
    const pulso = setInterval(busca, PASSO);
    // o relógio anda de segundo em segundo porque o "há quanto tempo" é a única
    // coisa que muda de verdade entre uma passagem de satélite e a seguinte
    const relogio = setInterval(() => setAgora(Date.now()), 1000);
    return () => {
      vivo = false;
      clearInterval(pulso);
      clearInterval(relogio);
    };
  }, []);

  useEffect(() => {
    if (!chegaram) return;
    const t = setTimeout(() => setChegaram(0), 12000);
    return () => clearTimeout(t);
  }, [chegaram]);

  if (erro) return <p className="aviso">Não consegui buscar as detecções: {erro}.</p>;
  if (!focos) return <p className="aviso carregando">Buscando as últimas detecções.</p>;
  if (!focos.length) return null;

  const ultima = new Date(focos[0].detectado_em);
  const desde = Math.max(0, (agora - ultima) / 1000);

  return (
    <section className="aovivo">
      <header>
        <h3>
          <span className={`pulso${buscando ? " batendo" : ""}`} aria-hidden="true" />
          Chegando do INPE
        </h3>
        <p className="apoio">
          A tela se atualiza sozinha a cada 30 segundos. O número só muda quando um satélite
          passa, e entre uma passagem e outra ele fica parado de propósito.
        </p>
      </header>

      <p className="desde">
        Última detecção <strong>há {faz(desde)}</strong>, às {hora(focos[0].detectado_em)}, em{" "}
        {focos[0].nome}.
      </p>

      {chegaram > 0 && (
        <p className="chegaram" role="status">
          {chegaram === 1 ? "Chegou 1 foco novo" : `Chegaram ${chegaram} focos novos`} desde a
          última conferida.
        </p>
      )}

      <ol className="deteccoes">
        {focos.map((f) => (
          <li key={f.id}>
            <span className="quando">{hora(f.detectado_em)}</span>
            <span className="onde">{f.nome}</span>
            <span className="quem">{f.satelite}</span>
            <span className="forca">
              {f.frp == null ? "sem medida" : `${f.frp.toLocaleString("pt-BR")} MW`}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
