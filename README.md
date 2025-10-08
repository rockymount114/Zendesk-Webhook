# Zendesk Integration Service

A modern Flask-based web service that integrates with Zendesk to provide real-time ticket monitoring, webhook processing, and API integration with an interactive dashboard.

## Overview

This application provides comprehensive Zendesk integration with:
1. **Interactive Dashboard**: Real-time web interface showing recent tickets with auto-refresh
2. **Webhook Endpoint**: Receives real-time notifications from Zendesk when tickets are created
3. **API Integration**: Fetches and displays tickets from Zendesk REST API
4. **Debug Tools**: Built-in debugging endpoints for troubleshooting

## Features

- **Real-time Dashboard**: Interactive web interface with live ticket display in Apple-inspired design
- **Auto-Refresh**: Dashboard automatically updates every 60 seconds with smart tab handling
- **Enhanced Ticket Display**: Shows 10 most recent tickets with comprehensive details in full-width layout
- **Timezone Support**: All timestamps displayed in EST (UTC-4) for New York timezone
- **Rich Ticket Information**: Displays requester, assignee, description, priority, and status
- **Apple-Style Design**: Modern glassmorphism UI with backdrop blur effects and smooth animations
- **Status Monitoring**: Color-coded ticket status and priority badges with Apple system colors
- **Webhook Handler**: Processes incoming Zendesk webhook notifications
- **Secure Authentication**: API token-based authentication with Zendesk
- **Error Handling**: Comprehensive error handling and debugging information
- **Environment Configuration**: Secure configuration via environment variables
- **Responsive Design**: Mobile-friendly interface with Apple design principles
- **Debug Endpoint**: Built-in API connection testing and troubleshooting

## Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) - Modern Python package manager
- A Zendesk account with API access
- Valid Zendesk API credentials

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

# Edit .env with your actual Zendesk credentials
# Required variables:
# ZENDESK_BASE_URL=https://your-domain.zendesk.com
# ZENDESK_API_KEY=your_api_token_here
# ZENDESK_USER=your.email@domain.com
```

## Configuration

### Environment Variables

Edit the `.env` file with your Zendesk credentials:

```env
# Zendesk Configuration (Required)
ZENDESK_BASE_URL=https://your-domain.zendesk.com
ZENDESK_API_KEY=your_api_token_here
ZENDESK_USER=your.email@domain.com

# Optional: Database Configuration (for future use)
DB_SERVER=your_db_server
DB_DATABASE=zendesk
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password

# Optional: Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### Zendesk Setup

1. **Generate API Token**:
   - Go to Zendesk Admin → Channels → API
   - Enable Token Access
   - Generate a new API token

2. **Configure Webhook** (Optional):
   - Go to Zendesk Admin → Extensions → Webhooks
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
# Using gunicorn (install with production extras)
uv pip install -e ".[production]"
gunicorn --bind 0.0.0.0:5000 app:app

# Or using waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

The application will start on `http://localhost:5000`

### Web Interface

#### Dashboard (Home Page)
- **URL**: `http://localhost:5000/`
- **Features**:
  - Real-time display of 10 most recent tickets
  - Auto-refresh every 60 seconds with live countdown
  - Configuration status overview
  - Service documentation and quick start guide
  - Color-coded ticket status badges
  - Ticket details: ID, status, subject, priority, creation date

#### Debug Endpoint
- **URL**: `http://localhost:5000/debug-api`
- **Purpose**: Test Zendesk API connection and troubleshoot issues
- **Returns**: JSON with connection status, configuration details, and error information

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

## Dashboard Features

### Real-time Ticket Display
- Shows 10 most recent tickets from Zendesk in full-width layout
- Modern Apple-inspired design with glassmorphism effects
- Color-coded status and priority badges:
  - **Status**: NEW (Green), OPEN (Orange), PENDING (Red-Orange), SOLVED (Gray), CLOSED (Dark)
  - **Priority**: URGENT (Red), HIGH (Orange), NORMAL (Blue), LOW (Gray)
- Comprehensive ticket information includes:
  - Ticket ID with monospace styling
  - Current status and priority badges
  - Full subject line (truncated if very long)
  - Ticket description preview
  - Requester and assignee names
  - Creation and last updated timestamps in EST (UTC-4)

### Auto-Refresh Functionality
- Automatically refreshes every 60 seconds
- Live countdown indicator in top-right corner
- Smart behavior:
  - Pauses when browser tab is inactive (saves resources)
  - Resumes when tab becomes active again
  - Shows "Refreshing..." message during reload

### Configuration Overview
- Shows Zendesk domain and user configuration
- API key status indicator
- Overall service readiness status
- Real-time connection testing

### Service Information
- Available API endpoints documentation
- Quick start guide with copy-paste curl examples
- Feature checklist (current and planned)

## Development

