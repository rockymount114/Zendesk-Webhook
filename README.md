# Zendesk Integration Service

A modern Flask-based web service that integrates with Zendesk to provide real-time ticket monitoring, webhook processing, and API integration with an interactive dashboard.

## Overview

This application provides comprehensive Zendesk integration with:
1. **Interactive Dashboard**: Real-time web interface showing recent tickets and KPI metrics with auto-refresh
2. **Webhook Endpoint**: Receives real-time notifications from Zendesk when tickets are created
3. **API Integration**: Fetches and displays tickets and ticket comments from the Zendesk REST API
4. **OAuth2 Authentication**: Modern OAuth2 Client Credentials flow with thread-safe caching, auto-renewal, and 401 recovery
5. **Debug Tools**: Built-in debugging endpoints for connection and authentication troubleshooting

## Features

- **Real-time Dashboard**: Interactive web interface with live ticket display in Apple-inspired design
- **KPI Metrics**: Dashboard view showing counts and distribution percentages for open, pending, solved, new, and on-hold tickets
- **Auto-Refresh**: Dashboard automatically updates every 60 seconds with smart tab handling
- **Enhanced Ticket Display**: Shows 10 most recent tickets with comprehensive details in full-width layout
- **Timezone Support**: All timestamps displayed in EST (UTC-4) for New York timezone
- **Rich Ticket Information**: Displays requester, assignee, description, priority, and status
- **Apple-Style Design**: Modern glassmorphism UI with backdrop blur effects and smooth animations
- **Status Monitoring**: Color-coded ticket status and priority badges with Apple system colors
- **Webhook Handler**: Processes incoming Zendesk webhook notifications
- **OAuth2 Authentication**: Secure OAuth2 (Client Credentials Grant) Bearer token authentication with Zendesk, with automatic token management, caching, 401 recovery, and legacy API token fallback
- **Ticket Comments API**: Fetches and serves comments for any ticket by ID
- **Error Handling**: Comprehensive error handling and debugging information
- **Environment Configuration**: Secure configuration via environment variables or Docker secrets
- **Responsive Design**: Mobile-friendly interface with Apple design principles
- **Debug Endpoint**: Built-in API connection testing and troubleshooting (`/debug-api`)

## Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) - Modern Python package manager (or pip)
- A Zendesk account with OAuth client credentials (or legacy API token access)

## Installation

### 1. Install uv (if not already installed)
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### 2. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/rockymount114/Zendesk-Webhook.git
cd Zendesk-Webhook

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies
```bash
# Core dependencies only
uv pip install -e .

# With development tools (recommended)
uv pip install -e ".[dev]"

# With all optional features
uv pip install -e ".[dev,scheduler,production]"
```

### 4. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Zendesk OAuth2 credentials
```

## Configuration

### Environment Variables

Edit the `.env` file with your Zendesk credentials:

```env
# Zendesk Configuration (Required)
SUBDOMAIN=your-domain.zendesk.com

# Zendesk OAuth2 Credentials (Recommended)
ZENDESK_CLIENT_ID="your_oauth_client_id"
ZENDESK_AUTH_SECRET="your_oauth_client_secret"
# Optional: OAuth scope (defaults to "read")
# ZENDESK_OAUTH_SCOPE=read

# Legacy Zendesk API Token (Optional fallback)
ZENDESK_USER=your.email@domain.com
ZENDESK_API_KEY=your_api_token_here

# Database Configuration (Optional)
DB_SERVER=your_db_server
DB_DATABASE=zendesk
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
REFRESHTIME=60
```

### Zendesk OAuth Setup

Since Zendesk has disabled API tokens, use the **Client Credentials Flow**:

1. **Create an OAuth Client**:
   - Go to Zendesk **Admin Center** → **Apps and integrations** → **APIs** → **Zendesk API**
   - Click on the **OAuth clients** tab and select **Add OAuth client**
   - Fill in:
     - **Client Name**: `zendesk-ticket-webhook` (or your preferred name)
     - **Company / Description**: Brief description of your integration
     - **Unique Identifier**: Your `ZENDESK_CLIENT_ID`
   - Click **Save**
   - Copy the generated **Secret** immediately and set it as `ZENDESK_AUTH_SECRET` in `.env` (it is only shown once).

2. **Configure Webhook** (Optional):
   - Go to Zendesk **Admin Center** → **Apps and integrations** → **Webhooks**
   - Create a new webhook pointing to `http://your-server:5000/zendesk-webhook`
   - Set trigger conditions for ticket creation

## Usage

### Running the Application

**Development Mode**:
```bash
python app.py
```

**Production Mode**:
```bash
# Using gunicorn (Linux/macOS)
uv pip install -e ".[production]"
gunicorn --bind 0.0.0.0:5000 app:app

# Or using waitress (Windows/cross-platform)
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

The application will start on `http://localhost:5000`

### Web Interface

#### Recent Tickets Dashboard
- **URL**: `http://localhost:5000/`
- **Features**:
  - Real-time display of 10 most recent tickets
  - Auto-refresh every 60 seconds with live countdown
  - Color-coded status badges and priority tags
  - Ticket details: ID, status, subject, description preview, requester, assignee, timestamps

#### KPI Dashboard
- **URL**: `http://localhost:5000/dashboard`
- **Features**:
  - Ticket count cards: Total, Open, Pending, Solved, New, On-Hold
  - Percentage distribution breakdown
  - Date range filtering
  - Detailed lists of active tickets by status

