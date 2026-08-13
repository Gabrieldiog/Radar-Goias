# Radar Goiás

Uma plataforma que junta dados públicos do estado de Goiás, cruza fontes que não conversam entre si e calcula indicadores que não existem prontos em lugar nenhum.

Projeto da disciplina Projeto 2.

## O problema

Goiás publica muita coisa. O portal de dados abertos do estado tem 446 conjuntos de dados e mais de 10 GB de arquivos. O Tesouro Nacional expõe as contas do estado e dos 246 municípios por API. O IBGE dá população, malha geográfica e códigos. O Ministério da Saúde tem cadastro de estabelecimentos. O Tribunal de Contas dos Municípios publica índices de aplicação em educação e saúde por município desde 2011.

O problema não é falta de dado. É que cada um desses lugares fala uma língua diferente e nenhum deles conversa com o outro.

Um exemplo concreto que encontrei enquanto pesquisava: o estado publica a ocupação de leitos hospitalares num arquivo atualizado diariamente. Ótimo. Só que o hospital vem identificado como "86126/ HCAMP GOIANIA/ HOSPITAL DE ENFRENTAMENTO AO CORONAVIRUS DE GOIANIA", tudo num campo só. Não existe coluna de município. O que existe é um código CNES grudado no começo de um texto livre.

Para responder "quantos leitos de UTI existem por 100 mil habitantes em cada município de Goiás", que é uma pergunta que qualquer pessoa acharia razoável, você precisa extrair o CNES daquela string, achar o município do estabelecimento em outra base, pegar a população no IBGE e só então dividir.

Ninguém faz isso. Então a pergunta fica sem resposta.

O Radar Goiás existe para fazer esse trabalho chato uma vez, direito, e deixar o resultado disponível por uma API.

## Os cinco eixos

**Dinheiro público.** Para onde vai o dinheiro, e quanto sobra por habitante em cada município?

**Saúde.** Onde faltam leitos, onde a dengue aperta, onde estão as unidades básicas?

**Educação.** Quanto chega por aluno matriculado, e isso se reflete em alguma coisa?

**Segurança.** Quanto de crime, onde, por 100 mil habitantes?

**Atendimento ao cidadão.** O estado responde a ouvidoria no prazo? Quais órgãos travam?

O eixo de segurança é o mais frágil dos cinco e não adianta fingir o contrário. O motivo está em limitações conhecidas, mais abaixo.

## O que já foi verificado

Antes de escrever qualquer linha de código, testei as fontes na mão, uma requisição por segundo e com User-Agent identificável. Registrei URL exata, status HTTP e as primeiras linhas de cada resposta. A ideia era descobrir agora, e não na semana da entrega, que uma fonte é inviável.

Deu certo. Descobri que várias coisas que a documentação promete não funcionam, e que uma coisa que ninguém documenta funciona muito bem.

### O portal de Goiás tem SQL aberto, e isso muda tudo

O portal roda CKAN 2.9.5. A documentação promete a API DataStore, mas em muitos portais CKAN esse endpoint é decorativo: só responde para recursos efetivamente carregados no banco, e na prática quase nenhum está.

Aqui não é o caso. Dos 2.931 recursos do portal, 1.796 respondem à API. Entre os arquivos CSV, são 1.707 de 1.732, ou seja, 99%.

E tem mais. O endpoint de consulta SQL está aberto, então dá para rodar consulta de leitura direto no banco do portal. A tabela de casos notificados de dengue tem 2,5 milhões de linhas e o arquivo correspondente pesa 185 MB. Com um agrupamento por município, a resposta inteira vem em 625 bytes: Goiânia com 38.232 casos em 2025, Aparecida de Goiânia com 19.817, Anápolis com 11.375.

E aceita junção entre recursos diferentes. Cruzei o georreferenciamento das UBS com os casos de dengue por município numa única requisição, porque os dois vivem no mesmo banco.

Isso derruba metade da complexidade que um projeto desses normalmente tem. Para tudo que está dentro do portal de Goiás, não precisamos de pipeline de ingestão, porque o cruzamento acontece no servidor deles.

### A chave que faz tudo se encaixar

Cada fonte identifica município de um jeito. O IBGE usa código de 7 dígitos, Goiânia é 5208707. Os dados de saúde do estado usam 6 dígitos, que é o mesmo código sem o dígito verificador, então Goiânia vira 520870. O Portal da Transparência federal usa código SIAFI de 4 dígitos. O FNDE usa uma codificação do IBGE anterior a 1997.

