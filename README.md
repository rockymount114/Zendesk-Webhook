# Zendesk Integration Service

A Flask-based web service that integrates with Zendesk to handle ticket notifications and retrieve ticket data via webhooks and API calls.

## Overview

This application provides two main functionalities:
1. **Webhook Endpoint**: Receives real-time notifications from Zendesk when new tickets are created
2. **Ticket Retrieval**: Fetches tickets from Zendesk using their REST API

## Features

- 🎯 **Webhook Handler**: Processes incoming Zendesk webhook notifications
- 📊 **Real-time Dashboard**: Live dashboard showing recent tickets with auto-refresh
- 🔄 **Auto-Refresh**: Dashboard automatically updates every 60 seconds
- 🎫 **Ticket Display**: Shows ticket ID, status, subject, priority, and creation date
- 🔐 **Secure Authentication**: Uses API token-based authentication
- 🛡️ **Error Handling**: Comprehensive error handling for API calls and webhook processing
- 🔧 **Environment Configuration**: Configurable via environment variables
- 📱 **Responsive Design**: Modern, mobile-friendly web interface

## Prerequisites

- Python 3.6+
- Flask
- requests library
- A Zendesk account with API access
- Valid Zendesk API credentials

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd zendesk-integration
   ```

2. **Install dependencies**:
   ```bash
   pip install flask requests
   ```

3. **Configure environment variables**:
   Copy the `.env.example` to `.env` and update with your Zendesk credentials:
   ```bash
   cp .env.example .env
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
ZENDESK_BASE_URL=https://your-domain.zendesk.com
ZENDESK_API_KEY=your_api_key_here
ZENDESK_USER=your_email@domain.com
```

### Zendesk Setup

1. **Generate API Token**:
   - Go to Zendesk Admin → Channels → API
   - Enable Token Access
   - Generate a new API token

2. **Configure Webhook** (Optional):
   - Go to Zendesk Admin → Extensions → Webhooks
   - Create a new webhook pointing to `http://your-server/zendesk-webhook`
   - Set trigger conditions for ticket creation

## Usage

### Running the Application

**Development Mode**:
```bash
python app.py
```

The application will start on `http://localhost:5000` with debug mode enabled.

**Production Mode**:
```bash
export FLASK_ENV=production
flask run --host=0.0.0.0 --port=5000
```

### Web Interface

#### Dashboard (Home Page)
- **URL**: `/`
- **Method**: `GET`
- **Description**: Interactive dashboard showing service status and recent tickets
- **Features**:
  - Real-time ticket display (5 most recent)
  - Auto-refresh every 60 seconds
  - Configuration status overview
  - Service documentation
  - Quick start guide

#### API Endpoints

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

### Functions

#### `get_new_tickets()`
Retrieves all tickets from Zendesk and processes them. This function can be:
- Called manually
- Scheduled to run at regular intervals using a task scheduler

**Example with scheduler**:
```python
import schedule
import time

schedule.every(1).minutes.do(get_new_tickets)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## Database Integration

The application includes database configuration for potential data persistence:

- **Server**: 172.20.22.216
- **Database**: zendesk
- **Note**: Database integration code is not implemented in the current version

## Error Handling

The application includes comprehensive error handling:
- Webhook processing errors return HTTP 500 with error details
- API call failures are logged with status codes
- General exceptions are caught and logged

## Security Considerations

- ⚠️ **API Credentials**: Never commit `.env` files to version control
- 🔒 **HTTPS**: Use HTTPS in production for webhook endpoints
- 🛡️ **Webhook Validation**: Consider implementing webhook signature validation
- 🔐 **Environment Variables**: Store sensitive data in environment variables

## Development

### Project Structure
```
.
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   └── index.html      # Dashboard template with auto-refresh
├── .env                # Environment variables (not in version control)
├── .env.example        # Example environment file
└── README.md           # This file
```

### Dashboard Features

The web dashboard (`http://localhost:5000/`) provides:

#### 🎫 **Real-time Ticket Display**
- Shows 5 most recent tickets from Zendesk
- Color-coded status badges (New, Open, Pending, Solved, Closed)
- Ticket information includes:
  - Ticket ID and status
  - Subject (truncated if long)
  - Priority level
  - Creation timestamp

#### 🔄 **Auto-Refresh Functionality**
- Automatically refreshes every 60 seconds
- Live countdown indicator in top-right corner
- Pauses when tab is inactive (saves resources)
- Resumes when tab becomes active again

#### ⚙️ **Configuration Overview**
- Shows Zendesk domain and user configuration
- API key status indicator
- Overall service readiness status

#### 📊 **Service Information**
- Available API endpoints documentation
- Quick start guide with curl examples
- Feature checklist (current and planned)

### Adding Features

To extend the application:
1. Add new routes in `app.py`
2. Implement additional Zendesk API endpoints
3. Add database models and operations
4. Implement proper logging
5. Customize the dashboard template in `templates/index.html`

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify API token is correct
   - Ensure email format is correct
   - Check Zendesk domain URL

2. **Webhook Not Receiving Data**:
   - Verify webhook URL is accessible
   - Check Zendesk webhook configuration
   - Ensure proper trigger conditions

3. **Dashboard Not Loading Tickets**:
   - Check browser console for JavaScript errors
   - Verify API credentials in `.env` file
   - Ensure Zendesk domain URL is correct
   - Check network connectivity to Zendesk

4. **Auto-Refresh Not Working**:
   - Check browser console for errors
   - Ensure JavaScript is enabled
   - Try manually refreshing the page
   - Check if tab is active (refresh pauses on inactive tabs)

5. **API Rate Limiting**:
   - Zendesk has API rate limits
   - Implement proper retry logic
   - Consider caching strategies

### Logs

Check application logs for detailed error information:
```bash
python app.py 2>&1 | tee app.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Check the troubleshooting section
- Review Zendesk API documentation
- Create an issue in the repository

---

**Note**: This is a basic integration service. For production use, consider adding:
- Proper logging framework
- Database integration
- Authentication middleware
- Rate limiting
- Monitoring and health checks
- Unit tests