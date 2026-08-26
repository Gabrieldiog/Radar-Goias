# Diário de desenvolvimento

## Dia 1, 14 de agosto de 2026

foi construído a espinha dorsal do projeto: o módulo que resolve município. Cada fonte pública identifica município de um jeito, seja o código IBGE de 7 dígitos, o mesmo código sem o dígito verificador ou o nome em caixa alta, e agora tudo converge para um formato só. Ele também barra os valores que ocupam a coluna de município nas fontes sem serem município. Junto veio a guarda que recusa consulta SQL sem LIMIT, porque o firewall do portal de Goiás responde 403 sem ele, os testes foram escritos antes do código e vistos falhar. Depois quebramos o código de propósito três vezes, para provar que eles pegam regressão de verdade.


## Dia 2, 15 de agosto de 2026

O projeto ganhou banco. Criamos o esquema com três tabelas, município, população e coleta, essa última guardando de qual requisição cada dado veio, que é o que sustenta a promessa de procedência. O Docker sobe o Postgres já com o esquema aplicado, sem passo manual. Os 246 municípios foram carregados de verdade, e a leitura da população do IBGE recusa a resposta se não vierem exatamente 246, porque resposta incompleta de servidor de governo é comum e passa despercebida, duas armadilhas viraram teste: o IBGE devolve o nome do município sufixado com a UF, então a chave tem que ser o código, e recarregar a população atualiza em vez de duplicar.

## Dia 3, 15 de agosto de 2026

Agora existe um comando só. Rodar `python -m radar` cria as tabelas se faltarem, carrega os 246 municípios, busca a população no IBGE e grava tudo, registrando de qual requisição cada número veio. Apagamos o banco inteiro e reconstruímos com esse comando para confirmar que funciona do zero.

Foi a primeira vez que o projeto tocou a rede, então veio junto o controle de ritmo: no máximo uma requisição por segundo por domínio, com User-Agent que diz quem somos e como nos achar. O limite é por domínio e não global, senão consultar duas fontes diferentes ficaria duas vezes mais lento sem necessidade.

Rodar duas vezes não duplica dado, e fonte que responde incompleta não grava nada pela metade. Quatro mutações para provar que os testes seguram isso.

## Dia 4, 17 de agosto de 2026

O Radar calculou seu primeiro indicador: incidência de dengue por 100 mil habitantes, nos 246 municípios. A consulta é agregada no servidor do portal, então trazemos 200 KB em vez de baixar um arquivo de 193 MB.

A guarda de LIMIT do dia 1 finalmente foi usada de verdade, e ganhou uma regra nova: LIMIT zero também é barrado, porque devolve vazio em silêncio e parece ausência de dado em vez de erro.

O portal se mostrou lento e irregular, de 2 segundos a mais de 30 na mesma consulta, então cada fonte agora pode esticar seu próprio tempo de espera.

O resultado declara qual população foi usada como denominador, e isso quase passou batido: a mutação que trocava a população mais recente pela mais antiga não quebrou teste nenhum, porque o teste só tinha um ano cadastrado. Corrigimos o teste, que agora pega.

## Dia 5, 18 de agosto de 2026

A API REST subiu. Ela serve o catálogo de indicadores, a lista dos 246 municípios, a ficha de um município e o valor do indicador filtrado por município e ano. Toda resposta de indicador carrega as fontes que a produziram, porque número sem procedência não vale nada. A rota de saúde responde sem chave, para o monitoramento poder bater nela.

Chave de API no cabeçalho ou na query, e o limite de requisições conta por chave, não por IP. Isso importa: numa faculdade, todo mundo sai pelo mesmo IP, e um balde compartilhado faria um usuário derrubar os colegas.

Foi justamente aí que a mutação pegou a gente. Trocar o balde por chave por um balde por IP não quebrou teste nenhum, porque nenhum teste usava duas chaves diferentes. Escrevemos o teste que faltava e agora ele pega.

Também vimos o portal mudar o dado embaixo da gente: Goiânia tinha 38.232 casos ontem e 38.231 hoje. É a fonte se corrigindo, e é o motivo de guardarmos data e URL de cada coleta.

## Dia 6, 20 de agosto de 2026

Resolvemos o problema que abre a apresentação: o arquivo de leitos do estado não diz em qual município fica cada hospital, só traz um código de cadastro colado no nome da unidade. Agora o sistema separa esse código, pergunta ao cadastro nacional de saúde a qual município ele pertence e fecha o cruzamento. Das 46 unidades, nenhuma ficou sem município.

O resultado mostra uma concentração forte: só 23 dos 246 municípios têm leito da rede estadual. Aparecida de Goiânia, com 556 mil habitantes, tem 34 leitos por 100 mil, quatro vezes menos que Goiânia, que fica do lado.

O firewall do portal nos bloqueou de novo, agora por causa de uma função de conversão de data. Aprendemos que ele barra mais coisa do que imaginávamos, e passamos a fazer a lógica de data do nosso lado.

Um teste meu falhou porque chutei o dígito verificador de Uruaçu. O código acertou, porque busca na tabela em vez de calcular. Era exatamente para isso que a busca existia.

## Dia 7, 20 de agosto de 2026

O backend passou a servir o mapa. A malha dos 246 municípios veio do IBGE e ficou versionada junto do código, porque contorno de município não muda e assim os testes não dependem de servidor de governo. O código de área de cada polígono bate exatamente com os nossos 246, então o painel vai conseguir pintar o mapa juntando pelo código, sem conversão nenhuma.

A rota do mapa manda o navegador guardar o arquivo por um dia, já que a geometria é fixa e pesa 176 KB.

A ficha do município também cresceu: agora ela devolve os indicadores daquele município junto com a população. Goiânia responde com 2.540 casos de dengue e 130,6 leitos por 100 mil habitantes numa requisição só, que é o que a tela de detalhe do painel vai precisar.

Município sem leito cadastrado devolve o campo vazio em vez de sumir com ele, para o painel não ter que adivinhar se o dado não existe ou se a rota mudou.

## Dia 8, 20 de agosto de 2026

O painel nasceu. É um projeto Next.js separado, na pasta web, que mostra os 246 municípios num mapa colorido conforme o indicador escolhido, e um botão para trocar entre leitos e dengue. Clicar num município mostra o número dele.

O mapa é desenhado em SVG direto do contorno do IBGE, sem biblioteca de mapa. Para um estado só, uma projeção linear simples já sai correta, e assim o projeto não ganha uma dependência pesada para desenhar polígono.

O navegador nunca fala com a API direto. Ele chama uma rota do próprio Next, que repassa o pedido por trás com a chave. Conferimos no HTML entregue ao navegador: nem a chave nem o endereço interno da API aparecem lá. Isso também elimina o problema de CORS entre as duas metades.

Municípios sem dado ficam em cinza em vez de sumir do mapa, e a legenda avisa isso, para ninguém achar que é falha de carregamento.
