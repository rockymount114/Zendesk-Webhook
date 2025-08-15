# GEMINI.md

## Project Overview

This project is a Flask-based web service that integrates with Zendesk to provide real-time ticket monitoring and webhook processing. It features an interactive dashboard that displays the 10 most recent tickets, with details such as requester, assignee, description, priority, and status. The dashboard is designed with a modern, Apple-inspired aesthetic and automatically refreshes every 60 seconds.

The application is built with Python and Flask for the backend, and uses HTML, CSS, and JavaScript for the frontend. It relies on the `requests` library to communicate with the Zendesk API and `python-dotenv` for managing environment variables.

## Building and Running

### Prerequisites

*   Python 3.8+
*   `uv` (or `pip`)
*   A Zendesk account with API access

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rockymount114/Zendesk-Webhook.git
    cd Zendesk-Webhook
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Linux/Mac
    # or
    .venv\Scripts\activate     # On Windows
    ```

3.  **Install dependencies:**
    ```bash
    uv pip install -e .
    ```

4.  **Configure environment variables:**
    *   Copy `.env.example` to `.env`.
    *   Edit `.env` with your Zendesk credentials:
        ```
        ZENDESK_BASE_URL=https://your-domain.zendesk.com
        ZENDESK_API_KEY=your_api_token_here
        ZENDESK_USER=your.email@domain.com
        ```

### Running the Application

*   **Development:**
    ```bash
    python app.py
    ```

*   **Production:**
    ```bash
    # Using gunicorn
    uv pip install -e ".[production]"
    gunicorn --bind 0.0.0.0:5000 app:app

    # Or using waitress
    waitress-serve --host=0.0.0.0 --port=5000 app:app
    ```

The application will be available at `http://localhost:5000`.

## Development Conventions

*   **Code Style:** The project uses `black` for code formatting and `flake8` for linting.
*   **Type Checking:** `mypy` is used for static type checking.
*   **Testing:** The project is set up to use `pytest` for testing, although no tests are currently implemented.
*   **Dependencies:** Dependencies are managed in `pyproject.toml`.
*   **Branching:** The `README.md` suggests a feature-branching workflow for contributions.



ZENDESK ENDPOINT


***get tickets url {ZENDESK_BASE_URL}/api/v2/tickets.json***
ticket sample json as ticket_4021.json

***get ticket comments url {ZENDESK_BASE_URL}/tickets/{ticket_id}/comments.json***
comments sample json as ticket_4021_comments.json

***get users url {ZENDESK_BASE_URL}/users/{user_id}.json***