Verifiquei que truncar o sétimo dígito é bijetivo para os 246 municípios de Goiás, sem nenhuma colisão. O nome normalizado em caixa alta e sem acento também é único dentro de Goiás, embora não seja nacionalmente.

Na prática, o município vira a espinha dorsal do banco e todo o resto se pendura nele.

### O que funciona e o que não funciona

O portal de dados abertos de Goiás funciona muito bem, com API e SQL, e 99% dos arquivos CSV consultáveis.

As APIs do IBGE de localidades, população e malhas funcionam sem chave e sem limite aparente.

O SICONFI, do Tesouro Nacional, funciona sem autenticação e já tem dado de 2026.

O Tribunal de Contas dos Municípios exporta índices por município em CSV, cobrindo os 246 municípios, com série de 2011 a 2024.

O Portal da Transparência federal funciona pelo download em lote, sem precisar de chave. A API com chave a gente não chegou a obter.

O FNDE funciona por uma consulta HTTP legada, mas exige uma requisição por município, o que encarece a coleta.

Três fontes ficaram pelo caminho. A SSP-GO não serve, porque publica apenas PDFs de uma página com números estaduais. O dados.gov.br não serve, porque exige token e mesmo assim só devolve metadado. E o PNCP está fora do ar, com erro 504 em todas as tentativas.

Cada achado passou por uma segunda checagem adversarial, feita de propósito para tentar derrubar a conclusão da primeira. Foi útil: pegou um erro de código de município que teria entrado silenciosamente no banco, e um valor de repasse federal que estava 19% inflado porque incluía linhas sem município.

## Indicadores que queremos calcular

A graça não está em republicar dado. Está em calcular coisa que não existe pronta.

- Leitos por 100 mil habitantes, por município, o que exige resolver CNES para município e cruzar com população do IBGE
- Transferência federal per capita, por município e por função, separando saúde e educação
- Casos de dengue por 100 mil habitantes, por semana epidemiológica
- UBS por 10 mil habitantes, com o mapa junto
- Taxa de resposta da ouvidoria no prazo, por órgão, para ver quais secretarias respondem e quais empurram
- Tempo médio de atendimento de manifestações e de pedidos de acesso à informação
- Percentual da receita aplicado em educação e saúde, por município, na série de 2011 a 2024
- Transferências diretas do FNDE por aluno matriculado, por município

Esse último nome é feio de propósito. O impulso era chamar de gasto em educação por aluno, que é bem mais bonito. Só que o FUNDEB, que é a maior fonte de financiamento da educação básica, não está disponível naquele sistema. Chamar de gasto por aluno o que na verdade são apenas as transferências diretas seria uma promessa que o dado não sustenta. Fica o nome feio e honesto.

## Como o sistema funciona

O caminho do dado tem três camadas, e a regra é nunca sobrescrever a de baixo.

A camada bruta guarda a resposta exata da fonte, com data e URL de origem. Se amanhã descobrirmos que interpretamos uma coluna errado, dá para reprocessar sem sair pedindo tudo de novo aos servidores do governo.

A camada tratada é onde o município vira chave única e as datas viram data de verdade. É aqui que o CNES escondido no texto do arquivo de leitos vira uma coluna própria, e que o código SIAFI vira código IBGE.

A camada de indicadores é o produto final: número calculado, com denominador explícito e a fonte de cada parcela registrada. Em cima dela ficam a API e o painel.

Um princípio que vale escrever: nenhum indicador entra na API sem que dê para responder de onde veio cada número dele. Se não dá para rastrear, não publica.

### A API

REST, com chave de API e limite de requisições por chave. As rotas devem ficar mais ou menos assim:

- Uma rota de municípios, que lista os 246 com código IBGE e população
- Uma rota de município individual, com a ficha completa daquele município
- Uma rota de catálogo, dizendo quais indicadores existem
- Uma rota de série, que devolve um indicador filtrado por município e por ano
- Uma rota de fontes, com a procedência e a data da última coleta

Toda resposta traz a data da coleta e a fonte. Um indicador sem procedência não vale nada.

Uma nota de segurança que vale registrar desde já: o portal de Goiás aceita SQL, e é tentador repassar isso para quem chama a nossa API. Não vamos fazer isso. As consultas ficam montadas no servidor, com parâmetros validados. A API pública nunca aceita SQL de fora.

