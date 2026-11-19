# DemoQA Book Store API

Automação do fluxo da DemoQA Book Store API com Python e Behave
(BDD/Gherkin). Consulte o [Swagger da DemoQA](https://demoqa.com/swagger/)
para a referência dos endpoints.

## Escopo do desafio

O [cenário principal](features/bookstore_api.feature#L7) cobre os seis
passos do enunciado em uma única execução.

| Passo | Endpoint | Evidência no teste |
| --- | --- | --- |
| Criar usuário | `POST /Account/v1/User` | HTTP 201, nome esperado e ID do usuário |
| Gerar token | `POST /Account/v1/GenerateToken` | HTTP 200, sucesso e token configurado na sessão |
| Confirmar autorização | `POST /Account/v1/Authorized` | HTTP 200 e resposta booleana `true` |
| Listar livros | `GET /BookStore/v1/Books` | HTTP 200 e catálogo com livros identificados por ISBN |
| Reservar dois livros | `POST /BookStore/v1/Books` | HTTP 201 e exatamente os dois ISBNs distintos selecionados |
| Consultar usuário e livros reservados | `GET /Account/v1/User/{userID}` | HTTP 200, ID do usuário criado e exatamente os dois ISBNs reservados |

Para executar o cenário principal isoladamente:

```bash
behave features/bookstore_api.feature --name "^Criar usuario, reservar dois livros e consultar os detalhes$"
```

Os complementos incluem consulta de detalhes de um livro, exclusão de
usuário, cenários negativos, latência e GitHub Actions. O cenário de
atomicidade documenta uma divergência observada na DemoQA e depende de
uma decisão de Produto para virar critério de promoção.

## Requisitos

- Python 3.10 ou superior
- Acesso a internet

## Instalacao e execucao

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
behave --tags="not @performance"
```

No Windows, ative o ambiente com `.venv\Scripts\activate`.

O teste cria um usuario com nome unico e gera uma senha temporaria em tempo de
execucao. Ao final, o hook recupera um token se necessario e remove o usuario;
falhas de limpeza sao reportadas. Se a criação retornar HTTP 201 sem um ID
utilizável, a falha identifica o usuário pelo nome para investigação. A URL
base pode ser configurada pela variavel `DEMOQA_BASE_URL` (padrao: `https://demoqa.com`).
O Behave executa o fluxo positivo em `features/bookstore_api.feature` e os
cenarios negativos em `features/api_negative_responses.feature`. O teste de
desempenho em `features/api_performance.feature` mede cinco chamadas sequenciais
ao catalogo e exige tempo medio de ate 2 segundos; e uma verificacao de latencia,
nao um teste de carga concorrente.

Para executar somente a medição de latência e exibir as amostras, a média e o máximo:

```bash
behave --no-capture -f plain features/api_performance.feature
```

### Verificação rápida com tags

A tag `@smoke` seleciona quatro cenários:

- **Positivos** — um cenário cria uma conta, reserva dois livros e confere a
  coleção. O outro exclui uma conta e confirma que ela foi removida.
- **Negativo** — recusar a consulta de um usuário existente sem token.
- **Performance** — medir a latência de cinco consultas ao catálogo.

```bash
behave --tags="@smoke" --no-capture -f plain
```

Para executar os três cenários funcionais da seleção:

```bash
behave --tags="@smoke and not @performance"
```

### Testes unitários

Para testar a limpeza e a validação das respostas localmente:

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


## Riscos e critérios de aprovação

| Risco | Evidência | Impacto | Decisão |
| --- | --- | --- | --- |
| Reserva salva ISBNs errados, extras ou duplicados | Resposta da reserva e consulta da coleção; nova consulta após recusar duplicidade | Alta. O usuário fica com uma coleção incorreta. | Bloquear a aprovação funcional. |
| Lote rejeitado persiste parte da reserva | Coleção com um livro antes e depois de enviar um ISBN disponível e um ausente | Alta. Uma operação informada como rejeitada altera os dados. | Bloquear a aprovação funcional. |
| Consulta aceita uma sessão anônima ou credenciais inválidas geram token | Cenários de autenticação e consulta sem token de usuário existente | Alta. Dados podem ser expostos. | Bloquear a aprovação funcional. |
| Resposta viola o contrato esperado | Validação de status, códigos de erro, detalhes e campos obrigatórios | Média a alta. Consumidores da API podem falhar ou exibir dados incorretos. | Bloquear a aprovação funcional em caso de regressão. |
| Contas temporárias ficam no ambiente | Hook de limpeza e seus testes unitários | Média. Resíduos dificultam novas execuções e diagnóstico. | Investigar e repetir antes de aprovar a execução. |
| Serviço externo indisponível | Logs de DNS, conexão e HTTP no workflow de integração | Execução inconclusiva quando a causa externa for confirmada. | Investigar e repetir após a recuperação. O check local do PR continua independente. |
| Média do catálogo excede 2 s | Cinco consultas sequenciais com tempos individuais, média e máximo | Impacto na experiência, sujeito à rede e ao ambiente da medição. | Falhar a medição e investigar. Ela roda fora do check de merge. |

O cenário de lote misto compara os ISBNs antes e depois da tentativa de
reserva. A atomicidade é um critério de aceitação adotado no projeto para
avaliar a consistência do lote. Carga concorrente e cobertura de todos os
endpoints ficam fora do escopo.

**Resultado na DemoQA pública em 19/11/2026.** O lote com o ISBN disponível
`9781449331818` e o ISBN ausente `9780000000002` retornou HTTP 201 e
acrescentou o livro disponível à coleção. A execução funcional sinaliza essa
divergência em relação ao critério de atomicidade adotado pelo projeto.

**Pergunta para Produto.** Quando o lote contém ISBNs disponíveis e
inexistentes, a API deve rejeitar o lote inteiro e preservar a coleção, ou
salvar os ISBNs disponíveis? Se o sucesso parcial for permitido, qual status
HTTP e quais campos devem indicar, por ISBN, o que foi salvo e o que foi
recusado? A resposta define a asserção esperada e se o cenário deve bloquear
a promoção.

## GitHub Actions

| Workflow | Gatilho | Evidência |
| --- | --- | --- |
| [Validação de QA](.github/workflows/qa-ci.yml) | PR, push e fila de merge | Logs dos testes unitários e da validação Gherkin, sem chamadas à DemoQA |
| [Integração da Book Store API](.github/workflows/qa-integration.yml) | Manual, segunda a sexta às 12h23 UTC (9h23 em São Paulo) ou chamado por outra esteira | Logs e XML JUnit dos cenários funcionais; latência opcional nas execuções manuais ou chamadas |

Os artefatos ficam na execução do GitHub Actions por 14 dias. Falhas de teste
preservam o código de saída e os relatórios já gerados. Quando solicitada, a
medição de latência roda mesmo após uma falha funcional, desde que as
dependências tenham sido instaladas e a execução esteja ativa.

### Ativar no GitHub

1. Publicar os arquivos de workflow na branch padrão e habilitar GitHub Actions
   nas configurações do repositório.
2. Abrir um PR e, após o primeiro check bem-sucedido, configurar a proteção da
   branch para exigir **Testes locais e Gherkin**.
3. Na aba **Actions**, abrir **Integração da Book Store API** e usar **Run
   workflow**. A variável de repositório `DEMOQA_BASE_URL` é opcional e substitui
   a URL pública no agendamento e na execução manual.

### Usar após um deploy em staging

Em uma esteira no mesmo repositório, passe a URL de staging como entrada do
workflow reutilizável. O ambiente deve estar acessível pelo runner e permitir
a criação e exclusão das contas temporárias. A DemoQA pública pode ser usada
para a apresentação do desafio. Para aprovar uma implantação, execute a suíte
contra o ambiente que recebeu a versão candidata.

```yaml
jobs:
  qa-staging:
    needs: deploy-staging
    uses: ./.github/workflows/qa-integration.yml
    with:
      base_url: ${{ needs.deploy-staging.outputs.url }}
```

O exemplo pressupõe um job `deploy-staging` que valida a URL de staging e a
publica em `outputs.url`. Faça esse job falhar se a URL estiver vazia para
evitar que a execução use a URL padrão.
Faça a promoção depender de `qa-staging` e configure a aprovação do ambiente
de produção na esteira de deploy. Se staging exigir autenticação adicional
ou estiver em rede privada, configure os segredos no ambiente e use um runner
com acesso à rede antes de ativar essa integração.
