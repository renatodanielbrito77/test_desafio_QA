# DemoQA Book Store API

Automacao do fluxo da API DemoQA com Python e Behave (BDD/Gherkin):

1. Criar um usuario.
2. Gerar um token e confirmar a autorizacao.
3. Consultar o catalogo.
4. Consultar os detalhes de um livro do catalogo.
5. Reservar dois livros disponiveis e validar exatamente os dois ISBNs.
6. Consultar os dados do usuario e validar os livros.

Um segundo cenario positivo exclui um usuario e confirma que ele nao pode mais
ser consultado.

## Requisitos

- Python 3.10 ou superior
- Acesso a internet

## Instalacao e execucao

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
behave
```

No Windows, ative o ambiente com `.venv\Scripts\activate`.

O teste cria um usuario com nome unico e gera uma senha temporaria em tempo de
execucao. Ao final, o hook recupera um token se necessario e remove o usuario;
falhas de limpeza sao reportadas. A URL base pode ser configurada pela
variavel `DEMOQA_BASE_URL` (padrao: `https://demoqa.com`).
O Behave executa o fluxo positivo em `features/bookstore_api.feature` e os
cenarios negativos em `features/api_negative_responses.feature`. O teste de
desempenho em `features/api_performance.feature` mede cinco chamadas sequenciais
ao catalogo e exige tempo medio de ate 2 segundos; e uma verificacao de latencia,
nao um teste de carga concorrente.

Para executar somente o teste de desempenho:

```bash
behave features/api_performance.feature
```

Os testes unitarios do hook de limpeza podem ser executados com:

```bash
python -m unittest discover -s tests -v
```

## Onde adicionar cenarios

- Escreva os cenarios em Gherkin em `features/*.feature`.
- Implemente ou reutilize os steps em `features/steps/`.
- Adicione chamadas HTTP reutilizaveis em `src/api_client.py`.

Os steps compartilham estado pelo objeto `context` do Behave. O cliente HTTP
fica isolado em uma classe para manter os cenarios legiveis e facilitar a
inclusao de novos fluxos.
