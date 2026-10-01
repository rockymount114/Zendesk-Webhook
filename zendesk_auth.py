import logging
import threading
import time
from typing import Optional
import requests
from requests.auth import AuthBase, HTTPBasicAuth

logger = logging.getLogger(__name__)


def clean_secret(val: Optional[str]) -> Optional[str]:
    """Strip whitespace and surrounding single or double quotes."""
    if val is None:
        return None
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].strip()
    return val if val else None


def normalize_base_domain(subdomain_env: Optional[str]) -> Optional[str]:
    """Normalize subdomain or full Zendesk domain to plain host name."""
    if not subdomain_env:
        return None
    s = subdomain_env.strip()
    if not s:
        return None
    if s.startswith("http://"):
        s = s[7:]
    elif s.startswith("https://"):
        s = s[8:]
    res = s.strip("/").strip()
    return res if res else None


class ZendeskOAuthTokenManager:
    """Manages Zendesk OAuth2 client_credentials access tokens with thread-safe caching."""

    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
        scope: str = "read",
        timeout: int = 15,
    ):
        self.domain = normalize_base_domain(domain)
        self.client_id = clean_secret(client_id)
        self.client_secret = clean_secret(client_secret)
        self.scope = clean_secret(scope) or "read"
        self.timeout = timeout
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def is_configured(self) -> bool:
        return bool(self.domain and self.client_id and self.client_secret)

    def invalidate(self) -> None:
        """Clear cached access token."""
        with self._lock:
            self._token = None
            self._expires_at = 0.0

    def get_token(self, force_refresh: bool = False) -> Optional[str]:
        """Retrieve a valid OAuth access token, refreshing if necessary."""
        now = time.time()
        if not force_refresh and self._token and now < self._expires_at:
            return self._token

        with self._lock:
            # Double-checked locking
            now = time.time()
            if not force_refresh and self._token and now < self._expires_at:
                return self._token

            if not self.is_configured():
                logger.warning("Zendesk OAuth2 is not fully configured (missing domain, client_id, or client_secret).")
                return None

            token_url = f"https://{self.domain}/oauth/tokens"
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scope,
            }

            try:
                logger.info("Requesting new Zendesk OAuth token from %s", token_url)
                resp = requests.post(token_url, data=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    self._token = data.get("access_token")
                    expires_in = int(data.get("expires_in", 1800))
                    # Refresh 60 seconds before expiration, min 30s validity
                    self._expires_at = now + max(expires_in - 60, 30)
                    logger.info("Zendesk OAuth token acquired successfully (valid for %d seconds).", expires_in)
                    return self._token
                else:
                    logger.error(
                        "Zendesk OAuth token request failed: HTTP %d - %s",
                        resp.status_code,
                        resp.text[:200],
                    )
                    return None
            except Exception as e:
                logger.exception("Exception during Zendesk OAuth token request: %s", e)
                return None


class ZendeskAuth(AuthBase):
    """Custom Requests Auth handler for Zendesk API.

    Prioritizes OAuth2 Bearer token authentication via ZendeskOAuthTokenManager.
    Falls back to legacy HTTP Basic Auth (user/token + API key) when OAuth is not configured.
    Also automatically retries once upon HTTP 401 Unauthorized by refreshing the OAuth token.
    """

    def __init__(
        self,
        token_manager: Optional[ZendeskOAuthTokenManager] = None,
        user: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.token_manager = token_manager
        self.user = clean_secret(user)
        self.api_key = clean_secret(api_key)

    @property
    def is_oauth(self) -> bool:
        return bool(self.token_manager and self.token_manager.is_configured())

    @property
    def is_api_key(self) -> bool:
        return bool(self.user and self.api_key)

    @property
    def is_configured(self) -> bool:
        return self.is_oauth or self.is_api_key

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        if self.is_oauth and self.token_manager:
            token = self.token_manager.get_token()
            if token:
                r.headers["Authorization"] = f"Bearer {token}"
                r.register_hook("response", self.handle_401)
                return r

        if self.is_api_key:
            return HTTPBasicAuth(f"{self.user}/token", self.api_key)(r)

        return r

    def handle_401(self, r: requests.Response, **kwargs) -> requests.Response:
        """Handle 401 Unauthorized by refreshing the OAuth token and retrying the request once."""
        if r.status_code == 401 and self.is_oauth and self.token_manager:
            logger.warning("Received 401 Unauthorized from Zendesk. Invalidate token and retry once.")
            token = self.token_manager.get_token(force_refresh=True)
            if token:
                # Re-send original request with new token
                req = r.request.copy()
                req.headers["Authorization"] = f"Bearer {token}"
                new_resp = r.connection.send(req, **kwargs)
                new_resp.history.append(r)
                return new_resp
        return r