## Requisitos funcionais

O que o sistema tem que fazer.

RF01. Coletar dados das fontes públicas de forma automatizada, cada fonte com seu próprio coletor, para que a falha de uma não derrube as outras.

RF02. Registrar a procedência de tudo que entra: URL exata, data e hora da coleta, status HTTP e tamanho da resposta.

RF03. Guardar a resposta original da fonte sem alteração, para permitir reprocessamento sem nova requisição ao servidor de origem.

RF04. Normalizar o identificador de município para o código IBGE de 7 dígitos, convertendo os formatos de 6 dígitos, de código SIAFI e de nome que as diferentes fontes usam.

RF05. Extrair o código CNES do campo de texto do arquivo de leitos e resolver a qual município cada estabelecimento pertence.

RF06. Calcular indicadores derivados do cruzamento de pelo menos duas fontes, com o denominador populacional vindo do IBGE.

RF07. Recalcular os indicadores quando a fonte for atualizada, mantendo o histórico das versões anteriores.

RF08. Expor os dados por uma API REST própria, com respostas em JSON.

RF09. Autenticar quem chama a API por chave, emitida por cadastro.

RF10. Limitar a quantidade de requisições por chave num intervalo de tempo, devolvendo status apropriado quando o limite estourar.

RF11. Oferecer um catálogo que liste os indicadores disponíveis, com descrição, unidade, fórmula e fontes de cada um.

RF12. Permitir filtrar qualquer indicador por município e por período.

RF13. Devolver, junto de cada resposta, a data da coleta e a identificação das fontes usadas naquele número.

RF14. Permitir comparar municípios entre si e ordenar por indicador.

RF15. Apresentar os dados num painel web com mapa dos 246 municípios de Goiás.

RF16. Registrar as falhas de coleta em log consultável, com o erro literal retornado pela fonte.

RF17. Trabalhar apenas com dados agregados nas bases de ouvidoria e de acesso à informação, sem expor manifestação individual.

## Requisitos não funcionais

Como o sistema tem que se comportar. Vários destes saíram direto do que a pesquisa de fontes revelou, e não de boa prática genérica.

RNF01. Nenhum domínio pode receber mais de uma requisição por segundo, e toda requisição sai com User-Agent identificável contendo forma de contato. São servidores públicos e o projeto não tem o direito de atrapalhar.

RNF02. Toda consulta SQL enviada ao portal de Goiás precisa levar limite explícito de linhas. Sem isso, o firewall de aplicação do estado responde com bloqueio, conforme já observado durante a pesquisa.

RNF03. A API pública nunca aceita SQL vindo de quem chama. As consultas são montadas no servidor com parâmetros validados.

RNF04. A camada de dados brutos é imutável. Correção de interpretação gera novo processamento, nunca sobrescrita do original.

RNF05. O coletor precisa validar se o arquivo mudou, por data de modificação ou identificador de versão, antes de baixar de novo.

RNF06. Antes de baixar arquivo grande, o coletor consulta o tamanho e decide. Nada de puxar centenas de megabytes por descuido.

RNF07. O coletor não pode presumir que um recurso disponível hoje continua disponível amanhã. Cerca de 1,5% dos arquivos do portal não carregam no banco, sem padrão, então é obrigatório checar recurso por recurso e ter caminho alternativo.

RNF08. A queda de uma fonte não pode derrubar a API. O sistema serve o último dado bom que tiver, sinalizando a data daquela coleta.

RNF09. Todo número publicado tem que ser rastreável até as parcelas que o originaram. Indicador que não se explica não vai ao ar.

RNF10. A API precisa ser documentada em formato aberto, de modo que outra pessoa consiga consumir sem perguntar nada para a gente.

RNF11. A coleta precisa ser idempotente. Rodar duas vezes o mesmo período não pode duplicar registro nem alterar resultado.

RNF12. O ambiente precisa ser reproduzível por outra pessoa a partir do repositório, sem configuração manual escondida.

RNF13. Credenciais e chaves ficam fora do código e fora do repositório.

RNF14. O tratamento de dados pessoais segue a LGPD, com a decisão de projeto de nem sequer armazenar campo identificável de cidadão.

RNF15. As fontes usadas precisam ser creditadas de forma visível, respeitando os termos de uso de cada portal.

