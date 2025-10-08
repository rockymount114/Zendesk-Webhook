import os
import requests
import json
from datetime import date, datetime, timezone, timedelta
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)


def get_secret(secret_name):
    # The path inside the container where Docker mounts secrets
    path = f"/run/secrets/{secret_name}"
    try:
        # Use 'utf-8-sig' to handle the BOM (Byte Order Mark) that Windows
        # sometimes adds to text files, which causes a UnicodeDecodeError.
        with open(path, encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback to environment variable if secret file not found
        return os.getenv(secret_name)

# Load secrets/environment variables
ZENDESK_USER = get_secret("ZENDESK_USER")
ZENDESK_API_KEY = get_secret("ZENDESK_API_KEY")
SUBDOMAIN = get_secret("SUBDOMAIN")
DB_SERVER = get_secret("DB_SERVER")
DB_DATABASE = get_secret("DB_DATABASE")
DB_USERNAME = get_secret("DB_USERNAME")
DB_PASSWORD = get_secret("DB_PASSWORD")


# Normalize base domain
# Accept either "rockymountnchelp.zendesk.com" or full "https://rockymountnchelp.zendesk.com"
def normalize_base_domain(subdomain_env: str) -> str:
    if not subdomain_env:
        return None
    s = subdomain_env.strip()
    if s.startswith("http://") or s.startswith("https://"):
        s = s.replace("http://", "").replace("https://", "")
    return s  # e.g., rockymountnchelp.zendesk.com

BASE_DOMAIN = normalize_base_domain(SUBDOMAIN)

# Set Zendesk API credentials
auth = (f"{ZENDESK_USER}/token", ZENDESK_API_KEY) if ZENDESK_USER and ZENDESK_API_KEY else None

# ---------- Existing index route (kept as-is with minor domain normalization) ----------
@app.route('/')
def index():
    zendesk_domain = BASE_DOMAIN if BASE_DOMAIN else 'Not configured'
    zendesk_user = ZENDESK_USER if ZENDESK_USER else 'Not configured'
    api_key_status = 'Configured' if ZENDESK_API_KEY else 'Not configured'

    if BASE_DOMAIN and ZENDESK_API_KEY and ZENDESK_USER:
        config_status = 'Ready'
    else:
        config_status = 'Incomplete'

    recent_tickets = []
    tickets_error = None

    if BASE_DOMAIN and auth:
        try:
            url = f"https://{BASE_DOMAIN}/api/v2/tickets.json?sort_by=created_at&sort_order=desc"
            headers = {"Content-Type": "application/json"}
            response = requests.get(url, auth=auth, headers=headers)

            if response.status_code == 200:
                tickets_data = response.json()
                recent_tickets = tickets_data.get('tickets', [])[:10]

                # Collect user IDs from tickets
                user_ids = set()
                for ticket in recent_tickets:
                    if ticket.get('requester_id'):
                        user_ids.add(ticket['requester_id'])
                    if ticket.get('assignee_id'):
                        user_ids.add(ticket['assignee_id'])

                # Fetch user names
                users_data = {}
                if user_ids:
                    try:
                        user_url = f"https://{BASE_DOMAIN}/api/v2/users/show_many.json?ids={','.join(map(str, user_ids))}"
                        user_response = requests.get(user_url, auth=auth, headers=headers)
                        if user_response.status_code == 200:
                            users = user_response.json().get('users', [])
                            for user in users:
                                users_data[user['id']] = user['name']
                    except Exception as e:
                        print(f"Error fetching users: {e}")

                # Format ticket fields
                from datetime import datetime, timezone, timedelta
                for ticket in recent_tickets:
                    created_at = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))
                    ny_timezone = timezone(timedelta(hours=-4))
                    created_at_ny = created_at.astimezone(ny_timezone)
                    ticket['created_at_formatted'] = created_at_ny.strftime('%Y-%m-%d %H:%M:%S EST')

                    if ticket.get('updated_at'):
                        updated_at = datetime.fromisoformat(ticket['updated_at'].replace('Z', '+00:00'))
                        updated_at_ny = updated_at.astimezone(ny_timezone)
                        ticket['updated_at_formatted'] = updated_at_ny.strftime('%Y-%m-%d %H:%M:%S EST')

                    # Truncate subject/description
                    subject = ticket.get('subject', 'No subject')
                    ticket['subject_short'] = subject[:80] + ('...' if len(subject) > 80 else '')
                    description = ticket.get('description', 'No description')
                    ticket['description_short'] = description[:150] + ('...' if len(description) > 150 else '')

                    ticket['requester_name'] = users_data.get(ticket.get('requester_id'), 'Unknown')
                    ticket['assignee_name'] = users_data.get(ticket.get('assignee_id'), 'Unassigned')
            else:
                tickets_error = f"API Error: {response.status_code}"
        except Exception as e:
            tickets_error = f"Error fetching tickets: {str(e)}"
            print(f"Exception details: {e}")

    return render_template(
        'index.html',
        zendesk_domain=zendesk_domain,
        zendesk_user=zendesk_user,
        api_key_status=api_key_status,
        config_status=config_status,
        recent_tickets=recent_tickets,
        tickets_error=tickets_error
    )

