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

## Dia 13, 22 de agosto de 2026

O eixo que faltava começou pelo denominador. Antes de saber se dinheiro vira aprendizagem, é preciso saber quantos alunos existem, e isso mora no Censo Escolar do INEP. O arquivo é um ZIP de 33 MB com um CSV de 426 colunas e 218 MB por dentro, então é lido em fluxo como a planilha do SINESP. Goiás inteiro sai em oito segundos: 4.746 escolas em atividade, nos 246 municípios, com 1.550.149 matrículas.

A decisão que muda o resultado é separar por rede. O gasto que o município declara ao Tesouro é o gasto dele, então o denominador certo é o aluno da rede municipal, que são 703.735, e não o total do território. Dividir pelo total daria ao município a conta de aluno que é do estado, do governo federal ou da escola particular, e faria todo município parecer gastar menos da metade do que gasta.

Três armadilhas apareceram, e as três já estavam previstas na pesquisa de fontes. O arquivo é LATIN-1 mas o cabeçalho é ASCII puro, o que faz o programa parecer certo até chegar num nome com acento. Existem três contagens diferentes de escola no mesmo arquivo, e só a de escolas em atividade serve como denominador, senão entram 280 escolas paralisadas ou extintas. E o servidor do INEP derruba cerca de uma conexão em dez, o que aconteceu logo na primeira tentativa de hoje, então o download ganhou retry com espera crescente.

Um número que não esperávamos: Goiânia tem mais aluno na rede privada, 111.390, do que na rede municipal, 102.505. E enquanto todos os 246 municípios têm rede municipal e estadual, só 119 têm alguma escola particular e 25 têm escola federal.

Quebramos o código de propósito cinco vezes para conferir os testes, e as cinco foram pegas.

## Dia 14, 22 de agosto de 2026

O quinto eixo fechou. Com a matrícula de ontem servindo de denominador, o Radar passou a calcular quanto cada município gasta por aluno da rede municipal, cruzando a despesa que ele declara ao Tesouro com o censo do INEP. São 244 municípios, dos 246, porque dois não entregaram a declaração de educação.

A mediana é de 16.996 reais por aluno no ano, e a distância entre as pontas é menor do que parecia: Aloândia gasta 43.103 e Brazabrantes 7.480, cinco vezes e oito décimos. Não é o caso de denominador pequeno que aparece nos indicadores por habitante, porque Goiatuba, com 3.223 alunos, está quase no topo.

O resultado carrega os dois anos que o produziram, o exercício da despesa e o ano do censo, porque eles não coincidem: a despesa é de 2025 e o censo é de 2024. Número que junta duas datas precisa dizer quais são, senão vira comparação escondida.

O despacho da API precisou de cuidado. Já existia gasto em educação por habitante, e o novo é gasto em educação por aluno. Os dois começam igual, e a regra que separava indicador por prefixo mandaria o novo para a rota antiga, devolvendo o número errado com status 200. Escrevemos o teste que prova a separação antes de confiar nela.

Cinco mutações, e três sobreviveram na primeira rodada. Duas eram falha de teste de verdade. A que tirava o filtro de rede passou porque o teste olhava só a primeira linha do resultado, e a linha certa continuava em primeiro; agora ele exige que exista uma linha só. A que trocava o censo mais recente pelo mais antigo passou porque o teste tinha um ano só cadastrado, exatamente o erro que já tínhamos cometido com a população no dia 4; agora ele cadastra dois anos. A terceira era mutação equivalente, sem efeito, e a rodada seguinte confirmou isso.

## Dia 15, 23 de agosto de 2026

O IDEB entrou, e com ele o eixo educação ficou completo. São três planilhas do INEP, uma por etapa, somando 58 MB, e 14.295 notas de Goiás guardadas, cobrindo onze medições de 2005 a 2025.

