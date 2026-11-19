import secrets
import string
import uuid

from behave import given, then, when

from src.api_client import BookStoreApiClient


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
    _remember_created_user(context, context.create_user_response)


def _remember_created_user(context, response) -> None:
    if response.status_code != 201:
        return

    error_message = f"HTTP 201 sem identificador utilizável para limpar o usuário {context.username}."
    try:
        payload = response.json()
    except ValueError as exc:
        raise AssertionError(error_message) from exc
    assert isinstance(payload, dict), error_message
    user_id = payload.get("userID") or payload.get("userId")
    assert isinstance(user_id, str) and user_id.strip(), error_message
    context.user_id = user_id


@then("o usuario e criado com sucesso")
def user_is_created(context) -> None:
    response = context.create_user_response
    assert response.status_code == 201, f"Esperado HTTP 201, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("username") == context.username, "A resposta nao corresponde ao usuario criado."
    assert context.user_id, "A resposta da criacao nao contem userID/userId."


@when("gero um token de acesso para o usuario")
def generate_access_token(context) -> None:
    context.token_response = context.api.generate_token(context.username, context.password)


@then("o token e gerado com sucesso")
def token_is_generated(context) -> None:
    response = context.token_response
    assert response.status_code == 200, f"Esperado HTTP 200, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("status") == "Success", "A API não confirmou a geração do token."
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
    books = _response_books(response.json())
    assert books, "O catalogo retornou vazio."
    context.available_books = books


@when("consulto os detalhes do primeiro livro do catalogo")
def get_first_book_details(context) -> None:
    assert context.available_books, "Nao ha livros no catalogo para consultar."
    context.selected_book = context.available_books[0]
    context.book_details_response = context.api.get_book(context.selected_book["isbn"])


@then("os detalhes do livro correspondem ao catalogo")
def book_details_match_catalog(context) -> None:
    response = context.book_details_response
    assert response.status_code == 200, f"Esperado HTTP 200, recebido {response.status_code}."
    details = response.json()
    assert isinstance(details, dict), "Os detalhes do livro devem ser um objeto."
    for field in ("isbn", "title", "author"):
        expected = context.selected_book.get(field)
        actual = details.get(field)
        assert isinstance(expected, str) and expected.strip(), f"Campo {field} inválido no catálogo."
        assert isinstance(actual, str) and actual.strip(), f"Campo {field} inválido nos detalhes."
        assert actual == expected, (
            f"O campo {field} difere do catalogo."
        )


@when("reservo dois livros disponiveis")
def reserve_two_books(context) -> None:
    books = context.available_books
    assert len(books) >= 2, "Sao necessarios pelo menos dois livros no catalogo."
    context.selected_isbns = [book["isbn"] for book in books[:2]]
    assert len(set(context.selected_isbns)) == 2, "O catalogo nao retornou dois ISBNs distintos."
    context.reserve_response = context.api.add_books(context.user_id, context.selected_isbns)


@then("os detalhes do usuario mostram os dois livros reservados")
def user_details_show_reserved_books(context) -> None:
    response = context.reserve_response
    assert response.status_code == 201, f"Esperado HTTP 201, recebido {response.status_code}."
    returned_isbns = [book["isbn"] for book in _response_books(response.json())]
    assert sorted(returned_isbns) == sorted(context.selected_isbns), (
        "A resposta da reserva nao corresponde aos ISBNs enviados."
    )

    reserved_isbns = _user_collection(context)
    assert sorted(reserved_isbns) == sorted(context.selected_isbns), (
        "A colecao do usuario deve conter exatamente os dois livros reservados."
    )


def _response_books(payload: object) -> list[dict]:
    assert isinstance(payload, dict), "A resposta deve ser um objeto JSON."
    books = payload.get("books")
    assert isinstance(books, list), "A resposta deve conter uma lista books."
    for index, book in enumerate(books, start=1):
        assert isinstance(book, dict), f"Item {index} de books deve ser um objeto."
        isbn = book.get("isbn")
        assert isinstance(isbn, str) and isbn.strip(), f"Item {index} de books tem ISBN inválido."
    return books


