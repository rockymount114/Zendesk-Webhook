import os
import pytest

# Ensure dummy test environment variables exist before app is loaded
os.environ.setdefault("SUBDOMAIN", "test.zendesk.com")
os.environ.setdefault("ZENDESK_CLIENT_ID", "test-client-id")
os.environ.setdefault("ZENDESK_AUTH_SECRET", "test-auth-secret")


@pytest.fixture(autouse=True)
def configure_test_app(monkeypatch):
    """Ensure app configuration is set for all tests."""
    import app
    monkeypatch.setattr(app, "SUBDOMAIN", "test.zendesk.com")
    monkeypatch.setattr(app, "BASE_DOMAIN", "test.zendesk.com")
    monkeypatch.setattr(app, "ZENDESK_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(app, "ZENDESK_AUTH_SECRET", "test-auth-secret")
    if not app.oauth_token_manager or not app.oauth_token_manager.is_configured():
        from zendesk_auth import ZendeskOAuthTokenManager, ZendeskAuth
        mgr = ZendeskOAuthTokenManager("test.zendesk.com", "test-client-id", "test-auth-secret")
        monkeypatch.setattr(app, "oauth_token_manager", mgr)
        monkeypatch.setattr(app, "auth", ZendeskAuth(token_manager=mgr))
