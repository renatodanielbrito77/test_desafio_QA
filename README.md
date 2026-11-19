# DemoQA Book Store API

Automacao do fluxo da API DemoQA com Python e Behave (BDD/Gherkin):

1. Criar um usuario.
2. Gerar um token e confirmar a autorizacao.
3. Consultar o catalogo.
4. Reservar dois livros disponiveis.
5. Consultar os dados do usuario e validar os livros.

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
execucao. Ao final, tenta remover o usuario criado. A URL base pode ser
configurada pela variavel `DEMOQA_BASE_URL` (padrao: `https://demoqa.com`).

## Onde adicionar cenarios

- Escreva os cenarios em Gherkin em `features/*.feature`.
- Implemente ou reutilize os steps em `features/steps/`.
- Adicione chamadas HTTP reutilizaveis em `src/api_client.py`.

Os steps compartilham estado pelo objeto `context` do Behave. O cliente HTTP
fica isolado em uma classe para manter os cenarios legiveis e facilitar a
inclusao de novos fluxos.