# ---------- Debug API ----------
@app.route('/debug-api')
def debug_api():
    debug_info = {
        "zendesk_url": BASE_DOMAIN,
        "zendesk_user": ZENDESK_USER,
        "api_key_configured": bool(ZENDESK_API_KEY),
        "api_key_length": len(ZENDESK_API_KEY) if ZENDESK_API_KEY else 0
    }

    if BASE_DOMAIN and auth:
        try:
            url = f"https://{BASE_DOMAIN}/api/v2/tickets.json?per_page=1"
            headers = {"Content-Type": "application/json"}
            response = requests.get(url, auth=auth, headers=headers)
            debug_info.update({
                "api_test_status": response.status_code,
                "api_test_response": response.text[:500] if response.text else "No response",
                "auth_header": f"{ZENDESK_USER}/token:***"
            })
        except Exception as e:
            debug_info["api_test_error"] = str(e)
    else:
        debug_info["error"] = "Missing configuration"

    return jsonify(debug_info)

# ---------- Webhook ----------
@app.route('/zendesk-webhook', methods=['POST'])
def handle_zendesk_webhook():
    try:
        ticket_data = request.get_json()
        ticket_id = ticket_data['ticket']['id']
        print(f"New ticket created: {ticket_id}")
        return jsonify({"message": "Webhook received successfully","data": ticket_data}), 200
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"message": "Error processing webhook"}), 500

# ---------- KPI: ticket counts with pagination ----------
def get_ticket_counts(start_date: str, end_date: str):
    if not (BASE_DOMAIN and auth):
        return {"error": "Zendesk not configured"}, 0

    headers = {'Content-Type': 'application/json'}

    # Validate dates
    try:
        # More robust date parsing
        sd = datetime.strptime(start_date, '%Y-%m-%d').date()
        ed = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return {"error": f"Invalid date format: '{start_date}' or '{end_date}'. Expected YYYY-MM-DD"}, 422
    if sd > ed:
        return {"error": "Start date cannot be after end date"}, 422

    total_stats = {
        'total': 0, 'open': 0, 'pending': 0, 'closed': 0, 'new': 0, 'on-hold': 0, 'solved': 0,
        'open_tickets': [], 'pending_tickets': [], 'solved_tickets': [], 'new_tickets': [], 'on_hold_tickets': [],
    }

    # Helper to accumulate stats for a page of results
    def accumulate_page_stats(page_data, stats_accumulator):
        for t in page_data.get('results', []):
            stats_accumulator['total'] += 1
            status = (t.get('status') or '').lower()
            if status in stats_accumulator:
                stats_accumulator[status] += 1
            
            if status == 'open':
                stats_accumulator['open_tickets'].append(t)
            elif status == 'pending':
                stats_accumulator['pending_tickets'].append(t)
            elif status == 'solved':
                stats_accumulator['solved_tickets'].append(t)
            elif status == 'new':
                stats_accumulator['new_tickets'].append(t)
            elif status == 'on-hold':
                stats_accumulator['on_hold_tickets'].append(t)

    current_start = sd
    while current_start <= ed:
        # Chunk date range into 60-day intervals to avoid API errors
        current_end = current_start + timedelta(days=59)
        if current_end > ed:
            current_end = ed

        start_ts = f"{current_start.isoformat()}T00:00:00Z"
        end_ts = f"{current_end.isoformat()}T23:59:59Z"
        query = f'type:ticket created>={start_ts} created<={end_ts}'
        
        base_url = f"https://{BASE_DOMAIN}/api/v2/search.json"
        
        resp = requests.get(base_url, headers=headers, params={'query': query}, auth=auth)
        
        if resp.status_code != 200:
            return total_stats, resp.status_code

        data = resp.json()
        accumulate_page_stats(data, total_stats)

        next_page = data.get('next_page')
        while next_page:
            resp_page = requests.get(next_page, headers=headers, auth=auth)
            if resp_page.status_code != 200:
                break
            page_data = resp_page.json()
            accumulate_page_stats(page_data, total_stats)
            next_page = page_data.get('next_page')

        current_start = current_end + timedelta(days=1)

    return total_stats, 200

