import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from features.environment import after_scenario


class ScenarioCleanupTests(unittest.TestCase):
    def test_recovers_token_and_deletes_user_when_scenario_has_no_token(self) -> None:
        api = Mock()
        api.generate_token.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {"status": "Success", "token": "temporary-token"},
        )
        api.delete_user.return_value = SimpleNamespace(status_code=204, text="")
        context = SimpleNamespace(
            api=api,
            user_id="created-user-id",
            username="temporary-user",
            password="temporary-password",
            token=None,
        )

        after_scenario(context, scenario=None)

        api.generate_token.assert_called_once_with("temporary-user", "temporary-password")
        api.set_bearer_token.assert_called_once_with("temporary-token")
        api.delete_user.assert_called_once_with("created-user-id")
        api.close.assert_called_once_with()

    def test_closes_api_and_reports_failed_user_deletion(self) -> None:
        api = Mock()
        api.delete_user.return_value = SimpleNamespace(
            status_code=500,
            text="server error",
        )
        context = SimpleNamespace(
            api=api,
            user_id="created-user-id",
            username="temporary-user",
            password="temporary-password",
            token="temporary-token",
        )

        with self.assertRaisesRegex(RuntimeError, "HTTP 500"):
            after_scenario(context, scenario=None)

        api.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
