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
        assert "app-topbar" in content
        assert "footer-card" in content
        assert "Designed by XL" in content
        assert 'nav-link active" aria-current="page">Recent' in content
        assert "ticket-preview-drawer" in content
        assert "ticket_preview.js" in content
        assert 'data-id="4021"' in content
        assert 'data-description=' in content
        assert 'id="drawer-conversation-section" class="drawer-section" hidden' in content
        assert "ticket-external-link" not in content
        assert 'href="https://test.zendesk.com/agent/tickets/4021"' in content
        assert "toggle-index-refresh" in content
        assert "auto-refresh-toggle-sm" in content
        assert "refresh-timer-label" in content
        assert "refresh-control" not in content


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
            ],
            "users": [
                {
                    "id": 101,
                    "name": "Support Agent",
                }
            ]
        }
        mock_get.return_value = mock_resp

        response = client.get("/tickets/4021/comments")
        assert response.status_code == 200
        data = response.get_json()
        assert "comments" in data
        assert data["comments"][0]["body"] == "First comment"
        assert "users" in data
        assert data["users"][0]["name"] == "Support Agent"
        # Verify params={"include": "users"} was passed
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs.get("params") == {"include": "users"}

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
                "tickets": [
                    {
                        "id": 4021,
                        "subject": "Test open ticket",
                        "status": "open",
                        "priority": "high",
                        "created_at": "2026-03-01T12:00:00Z",
                        "updated_at": "2026-03-01T13:00:00Z",
                    }
                ],
            },
            200,
        )
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert b"Zendesk KPIs" in response.data
        assert b'data-status="open"' in response.data
        assert b"Test open ticket" in response.data
        assert b'data-status="all"' in response.data
        assert b'id="statusChart"' in response.data
        assert b'id="assigneeChart"' in response.data
        assert b'id="trendChart"' in response.data
        assert b'id="chart-data"' in response.data
        assert b'data-assignee="Unassigned"' in response.data
        assert b"app-topbar" in response.data
        assert b"footer-card" in response.data
        assert b"Designed by XL" in response.data
        assert b'nav-link active" aria-current="page">KPIs' in response.data
        assert b"ticket-preview-drawer" in response.data
        assert b"ticket_preview.js" in response.data
        assert b'class="ticket-row"' in response.data
        assert b'data-id="4021"' in response.data
        assert b'data-description=' in response.data



    @patch("app.requests.get")
    def test_ticket_counts_collects_all_ticket_details_and_hold_status(self, mock_get):
        import app

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "results": [
                {"id": 1, "status": "open"},
                {"id": 2, "status": "hold"},
            ],
            "next_page": None,
        }
        mock_get.return_value = response

        stats, status_code = app.get_ticket_counts("2026-03-01", "2026-03-01")

        assert status_code == 200
        assert stats["total"] == 2
        assert stats["on-hold"] == 1
        assert [ticket["id"] for ticket in stats["tickets"]] == [1, 2]

    @patch("app.requests.get")
    def test_open_tickets_page_configured(self, mock_get, client):
        import app
        app._open_tickets_cache = {"timestamp": 0, "tickets": [], "requesters": [], "assignees": []}

        mock_search_resp = MagicMock()
        mock_search_resp.status_code = 200
        mock_search_resp.json.return_value = {
            "results": [
                {
                    "id": 5001,
                    "subject": "Printer issue in room 102",
                    "description": "Paper jam",
                    "status": "open",
                    "priority": "normal",
                    "created_at": "2026-03-01T14:00:00Z",
                    "updated_at": "2026-03-01T15:00:00Z",
                    "requester_id": 101,
                    "assignee_id": 202,
                }
            ],
            "next_page": None,
        }

        mock_users_resp = MagicMock()
        mock_users_resp.status_code = 200
        mock_users_resp.json.return_value = {
            "users": [
                {"id": 101, "name": "Alice Cooper"},
                {"id": 202, "name": "Bob Dylan"},
            ]
        }

        mock_get.side_effect = [mock_search_resp, mock_users_resp]

        response = client.get("/open-tickets")
        assert response.status_code == 200
        content = response.data.decode("utf-8")
        assert "All Open Tickets" in content
        assert "5001" in content
        assert "Printer issue in room 102" in content
        assert "Alice Cooper" in content
        assert "Bob Dylan" in content
        assert "ticket-counter" in content
        assert "app-topbar" in content
        assert "footer-card" in content
        assert "Designed by XL" in content
        assert 'nav-link active" aria-current="page">Open tickets' in content
        assert "ticket-preview-drawer" in content
        assert "ticket_preview.js" in content
        assert 'data-description="Paper jam"' in content


    def test_open_tickets_page_unconfigured(self, monkeypatch, client):
        import app
        app._open_tickets_cache = {"timestamp": 0, "tickets": [], "requesters": [], "assignees": []}
        monkeypatch.setattr(app, "BASE_DOMAIN", None)
        monkeypatch.setattr(app, "auth", None)

        response = client.get("/open-tickets")
        assert response.status_code == 200
        content = response.data.decode("utf-8")
        assert "Zendesk not configured" in content


