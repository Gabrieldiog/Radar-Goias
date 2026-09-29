// A escala de cor vivia copiada em três arquivos, e os três já discordavam do
// primeiro degrau. Agora mora aqui, e o CSS lê as mesmas variáveis.
//
// O caminho é o do Cerrado na virada da seca para a água: areia, capim seco,
// olho de mato, verde fechado. Termina no verde da marca, então o mapa e a
// faixa pertencem à mesma página em vez de flutuarem nela.
export const RAMPA = ["#f1e6cb", "#ddc179", "#a8ad6a", "#5d8a68", "#1f5a4f"];

// A raiz quadrada abre a parte de baixo da escala. Sem ela, um município muito
// acima da média achata todos os outros numa cor só.
export function degrau(valor, maximo) {
  const posicao = Math.sqrt(Math.max(0, valor) / (maximo || 1));
  return Math.min(RAMPA.length - 1, Math.floor(posicao * RAMPA.length));
}

export function cor(valor, maximo) {
  return valor == null ? null : RAMPA[degrau(valor, maximo)];
}

// A altura da barra usa a mesma raiz, e nunca cai a zero: barra de altura zero
// some, e sumir é o que a fonte faz com quem não publicou. Quem tem valor zero
// precisa continuar visível, porque zero é um dado.
export function altura(valor, maximo) {
  return 7 + Math.sqrt(Math.max(0, valor) / (maximo || 1)) * 93;
}
