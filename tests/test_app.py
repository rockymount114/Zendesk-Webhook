import json
from unittest.mock import MagicMock, patch
import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestAppRoutes:
    def test_webhook_endpoint(self, client):
        payload = {
            "ticket": {
                "id": 12345,
                "subject": "Test Ticket",
                "status": "open",
            }
        }
        response = client.post(
            "/zendesk-webhook",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Webhook received successfully"
        assert data["data"]["ticket"]["id"] == 12345

    def test_webhook_endpoint_invalid(self, client):
        response = client.post(
            "/zendesk-webhook",
            data="not-a-json",
            content_type="text/plain",
        )
        assert response.status_code == 500

    @patch("app.requests.get")
    def test_index_route(self, mock_get, client):
        mock_tickets_resp = MagicMock()
        mock_tickets_resp.status_code = 200
        mock_tickets_resp.json.return_value = {
            "tickets": [
                {
                    "id": 4021,
                    "subject": "Test Ticket Subject",
                    "description": "Test Ticket Description",
                    "status": "open",
                    "priority": "high",
                    "created_at": "2026-03-01T12:00:00Z",
                    "updated_at": "2026-03-01T13:00:00Z",
                    "requester_id": 101,
                    "assignee_id": 202,
                }
            ]
        }

        mock_users_resp = MagicMock()
        mock_users_resp.status_code = 200
        mock_users_resp.json.return_value = {
            "users": [
                {"id": 101, "name": "Jane Doe"},
                {"id": 202, "name": "Agent Smith"},
            ]
        }

        mock_get.side_effect = [mock_tickets_resp, mock_users_resp]

        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode("utf-8")
        assert "Zendesk Ticket Dashboard" in content
        assert "4021" in content
        assert "Jane Doe" in content

    @patch("app.requests.get")
    def test_debug_api_route(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"tickets": []}'
        mock_get.return_value = mock_resp

        response = client.get("/debug-api")
        assert response.status_code == 200
        data = response.get_json()
        assert "auth_mode" in data
        assert "oauth_configured" in data
        assert data["oauth_configured"] is True
        assert data["auth_mode"] == "OAuth2"
        assert data["auth_header"] == "Bearer ***"

    @patch("app.requests.get")
    def test_comments_route(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "comments": [
                {
                    "id": 1,
                    "body": "First comment",
                    "author_id": 101,
                    "created_at": "2026-03-01T12:00:00Z",
                }
            ]
        }
        mock_get.return_value = mock_resp

        response = client.get("/tickets/4021/comments")
        assert response.status_code == 200
        data = response.get_json()
        assert "comments" in data
        assert data["comments"][0]["body"] == "First comment"

    def test_comments_route_unconfigured(self, monkeypatch, client):
        import app
        monkeypatch.setattr(app, "BASE_DOMAIN", None)
        monkeypatch.setattr(app, "auth", None)
        response = client.get("/tickets/4021/comments")
        assert response.status_code == 500
        assert response.get_json()["error"] == "Zendesk not configured"

    @patch("app.get_ticket_counts")
    def test_dashboard_route(self, mock_counts, client):
        mock_counts.return_value = (
            {
                "total": 1,
                "open": 1,
                "pending": 0,
                "closed": 0,
                "new": 0,
                "on-hold": 0,
                "solved": 0,
                "open_tickets": [],
                "pending_tickets": [],
                "solved_tickets": [],
                "new_tickets": [],
                "on_hold_tickets": [],
            },
            200,
        )
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert b"Zendesk KPIs" in response.data
