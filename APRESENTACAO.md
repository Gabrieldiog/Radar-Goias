# Roteiro da apresentação

## A fala

**O que é.** O Radar Goiás junta dados públicos do estado num lugar só e cruza fontes que não conversam entre si.

**O que ele propõe.** Cada órgão publica do seu jeito, então ninguém consegue comparar nada. O estado publica todo dia quantos leitos de hospital estão ocupados, mas o arquivo não diz em qual município fica cada hospital: vem só um código de cadastro colado no nome da unidade. A gente separou esse código, perguntou ao cadastro nacional de saúde a qual cidade ele pertence, e cruzou com a população do IBGE. Aí apareceu que só 23 dos 246 municípios têm leito da rede estadual, e que Aparecida de Goiânia, com 556 mil habitantes, tem quatro vezes menos leitos por pessoa que Goiânia, que fica do lado, com 97% deles ocupados.

**O que fizemos.** Testamos 17 fontes públicas, uma por uma, e descartamos quatro que não serviam. Depois construímos o sistema todo, da coleta até a API, com 82 testes automáticos.

**Como funciona.** O `http` busca nos sites do governo, a pasta `fontes` traduz cada resposta, o `municipios` padroniza a chave, que é por onde as fontes se cruzam, o `banco` guarda, o `indicadores` faz a conta e o `api` entrega para fora, com chave de acesso.

**As stacks.** Python com FastAPI no backend, PostgreSQL como banco e Next.js no painel.

## Se ele pedir os números

Goiânia tem 1.963 leitos para 1,5 milhão de habitantes, o que dá 130 por 100 mil. Aparecida de Goiânia tem 189 leitos para 556 mil habitantes, o que dá 34 por 100 mil. E 223 dos 246 municípios não têm nenhum leito da rede estadual.

O dado é da rede estadual, não inclui hospital municipal nem privado. É importante dizer isso, senão o número parece pior do que é.

## Se ele perguntar como o cruzamento funciona

Cada fonte tem seu arquivo que sabe pedir e traduzir, o sistema recusa resposta incompleta, e converte o município para um formato único, que é por onde as fontes se cruzam.

## Demonstração ao vivo

**1.** `pytest` mostra os 82 testes passando em 2 segundos.

**2.** `python -m radar` busca os dados e enche o banco. Leva cerca de um minuto, porque consulta o cadastro de cada hospital respeitando o limite de um pedido por segundo.

**3.** No banco, o ranking de leitos por 100 mil habitantes.

**4.** `RADAR_CHAVES=demo .venv/bin/uvicorn --factory radar.api:cria_app` sobe a API, e `/docs` no navegador mostra a documentação que o FastAPI gera sozinho.

## Por que FastAPI

Ele gera a documentação sozinho, a partir das próprias funções, o que já cumpre um requisito do projeto. Confere os dados de entrada sozinho. E o ecossistema Python é onde estão as bibliotecas que a coleta precisa.