@given("credenciais de um usuario inexistente")
def missing_user_credentials(context) -> None:
    context.username = f"qa_missing_{uuid.uuid4().hex[:12]}"
    context.password = _temporary_password()


@when("solicito um token com essas credenciais")
def request_token_with_invalid_credentials(context) -> None:
    context.invalid_token_response = context.api.generate_token(
        context.username,
        context.password,
    )


@then("a API informa que o token nao foi gerado")
def token_generation_is_rejected(context) -> None:
    response = context.invalid_token_response
    assert response.status_code == 200, f"Esperado HTTP 200, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("status") == "Failed", "A API nao rejeitou as credenciais."
    assert payload.get("token") is None, "A API retornou token para credenciais invalidas."
    assert payload.get("result"), "A resposta nao explica a falha de autenticacao."


@when("solicito um token com a senha incorreta")
def request_token_with_wrong_password(context) -> None:
    context.wrong_password = f"{context.password}wrong"
    context.invalid_token_response = context.api.generate_token(
        context.username,
        context.wrong_password,
    )


@when("verifico a autorizacao com essas credenciais")
def request_authorization_with_invalid_credentials(context) -> None:
    context.invalid_authorization_response = context.api.authorize_user(
        context.username,
        context.password,
    )


@then("a API recusa a autorizacao com erro de usuario")
def invalid_user_authorization_is_rejected(context) -> None:
    response = context.invalid_authorization_response
    assert response.status_code == 404, f"Esperado HTTP 404, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("code") == "1207", (
        f"Esperado código 1207, recebido {payload.get('code')!r}."
    )
    message = payload.get("message")
    assert isinstance(message, str) and message.strip(), "A resposta de erro não contém mensagem."


@when("verifico a autorizacao com a senha incorreta")
def request_authorization_with_wrong_password(context) -> None:
    context.invalid_authorization_response = context.api.authorize_user(
        context.username,
        context.wrong_password,
    )


def _missing_isbn(catalog: list[dict]) -> str:
    # ISBN-13 com dígito verificador válido.
    isbn = "9780000000002"
    assert all(book["isbn"] != isbn for book in catalog), (
        "O ISBN de teste passou a fazer parte do catálogo."
    )
    return isbn


@when("tento reservar um ISBN inexistente")
def reserve_missing_isbn(context) -> None:
    isbn = _missing_isbn(context.available_books)
    context.invalid_reservation_response = context.api.add_books(context.user_id, [isbn])


@when("tento reservar outro livro junto com um ISBN inexistente")
def reserve_with_one_missing_isbn(context) -> None:
    context.original_collection = _user_collection(context)
    assert context.original_collection == [context.first_reserved_isbn], (
        "A coleção inicial deve conter o livro reservado no cenário."
    )
    remaining_isbns = [
        book["isbn"] for book in context.available_books
        if book["isbn"] not in context.original_collection
    ]
    assert remaining_isbns, "O catálogo deve conter outro livro disponível para reserva."
    missing_isbn = _missing_isbn(context.available_books)
    context.invalid_reservation_response = context.api.add_books(
        context.user_id, [remaining_isbns[0], missing_isbn]
    )


@then("a API rejeita o lote sem alterar a colecao")
def mixed_reservation_is_rejected_without_changes(context) -> None:
    current_collection = _user_collection(context)
    assert sorted(current_collection) == sorted(context.original_collection), (
        f"O lote retornou HTTP {context.invalid_reservation_response.status_code} e alterou "
        f"a coleção de {context.original_collection!r} para {current_collection!r}."
    )
    invalid_reservation_is_rejected(context)


@then("a API rejeita a reserva e informa o motivo")
def invalid_reservation_is_rejected(context) -> None:
    response = context.invalid_reservation_response
    assert response.status_code == 400, f"Esperado HTTP 400, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("code") == "1205", (
        f"Esperado código 1205, recebido {payload.get('code')!r}."
    )
    message = payload.get("message")
    assert isinstance(message, str) and message.strip(), "A resposta de erro não contém mensagem."


@when("reservo um livro disponivel")
def reserve_one_available_book(context) -> None:
    assert context.available_books, "Nao ha livros disponiveis para reservar."
    context.first_reserved_isbn = context.available_books[0]["isbn"]
    context.first_reservation_response = context.api.add_books(
        context.user_id,
        [context.first_reserved_isbn],
    )


