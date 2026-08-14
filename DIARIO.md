# Diário de desenvolvimento

## Dia 1, 14 de agosto de 2026

foi conrtuido a espinha dorsal do projeto: o módulo que resolve município. Cada fonte pública identifica município de um jeito, seja o código IBGE de 7 dígitos, o mesmo código sem o dígito verificador ou o nome em caixa alta, e agora tudo converge para um formato só. Ele também barra os valores que ocupam a coluna de município nas fontes sem serem município. Junto veio a guarda que recusa consulta SQL sem LIMIT, porque o firewall do portal de Goiás responde 403 sem ele, os testes foram escritos antes do código e vistos falhar. Depois quebramos o código de propósito três vezes, para provar que eles pegam regressão de verdade.


