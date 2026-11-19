import secrets
import string
import uuid

from behave import given, then, when


def _temporary_password() -> str:
    groups = [
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        "!@#$%^&*",
    ]
    characters = [secrets.choice(group) for group in groups]
    alphabet = "".join(groups)
    characters.extend(secrets.choice(alphabet) for _ in range(12))
    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)


@given("que a API da Book Store esta configurada")
def api_is_configured(context) -> None:
    assert context.api.base_url, "A URL base da API nao foi configurada."


@when("crio um novo usuario")
def create_user(context) -> None:
    context.username = f"qa_{uuid.uuid4().hex[:12]}"
    context.password = _temporary_password()
    context.create_user_response = context.api.create_user(context.username, context.password)


@then("o usuario e criado com sucesso")
def user_is_created(context) -> None:
    response = context.create_user_response
    assert response.status_code == 201, f"Esperado HTTP 201, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("username") == context.username, "A resposta nao corresponde ao usuario criado."
    assert payload.get("userId"), "A resposta da criacao nao contem userId."
    context.user_id = payload["userId"]


@when("gero um token de acesso para o usuario")
def generate_access_token(context) -> None:
    context.token_response = context.api.generate_token(context.username, context.password)


@then("o token e gerado com sucesso")
def token_is_generated(context) -> None:
    response = context.token_response
    assert response.status_code == 200, f"Esperado HTTP 200, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("status") == "Success", f"Falha ao gerar token: {payload!r}"
    assert payload.get("token"), "A resposta nao contem token."
    context.token = payload["token"]
    context.api.set_bearer_token(context.token)


@then("o usuario esta autorizado")
def user_is_authorized(context) -> None:
    response = context.api.authorize_user(context.username, context.password)
    assert response.status_code == 200, f"Esperado HTTP 200, recebido {response.status_code}."
    assert response.json() is True, "A API nao confirmou a autorizacao do usuario."


@when("consulto os livros disponiveis")
def list_available_books(context) -> None:
    context.books_response = context.api.list_books()


@then("o catalogo possui livros")
def catalog_contains_books(context) -> None:
    response = context.books_response
    assert response.status_code == 200, f"Esperado HTTP 200, recebido {response.status_code}."
    books = response.json().get("books", [])
    assert books, "O catalogo retornou vazio."
    context.available_books = books


@when("reservo dois livros disponiveis")
def reserve_two_books(context) -> None:
    books = context.available_books
    assert len(books) >= 2, "Sao necessarios pelo menos dois livros no catalogo."
    context.selected_isbns = [book["isbn"] for book in books[:2]]
    context.reserve_response = context.api.add_books(context.user_id, context.selected_isbns)


@then("os detalhes do usuario mostram os dois livros reservados")
def user_details_show_reserved_books(context) -> None:
    response = context.reserve_response
    assert response.status_code == 201, f"Esperado HTTP 201, recebido {response.status_code}."

    details_response = context.api.get_user(context.user_id)
    assert details_response.status_code == 200, (
        f"Esperado HTTP 200, recebido {details_response.status_code}."
    )
    details = details_response.json()
    assert details.get("userId") == context.user_id, "Os detalhes retornaram outro usuario."
    reserved_isbns = {book["isbn"] for book in details.get("books", [])}
    assert set(context.selected_isbns).issubset(reserved_isbns), (
        "Os detalhes do usuario nao contem os dois livros reservados."
    )