@then("a primeira reserva e confirmada")
def first_reservation_is_confirmed(context) -> None:
    response = context.first_reservation_response
    assert response.status_code == 201, f"Esperado HTTP 201, recebido {response.status_code}."
    books = _response_books(response.json())
    assert [book["isbn"] for book in books] == [
        context.first_reserved_isbn
    ], "A primeira reserva nao retornou exclusivamente o ISBN solicitado."


@when("tento reservar novamente o mesmo livro")
def reserve_duplicate_book(context) -> None:
    context.duplicate_reservation_response = context.api.add_books(
        context.user_id,
        [context.first_reserved_isbn],
    )


@then("a API rejeita a reserva duplicada")
def duplicate_reservation_is_rejected(context) -> None:
    response = context.duplicate_reservation_response
    assert response.status_code == 400, f"Esperado HTTP 400, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("code") == "1210", "A API retornou um codigo inesperado para duplicidade."
    assert "already present" in payload.get("message", "").lower(), (
        "A resposta nao explica que o ISBN ja esta na colecao."
    )


@then("a colecao continua com uma unica copia do livro")
def collection_keeps_one_copy_of_book(context) -> None:
    assert _user_collection(context) == [context.first_reserved_isbn], (
        "A coleção deve manter exclusivamente o ISBN da primeira reserva."
    )


def _user_collection(context) -> list[str]:
    response = context.api.get_user(context.user_id)
    assert response.status_code == 200, f"Esperado HTTP 200, recebido {response.status_code}."
    payload = response.json()
    books = _response_books(payload)
    assert payload.get("userId") == context.user_id, "Os detalhes retornaram outro usuario."
    return [book["isbn"] for book in books]


@when("consulto os detalhes de usuario sem token")
def request_user_details_without_token(context) -> None:
    anonymous_api = BookStoreApiClient(base_url=context.api.base_url, timeout=context.api.timeout)
    try:
        context.unauthenticated_user_response = anonymous_api.get_user(context.user_id)
    finally:
        anonymous_api.close()


@then("a API recusa a consulta por falta de autorizacao")
def unauthenticated_user_details_are_rejected(context) -> None:
    response = context.unauthenticated_user_response
    assert response.status_code == 401, f"Esperado HTTP 401, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("code") == "1200", "A API retornou um codigo inesperado."
    assert payload.get("message"), "A resposta de erro nao contem uma mensagem."


@when("tento criar um usuario com senha fraca")
def create_user_with_weak_password(context) -> None:
    context.username = f"qa_weak_{uuid.uuid4().hex[:12]}"
    context.password = "weak"
    context.weak_password_create_response = context.api.create_user(
        context.username,
        context.password,
    )
    _remember_created_user(context, context.weak_password_create_response)


@then("a API rejeita a senha fraca com erro de validacao")
def weak_password_is_rejected(context) -> None:
    response = context.weak_password_create_response
    assert response.status_code == 400, f"Esperado HTTP 400, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("code") == "1300", "A API retornou um codigo inesperado."
    message = payload.get("message", "")
    assert "eight characters or longer" in message, (
        "A mensagem nao explica a politica de senha."
    )


@when("excluo o usuario criado")
def delete_created_user(context) -> None:
    context.deleted_user_id = context.user_id
    context.delete_user_response = context.api.delete_user(context.deleted_user_id)


@then("a API confirma a exclusao do usuario")
def user_deletion_is_confirmed(context) -> None:
    response = context.delete_user_response
    assert response.status_code in (200, 204), (
        f"Esperado HTTP 200 ou 204, recebido {response.status_code}."
    )
    context.user_id = None


@when("consulto os detalhes do usuario excluido")
def get_deleted_user_details(context) -> None:
    context.deleted_user_response = context.api.get_user(context.deleted_user_id)


@then("a API confirma que o usuario foi removido")
def deleted_user_is_not_accessible(context) -> None:
    response = context.deleted_user_response
    assert response.status_code == 401, f"Esperado HTTP 401, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("code") == "1207", "A API retornou um codigo inesperado."
    assert payload.get("message"), "A resposta nao confirma que o usuario nao existe."
