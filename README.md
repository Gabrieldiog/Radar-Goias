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

O eixo de segurança é o mais delicado dos cinco. A fonte estadual não serve e quem salva o eixo é uma fonte federal, que cobre homicídio mas não cobre crime patrimonial por município. Está explicado em limitações conhecidas, mais abaixo, porque é o tipo de detalhe que muda a leitura do número.

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

O SINESP, do Ministério da Justiça, resolve o eixo de segurança. São planilhas anuais de 2015 a 2026, atualizadas mensalmente, e onze dos trinta e um tipos de ocorrência vêm por município. Em Goiás no ano de 2025 a grade está completa: 246 municípios vezes 12 meses, sem um buraco sequer.

O INEP cobre o eixo de educação inteiro, com o Censo Escolar e o IDEB por município, ambos identificando o município por código IBGE de 7 dígitos.

O DATASUS resolve o problema do CNES. Um arquivo de 700 KB por competência traz o cadastro de estabelecimentos de Goiás, e os 246 municípios batem exatamente com a lista do IBGE.

O IPEADATA entrega taxa de homicídio por município já calculada, de 1980 a 2022, com código IBGE de 7 dígitos. Serve de série histórica longa e de conferência independente contra o SINESP.

Quatro fontes ficaram pelo caminho. A SSP-GO não serve, porque publica apenas PDFs de uma página com números estaduais. O dados.gov.br não serve, porque exige token e mesmo assim só devolve metadado. O PNCP está fora do ar, com erro 504 em todas as tentativas. E o FTP citado pelo Portal da Transparência de Goiás existe, mas recusa acesso anônimo e exige credencial nominal, o que não adianta: os dados de lá são do Executivo estadual e não têm coluna de município.

Um aviso para quem for repetir esta pesquisa. O endereço `dados.mj.gov.br`, que muita documentação ainda cita como portal do SINESP, **não existe mais**. O domínio não resolve em nenhum servidor de nomes. Os arquivos migraram para o site do Ministério da Justiça, e o próprio ministério mantém links quebrados apontando para o portal morto.

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
- Taxa de homicídio, feminicídio e suicídio por 100 mil habitantes, por município e por mês
- IDEB do município cruzado com a despesa em educação por aluno, para ver se dinheiro vira aprendizagem
- Homicídios cruzados com a despesa em segurança pública por habitante
- Incidência de dengue cruzada com cobertura de atenção primária e com volume de reclamações de saúde na ouvidoria

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

Segurança pública não tem dado municipal vindo do estado. A SSP-GO publica nove PDFs de uma página cada, todos com números agregados do estado inteiro, zero de 246 municípios. Os subdomínios de estatística respondem, mas o conteúdo é uma página de site em manutenção, e o host antigo está com certificado vencido desde abril.

Quem salva o eixo é o SINESP, do governo federal, mas com um limite que precisa estar escrito no painel: só onze dos trinta e um tipos de ocorrência vêm por município. Homicídio doloso, feminicídio, latrocínio, suicídio, tentativa de homicídio e mortes no trânsito, sim. Roubo, furto, roubo de veículo, estupro e tráfico de drogas, não, porque só existem no nível do estado. Ou seja, o crime patrimonial fica de fora do mapa. Se o painel não avisar, o usuário vai achar que o Radar esqueceu.

Duas armadilhas do SINESP que já custaram tempo na pesquisa. A chave de município é o nome em caixa alta com acento, não o código IBGE, então o cruzamento depende de normalizar texto e de filtrar o estado antes. E os campos de sexo da vítima são texto, não número, então somá-los sem converter concatena string em vez de somar.

Existe uma segunda fonte de homicídio, o IPEADATA, com série que vai de 1980 a 2022. Ela é útil como história longa e como conferência independente, mas conta coisa diferente: o número do IPEA vem de declaração de óbito, o do SINESP vem de registro policial. Não batem entre si, e colocar as duas no mesmo gráfico seria erro grosseiro.

