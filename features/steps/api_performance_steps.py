from time import perf_counter

from behave import then, when


SAMPLE_COUNT = 5
MAX_AVERAGE_RESPONSE_SECONDS = 2.0


@when("meco cinco chamadas sequenciais ao catalogo")
def measure_catalog_responses(context) -> None:
    context.catalog_response_samples = []

    for _ in range(SAMPLE_COUNT):
        started_at = perf_counter()
        response = context.api.list_books()
        elapsed_seconds = perf_counter() - started_at
        context.catalog_response_samples.append((response, elapsed_seconds))


@then("as cinco respostas do catalogo sao validas")
def catalog_responses_are_valid(context) -> None:
    samples = context.catalog_response_samples
    assert len(samples) == SAMPLE_COUNT, (
        f"Esperadas {SAMPLE_COUNT} amostras, recebidas {len(samples)}."
    )

    for index, (response, _) in enumerate(samples, start=1):
        assert response.status_code == 200, (
            f"Amostra {index}: esperado HTTP 200, recebido {response.status_code}."
        )
        books = response.json().get("books")
        assert isinstance(books, list) and books, (
            f"Amostra {index}: a resposta nao contem livros no catalogo."
        )


@then("a media de resposta nao excede dois segundos")
def average_catalog_response_is_within_limit(context) -> None:
    elapsed_times = [elapsed for _, elapsed in context.catalog_response_samples]
    average_seconds = sum(elapsed_times) / len(elapsed_times)
    sample_details = ", ".join(f"{elapsed:.3f}s" for elapsed in elapsed_times)

    assert average_seconds <= MAX_AVERAGE_RESPONSE_SECONDS, (
        f"Media de {average_seconds:.3f}s excede o limite de "
        f"{MAX_AVERAGE_RESPONSE_SECONDS:.3f}s. Amostras: {sample_details}."
    )
