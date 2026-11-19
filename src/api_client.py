import os
from typing import Any

import requests


class BookStoreApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 20) -> None:
        self.base_url = (base_url or os.getenv("DEMOQA_BASE_URL", "https://demoqa.com")).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def close(self) -> None:
        self.session.close()

    def create_user(self, username: str, password: str) -> requests.Response:
        return self._request(
            "POST",
            "/Account/v1/User",
            json_body={"userName": username, "password": password},
        )

    def generate_token(self, username: str, password: str) -> requests.Response:
        return self._request(
            "POST",
            "/Account/v1/GenerateToken",
            json_body={"userName": username, "password": password},
        )

    def authorize_user(self, username: str, password: str) -> requests.Response:
        return self._request(
            "POST",
            "/Account/v1/Authorized",
            json_body={"userName": username, "password": password},
        )

    def set_bearer_token(self, token: str) -> None:
        self.session.headers["Authorization"] = f"Bearer {token}"

    def list_books(self) -> requests.Response:
        return self._request("GET", "/BookStore/v1/Books")

    def get_book(self, isbn: str) -> requests.Response:
        return self._request(
            "GET",
            "/BookStore/v1/Book",
            params={"ISBN": isbn},
        )

    def add_books(self, user_id: str, isbns: list[str]) -> requests.Response:
        return self._request(
            "POST",
            "/BookStore/v1/Books",
            json_body={
                "userId": user_id,
                "collectionOfIsbns": [{"isbn": isbn} for isbn in isbns],
            },
        )

    def get_user(self, user_id: str) -> requests.Response:
        return self._request("GET", f"/Account/v1/User/{user_id}")

    def delete_user(self, user_id: str) -> requests.Response:
        return self._request("DELETE", f"/Account/v1/User/{user_id}")

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> requests.Response:
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            json=json_body,
            params=params,
            timeout=self.timeout,
        )
        return response
