import threading
import time
from unittest.mock import MagicMock, patch
import pytest
import requests

from zendesk_auth import (
    clean_secret,
    normalize_base_domain,
    ZendeskOAuthTokenManager,
    ZendeskAuth,
)


class TestHelpers:
    def test_clean_secret_none(self):
        assert clean_secret(None) is None

    def test_clean_secret_empty(self):
        assert clean_secret("") is None
        assert clean_secret("   ") is None

    def test_clean_secret_quotes(self):
        assert clean_secret('"my-secret"') == "my-secret"
        assert clean_secret("'my-secret'") == "my-secret"
        assert clean_secret('  "my-secret"  ') == "my-secret"
        assert clean_secret('  \'my-secret\'  ') == "my-secret"

    def test_clean_secret_normal(self):
        assert clean_secret("plain-text") == "plain-text"

    def test_normalize_base_domain_none_or_empty(self):
        assert normalize_base_domain(None) is None
        assert normalize_base_domain("") is None
        assert normalize_base_domain("   ") is None

    def test_normalize_base_domain_urls(self):
        assert normalize_base_domain("https://example.zendesk.com") == "example.zendesk.com"
        assert normalize_base_domain("http://example.zendesk.com/") == "example.zendesk.com"
        assert normalize_base_domain("https://example.zendesk.com///") == "example.zendesk.com"
        assert normalize_base_domain("example.zendesk.com") == "example.zendesk.com"


class TestZendeskOAuthTokenManager:
    def test_is_configured(self):
        manager = ZendeskOAuthTokenManager("example.zendesk.com", "client_1", "secret_1")
        assert manager.is_configured() is True

        manager_unconfigured = ZendeskOAuthTokenManager("", None, "secret_1")
        assert manager_unconfigured.is_configured() is False

    @patch("requests.post")
    def test_get_token_success_and_cache(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token_12345",
            "token_type": "bearer",
            "expires_in": 1800,
            "scope": "read",
        }
        mock_post.return_value = mock_response

        manager = ZendeskOAuthTokenManager("example.zendesk.com", "client_1", "secret_1")
        token = manager.get_token()

        assert token == "token_12345"
        assert mock_post.call_count == 1
        mock_post.assert_called_with(
            "https://example.zendesk.com/oauth/tokens",
            data={
                "grant_type": "client_credentials",
                "client_id": "client_1",
                "client_secret": "secret_1",
                "scope": "read",
            },
            timeout=15,
        )

        # Call again without force_refresh; should return cached token without calling API
        token_cached = manager.get_token()
        assert token_cached == "token_12345"
        assert mock_post.call_count == 1

        # Force refresh; should make a new POST request
        token_refreshed = manager.get_token(force_refresh=True)
        assert token_refreshed == "token_12345"
        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_get_token_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid client credentials"
        mock_post.return_value = mock_response

        manager = ZendeskOAuthTokenManager("example.zendesk.com", "bad_client", "bad_secret")
        token = manager.get_token()

        assert token is None

    @patch("requests.post")
    def test_get_token_exception(self, mock_post):
        mock_post.side_effect = requests.RequestException("Network error")

        manager = ZendeskOAuthTokenManager("example.zendesk.com", "client_1", "secret_1")
        token = manager.get_token()

        assert token is None

    @patch("requests.post")
    def test_token_thread_safety(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "threaded_token",
            "expires_in": 1800,
        }
        mock_post.return_value = mock_response

        manager = ZendeskOAuthTokenManager("example.zendesk.com", "client_1", "secret_1")
        results = []

        def worker():
            t = manager.get_token()
            results.append(t)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(r == "threaded_token" for r in results)
        assert mock_post.call_count == 1


class TestZendeskAuth:
    def test_auth_with_oauth(self):
        manager = MagicMock(spec=ZendeskOAuthTokenManager)
        manager.is_configured.return_value = True
        manager.client_id = "cid"
        manager.client_secret = "secret"
        manager.get_token.return_value = "fake_bearer_token"

        auth = ZendeskAuth(token_manager=manager)
        req = requests.Request("GET", "https://example.zendesk.com/api/v2/tickets.json").prepare()
        result_req = auth(req)

        assert result_req.headers.get("Authorization") == "Bearer fake_bearer_token"

    def test_auth_fallback_to_api_key(self):
        auth = ZendeskAuth(
            token_manager=None,
            user="user@example.com",
            api_key="api_token_val",
        )
        req = requests.Request("GET", "https://example.zendesk.com/api/v2/tickets.json").prepare()
        result_req = auth(req)

        # Basic Auth header begins with "Basic "
        auth_header = result_req.headers.get("Authorization", "")
        assert auth_header.startswith("Basic ")

    def test_auth_unconfigured(self):
        auth = ZendeskAuth()
        req = requests.Request("GET", "https://example.zendesk.com/api/v2/tickets.json").prepare()
        result_req = auth(req)

        assert "Authorization" not in result_req.headers

    def test_auth_handle_401_retry(self):
        manager = MagicMock(spec=ZendeskOAuthTokenManager)
        manager.is_configured.return_value = True
        manager.client_id = "cid"
        manager.client_secret = "secret"
        manager.get_token.side_effect = ["old_token", "new_token"]

        auth = ZendeskAuth(token_manager=manager)

        # Mock initial 401 response
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 401
        mock_req = requests.Request("GET", "https://example.zendesk.com/api/v2/tickets.json").prepare()
        mock_resp.request = mock_req
        mock_resp.history = []

        mock_conn = MagicMock()
        mock_resp.connection = mock_conn
        retry_resp = MagicMock(spec=requests.Response)
        retry_resp.status_code = 200
        retry_resp.history = []
        mock_conn.send.return_value = retry_resp

        handled = auth.handle_401(mock_resp)

        assert handled.status_code == 200
        manager.get_token.assert_called_with(force_refresh=True)
        assert mock_conn.send.call_count == 1
