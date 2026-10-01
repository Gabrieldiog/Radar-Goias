# Roteiro para falar

Feito para ser lido em voz alta. Nada precisa ser decorado palavra por palavra,
mas os números precisam sair certos, porque são eles que sustentam tudo.

Painel no ar: **http://204.168.195.120:3010**

## Em uma frase

O Radar Goiás junta dados públicos do estado num lugar só, cruza fontes que não
conversam entre si, e entrega tudo de volta por uma API própria.

## Abra pelo exemplo, não pelo sistema

É o que faz o professor entender em dez segundos.

> O estado publica quantos leitos de hospital existem, mas o arquivo não diz em qual município
> fica cada hospital. Ele só traz um código de cadastro colado no meio do nome da unidade. Dá
> para saber que existem leitos, mas não dá para saber onde.
>
> A gente separa esse código, pergunta ao cadastro nacional de saúde a qual município ele
> pertence, e cruza com a população do IBGE. Nenhuma unidade ficou sem município.
>
> Aí aparece uma coisa que ninguém tinha como ver antes: **222 dos 246 municípios de Goiás não
> têm nenhum leito da rede estadual.** E Goiânia tem 134,7 leitos por 100 mil habitantes
> enquanto Aparecida de Goiânia, que fica colada nela, tem 33,7.

## O que o sistema é

> São **12 indicadores dos 246 municípios**, em seis eixos: saúde, educação, segurança, dinheiro
> público, meio ambiente e atendimento ao cidadão. Vêm de **sete fontes públicas**, e cada número
> traz junto de onde veio, com data, endereço e o status que o servidor respondeu.
>
> O sistema tem três partes: a coleta, que busca nos sites do governo; uma API própria, com chave
> de acesso e limite de requisições; e o painel, que é o que está na tela.
>
> São **348 testes automáticos**, e o painel está publicado numa VPS, rodando fora da nossa
> máquina.

## Os três achados fortes

Guarde-os para o meio da apresentação. É o que diferencia o trabalho de um CRUD.

### 1. Gastar mais em saúde não explica ter menos dengue

> A gente dividiu os 245 municípios que têm os dois números em cinco grupos, do que menos gasta
> em saúde por morador ao que mais gasta. Os que menos gastam têm mediana de **1.410** casos de
> dengue por 100 mil. Os que mais gastam têm **1.602**. Praticamente igual, e o meio sobe e desce
> sem ordem.
>
> Isso não é o sistema falhando, é a resposta. E é uma resposta que ninguém consegue dar sem
> cruzar o Tesouro Nacional com o portal de Goiás, que é exatamente o que este projeto faz.

### 2. Dois milhões de pessoas moram longe de uma porta aberta à noite

> A gente leu o cadastro das unidades de saúde unidade por unidade, inclusive o turno de
> atendimento e a coordenada. **155 dos 246 municípios não têm nenhuma unidade que atenda à
> noite.** São **2.016.452 pessoas**, mais de um quarto de Goiás.
>
> Aí a gente calculou a distância até a unidade noturna mais próxima, com a fórmula de
> haversine escrita em SQL puro. A mediana é **31,2 km**. O pior caso é Britânia, a **133,9 km**.

### 3. A pandemia aparece quando você quebra o IDEB em duas metades

> O IDEB é aprovação multiplicada por aprendizagem. De 2019 para 2021 a nota caiu de 6,09 para
> 5,83. Mas a aprovação **subiu**, de 97% para 98%. Quem caiu foi a aprendizagem, de 6,27 para
> 5,92. A nota sozinha esconde isso.
>
> E olhem a série inteira: a aprovação saiu de 85% em 2005 e chegou a **99%**. Está no teto. De
> agora em diante, quase todo ganho de IDEB em Goiás tem que vir de aprendizagem.

## O que mostrar na tela, nesta ordem

**1. O mapa.** Troque de indicador clicando nos botões de cima e chame a atenção para a frase
grande, dentro do cartão.

> Essa frase não foi escrita, foi calculada do próprio dado. Se eu trocar de indicador, ela troca
> junto. Se a fonte se corrigir amanhã, ela se corrige também.

**2. A faixa dos 246.** Cada barra é um município, do maior para o menor.

> Aqui estão os 246 de uma vez, e a altura é o valor. Onde a faixa perde altura é onde o dado
> acaba: a divisa marca quantos municípios não têm esse número publicado, o que é diferente de
> ter valor zero.

**3. A aba "Uma coisa explica a outra?"** Deixe em gasto em saúde contra dengue, que é o achado 1.

**4. A aba "Como mudou".** Mostre que são quatro séries com quatro grãos de tempo diferentes.

> Dengue por ano, IDEB por edição, homicídio por mês e queimada por dia. O grão não é escolha
> nossa: é o que cada fonte publica. A linha tracejada é a mediana da série, e é ela que separa
> "esse período foi fora do comum" de "esse período foi como sempre".

Troque para IDEB e conte o achado 3.

**5. A página "Puxar pela API".** Este é o momento mais forte da demonstração.

> Qualquer pessoa pede uma chave aqui, na hora, sem cadastro.

Peça alguém da sala para dar um nome. Digite, clique, a chave aparece. Copie, cole no console ao
lado, escolha uma rota e chame.

