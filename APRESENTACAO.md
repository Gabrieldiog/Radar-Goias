# Roteiro da apresentação

## A fala

**O que é.** O Radar Goiás junta dados públicos do estado num lugar só e cruza fontes que não conversam entre si.

**O que ele propõe.** Cada órgão publica do seu jeito, então ninguém consegue comparar nada. O estado publica quantos leitos de hospital estão ocupados, mas não diz em qual município fica cada hospital. A gente descobriu isso pelo cadastro nacional de saúde e cruzou com a população do IBGE. Aí apareceu que só 23 dos 246 municípios têm leito da rede estadual, e que Aparecida de Goiânia tem quatro vezes menos leitos por pessoa que Goiânia, que fica do lado.

**O que fizemos.** Testamos 17 fontes públicas, uma por uma, e descartamos quatro que não serviam. Depois construímos o sistema todo, da coleta até a API, com 140 testes automáticos. E o painel, que é onde isso vira coisa de olhar.

**Como funciona.** O `http` busca nos sites do governo, a pasta `fontes` traduz cada resposta, o `municipios` padroniza a chave, que é por onde as fontes se cruzam, o `banco` guarda, o `indicadores` faz a conta e o `api` entrega para fora, com chave de acesso.

**O painel.** Ele não mostra dado, ele responde três perguntas. Onde está, que é o mapa dos 246 municípios. Uma coisa explica a outra, que cruza dois indicadores. E como mudou, que é a série de dezessete anos.

**A frase em cima do mapa não foi escrita, foi calculada.** Ela sai do próprio dado. Se eu trocar de indicador, ela troca junto. Se o dado mudar amanhã, ela muda sozinha.

**As stacks.** Python com FastAPI no backend, PostgreSQL como banco e Next.js no painel.

## O achado que vale mostrar

Gastar mais em saúde não explica ter menos dengue. Dividimos em cinco grupos os 244 municípios que têm os dois números, pelo gasto em saúde por morador. Os 48 que menos gastam têm 1.448 casos por 100 mil. Os 49 que mais gastam têm 1.602. Praticamente igual, e o painel diz isso com todas as letras.

Isso não é o sistema falhando. É a resposta, e é uma resposta que ninguém consegue dar sem cruzar o Tesouro Nacional com o portal de Goiás, que é exatamente o que o projeto faz.

## Se ele perguntar se dá para confiar no gráfico

Três coisas seguram ele. A altura da barra é a mediana e não a média, porque uma cidade de dois mil habitantes com número fora da curva desloca a média do grupo inteiro. A frase que resume não compara só as pontas, ela conta quantos degraus sobem, senão anunciaria padrão num desenho que sobe e desce. E quando o cruzamento tem menos de cinquenta municípios, ela avisa em vez de fingir que achou padrão.

Os dois últimos apareceram quando rodamos as trinta combinações possíveis contra o banco, em vez de olhar uma e dar por bom.

## Se ele pedir os números

Goiânia tem 1.963 leitos para 1,5 milhão de habitantes, o que dá 130 por 100 mil. Aparecida de Goiânia tem 189 leitos para 556 mil habitantes, o que dá 34 por 100 mil. E 223 dos 246 municípios não têm nenhum leito da rede estadual.

O dado é da rede estadual, não inclui hospital municipal nem privado. É importante dizer isso, senão o número parece pior do que é.

## Se ele perguntar como o cruzamento funciona

Cada fonte tem seu arquivo que sabe pedir e traduzir, o sistema recusa resposta incompleta, e converte o município para um formato único, que é por onde as fontes se cruzam.

## Demonstração ao vivo

**1.** `pytest` mostra os 140 testes passando em 3 segundos.

**2.** `python -m radar` busca os dados e enche o banco. Leva cerca de um minuto, porque consulta o cadastro de cada hospital respeitando o limite de um pedido por segundo.

**3.** No banco, o ranking de leitos por 100 mil habitantes.

**4.** `RADAR_CHAVES=demo .venv/bin/uvicorn --factory radar.api:cria_app` sobe a API, e `/docs` no navegador mostra a documentação que o FastAPI gera sozinho.

**5.** Na pasta `web`, `pnpm dev` sobe o painel em `localhost:3000`. Troco de indicador para a frase mudar, abro o cruzamento no gasto em saúde contra dengue, e a série para mostrar 2024.

**A dengue, se sobrar tempo.** 2024 teve 437 mil casos em Goiás, 12,6 vezes o ano mais brando dos dezessete. E 2026 já está em 157 mil com o ano pela metade.

## Por que FastAPI

Ele gera a documentação sozinho, a partir das próprias funções, o que já cumpre um requisito do projeto. Confere os dados de entrada sozinho. E o ecossistema Python é onde estão as bibliotecas que a coleta precisa.