A planilha é larga do jeito que planilha feita para gente ler costuma ser: cada ano é uma coluna, e são 133 delas. O código transforma isso em uma linha por ano, que é a forma que o banco e o gráfico precisam. As três armadilhas que a pesquisa tinha anotado estavam todas lá. O cabeçalho de máquina está na linha 10, porque as nove primeiras são título e legenda. Ausência de medida é escrita como um traço, e virar zero seria dizer que o município tirou a pior nota possível. E a rede "Pública" é o agregado das outras, então ela entra com nome próprio e nunca é somada junto.

Uma quarta armadilha a pesquisa não tinha visto: existem quatro redes em Goiás, e não três. Há uma escola federal.

O problema do dia foi de rede, não de dado. O download morria com erro de certificado, mesmo o curl funcionando na mesma URL. O servidor do INEP manda só o certificado da ponta e omite o intermediário, e o curl no macOS disfarça porque vai buscar o que falta sozinho, enquanto o Python não vai. A saída fácil seria desligar a verificação, e a saída certa foi baixar o intermediário do endereço que o próprio certificado indica, conferir que ele é assinado por uma raiz que o Python já confiava, e deixá-lo viajar junto do código. A cadeia fecha com a verificação inteira ligada, e isso vale também para o Docker, onde o sistema operacional não teria esse certificado guardado.

Guardamos as duas metades que formam a nota, e não só a nota. Cinco mutações, todas pegas.

## Dia 16, 23 de agosto de 2026

A nota virou indicador e virou gráfico, e o gráfico descobriu sozinho uma coisa que o número do IDEB esconde.

O IDEB é o produto de duas medidas que o INEP publica separadas: quanto se aprova e quanto se aprende. O painel mostra as duas embaixo das barras, e a frase do topo procura o ano em que a nota caiu e diz de onde veio a queda. Em Goiás ela aponta para 2021: a nota caiu de 6,1 para 5,8, mas a aprovação subiu, de 97% para 98%. Ou seja, aprovou mais e aprendeu menos. É a pandemia aparecendo na decomposição, e é uma leitura que a nota sozinha não entrega.

Tem outra coisa nesse mesmo gráfico. A aprovação saiu de 85% em 2005 e chegou a 99% em 2025, o que quer dizer que ela está no teto. De agora em diante, quase todo ganho de IDEB em Goiás tem que vir de aprendizagem, porque do outro lado não sobrou espaço.

Escolhemos anos iniciais na rede municipal de propósito, e o dado justifica: 241 dos 246 municípios têm rede própria nos anos iniciais, contra 3 no ensino médio, que é do estado. Comparar o gasto do município com uma etapa que ele não comanda seria cobrar dele o resultado de outro.

## Dia 17, 23 de agosto de 2026

O município ganhou página própria. Antes dava para clicar no mapa e ver um número; agora `/municipio/5208707` abre a ficha inteira, com os oito indicadores agrupados por eixo, a posição de cada um no ranking estadual e a série do IDEB daquele município.

A posição passou a vir da API, e ela tem um cuidado que parece detalhe e não é: município sem dado publicado fica de fora da contagem, em vez de aparecer em último lugar. Não ter leito cadastrado é diferente de ser o pior em leitos.

Goiânia mostra bem para que serve a ficha. Ela é 6ª em leitos entre os 23 que têm, 73ª em dengue entre 246, e a pior do estado em unidades de saúde por habitante. No IDEB fica em 114º de 241, atrás da maioria dos municípios pequenos.

Oito mutações e uma sobreviveu. O teste que dizia proteger o ranking de município sem dado não protegia nada, porque o indicador que usei no cenário nunca devolve linha com valor nulo, então o filtro nunca era exercido. Trocamos por um teste da função direto, com uma linha nula no meio, e agora ele pega.

## Dia 18, 24 de agosto de 2026

Duas cidades agora aparecem lado a lado. Escolhe-se um município de cada lado e os oito indicadores saem na mesma tela, com o valor, uma barra que compara só aquela linha e a posição de cada um entre os 246.