Sobre o mínimo constitucional em educação e saúde, aquele percentual que a lei obriga o município a aplicar: ele não sai da API do Tesouro, porque os anexos que trazem esse cálculo não existem por lá. O que se calcula pela função orçamentária não é a mesma conta e não pode receber esse nome. O caminho certo é o Tribunal de Contas dos Municípios, que publica o índice já pronto.

O portal do estado tem um firewall de aplicação que bloqueia consulta SQL sem limite de linhas. Descobri tomando um erro 403 com página de bloqueio da Subsecretaria de Tecnologia da Informação, código de bloqueio e tudo. Não houve bloqueio de IP, e a mesma consulta com limite explícito passa normalmente. Fica valendo como regra do projeto: toda consulta leva limite.

Cerca de 1,5% dos arquivos do portal não carregam no banco, sem padrão previsível. Cheguei a suspeitar que fossem sempre os mais recentes. Medi, e a hipótese caiu, porque 99,2% dos arquivos dos últimos sete dias estão lá. São falhas isoladas. Por isso o coletor precisa checar recurso por recurso e ter o download direto como plano B.

Há também tabela vazia se passando por tabela boa. Alguns recursos aparecem como carregados mas retornam zero registros, então é preciso checar o total antes de confiar.

## Dados pessoais

Comecei achando que a ouvidoria seria o ponto sensível do projeto. Verifiquei coluna por coluna e ela passou: as bases de manifestações e de pedidos de acesso à informação trazem data de abertura, data de finalização, órgão, tipo, município e situação, mas não trazem nome, CPF nem o texto escrito pelo cidadão. O campo mais longo tem 105 caracteres e é nome de setor.

O risco estava em outro lugar, e é sério. Três achados que mudaram regra de projeto.

O cadastro de estabelecimentos do DATASUS traz CPF de pessoa física. Um em cada quatro registros é consultório de profissional autônomo, e naquele caso o campo que parece CNPJ é o CPF da pessoa, com dígito verificador válido. Mais de cem registros trazem também agência e conta bancária. A regra virou obrigatória: ao ler o arquivo, essas colunas são descartadas na entrada, antes de qualquer coisa tocar o banco.

A API do Ministério da Saúde expõe, sem token nenhum, uma listagem nominal de médicos com nome civil, registro profissional e raça declarada. Raça é dado sensível pela LGPD, associado a pessoa identificada. Esse endpoint não entra no projeto em hipótese alguma.

A folha de pagamento do estado traz nome do servidor, cargo, lotação, data de admissão e remuneração, por pessoa e por mês. Ser público por transparência não autoriza republicar. E como não tem coluna de município, nem serve ao projeto.

Duas regras gerais que saíram disso. Agregar por município não basta sozinho, porque em município pequeno a própria contagem reidentifica: mais da metade dos municípios com consultório autônomo tem dois ou menos. Então vale supressão de contagens abaixo de cinco. E nenhuma linha de microdado individual é exposta pela API, em nenhuma circunstância.

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

Se o tempo apertar, o mapa vira uma tabela, a série do Tesouro encolhe para os três exercícios mais recentes e o eixo de segurança fica só com homicídio e feminicídio, que são baratos de calcular.

Duas coisas que a pesquisa mostrou não valerem o esforço e que já ficam cortadas de antemão. A sinopse estatística do INEP, que parecia ser a alternativa leve aos microdados, é na verdade 72 vezes maior que a fatia de Goiás dos próprios microdados. E o arquivo de pedidos de acesso à informação do portal estadual é duplicata exata de um recorte do arquivo de manifestações, com os mesmos identificadores linha a linha, então ingerir os dois contaria tudo em dobro.

## Stack

**Backend em Python 3.12 com FastAPI.** FastAPI porque ele gera a documentação OpenAPI sozinho, o que já entrega um dos requisitos sem trabalho extra, e porque a coleta depende de bibliotecas que só existem maduras em Python. Duas em particular: a que descomprime o formato proprietário do cadastro de estabelecimentos do DATASUS, e a que lê planilha em modo de fluxo, necessária porque o arquivo do SINESP tem planilha interna de até 410 MB e estoura a memória se lido de uma vez.