#### Debug Endpoint
- **URL**: `http://localhost:5000/debug-api`
- **Purpose**: Test Zendesk API connection and verify OAuth2 authentication status
- **Returns**: JSON with authentication mode (`OAuth2`), connection status, client ID, and sample API response

### API Endpoints

#### Webhook Endpoint
- **URL**: `/zendesk-webhook`
- **Method**: `POST`
- **Description**: Receives webhook notifications from Zendesk
- **Response**: JSON confirmation message

**Example webhook payload**:
```json
{
  "ticket": {
    "id": 12345,
    "subject": "Customer inquiry",
    "status": "new"
  }
}
```

**Test webhook with curl**:
```bash
curl -X POST http://localhost:5000/zendesk-webhook \
  -H "Content-Type: application/json" \
  -d '{"ticket":{"id":12345,"subject":"Test ticket","status":"new"}}'
```

#### Ticket Comments Endpoint
- **URL**: `/tickets/<ticket_id>/comments` or `/api/tickets/<ticket_id>/comments`
- **Method**: `GET`
- **Description**: Fetches comments for a specific Zendesk ticket using OAuth Bearer authentication

**Example**:
```bash
curl http://localhost:5000/tickets/4021/comments
```

## Testing

The project includes an automated test suite powered by `pytest` covering OAuth token management, thread-safe caching, 401 error recovery, and Flask API endpoints.

Run the tests with:
```bash
pytest
```

## Development

### Project Structure
```
.
├── app.py                  # Main Flask application and routes
├── zendesk_auth.py         # OAuth2 token manager and requests Auth handler
├── templates/              # HTML templates
│   ├── index.html          # Recent tickets dashboard template
│   └── dashboard.html      # KPI metrics dashboard template
├── static/                 # Static assets (CSS, JS)
│   ├── style.css           # Modern Apple-inspired styles
│   └── script.js           # Auto-refresh and UI behavior
├── tests/                  # Automated test suite
│   ├── test_zendesk_auth.py# Token manager and auth unit tests
│   └── test_app.py         # Flask route and integration tests
├── pyproject.toml          # Package configuration and dependencies
├── .env.example            # Environment variables template
├── .env                    # Actual configuration (gitignored)
├── changes.txt             # Changelog and modification records
├── docker-compose.yml      # Docker Compose configuration (dev)
├── docker-compose.prod.yml # Production Docker Compose with secrets
├── Dockerfile              # Container definition
└── README.md               # Documentation
```

### Package Management with uv

**Core dependencies**:
- `flask>=2.0.0` - Web framework
- `requests>=2.25.0` - HTTP library for API calls
- `python-dotenv>=0.19.0` - Environment variable management

**Optional dependencies**:
- `dev`: Development tools (`pytest`, `pytest-flask`, `black`, `flake8`, `mypy`)
- `scheduler`: Task scheduling (`schedule`, `apscheduler`)
- `production`: Production servers (`gunicorn`, `waitress`)

## Docker Deployment

### Local Docker Build
```bash
# Build image
docker build -t zendesk-webhook .

# Run with .env file
docker run -p 5000:5000 --env-file .env zendesk-webhook

# Or using Docker Compose
docker compose up --build
```

### Docker Swarm / Portainer Production Deployment

Production deployment supports Docker secrets for confidential OAuth credentials:

```yaml
version: "3.8"

services:
  zendesk-webhook:
    image: zjxteusa/zendesk-webhook:latest
    container_name: zendesk-webhook
    ports:
      - target: 5000
        published: 5000
        protocol: tcp
        mode: host
    restart: unless-stopped
    secrets:
      - SUBDOMAIN
      - ZENDESK_CLIENT_ID
      - ZENDESK_AUTH_SECRET
      - ZENDESK_API_KEY
      - ZENDESK_USER
      - DB_SERVER
      - DB_DATABASE
      - DB_USERNAME
      - DB_PASSWORD

secrets:
  SUBDOMAIN:
    external: true
  ZENDESK_CLIENT_ID:
    external: true
  ZENDESK_AUTH_SECRET:
    external: true
  ZENDESK_API_KEY:
    external: true
  ZENDESK_USER:
    external: true
  DB_SERVER:
    external: true
  DB_DATABASE:
    external: true
  DB_USERNAME:
    external: true
  DB_PASSWORD:
    external: true
```

## CI/CD & Docker Hub Automated Build

A GitHub Actions workflow is configured in [`.github/workflows/docker-build-push.yml`](.github/workflows/docker-build-push.yml) to automatically:
1. Run the automated test suite (`pytest`) on Python 3.11.
2. Build the Docker container image.
3. Push the image to Docker Hub as [`zjxteusa/zendesk-webhook:latest`](https://hub.docker.com/r/zjxteusa/zendesk-webhook) on push to the `main` branch or on release tags.

### Required GitHub Secrets

To allow GitHub Actions to authenticate and push to Docker Hub, configure these secrets in your repository (**Settings** → **Secrets and variables** → **Actions** → **New repository secret**):

| Secret Name | Description | Example |
|---|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username | `zjxteusa` |
| `DOCKERHUB_TOKEN` | Docker Hub Personal Access Token (PAT) with Read/Write permissions | `dckr_pat_...` |

## License

This project is licensed under the MIT License - see the LICENSE file for details.


