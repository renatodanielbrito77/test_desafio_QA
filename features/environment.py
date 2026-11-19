from src.api_client import BookStoreApiClient


def before_scenario(context, scenario) -> None:
    context.api = BookStoreApiClient()
    context.user_id = None
    context.token = None


def after_scenario(context, scenario) -> None:
    try:
        if context.user_id:
            if not context.token:
                token_response = context.api.generate_token(context.username, context.password)
                if token_response.status_code != 200:
                    raise RuntimeError(
                        "Falha ao gerar token para limpeza: "
                        f"HTTP {token_response.status_code}."
                    )
                token_payload = token_response.json()
                token = token_payload.get("token")
                if token_payload.get("status") != "Success" or not token:
                    raise RuntimeError(
                        "A API nao retornou um token valido para limpar o usuario."
                    )
                context.api.set_bearer_token(token)

            delete_response = context.api.delete_user(context.user_id)
            if delete_response.status_code not in (200, 204):
                raise RuntimeError(
                    "Falha ao remover usuario criado: "
                    f"HTTP {delete_response.status_code} - {delete_response.text}."
                )
    finally:
        context.api.close()
