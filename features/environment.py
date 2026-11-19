from src.api_client import BookStoreApiClient


def before_scenario(context, scenario) -> None:
    context.api = BookStoreApiClient()


def after_scenario(context, scenario) -> None:
    try:
        user_id = getattr(context, "user_id", None)
        if user_id and getattr(context, "token", None):
            context.api.delete_user(user_id)
    finally:
        context.api.close()