# ---------- Dashboard route at /dashboard ----------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    stats = None
    error = None
    open_tickets = []
    pending_tickets = []
    solved_tickets = []
    open_perc = 0
    pending_perc = 0
    closed_perc = 0
    new_perc = 0
    on_hold_perc = 0
    solved_perc = 0

    today = date.today()
    default_start = date(today.year, today.month, 1).isoformat()
    default_end = today.isoformat()

    if request.method == 'POST':
        start_date = request.form.get('start_date') or default_start
        end_date = request.form.get('end_date') or default_end
    else:
        start_date = default_start
        end_date = default_end

    # Always load KPIs with current date range (whether GET or POST)
    stats, status_code = get_ticket_counts(start_date, end_date)
    if isinstance(stats, dict) and stats.get("error"):
        error = stats["error"]
    elif status_code != 200:
        error = f"Zendesk API returned status {status_code}"
    
    if stats:
        total_count = stats.get('total', 0)
        if total_count > 0:
            open_perc = (stats.get('open', 0) / total_count) * 100
            pending_perc = (stats.get('pending', 0) / total_count) * 100
            closed_perc = (stats.get('closed', 0) / total_count) * 100
            new_perc = (stats.get('new', 0) / total_count) * 100
            on_hold_perc = (stats.get('on-hold', 0) / total_count) * 100
            solved_perc = (stats.get('solved', 0) / total_count) * 100

        open_tickets = stats.get('open_tickets', [])
        pending_tickets = stats.get('pending_tickets', [])
        solved_tickets = stats.get('solved_tickets', [])
        new_tickets = stats.get('new_tickets', [])
        on_hold_tickets = stats.get('on_hold_tickets', [])

        # Sort tickets by creation date in descending order
        open_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        pending_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        solved_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        new_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        on_hold_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        
        # Combine tickets to fetch user data in one go
        all_tickets = open_tickets + pending_tickets + solved_tickets + new_tickets + on_hold_tickets      
        
        
        if all_tickets and BASE_DOMAIN and auth:
            user_ids = set()
            for ticket in all_tickets:
                if ticket.get('requester_id'):
                    user_ids.add(ticket['requester_id'])
                if ticket.get('assignee_id'):
                    user_ids.add(ticket['assignee_id'])

            users_data = {}
            if user_ids:
                user_id_list = list(user_ids)
                chunk_size = 100
                for i in range(0, len(user_id_list), chunk_size):
                    chunk = user_id_list[i:i + chunk_size]
                    try:
                        user_url = f"https://{BASE_DOMAIN}/api/v2/users/show_many.json?ids={','.join(map(str, chunk))}"
                        headers = {"Content-Type": "application/json"}
                        user_response = requests.get(user_url, auth=auth, headers=headers)
                        if user_response.status_code == 200:
                            users = user_response.json().get('users', [])
                            for user in users:
                                users_data[user['id']] = user['name']
                        else:
                            print(f"Error fetching user chunk: Status {user_response.status_code}")
                    except Exception as e:
                        print(f"Error fetching users for dashboard: {e}")

            # Format ticket fields for display
            ny_timezone = timezone(timedelta(hours=-4))
            for ticket in all_tickets:
                if ticket.get('created_at'):
                    created_at = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))
                    ticket['created_at_formatted'] = created_at.astimezone(ny_timezone).strftime('%Y-%m-%d %H:%M:%S EST')
                else:
                    ticket['created_at_formatted'] = 'N/A'

                if ticket.get('updated_at'):
                    updated_at = datetime.fromisoformat(ticket['updated_at'].replace('Z', '+00:00'))
                    ticket['updated_at_formatted'] = updated_at.astimezone(ny_timezone).strftime('%Y-%m-%d %H:%M:%S EST')
                else:
                    ticket['updated_at_formatted'] = 'N/A'


                subject = ticket.get('subject', 'No subject')
                ticket['subject_short'] = subject[:80] + ('...' if len(subject) > 80 else '')
                description = ticket.get('description', 'No description')
                ticket['description'] = description

                ticket['requester_name'] = users_data.get(ticket.get('requester_id'), 'Unknown')
                ticket['assignee_name'] = users_data.get(ticket.get('assignee_id'), 'Unassigned')
            
    return render_template('dashboard.html',
                           stats=stats,
                           error=error,
                           start_date=start_date,
                           end_date=end_date,
                           open_tickets=open_tickets,
                           pending_tickets=pending_tickets,
                           solved_tickets=solved_tickets,
                           new_tickets=new_tickets,
                           on_hold_tickets=on_hold_tickets,
                           open_perc=open_perc,
                           pending_perc=pending_perc,
                           closed_perc = closed_perc,
                           new_perc=new_perc,
                           on_hold_perc=on_hold_perc,
                           solved_perc=solved_perc,
                           zendesk_domain=BASE_DOMAIN)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)

