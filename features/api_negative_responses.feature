Feature: Respostas negativas da Book Store API
  Como pessoa usuaria da API
  Quero receber erros claros ao enviar dados invalidos
  Para saber quando uma operacao nao foi autorizada ou aceita

  Scenario: Rejeitar credenciais de usuario inexistente
    Given credenciais de um usuario inexistente
    When solicito um token com essas credenciais
    Then a API informa que o token nao foi gerado
    When verifico a autorizacao com essas credenciais
    Then a API recusa a autorizacao com erro de usuario

  Scenario: Rejeitar reserva de ISBN inexistente
    Given que a API da Book Store esta configurada
    When crio um novo usuario
    Then o usuario e criado com sucesso
    When gero um token de acesso para o usuario
    Then o token e gerado com sucesso
    When consulto os livros disponiveis
    Then o catalogo possui livros
    When tento reservar um ISBN inexistente
    Then a API rejeita a reserva e informa o motivo

  Scenario: Rejeitar reserva parcialmente invalida sem alterar a colecao
    Given que a API da Book Store esta configurada
    When crio um novo usuario
    Then o usuario e criado com sucesso
    When gero um token de acesso para o usuario
    Then o token e gerado com sucesso
    When consulto os livros disponiveis
    Then o catalogo possui livros
    When reservo um livro disponivel
    Then a primeira reserva e confirmada
    When tento reservar outro livro junto com um ISBN inexistente
    Then a API rejeita o lote sem alterar a colecao

  Scenario: Rejeitar senha incorreta de usuario existente
    Given que a API da Book Store esta configurada
    When crio um novo usuario
    Then o usuario e criado com sucesso
    When gero um token de acesso para o usuario
    Then o token e gerado com sucesso
    When solicito um token com a senha incorreta
    Then a API informa que o token nao foi gerado
    When verifico a autorizacao com a senha incorreta
    Then a API recusa a autorizacao com erro de usuario

  Scenario: Rejeitar reserva duplicada e manter uma unica copia
    Given que a API da Book Store esta configurada
    When crio um novo usuario
    Then o usuario e criado com sucesso
    When gero um token de acesso para o usuario
    Then o token e gerado com sucesso
    When consulto os livros disponiveis
    Then o catalogo possui livros
    When reservo um livro disponivel
    Then a primeira reserva e confirmada
    When tento reservar novamente o mesmo livro
    Then a API rejeita a reserva duplicada
    And a colecao continua com uma unica copia do livro

  Scenario: Recusar consulta de usuario sem token
    Given que a API da Book Store esta configurada
    When crio um novo usuario
    Then o usuario e criado com sucesso
    When gero um token de acesso para o usuario
    Then o token e gerado com sucesso
    When consulto os detalhes de usuario sem token
    Then a API recusa a consulta por falta de autorizacao

  Scenario: Rejeitar criacao de usuario com senha fraca
    Given que a API da Book Store esta configurada
    When tento criar um usuario com senha fraca
    Then a API rejeita a senha fraca com erro de validacao
