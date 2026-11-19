@performance
Feature: Desempenho de resposta da Book Store API
  Como pessoa responsavel pela qualidade
  Quero acompanhar a latencia do catalogo
  Para verificar se a resposta media atende ao limite esperado

  Scenario: Retornar o catalogo em ate dois segundos na media
    Given que a API da Book Store esta configurada
    When meco cinco chamadas sequenciais ao catalogo
    Then as cinco respostas do catalogo sao validas
    And a media de resposta nao excede dois segundos