> O que respondeu não foi esta página, foi a API. Se eu apagar um caractere da chave, ela
> devolve 401.

Faça isso: apague um caractere e chame de novo. O 401 aparece em vermelho.

> E o limite de 60 requisições por minuto é contado por chave, não por IP. Numa faculdade todo
> mundo sai pelo mesmo IP, e um balde compartilhado faria um aluno derrubar os colegas.

**6. A página "De onde veio cada número".** Feche por aqui.

> Toda vez que o sistema bate num servidor do governo, ele grava o endereço, a data, o que o
> servidor respondeu e o tamanho da resposta. São mais de 53 mil registros, trazidos por quase
> trezentos pedidos a sete fontes, e **nenhum pedido foi recusado**. É isso que permite rastrear
> qualquer número do painel até a requisição que o trouxe.

Os números exatos estão na tela. Não decore: eles mudam a cada coleta.

Se perguntarem por que só trezentos pedidos para tanto dado:

> Porque um pedido pode trazer um arquivo enorme. O do censo escolar sozinho passa de 200 MB. E
> 245 dos pedidos são do Tesouro Nacional, porque a API dele responde um município por vez.

## Se o professor perguntar

**"Dá para confiar nesses gráficos?"**

> Três coisas seguram. A altura da barra é a mediana e não a média, porque uma cidade de dois mil
> habitantes com número fora da curva desloca a média do grupo inteiro. A frase que resume não
> compara só as pontas, ela conta quantos degraus sobem. E quando o cruzamento tem menos de
> cinquenta municípios, ela avisa em vez de fingir que achou padrão.

**"E se o dado estiver errado?"**

> A fonte se corrige o tempo todo. Goiânia tinha 38.232 casos de dengue numa coleta e 38.216 na
> seguinte. É por isso que a gente guarda data, endereço e status de cada requisição: o número da
> tela sempre pode ser rastreado até o pedido que o trouxe.

**"Vocês inventaram algum número?"**

> Nenhum. Mas a gente descobriu erros nas fontes. A Secretaria de Segurança publica uma linha por
> município por mês mesmo quando não houve homicídio: de 1.722 linhas, 1.483 têm zero vítima.
> Contar linha em vez de ocorrência diria que os 246 municípios tiveram homicídio em janeiro,
> quando foram 29.

**"Por que FastAPI?"**

> Ele gera a documentação sozinho, a partir das próprias funções, o que já cumpre um requisito do
> projeto. Confere os dados de entrada sozinho. E o ecossistema Python é onde estão as
> bibliotecas que a coleta precisa, como a que lê planilha em fluxo, necessária porque um dos
> arquivos passa de 200 MB.

**"Como vocês rodam isso?"**

> Um comando: `docker compose up -d`. Sobe o banco, a API e o painel juntos. E está publicado
> numa VPS, então não depende da nossa máquina estar ligada.

**"E a segurança?"**

Esta resposta vale ouro, e é verdade.

> A gente rodou análise estática e teste dinâmico no próprio sistema. Achamos e consertamos dois
> defeitos: um byte nulo no código do município derrubava a API com 500, e o painel entrava em
> iframe de qualquer site, o que permite sequestro de clique.
>
> E achamos uma invasão de verdade. O banco estava publicado para a internet sem senha, e um
> minerador entrou e ficou 27 horas consumindo o servidor. A gente fechou a porta, matou o
> minerador e encontrou um superusuário que o invasor tinha deixado escondido no banco. Hoje a
> porta do banco só responde para o próprio servidor, e tem um teste automático que reprova
> qualquer porta nova publicada para fora.

**"O que falta?"**

> Mais histórico em segurança e educação, mas isso depende da fonte publicar: a Secretaria só
> divulgou 2026 e o censo escolar só 2024. Não dá para inventar passado que o governo não
> publicou.

## Números que precisam sair certos

| | |
|---|---|
| Municípios | 246 |
| Indicadores | 12 |
| Eixos | 6 |
| Fontes públicas | 7 |
| Testes automáticos | 348 |
| Registros guardados | mais de 53 mil, leia o número exato na tela |
| Requisições a servidores do governo | quase 300, nenhuma recusada |
| Sem leito da rede estadual | 222 de 246 |
| Sem unidade de saúde noturna | 155 de 246 |
| Pessoas nesses municípios | 2.016.452 |
| Distância mediana até a porta noturna | 31,2 km |
| Pior caso, Britânia | 133,9 km |
| Goiânia contra Aparecida, leitos por 100 mil | 134,7 contra 33,7 |
| Pior ano de dengue, 2024 | 436.824 casos |
| Gasto em saúde contra dengue, pontas | 1.410 contra 1.602 |
| Aprovação no IDEB, 2005 e 2025 | 85% e 99% |

## Três ressalvas para dizer antes que perguntem

**Município pequeno oscila muito.** Poucos casos numa cidade de dois mil habitantes viram uma
taxa alta que não se repete no ano seguinte. O painel avisa isso sozinho.

**Os leitos são só da rede estadual.** Não incluem hospital municipal nem privado. É importante
dizer, senão o número parece pior do que é.

**Foco de queimada não é incêndio.** É detecção de satélite, e doze satélites cobrem o Brasil, e
vários veem o mesmo fogo na mesma passagem.
