# Diário de desenvolvimento

## Dia 1, 14 de agosto de 2026

foi construído a espinha dorsal do projeto: o módulo que resolve município. Cada fonte pública identifica município de um jeito, seja o código IBGE de 7 dígitos, o mesmo código sem o dígito verificador ou o nome em caixa alta, e agora tudo converge para um formato só. Ele também barra os valores que ocupam a coluna de município nas fontes sem serem município. Junto veio a guarda que recusa consulta SQL sem LIMIT, porque o firewall do portal de Goiás responde 403 sem ele, os testes foram escritos antes do código e vistos falhar. Depois quebramos o código de propósito três vezes, para provar que eles pegam regressão de verdade.


## Dia 2, 14 de agosto de 2026

O projeto ganhou banco. Criamos o esquema com três tabelas, município, população e coleta, essa última guardando de qual requisição cada dado veio, que é o que sustenta a promessa de procedência. O Docker sobe o Postgres já com o esquema aplicado, sem passo manual. Os 246 municípios foram carregados de verdade, e a leitura da população do IBGE recusa a resposta se não vierem exatamente 246, porque resposta incompleta de servidor de governo é comum e passa despercebida.

Duas armadilhas viraram teste: o IBGE devolve o nome do município sufixado com a UF, então a chave tem que ser o código, e recarregar a população atualiza em vez de duplicar.

Testes de novo antes do código, e três mutações para provar que eles pegam regressão.
