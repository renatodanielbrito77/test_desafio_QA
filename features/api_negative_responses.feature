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
    When tento reservar um ISBN inexistente
    Then a API rejeita a reserva e informa o motivo
