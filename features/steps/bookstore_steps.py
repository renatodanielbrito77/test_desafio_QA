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
    if context.create_user_response.status_code == 201:
        payload = context.create_user_response.json()
        context.user_id = payload.get("userID") or payload.get("userId")


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
    for field in ("isbn", "title", "author"):
        assert details.get(field) == context.selected_book.get(field), (
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
    reservation = response.json()
    assert isinstance(reservation, dict), "A resposta da reserva deve ser um objeto."
    returned_books = reservation.get("books")
    assert isinstance(returned_books, list), "A resposta da reserva nao contem a lista books."
    returned_isbns = [
        book.get("isbn") for book in returned_books if isinstance(book, dict)
    ]
    assert len(returned_isbns) == len(context.selected_isbns) and set(returned_isbns) == set(
        context.selected_isbns
    ), (
        "A resposta da reserva nao corresponde aos ISBNs enviados."
    )

    details_response = context.api.get_user(context.user_id)
    assert details_response.status_code == 200, (
        f"Esperado HTTP 200, recebido {details_response.status_code}."
    )
    details = details_response.json()
    assert details.get("userId") == context.user_id, "Os detalhes retornaram outro usuario."
    user_books = details.get("books")
    assert isinstance(user_books, list), "Os detalhes do usuario nao contem uma lista de livros."
    reserved_isbns = [book.get("isbn") for book in user_books if isinstance(book, dict)]
    assert len(reserved_isbns) == 2 and set(reserved_isbns) == set(context.selected_isbns), (
        "A colecao do usuario deve conter exatamente os dois livros reservados."
    )


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
    assert payload.get("message"), "A resposta de erro nao contem uma mensagem."


@when("verifico a autorizacao com a senha incorreta")
def request_authorization_with_wrong_password(context) -> None:
    context.invalid_authorization_response = context.api.authorize_user(
        context.username,
        context.wrong_password,
    )


@when("tento reservar um ISBN inexistente")
def reserve_missing_isbn(context) -> None:
    context.invalid_isbn = f"missing-{uuid.uuid4().hex}"
    context.invalid_reservation_response = context.api.add_books(
        context.user_id,
        [context.invalid_isbn],
    )


@then("a API rejeita a reserva e informa o motivo")
def invalid_reservation_is_rejected(context) -> None:
    response = context.invalid_reservation_response
    assert response.status_code == 400, f"Esperado HTTP 400, recebido {response.status_code}."
    payload = response.json()
    assert payload.get("message"), "A resposta de erro nao contem uma mensagem."


@when("reservo um livro disponivel")
def reserve_one_available_book(context) -> None:
    assert context.available_books, "Nao ha livros disponiveis para reservar."
    context.duplicate_isbn = context.available_books[0]["isbn"]
    context.first_reservation_response = context.api.add_books(
        context.user_id,
        [context.duplicate_isbn],
    )


@then("a primeira reserva e confirmada")
def first_reservation_is_confirmed(context) -> None:
    response = context.first_reservation_response
    assert response.status_code == 201, f"Esperado HTTP 201, recebido {response.status_code}."
    payload = response.json()
    books = payload.get("books", []) if isinstance(payload, dict) else []
    assert [book.get("isbn") for book in books if isinstance(book, dict)] == [
        context.duplicate_isbn
    ], "A primeira reserva nao retornou o ISBN solicitado."


@when("tento reservar novamente o mesmo livro")
def reserve_duplicate_book(context) -> None:
    context.duplicate_reservation_response = context.api.add_books(
        context.user_id,
        [context.duplicate_isbn],
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
    response = context.api.get_user(context.user_id)
    assert response.status_code == 200, f"Esperado HTTP 200, recebido {response.status_code}."
    books = response.json().get("books", [])
    isbn_count = sum(book.get("isbn") == context.duplicate_isbn for book in books)
    assert isbn_count == 1, f"Esperado uma copia do ISBN, encontradas {isbn_count}."


@when("consulto os detalhes de usuario sem token")
def request_user_details_without_token(context) -> None:
    context.unauthenticated_user_id = str(uuid.uuid4())
    context.unauthenticated_user_response = context.api.get_user(
        context.unauthenticated_user_id
    )


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
    if context.weak_password_create_response.status_code == 201:
        payload = context.weak_password_create_response.json()
        context.user_id = payload.get("userID") or payload.get("userId")


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
