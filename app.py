import os
import requests
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load environment variables
ZENDESK_BASE_URL = os.getenv("ZENDESK_BASE_URL")
ZENDESK_API_KEY = os.getenv("ZENDESK_API_KEY")
ZENDESK_USER = os.getenv("ZENDESK_USER")

# Set Zendesk API credentials
auth = (f"{ZENDESK_USER}/token", ZENDESK_API_KEY)

# Home page route
@app.route('/')
def index():
    # Prepare configuration data for the template
    zendesk_domain = ZENDESK_BASE_URL.replace('https://', '').replace('http://', '') if ZENDESK_BASE_URL else 'Not configured'
    zendesk_user = ZENDESK_USER if ZENDESK_USER else 'Not configured'
    api_key_status = 'Configured' if ZENDESK_API_KEY else 'Not configured'
    
    # Check overall configuration status
    if ZENDESK_BASE_URL and ZENDESK_API_KEY and ZENDESK_USER:
        config_status = 'Ready'
    else:
        config_status = 'Incomplete'
    
    # Get recent tickets
    recent_tickets = []
    tickets_error = None
    
    if ZENDESK_BASE_URL and ZENDESK_API_KEY and ZENDESK_USER:
        try:
            # Get recent tickets from Zendesk
            url = f"{ZENDESK_BASE_URL}/api/v2/tickets.json?sort_by=created_at&sort_order=desc"
            headers = {"Content-Type": "application/json"}
            response = requests.get(url, auth=auth, headers=headers)
            
            if response.status_code == 200:
                tickets_data = response.json()
                # Get the first 10 most recent tickets
                recent_tickets = tickets_data.get('tickets', [])[:10]
                
                # Debug information
                print(f"API Response Status: {response.status_code}")
                print(f"Total tickets found: {len(tickets_data.get('tickets', []))}")
                print(f"Displaying: {len(recent_tickets)} tickets")
                
                # Format ticket data for display
                for ticket in recent_tickets:
                    # Format the created date to New York time (UTC-4)
                    from datetime import datetime, timezone, timedelta
                    created_at = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))
                    ny_timezone = timezone(timedelta(hours=-4))  # UTC-4 for New York
                    created_at_ny = created_at.astimezone(ny_timezone)
                    ticket['created_at_formatted'] = created_at_ny.strftime('%Y-%m-%d %H:%M:%S EST')
                    
                    # Format updated date
                    if ticket.get('updated_at'):
                        updated_at = datetime.fromisoformat(ticket['updated_at'].replace('Z', '+00:00'))
                        updated_at_ny = updated_at.astimezone(ny_timezone)
                        ticket['updated_at_formatted'] = updated_at_ny.strftime('%Y-%m-%d %H:%M:%S EST')
                    
                    # Truncate long subjects and descriptions
                    if len(ticket.get('subject', '')) > 80:
                        ticket['subject_short'] = ticket['subject'][:80] + '...'
                    else:
                        ticket['subject_short'] = ticket.get('subject', 'No subject')
                    
                    # Truncate description
                    description = ticket.get('description', 'No description')
                    if len(description) > 150:
                        ticket['description_short'] = description[:150] + '...'
                    else:
                        ticket['description_short'] = description
                    
                    # Format requester and assignee names
                    ticket['requester_name'] = ticket.get('requester', {}).get('name', 'Unknown') if isinstance(ticket.get('requester'), dict) else 'Unknown'
                    ticket['assignee_name'] = ticket.get('assignee', {}).get('name', 'Unassigned') if isinstance(ticket.get('assignee'), dict) else 'Unassigned'
                        
            else:
                tickets_error = f"API Error: {response.status_code}"
                
        except Exception as e:
            tickets_error = f"Error fetching tickets: {str(e)}"
            print(f"Exception details: {e}")
            print(f"Zendesk URL: {ZENDESK_BASE_URL}")
            print(f"API User: {ZENDESK_USER}")
            print(f"API Key configured: {'Yes' if ZENDESK_API_KEY else 'No'}")
    
    return render_template('index.html', 
                         zendesk_domain=zendesk_domain,
                         zendesk_user=zendesk_user,
                         api_key_status=api_key_status,
                         config_status=config_status,
                         recent_tickets=recent_tickets,
                         tickets_error=tickets_error)

# Debug route to test API connection
@app.route('/debug-api')
def debug_api():
    debug_info = {
        "zendesk_url": ZENDESK_BASE_URL,
        "zendesk_user": ZENDESK_USER,
        "api_key_configured": bool(ZENDESK_API_KEY),
        "api_key_length": len(ZENDESK_API_KEY) if ZENDESK_API_KEY else 0
    }
    
    if ZENDESK_BASE_URL and ZENDESK_API_KEY and ZENDESK_USER:
        try:
            # Test API connection
            url = f"{ZENDESK_BASE_URL}/api/v2/tickets.json?per_page=1"
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

# Create a webhook endpoint
@app.route('/zendesk-webhook', methods=['POST'])
def handle_zendesk_webhook():
    try:
        # Get the ticket data from the webhook notification
        ticket_data = request.get_json()
        ticket_id = ticket_data['ticket']['id']

        # Process the new ticket
        print(f"New ticket created: {ticket_id}")

        # Return a success response
        return jsonify({"message": "Webhook received successfully"}), 200
    except Exception as e:
        # Handle any errors
        print(f"Error processing webhook: {e}")
        return jsonify({"message": "Error processing webhook"}), 500

# Create a function to get new tickets
def get_new_tickets():
    try:
        # Set the API endpoint URL
        url = f"{ZENDESK_BASE_URL}/api/v2/tickets.json"

        # Set the API request headers
        headers = {
            "Content-Type": "application/json"
        }

        # Make a GET request to the API
        response = requests.get(url, auth=auth, headers=headers)

        # Check if the response was successful
        if response.status_code == 200:
            # Get the tickets from the response
            tickets = response.json()['tickets']

            # Process the new tickets
            for ticket in tickets:
                print(f"New ticket: {ticket['id']}")

        else:
            # Handle any API errors
            print(f"Error getting new tickets: {response.status_code}")
    except Exception as e:
        # Handle any errors
        print(f"Error getting new tickets: {e}")

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)

    # Alternatively, you can use a scheduler like schedule or apscheduler to run the get_new_tickets function at regular intervals
    # import schedule
    # import time

    # schedule.every(1).minutes.do(get_new_tickets)  # Run every 1 minute

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)