A parte que exigiu decisão foi dizer quem está melhor. Mais leito e mais nota é melhor, mais dengue e mais homicídio é pior, mas gastar mais por morador não é nem uma coisa nem outra. Os três indicadores de gasto entram sem marca de vencedor, de propósito, porque marcar um vencedor ali seria a leitura mais errada possível deste painel, que vem justamente mostrando que dinheiro não prevê resultado.

No servidor, comparar dois municípios custa as mesmas consultas que ver um só. O peso está no indicador, que varre o estado inteiro de qualquer jeito, então os dois saem no mesmo passeio em vez de dobrar o trabalho.

Goiânia contra Aparecida de Goiânia, que é o par que abre a apresentação, fica claro na tela: 130,7 leitos por 100 mil contra 33,7, e IDEB 6,6 contra 5,9.

## Dia 19, 24 de agosto de 2026

O projeto promete desde o primeiro dia que todo número é rastreável até a requisição que o trouxe. Hoje essa promessa virou tela. A página de procedência mostra cada conjunto de dados com o endereço de onde veio, o status que o servidor devolveu, o tamanho da resposta e a data, mais um resumo de quantas vezes batemos em cada porta e quantas foram recusadas.

E a página achou um problema logo que abriu, que é exatamente para isso que ela serve. Quando o arquivo grande já estava baixado, a carga reusava ele e gravava o caminho no disco em vez do endereço de origem. O registro apontava para a máquina de quem rodou. Agora a coleta guarda sempre a URL de origem, e o teste que prova isso passa um cliente nulo, o que também demonstra que o arquivo em cache é reusado sem tocar a rede.

## Dia 20, 24 de agosto de 2026

O sistema inteiro sobe com um comando, e agora isso inclui o painel. Banco, API e painel num `docker compose up -d`, com o painel esperando a API ficar saudável antes de subir.

E aqui apareceu o pior bug que este projeto teve até agora, justamente no requisito que mais importa. O `openpyxl` nunca tinha sido declarado como dependência. Ele entrou no dia 11, junto com a planilha do SINESP, e funcionava na nossa máquina porque estava instalado no ambiente por acaso. Dentro do Docker ele não existia. Desde o dia 11, portanto, o sistema não subia na casa de ninguém, e nós não vimos porque nunca reconstruímos a imagem.

A correção é uma linha, mas o que importa é o que veio junto: um teste que lê o código com AST, junta tudo que ele importa de fora e confere contra o que o `pyproject` declara. Tirar qualquer uma das duas dependências faz ele falhar. Esse teste teria pego o problema no dia em que ele nasceu.

Subimos do zero, com o volume apagado, para conferir de verdade: os três containers de pé, as quatro telas do painel respondendo, a chave de acesso sem aparecer no HTML entregue ao navegador, e os 246 municípios com dado. A carga de educação dentro do container leva 45 segundos, e o certificado intermediário do INEP que guardamos no dia 15 funcionou no Linux do container, que é onde ele mais fazia falta.

## Dia 21, 25 de agosto de 2026

O painel ganhou um desenho de verdade, e não um retoque.

Antes, tudo na tela tinha mais ou menos o mesmo peso: título, botões, frase, mapa. Agora existe hierarquia. Uma faixa escura abre todas as telas, com a marca, os atalhos e o título grande. Entraram duas famílias tipográficas novas junto da que já havia: uma de display, que carrega personalidade, e uma monoespaçada para número e rótulo, que é o registro certo para um projeto que fala de código IBGE e status HTTP.

A frase que cada visão calcula do próprio dado virou manchete, no maior corpo da página depois do título. Era a coisa mais valiosa do painel e estava no tamanho de uma legenda.