class TestBuildChartData:
    def test_build_chart_data_empty(self):
        from app import build_chart_data

        data = build_chart_data([], None)
        assert data["has_data"] is False
        assert data["status_distribution"]["counts"] == [0, 0, 0, 0, 0, 0]
        assert data["assignees_workload"]["labels"] == []
        assert data["daily_trends"]["labels"] == []

    def test_build_chart_data_aggregation(self):
        from app import build_chart_data

        stats = {
            "total": 3,
            "open": 1,
            "pending": 1,
            "solved": 1,
            "closed": 0,
            "new": 0,
            "on-hold": 0,
        }
        tickets = [
            {
                "id": 1,
                "status": "open",
                "assignee_name": "Bob Dylan",
                "created_at": "2026-03-01T12:00:00Z",
            },
            {
                "id": 2,
                "status": "pending",
                "assignee_name": "Bob Dylan",
                "created_at": "2026-03-01T14:00:00Z",
            },
            {
                "id": 3,
                "status": "hold",  # should normalize to on-hold
                "assignee_name": "Alice Cooper",
                "created_at": "2026-03-02T10:00:00Z",
            },
            {
                "id": 4,
                "status": "solved",  # solved is not active, shouldn't add to assignee workload
                "assignee_name": "Alice Cooper",
                "created_at": "2026-03-02T11:00:00Z",
            },
        ]

        chart_data = build_chart_data(tickets, stats, start_date="2026-03-01", end_date="2026-03-02")
        assert chart_data["has_data"] is True

        # Status distribution
        assert chart_data["status_distribution"]["labels"] == ["Open", "Pending", "Solved", "Closed", "New", "On-hold"]
        assert chart_data["status_distribution"]["counts"] == [1, 1, 1, 0, 0, 0]

        # Assignee workload: Bob Dylan has 2 (1 open, 1 pending), Alice has 1 (1 on-hold)
        workload = chart_data["assignees_workload"]
        assert workload["labels"] == ["Bob Dylan", "Alice Cooper"]
        assert workload["datasets"]["open"] == [1, 0]
        assert workload["datasets"]["pending"] == [1, 0]
        assert workload["datasets"]["on_hold"] == [0, 1]
        assert workload["datasets"]["new"] == [0, 0]

        # Daily trends: 2 on 2026-03-01, 2 on 2026-03-02
        trends = chart_data["daily_trends"]
        assert len(trends["labels"]) == 2
        assert trends["counts"] == [2, 2]

    def test_build_chart_data_assignee_top_10_limit(self):
        from app import build_chart_data

        stats = {"total": 12, "open": 12}
        tickets = []
        for i in range(12):
            for _ in range(i + 1):  # Assignee 11 gets 12 tickets, Assignee 0 gets 1
                tickets.append({
                    "id": len(tickets) + 1,
                    "status": "open",
                    "assignee_name": f"Agent {i:02d}",
                    "created_at": "2026-03-01T12:00:00Z",
                })

        chart_data = build_chart_data(tickets, stats, start_date="2026-03-01", end_date="2026-03-01")
        workload = chart_data["assignees_workload"]
        # Only top 10 assignees
        assert len(workload["labels"]) == 10
        # Agent 11 has the most (12), followed by Agent 10 (11), ..., Agent 02 (3)
        assert workload["labels"][0] == "Agent 11"
        assert workload["datasets"]["open"][0] == 12
        assert workload["labels"][-1] == "Agent 02"
        assert workload["datasets"]["open"][-1] == 3


class TestThemeSupport:
    @patch("app.requests.get")
    def test_theme_switcher_rendered_in_pages(self, mock_get, client):
        mock_tickets_resp = MagicMock()
        mock_tickets_resp.status_code = 200
        mock_tickets_resp.json.return_value = {"tickets": []}
        mock_get.return_value = mock_tickets_resp

        response = client.get("/")
        assert response.status_code == 200
        html = response.data.decode("utf-8")

        # Zero-FOUC script
        assert "data-theme" in html
        assert "localStorage.getItem('theme')" in html

        # Theme switcher control and options
        assert "theme-switch-group" in html
        assert 'data-theme-value="light"' in html
        assert 'data-theme-value="dark"' in html
        assert 'data-theme-value="auto"' in html

        # Theme management script
        assert "theme.js" in html

    def test_theme_static_asset(self, client):
        response = client.get("/static/theme.js")
        assert response.status_code == 200
        js = response.data.decode("utf-8")
        assert "app-theme-changed" in js
        assert "ThemeManager" in js
        assert "prefers-color-scheme" in js


