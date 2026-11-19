import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from features.steps import bookstore_steps as steps


def response(status, payload):
    return SimpleNamespace(status_code=status, json=lambda: payload)


class BookResponseTests(unittest.TestCase):
    def test_reservation_and_collection_reject_extra_malformed_items(self):
        valid_books = [{"isbn": "first"}, {"isbn": "second"}]
        malformed_books = [*valid_books, "unexpected"]

        for reservation_books, user_books in (
            (malformed_books, valid_books),
            (valid_books, malformed_books),
        ):
            with self.subTest(reservation_books=reservation_books, user_books=user_books):
                api = Mock()
                api.get_user.return_value = response(200, {"userId": "user", "books": user_books})
                context = SimpleNamespace(
                    api=api,
                    user_id="user",
                    selected_isbns=["first", "second"],
                    reserve_response=response(201, {"books": reservation_books}),
                )

                with self.assertRaisesRegex(AssertionError, "Item 3"):
                    steps.user_details_show_reserved_books(context)

    def test_reservation_accepts_exact_isbns_in_different_order(self):
        api = Mock()
        api.get_user.return_value = response(
            200, {"userId": "user", "books": [{"isbn": "first"}, {"isbn": "second"}]}
        )
        context = SimpleNamespace(
            api=api,
            user_id="user",
            selected_isbns=["first", "second"],
            reserve_response=response(201, {"books": [{"isbn": "second"}, {"isbn": "first"}]}),
        )

        steps.user_details_show_reserved_books(context)

    def test_book_details_reject_fields_missing_in_both_responses(self):
        book = {"isbn": "first"}
        context = SimpleNamespace(selected_book=book, book_details_response=response(200, book))

        with self.assertRaisesRegex(AssertionError, "title"):
            steps.book_details_match_catalog(context)

    def test_duplicate_reservation_rejects_extra_book(self):
        api = Mock()
        api.get_user.return_value = response(
            200, {"userId": "user", "books": [{"isbn": "first"}, {"isbn": "extra"}]}
        )
        context = SimpleNamespace(api=api, user_id="user", first_reserved_isbn="first")

        with self.assertRaisesRegex(AssertionError, "exclusivamente"):
            steps.collection_keeps_one_copy_of_book(context)

    def test_rejected_reservation_detects_partial_write(self):
        api = Mock()
        api.get_user.return_value = response(
            200, {"userId": "user", "books": [{"isbn": "first"}, {"isbn": "extra"}]}
        )
        context = SimpleNamespace(
            api=api,
            user_id="user",
            original_collection=["first"],
            invalid_reservation_response=response(201, {}),
        )

        with self.assertRaisesRegex(AssertionError, "alterou a coleção"):
            steps.mixed_reservation_is_rejected_without_changes(context)


class ScenarioIsolationTests(unittest.TestCase):
    def test_created_user_with_unusable_response_reports_username(self):
        malformed_json = Mock(status_code=201)
        malformed_json.json.side_effect = ValueError("invalid JSON")

        for create_response in (malformed_json, response(201, {})):
            with self.subTest(response=create_response):
                api = Mock()
                api.create_user.return_value = create_response
                context = SimpleNamespace(api=api, user_id=None)

                with self.assertRaisesRegex(AssertionError, "qa_[0-9a-f]{12}"):
                    steps.create_user(context)

                self.assertIsNone(context.user_id)

    def test_request_without_token_uses_separate_client_and_existing_user(self):
        authenticated_api = Mock(base_url="https://test.invalid", timeout=5)
        context = SimpleNamespace(api=authenticated_api, user_id="existing-user", token="token")

        with patch.object(steps, "BookStoreApiClient") as client:
            steps.request_user_details_without_token(context)

        client.assert_called_once_with(base_url="https://test.invalid", timeout=5)
        client.return_value.get_user.assert_called_once_with("existing-user")
        client.return_value.set_bearer_token.assert_not_called()
        client.return_value.close.assert_called_once_with()
        authenticated_api.get_user.assert_not_called()


if __name__ == "__main__":
    unittest.main()