**PostgreSQL no Supabase.** A escolha do Supabase é por causa do prazo: o plano gratuito é permanente, enquanto banco gratuito que expira em 90 dias venceria no meio de um projeto de três meses.

**httpx** para as requisições, com controle de ritmo de uma por segundo por domínio.

**pytest** para os testes, que ficam na pasta `testes` na raiz do repositório.

**Front em React com JavaScript**, separado, entrando depois que a API estiver de pé.

**Docker** para subir o banco local. Ele não tem relação com a hospedagem do front: serve para desenvolver e para qualquer pessoa conseguir rodar o projeto sem instalar Postgres na mão.

**Deploy** em três pedaços independentes. O front React vai para a Vercel. A API vai para um host que roda container, porque FastAPI com conexão persistente de banco não combina com função serverless, que morre entre requisições e abre conexão nova toda vez. O banco fica no Supabase. O front conversa com a API por proxy no servidor, e não direto do navegador, o que elimina a necessidade de CORS entre as duas metades.

## Como rodar

Suba o banco com `docker compose up -d`. O esquema é aplicado sozinho na primeira subida, então não há passo de migração manual.

A porta é a 5433, escolhida para não brigar com uma instalação de Postgres que já exista na 5432. Se a 5433 também estiver ocupada na sua máquina, suba com outra, por exemplo `RADAR_PORTA=5434 docker compose up -d`, e aponte a aplicação para ela com `RADAR_BANCO_URL`.

Crie o ambiente virtual com `python3 -m venv .venv` e instale com `.venv/bin/python -m pip install -e ".[dev]"`.

Carregue os dados com `.venv/bin/python -m radar`. Esse comando cria as tabelas se faltarem, carrega os 246 municípios, busca a população no IBGE e grava, registrando de qual requisição o dado veio. Pode rodar quantas vezes quiser, porque ele atualiza em vez de duplicar.

Suba a API com `RADAR_CHAVES=sua-chave .venv/bin/uvicorn --factory radar.api:cria_app`. A documentação interativa fica em `/docs` e a rota `/saude` responde sem chave, para monitoramento.

Rode os testes com `.venv/bin/python -m pytest`.

### O painel

O painel fica na pasta `web` e é um projeto Next.js separado. Entre nela, instale com `pnpm install` e rode com `pnpm dev`. Ele sobe em `http://localhost:3000`.

O navegador nunca fala com a API direto: o painel chama uma rota do próprio Next, que repassa o pedido por trás. Por isso não existe CORS entre as duas metades, e a chave de acesso fica só no servidor, sem chegar ao navegador. As duas variáveis que configuram isso estão em `web/.env.example`.

Para apontar para outro banco, por exemplo o do Supabase, basta definir a variável de ambiente `RADAR_BANCO_URL`. É a única diferença entre rodar local e rodar publicado.

### Sobre os testes

Os testes de lógica não tocam a rede. Os 246 municípios ficam versionados em `radar/dados/municipios_go.json`, gerado a partir da API de localidades do IBGE, e a resposta de população usada nos testes está gravada em `testes/fixtures`. Isso é proposital: suíte que depende de servidor de governo falha por motivo errado e ensina a ignorar teste vermelho.

Os testes que precisam de banco são pulados automaticamente se não houver banco no ar, então a suíte roda em qualquer máquina, com ou sem Docker.

## Fontes

Portal de Dados Abertos de Goiás, SICONFI do Tesouro Nacional, IBGE, Ministério da Saúde, Tribunal de Contas dos Municípios de Goiás, Portal da Transparência federal, FNDE, INEP e Controladoria-Geral do Estado de Goiás.

Dados verificados em 12 de agosto de 2026. Fontes públicas mudam sem aviso, então se algo aqui parar de bater com a realidade, provavelmente a realidade mudou primeiro.