### Project Structure
```
.
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   └── index.html      # Dashboard template with auto-refresh
├── pyproject.toml      # Package configuration and dependencies
├── .env.example        # Environment variables template
├── .env                # Your actual config (gitignored)
├── .gitignore          # Version control exclusions
└── README.md           # This documentation
```

### Package Management with uv

The project uses modern Python packaging with `pyproject.toml`:

**Core dependencies**:
- `flask>=2.0.0` - Web framework
- `requests>=2.25.0` - HTTP library for API calls
- `python-dotenv>=0.19.0` - Environment variable management

**Optional dependencies**:
- `dev`: Development tools (pytest, black, flake8, mypy, pre-commit)
- `scheduler`: Task scheduling (schedule, apscheduler)
- `production`: Production servers (gunicorn, waitress)

### Code Quality Tools

```bash
# Format code
black .

# Check code style
flake8 .

# Type checking
mypy app.py

# Run tests (when available)
pytest
```

### Adding Features

To extend the application:
1. Add new routes in `app.py`
2. Create new templates in `templates/`
3. Update `pyproject.toml` for new dependencies
4. Customize the dashboard template in `templates/index.html`
5. Add tests in a `tests/` directory

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify API token is correct and active
   - Ensure email format matches your Zendesk account
   - Check Zendesk domain URL format

2. **Dashboard Not Loading Tickets**:
   - Visit `/debug-api` endpoint to test API connection
   - Check browser console for JavaScript errors
   - Verify all environment variables are set correctly
   - Ensure network connectivity to Zendesk

3. **Auto-Refresh Not Working**:
   - Check browser console for JavaScript errors
   - Ensure JavaScript is enabled in your browser
   - Try manually refreshing the page
   - Verify the tab is active (refresh pauses on inactive tabs)

4. **Webhook Not Receiving Data**:
   - Verify webhook URL is publicly accessible
   - Check Zendesk webhook configuration and triggers
   - Test with the provided curl command

5. **API Rate Limiting**:
   - Zendesk has API rate limits (700 requests per minute)
   - Monitor console output for rate limit messages
   - Consider implementing caching for production use

### Debug Information

**Check the debug endpoint**:
```bash
curl http://localhost:5000/debug-api
```

**Monitor application logs**:
```bash
python app.py 2>&1 | tee app.log
```

**Console debugging**: The application prints detailed debug information including:
- API response status codes
- Number of tickets found and displayed
- Configuration status
- Error details and stack traces

## Security Considerations

- **Environment Variables**: Never commit `.env` files to version control
- **HTTPS**: Use HTTPS in production for webhook endpoints
- **Webhook Validation**: Consider implementing webhook signature validation
- **API Credentials**: Store sensitive data only in environment variables
- **Debug Endpoint**: Disable `/debug-api` in production or add authentication

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run code quality checks (`black .`, `flake8 .`, `mypy app.py`)
5. Add tests if applicable
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- **Bug Reports**: Create an issue in the repository
- **Documentation**: Check this README and code comments
- **Troubleshooting**: Use the `/debug-api` endpoint
- **Zendesk API**: Review [Zendesk API documentation](https://developer.zendesk.com/api-reference/)

---

**Production Deployment Notes**: 
- Use a production WSGI server (gunicorn, waitress)
- Set up proper logging and monitoring
- Implement database persistence for ticket data
- Add authentication for sensitive endpoints
- Configure SSL/TLS certificates
- Set up automated backups and health checks



**Docker build image**:
- `docker build -t zendesk-webhook .`
- `docker run -p 5000:5000 --env-file .env zendesk-webhook`
- `docker compose build` or `docker compose up --build`



** set variables as:

ZENDESK_USER = get_secret("ZENDESK_USER")
ZENDESK_API_KEY = get_secret("ZENDESK_API_KEY")
SUBDOMAIN = get_secret("SUBDOMAIN")
DB_SERVER = get_secret("DB_SERVER")
DB_DATABASE = get_secret("DB_DATABASE")
DB_USERNAME = get_secret("DB_USERNAME")
DB_PASSWORD = get_secret("DB_PASSWORD")

** Run on Lunix

```
docker run --rm -p 5000:5000 \
    -v "$(pwd)/secrets/ZENDESK_USER:/run/secrets/ZENDESK_USER:ro" \
    -v "$(pwd)/secrets/ZENDESK_API_KEY:/run/secrets/ZENDESK_API_KEY:ro" \
    -v "$(pwd)/secrets/SUBDOMAIN:/run/secrets/SUBDOMAIN:ro" \
    -v "$(pwd)/secrets/DB_SERVER:/run/secrets/DB_SERVER:ro" \
    -v "$(pwd)/secrets/DB_DATABASE:/run/secrets/DB_DATABASE:ro" \
    -v "$(pwd)/secrets/DB_USERNAME:/run/secrets/DB_USERNAME:ro" \
    -v "$(pwd)/secrets/DB_PASSWORD:/run/secrets/DB_PASSWORD:ro" \
    zendesk-webhook
```