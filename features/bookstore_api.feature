Feature: Book Store API
  Como pessoa usuaria da Book Store API
  Quero criar uma conta e reservar livros
  Para consultar os livros associados a minha conta

  @smoke
  Scenario: Criar usuario, reservar dois livros e consultar os detalhes
    Given que a API da Book Store esta configurada
    When crio um novo usuario
    Then o usuario e criado com sucesso
    When gero um token de acesso para o usuario
    Then o token e gerado com sucesso
    And o usuario esta autorizado
    When consulto os livros disponiveis
    Then o catalogo possui livros
    When consulto os detalhes do primeiro livro do catalogo
    Then os detalhes do livro correspondem ao catalogo
    When reservo dois livros disponiveis
    Then os detalhes do usuario mostram os dois livros reservados

  @smoke
  Scenario: Excluir usuario e confirmar que nao pode mais ser consultado
    Given que a API da Book Store esta configurada
    When crio um novo usuario
    Then o usuario e criado com sucesso
    When gero um token de acesso para o usuario
    Then o token e gerado com sucesso
    When excluo o usuario criado
    Then a API confirma a exclusao do usuario
    When consulto os detalhes do usuario excluido
    Then a API confirma que o usuario foi removido
