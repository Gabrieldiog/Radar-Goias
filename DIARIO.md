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

## Dia 9, 20 de agosto de 2026

Abrimos um eixo novo. Além de saúde, o Radar agora cobre atendimento ao cidadão, com o desempenho da ouvidoria por órgão, e ganhou também as unidades básicas de saúde por habitante. São quatro indicadores no total, e o painel deixou de ser só mapa: indicador por órgão vira tabela, porque não cabe em mapa.

Dois achados sobre o dado. Nas UBS, a lógica se inverte em relação aos leitos: Goiânia tem a pior cobertura por habitante do estado, 0,58 unidade por 10 mil, enquanto cidades pequenas passam de 20. Na ouvidoria, o prazo legal de 30 dias não separa ninguém, porque quase todos cumprem; o que separa é o tempo médio, que vai de 2,5 dias na SEMAD a 16,5 na UEG.

Dois erros nossos apareceram e valeram a pena. O primeiro: a fonte deixa o campo de dias vazio em nove registros, e o código transformava vazio em zero, o que fazia a manifestação parecer respondida na hora e puxava a média para baixo. Além disso, sete linhas colidiam e eram sobrescritas, perdendo contagem. Agora vazio continua vazio, fica fora da média, e a soma bate exatamente com as 30.459 manifestações da fonte.

O segundo só apareceu testando de ponta a ponta: a rota usava 2025 como ano padrão, mas a ouvidoria só tem 2026, então o painel abria vazio. Agora o ano padrão vem do dado, e não fixo no código.

Também separamos o banco de testes do banco de trabalho. Antes, rodar os testes apagava os dados carregados, o que já tinha atrapalhado quatro vezes.

Fechamos o dia colocando o sistema inteiro no Docker. Antes, o compose subia só o banco; agora ele constrói a API, sobe o banco, roda a coleta buscando nas fontes públicas e deixa tudo respondendo. Testamos do zero, apagando até o volume de dados: em 70 segundos o sistema estava de pé com os quatro indicadores funcionando. É isso que garante que o projeto rode na máquina de qualquer pessoa com um comando só.

## Dia 10, 20 de agosto de 2026

Abrimos o eixo de dinheiro público, que era o primeiro da lista e o último a sair. Agora o Radar traz quanto cada município empenhou em saúde, educação e segurança, direto da declaração anual que eles entregam ao Tesouro Nacional, e divide pela população.

São seis indicadores no total, cobrindo três dos cinco eixos.

Essa fonte é lenta: o Tesouro exige um pedido por município, e respeitamos o limite de um por segundo, então a carga leva alguns minutos. Por isso ela ficou num comando separado. Como o dado é anual, não faz sentido pagar esse tempo toda vez.

A armadilha do dia foi de leitura. O Tesouro coloca função e subfunção no mesmo campo, então aparece "12 - Educação" e logo abaixo "12.365 - Educação Infantil", "12.366" e "12.367". Quem casar por pedaço do nome conta educação quatro vezes. Nosso código já casava exato, mas o teste não provava isso, e a mutação passou incólume. Reescrevemos o teste para exigir o valor certo, e agora ele pega.

Antes de começar o dia, juntamos os cinco branches acumulados na main, que já estava difícil de acompanhar.

## Dia 11, 20 de agosto de 2026

O eixo de segurança entrou, e ele era o mais difícil. A fonte estadual não serve, como a pesquisa já tinha mostrado, então usamos a base nacional do Ministério da Justiça. São 31 tipos de ocorrência publicados, mas só 11 vêm com município; os outros existem apenas no total do estado, e isso precisa ser dito no painel para ninguém achar que esquecemos o crime patrimonial.

A planilha tem 13 MB compactada e mais de 200 MB por dentro, então é lida em fluxo, uma linha por vez. Carregar Goiás inteiro leva 49 segundos.

O resultado tem um número que vale a apresentação: 138 dos 246 municípios não registraram nenhum homicídio nos sete meses de 2026. A própria secretaria de segurança cita esse tipo de dado nos comunicados dela, mas nunca publica a planilha que permitiria conferir. Agora dá para conferir.

Uma ressalva estatística que precisa acompanhar esse indicador: cidade pequena com duas vítimas aparece com taxa altíssima. Não é erro de conta, é o denominador pequeno, e o painel precisa avisar.

Também aprendemos que o tipo dos campos muda de um ano para o outro na mesma fonte: a pesquisa viu os campos de sexo como texto em 2025, e em 2026 eles vêm como número.

São sete indicadores cobrindo quatro dos cinco eixos. Falta educação.

## Dia 12, 21 de agosto de 2026

O painel deixou de ser um mapa com dois botões. Agora ele responde três perguntas: onde está, uma coisa explica a outra, e como mudou. Os sete indicadores aparecem agrupados pelos quatro eixos, e cada um traz uma frase de destaque calculada do próprio dado, não escrita à mão. Trocar de indicador troca a frase, e é ela que diz, por exemplo, que 223 dos 246 municípios não têm nenhum leito da rede estadual.

A API ganhou a série histórica de dengue, dezessete anos, com filtro por município. Com ela dá para ver que 2024 teve 437 mil casos no estado, 12,6 vezes o ano mais brando da série, e que 2026 já está em 157 mil com o ano pela metade.

Os dois gráficos novos foram refeitos no mesmo dia, porque a primeira versão não se explicava sozinha. A série era uma linha, que obriga o leitor a medir altura contra o eixo, e virou barra com o número escrito em cima de cada ano. O cruzamento era uma nuvem de 246 pontos, que não responde nada a quem olha, e virou cinco grupos de 49 municípios ordenados pelo primeiro indicador, com o segundo na altura da barra.

Dois erros apareceram quando rodamos as trinta combinações possíveis contra o banco em vez de olhar só uma. A frase que resume o cruzamento comparava apenas as pontas, então anunciava que uma coisa acompanha a outra num desenho que subia e descia no meio. Agora ela também conta quantos degraus sobem. E qualquer cruzamento com leitos formava grupos de quatro cidades, porque leitos só existe em 23 municípios, então abaixo de cinquenta ela avisa isso em vez de fingir que achou padrão.

Trocamos média por mediana nas barras pelo mesmo motivo que já tinha aparecido no eixo de segurança: uma cidade de dois mil habitantes com número fora da curva desloca a média do grupo inteiro.