O acréscimo que mais mudou a leitura foi uma faixa com 246 quadrinhos, um por município, do maior para o menor. É a única tela que mostra os 246 de uma vez e responde de relance a pergunta que este projeto mais repete: quantos ficaram de fora? Em leitos, 223 dos quadrinhos aparecem vazios. A frase já dizia isso, mas ver é outra coisa.

Dois cuidados de sentido, e não de gosto. Os quadrinhos sem dado usam a mesma hachura que o mapa usa para sem dado, então "não existe este número aqui" tem uma linguagem só no painel inteiro. E o tom mais claro da rampa foi escurecido, porque no papel novo ele quase sumia, e município de valor baixo parecia buraco no mapa em vez de dado.

As quatro telas passaram a compartilhar o mesmo cabeçalho num componente só, para o desenho não se soltar de uma página para a outra. O painel inteiro foi reconstruído no Docker e conferido ali, que é onde o professor vai ver.

## Dia 22, 26 de agosto de 2026

O painel quebrou na tela, e o erro apontava para o lugar errado.

A mensagem dizia que a frase da ouvidoria tentou reduzir uma lista vazia. Só que a lista não estava vazia: a API devolvia 51 órgãos, 26 deles com mais de cem manifestações. O problema era outro, e mais feio.

Quando se troca de indicador, o nome do escolhido muda na hora, mas os dados só chegam depois. Existe um quadro, um só, em que a tela roda a receita do indicador novo em cima das linhas do indicador velho. Ao ir de Leitos para Ouvidoria, a frase procurava tempo de resposta em linhas de leito, não achava nada, e estourava. Isso valia para todos os indicadores: os outros não quebravam, apenas mostravam o número errado por um instante, que é pior porque ninguém vê.

A correção é estrutural. A resposta passou a dizer de qual indicador ela é, e a tela só desenha quando os dois batem. O mesmo vale para o cruzamento, que tinha exatamente o mesmo descompasso entre os dois eixos escolhidos e os pontos já carregados.

Por cima disso veio uma segunda camada: cada frase agora aguenta receber menos linha do que espera e devolve um texto avisando, em vez de derrubar a página inteira. Conferimos as nove frases de três jeitos, com dado de verdade, com lista vazia e alimentadas de propósito com as linhas do indicador errado. Nenhuma quebra.

E aí o conserto encontrou um terceiro bug, que estava escondido desde o dia 16. A consulta do IDEB não devolvia população, então clicar num município com o IDEB escolhido quebrava a ficha. Nunca tínhamos clicado nessa combinação. A primeira tentativa de correção juntou população à consulta e um teste antigo falhou na hora, com razão: com junção exigida, município sem população cadastrada sumiria do IDEB, e a nota do IDEB não se divide por habitante nenhum. Virou junção opcional, e a ficha passou a aguentar município sem população. Entrou também um teste de contrato que percorre o catálogo inteiro e exige que todo indicador de município devolva habitantes. É o teste que teria pego isso no dia 16.

Fechamos com uma busca no ranking, que ignora acento, porque quem digita rápido escreve goiania e espera achar Goiânia, que é a mesma normalização que o sistema já faz para cruzar as fontes. A posição continua vindo da lista inteira, para filtrar não renumerar o ranking.

Fechamos o dia com duas melhorias na faixa dos 246. Cada quadrinho passou a mostrar as iniciais do município, que não servem como identificador, porque três letras não separam Goiânia de Goianira, mas servem como pista, com o nome inteiro no tooltip. E os municípios sem dado deixaram de ser quadrinhos anônimos: agora eles vêm da lista completa dos 246, com nome e clique, porque município sem dado é município do mesmo jeito.

A lista deixou de ser estática. Clicar no mapa ou num quadrinho rola o ranking até aquele município. Isso exigiu uma correção que parece detalhe: sem `position` na lista, a posição do item é medida a partir do corpo da página inteira, e a rolagem erra o alvo. E clicar no mapa com um filtro de busca ligado passou a limpar o filtro, porque senão a tela esconderia justamente quem foi clicado.