RNF16. Em domínio cujo robots.txt desaconselhe coleta automatizada, o acesso fica restrito a poucas coletas agendadas, e essa decisão é documentada na metodologia.

## Limitações conhecidas

Prefiro deixar isso registrado no README do que descobrir na apresentação.

Segurança pública não tem dado municipal. A SSP-GO publica nove PDFs de uma página cada, todos com números agregados do estado inteiro, zero de 246 municípios. Os subdomínios de estatística respondem, mas o conteúdo é uma página de site em manutenção, e o host antigo está com certificado vencido desde abril. O dado municipal existe internamente, tanto que os próprios comunicados da secretaria citam quantos municípios ficaram sem homicídio no ano, mas ele não vira arquivo público.

As saídas possíveis são três: tratar o eixo como estadual e dizer isso claramente, buscar fonte federal com recorte municipal, ou abrir pedido via Lei de Acesso à Informação. A terceira é assíncrona e não serve para alimentar um sistema automatizado, então no máximo entra como complemento.

O portal do estado tem um firewall de aplicação que bloqueia consulta SQL sem limite de linhas. Descobri tomando um erro 403 com página de bloqueio da Subsecretaria de Tecnologia da Informação, código de bloqueio e tudo. Não houve bloqueio de IP, e a mesma consulta com limite explícito passa normalmente. Fica valendo como regra do projeto: toda consulta leva limite.

Cerca de 1,5% dos arquivos do portal não carregam no banco, sem padrão previsível. Cheguei a suspeitar que fossem sempre os mais recentes. Medi, e a hipótese caiu, porque 99,2% dos arquivos dos últimos sete dias estão lá. São falhas isoladas. Por isso o coletor precisa checar recurso por recurso e ter o download direto como plano B.

Há também tabela vazia se passando por tabela boa. Alguns recursos aparecem como carregados mas retornam zero registros, então é preciso checar o total antes de confiar.

## Dados pessoais

Os dados de ouvidoria e de acesso à informação são os mais sensíveis do projeto. Verifiquei coluna por coluna: as bases de manifestações e de pedidos de LAI trazem data de abertura, data de finalização, órgão, tipo, município e situação, mas não trazem nome, CPF nem o texto escrito pelo cidadão.

Mesmo assim, a regra do projeto é trabalhar só com agregados. Nada que permita identificar uma manifestação individual entra na API.

## Etiqueta com os servidores

São servidores públicos, mantidos com orçamento apertado, e um projeto de faculdade não tem o direito de atrapalhar.

Uma requisição por segundo por domínio, no máximo. User-Agent identificável, com contato. Cache agressivo do lado de cá, porque se o arquivo não mudou não faz sentido pedir de novo. E sempre checar o tamanho antes de baixar arquivo grande.

O robots.txt do Tribunal de Contas dos Municípios desaconselha coleta automatizada, embora o dado seja público e exportável. A decisão foi respeitar: naquele domínio, poucas coletas agendadas em vez de robô contínuo.

## Escopo do projeto

- [x] Verificar empiricamente o que cada fonte entrega
- [x] Definir a chave de junção entre as fontes
- [x] Modelo de dados e migrações
- [x] Coletores das fontes do núcleo
- [x] Cálculo dos primeiros indicadores
- [x] API REST com autenticação e limite de requisições
- [x] Painel web com o mapa dos 246 municípios

A ordem de ataque começa pelo portal de Goiás com o IBGE junto, porque é onde a razão entre esforço e resultado é melhor: SQL aberto, dado atualizado diariamente e chave de município limpa. Com essas duas fontes já saem indicadores de saúde e de ouvidoria de verdade.

Se o tempo apertar, o primeiro a cair é o eixo de segurança, pelo motivo que já expliquei, e o mapa vira uma tabela.

## Stack pretendida

Ainda em aberto, mas a inclinação é Python para coleta e cálculo, PostgreSQL para armazenar, e uma API leve em cima. O painel provavelmente entra depois, quando houver indicador suficiente para valer a pena.

## Fontes

Portal de Dados Abertos de Goiás, SICONFI do Tesouro Nacional, IBGE, Ministério da Saúde, Tribunal de Contas dos Municípios de Goiás, Portal da Transparência federal, FNDE, INEP e Controladoria-Geral do Estado de Goiás.

Dados verificados em 12 de agosto de 2026. Fontes públicas mudam sem aviso, então se algo aqui parar de bater com a realidade, provavelmente a realidade mudou primeiro.
