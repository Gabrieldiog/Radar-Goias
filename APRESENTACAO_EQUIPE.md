# Roteiro para quem vai falar

Feito para ser lido em voz alta. Nada aqui precisa ser decorado palavra por palavra,
mas os números precisam sair certos, porque são eles que sustentam tudo.

## Em uma frase

O Radar Goiás junta dados públicos do estado num lugar só e cruza fontes que não conversam entre si.

## O problema, com um exemplo

Abra falando do exemplo, não do sistema. É o que faz o professor entender em dez segundos.

> O estado publica quantos leitos de hospital existem, mas o arquivo não diz em qual município fica
> cada hospital. Ele só traz um código de cadastro colado no meio do nome da unidade. Então dá para
> saber que existem leitos, mas não dá para saber onde.
>
> A gente separa esse código, pergunta ao cadastro nacional de saúde a qual município ele pertence,
> e cruza com a população do IBGE. Das 46 unidades, nenhuma ficou sem município.
>
> Aí aparece uma coisa que ninguém tinha como ver antes: **223 dos 246 municípios de Goiás não têm
> nenhum leito da rede estadual.** E Goiânia tem 130 leitos por 100 mil habitantes enquanto
> Aparecida de Goiânia, que fica do lado, tem 33.

## O que o sistema é

> São **nove indicadores dos 246 municípios**, cobrindo cinco eixos: saúde, educação, segurança,
> dinheiro público e atendimento ao cidadão. Eles vêm de seis fontes públicas diferentes, e cada
> número traz junto de onde veio, com data, endereço e o status que o servidor respondeu.
>
> O sistema tem três partes: a coleta, que busca nos sites do governo; uma API própria, com chave de
> acesso e limite de requisições; e o painel, que é o que está na tela.
>
> São **206 testes automáticos**, que rodam em cinco segundos.

## O achado mais forte

Guarde este para o final, porque é o que diferencia o trabalho.

> A gente dividiu os 244 municípios que têm os dois números em cinco grupos, do que menos gasta em
> saúde por morador ao que mais gasta. Os que menos gastam têm 1.448 casos de dengue por 100 mil.
> Os que mais gastam têm 1.602. Praticamente igual.
>
> **Gastar mais em saúde não explica ter menos dengue.** E isso não é o sistema falhando, é a
> resposta. É uma resposta que ninguém consegue dar sem cruzar o Tesouro Nacional com o portal de
> Goiás, que é exatamente o que este projeto faz.

## O que mostrar na tela, nesta ordem

**1. O mapa.** Abra em `localhost:3000`. Troque de indicador clicando nos botões de cima e chame a
atenção para a frase grande, que muda sozinha.

> Essa frase não foi escrita, foi calculada do próprio dado. Se eu trocar de indicador, ela troca
> junto. Se a fonte se corrigir amanhã, ela se corrige também.

**2. A faixa de quadrinhos.** Cada quadrinho é um município, do maior para o menor.

> Aqui estão os 246 de uma vez. Os hachurados no fim não têm esse dado publicado, e isso é diferente
> de ter valor zero. Dá para ver de relance quantos ficaram de fora.

**3. A aba "Uma coisa explica a outra?"** Deixe em gasto em saúde contra dengue, que é o achado
acima.

**4. A aba "Como mudou", trocando para IDEB.** Este é o segundo achado forte.

> De 2019 para 2021 a nota caiu, mas a aprovação subiu. A queda veio da aprendizagem, não da
> reprovação. É a pandemia aparecendo, e o número do IDEB sozinho esconde isso.
>
> E olhem a linha de aprovação: saiu de 85% em 2005 e chegou a 99%. Está no teto. De agora em
> diante, quase todo ganho de IDEB em Goiás tem que vir de aprendizagem.

**5. A página "De onde veio cada número".** Feche por aqui.

> Toda requisição que o sistema faz a um servidor público fica gravada com data, endereço, status e
> tamanho da resposta. Nenhum número do painel existe sem essa linha.

## Se o professor perguntar

**"Dá para confiar nesses gráficos?"**

> Três coisas seguram. A altura da barra é a mediana e não a média, porque uma cidade de dois mil
> habitantes com número fora da curva desloca a média do grupo inteiro. A frase que resume não
> compara só as pontas, ela conta quantos degraus sobem. E quando o cruzamento tem menos de cinquenta
> municípios, ela avisa em vez de fingir que achou padrão.

**"E se o dado estiver errado?"**

> A fonte se corrige o tempo todo. Goiânia tinha 38.232 casos de dengue numa coleta e 38.216 na
> seguinte. É por isso que a gente guarda data, endereço e status de cada requisição: o número da
> tela sempre pode ser rastreado até o pedido que o trouxe.

**"Por que FastAPI?"**

> Ele gera a documentação sozinho, a partir das próprias funções, o que já cumpre um requisito do
> projeto. Confere os dados de entrada sozinho. E o ecossistema Python é onde estão as bibliotecas
> que a coleta precisa, como a que lê planilha em fluxo, necessária porque um dos arquivos passa de
> 200 MB.

**"Como vocês rodam isso?"**

> Um comando: `docker compose up -d`. Sobe o banco, a API e o painel juntos.

**"O que falta?"**

> Publicar na internet, para rodar fora das nossas máquinas. O resto dos cinco eixos está pronto.

## Números que precisam sair certos

| | |
|---|---|
| Municípios | 246 |
| Indicadores | 9 |
| Eixos | 5 |
| Fontes públicas | 6 |
| Testes | 206 |
| Sem leito da rede estadual | 223 de 246 |
| Sem homicídio no período | 138 de 246 |
| Goiânia contra Aparecida, leitos por 100 mil | 130 contra 33 |
| Dengue em 2024, no estado | 437 mil casos |
| Gasto em saúde contra dengue | 1.448 contra 1.602 |
| Aprovação nos anos iniciais, 2025 | 99% |

## Duas ressalvas para dizer antes que perguntem

**Município pequeno oscila muito.** Poucos casos numa cidade de dois mil habitantes viram uma taxa
alta que não se repete no ano seguinte. O painel avisa isso.

**Os dados de leitos são só da rede estadual.** Não incluem hospital municipal nem privado. É
importante dizer, senão o número parece pior do que é.
