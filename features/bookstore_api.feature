Feature: Book Store API
  Como pessoa usuaria da Book Store API
  Quero criar uma conta e reservar livros
  Para consultar os livros associados a minha conta

  Scenario: Criar usuario, reservar dois livros e consultar os detalhes
    Given que a API da Book Store esta configurada
    When crio um novo usuario
    Then o usuario e criado com sucesso
    When gero um token de acesso para o usuario
    Then o token e gerado com sucesso
    And o usuario esta autorizado
    When consulto os livros disponiveis
    Then o catalogo possui livros
    When reservo dois livros disponiveis
    Then os detalhes do usuario mostram os dois livros reservados
