import os
import requests
import json
import time
import logging
from datetime import date, datetime, timezone, timedelta
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from urllib.parse import urlencode
from redis_cache import RedisCacheManager, CACHE_KEY_PATTERNS, CACHE_TTL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Initialize Redis Cache Manager
redis_cache = RedisCacheManager()


def get_secret(secret_name):
    path = f"/run/secrets/{secret_name}"
    try:
        with open(path, encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return os.getenv(secret_name)

# Load secrets/environment variables
ZENDESK_USER = get_secret("ZENDESK_USER")
ZENDESK_API_KEY = get_secret("ZENDESK_API_KEY")
SUBDOMAIN = get_secret("SUBDOMAIN")
DB_SERVER = get_secret("DB_SERVER")
DB_DATABASE = get_secret("DB_DATABASE")
DB_USERNAME = get_secret("DB_USERNAME")
DB_PASSWORD = get_secret("DB_PASSWORD")


def normalize_base_domain(subdomain_env: str) -> str:
    if not subdomain_env:
        return None
    s = subdomain_env.strip()
    if s.startswith("http://") or s.startswith("https://"):
        s = s.replace("http://", "").replace("https://", "")
    return s

BASE_DOMAIN = normalize_base_domain(SUBDOMAIN)

auth = (f"{ZENDESK_USER}/token", ZENDESK_API_KEY) if ZENDESK_USER and ZENDESK_API_KEY else None

# ---------- Cache buster helper ----------
def get_cache_buster():
    """Generate cache buster using current timestamp"""
    return str(int(time.time()))

# ---------- Redis caching functions ----------
def get_recent_tickets_with_cache(count: int = 10) -> tuple[list, str]:
    """Fetch recent tickets with Redis caching and robust fallback"""
    cache_key = CACHE_KEY_PATTERNS['recent_tickets'].format(count=count)
    fallback_tickets = []

    # Try to get from cache first
    try:
        cached_tickets = redis_cache.get_deserialized(cache_key)
        if cached_tickets:
            logger.info(f"Tickets cache hit - serving from Redis")
            return cached_tickets, "cache_hit"
    except Exception as e:
        logger.warning(f"Error reading from ticket cache: {e}")

    # Check if Redis is down and we have old cached data
    if not redis_cache.is_connected():
        logger.warning("Redis is not connected - attempting to serve stale data or falling back")
        # Return empty list with cache miss to let UI handle gracefully
        return [], "redis_down"

    # If not in cache, fetch from API
    logger.info("Tickets cache miss - fetching from Zendesk API")

    try:
        tickets_data = fetch_tickets_from_api(count)

        if tickets_data:
            # Cache the data for future use
            redis_cache.set_serialized(cache_key, tickets_data, CACHE_TTL['recent_tickets'])
            logger.info(f"Tickets cached with TTL {CACHE_TTL['recent_tickets']} seconds")
            return tickets_data, "api_call"
        else:
            # API call failed - return empty list with API error status
            logger.error("Failed to fetch tickets from API - returning empty list")
            return [], "api_error"
    except Exception as e:
        logger.error(f"Unexpected error during ticket fetch: {e}")
        return [], "error"

def fetch_tickets_from_api(count: int = 10) -> list:
    """Fetch tickets directly from Zendesk API"""
    try:
        url = f"https://{BASE_DOMAIN}/api/v2/tickets.json?sort_by=created_at&sort_order=desc"
        headers = {"Content-Type": "application/json"}
        response = requests.get(url, auth=auth, headers=headers, timeout=30)

        if response.status_code == 200:
            tickets_data = response.json()
            tickets = tickets_data.get('tickets', [])[:count]

            # Enrich tickets with user data
            tickets = enrich_tickets_with_users(tickets)
            logger.info(f"Successfully fetched {len(tickets)} tickets from API")
            return tickets
        else:
            logger.error(f"Zendesk API error: {response.status_code} - {response.text}")
            return []
    except requests.RequestException as e:
        logger.error(f"Error fetching tickets from API: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching tickets: {e}")
        return []

def enrich_tickets_with_users(tickets: list) -> list:
    """Enrich tickets with user data from cache or API"""
    if not tickets:
        return tickets

    # Extract unique user IDs
    user_ids = set()
    for ticket in tickets:
        if ticket.get('requester_id'):
            user_ids.add(ticket['requester_id'])
        if ticket.get('assignee_id'):
            user_ids.add(ticket['assignee_id'])

    if not user_ids:
        return tickets

    # Try cache first for user data
    user_cache_key = redis_cache.generate_cache_key("zendesk:users", {"ids": sorted(user_ids)})
    cached_users = redis_cache.get_deserialized(user_cache_key)

    if cached_users:
        users_data = cached_users
        logger.info("User data cache hit")
    else:
        # Fetch from API if not in cache
        users_data = fetch_users_from_api(user_ids)
        if users_data:
            redis_cache.set_serialized(user_cache_key, users_data, CACHE_TTL['user_data'])

    # Enrich tickets with user names
    ny_timezone = timezone(timedelta(hours=-4))
    for ticket in tickets:
        # Format timestamps
        created_at = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))
        created_at_ny = created_at.astimezone(ny_timezone)
        ticket['created_at_formatted'] = created_at_ny.strftime('%Y-%m-%d %H:%M:%S EST')

        if ticket.get('updated_at'):
            updated_at = datetime.fromisoformat(ticket['updated_at'].replace('Z', '+00:00'))
            updated_at_ny = updated_at.astimezone(ny_timezone)
            ticket['updated_at_formatted'] = updated_at_ny.strftime('%Y-%m-%d %H:%M:%S EST')

        # Add user names
        ticket['requester_name'] = users_data.get(ticket.get('requester_id'), 'Unknown')
        ticket['assignee_name'] = users_data.get(ticket.get('assignee_id'), 'Unassigned')

        # Truncate descriptions
        if ticket.get('subject'):
            ticket['subject_truncated'] = ticket['subject'][:60] + ('...' if len(ticket.get('subject', '')) > 60 else '')
        else:
            ticket['subject_truncated'] = 'No subject'

        if ticket.get('description'):
            ticket['description_truncated'] = ticket['description'][:120] + ('...' if len(ticket.get('description', '')) > 120 else '')
        else:
            ticket['description_truncated'] = 'No description'

    return tickets

def fetch_users_from_api(user_ids: set) -> dict:
    """Fetch user data from Zendesk API"""
    try:
        user_url = f"https://{BASE_DOMAIN}/api/v2/users/show_many.json?ids={','.join(map(str, user_ids))}"
        headers = {"Content-Type": "application/json"}
        user_response = requests.get(user_url, auth=auth, headers=headers, timeout=15)

        users_data = {}
        if user_response.status_code == 200:
            users = user_response.json().get('users', [])
            for user in users:
                users_data[user['id']] = user['name']
            logger.info(f"Successfully fetched {len(users_data)} users from API")
        else:
            logger.warning(f"Failed to fetch users: {user_response.status_code}")

        return users_data
    except Exception as e:
        logger.error(f"Error fetching users from API: {e}")
        return {}

# ---------- Existing index route with cache buster ----------
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
            # Use Redis cached ticket fetching
            recent_tickets, cache_status = get_recent_tickets_with_cache(10)

            if not recent_tickets:
                if cache_status == "redis_down":
                    tickets_error = "Redis cache is unavailable - tickets temporarily unavailable"
                elif cache_status == "api_error":
                    tickets_error = "Zendesk API temporarily unavailable - please try again later"
                elif cache_status == "error":
                    tickets_error = "Unexpected error loading tickets"
                else:
                    tickets_error = "No tickets found - please check API configuration"
            else:
                tickets_error = None  # Clear any previous error

            logger.info(f"Tickets loaded - status: {cache_status} | count: {len(recent_tickets)}")

        except Exception as e:
            tickets_error = f"Unexpected error loading tickets: {str(e)}"
            logger.error(f"Ticket loading error: {e}")
            recent_tickets = []
            cache_status = "error"

    return render_template(
        'index.html',
        zendesk_domain=zendesk_domain,
        zendesk_user=zendesk_user,
        api_key_status=api_key_status,
        config_status=config_status,
        recent_tickets=recent_tickets,
        tickets_error=tickets_error,
        cache_status='cache_hit',  # Add cache status for monitoring
        cache_buster=get_cache_buster(),
        redis_health="connected" if redis_cache.is_connected() else "disconnected"
    )

# ---------- Redis Health Check ----------
@app.route('/redis-health')
def redis_health():
    """Redis health and performance metrics endpoint"""
    try:
        redis_connected = redis_cache.is_connected()
        cache_hit_rate = redis_cache.get_cache_hit_rate()

        health_data = {
            "status": "healthy",
            "redis_connected": redis_connected,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "service": "zendesk-redis-cache",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if redis_connected:
            try:
                # Get detailed Redis info
                info = redis_cache._redis_client.info()
                health_data.update({
                    "redis_version": info.get("redis_version", "unknown"),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                })
            except:
                pass

        return jsonify(health_data), 200

    except Exception as e:
        logger.error(f"Redis health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "redis_connected": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

# ---------- Cache Warming ----------
def warm_cache_task():
    """Background task to warm up cache with frequently accessed data"""
    try:
        logger.info("Starting cache warming task...")
        # Warm up recent tickets cache
        tickets, _ = get_recent_tickets_with_cache(10)
        logger.info(f"Cache warming: Loaded {len(tickets)} tickets")

        # Try to warm up any cached user data
        if tickets and redis_cache.is_connected():
            logger.info("Cache warming completed successfully")
        else:
            logger.warning("Cache warming completed but Redis is not connected")

    except Exception as e:
        logger.error(f"Cache warming error: {e}")

@app.route('/warm-cache')
def trigger_cache_warming():
    """Endpoint to trigger manual cache warming"""
    try:
        warm_cache_task()
        return jsonify({
            "status": "success",
            "message": "Cache warming triggered",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Cache warming trigger error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

# ---------- Ticket Comments ----------
def get_ticket_comments_with_cache(ticket_id: int) -> tuple[list, str]:
    """Fetch ticket comments with Redis caching"""
    cache_key = CACHE_KEY_PATTERNS['ticket_comments'].format(ticket_id=ticket_id)

    # Try to get from cache first
    try:
        cached_comments = redis_cache.get_deserialized(cache_key)
        if cached_comments:
            logger.info(f"Comments cache hit for ticket {ticket_id}")
            return cached_comments, "cache_hit"
    except Exception as e:
        logger.warning(f"Error reading comments from cache for ticket {ticket_id}: {e}")

    # If not in cache, fetch from API
    logger.info(f"Comments cache miss for ticket {ticket_id} - fetching from Zendesk API")
    comments_data = fetch_comments_from_api(ticket_id)

    if comments_data:
        # Cache the data for future use
        redis_cache.set_serialized(cache_key, comments_data, CACHE_TTL['ticket_comments'])
        logger.info(f"Comments cached with TTL {CACHE_TTL['ticket_comments']} seconds for ticket {ticket_id}")

    return comments_data, "api_call"

def fetch_comments_from_api(ticket_id: int) -> list:
    """Fetch ticket comments from Zendesk API"""
    try:
        url = f"https://{BASE_DOMAIN}/api/v2/tickets/{ticket_id}/comments.json"
        headers = {"Content-Type": "application/json"}
        response = requests.get(url, auth=auth, headers=headers, timeout=30)

        if response.status_code == 200:
            comments_data = response.json()
            comments = comments_data.get('comments', [])

            # Format timestamps for comments
            ny_timezone = timezone(timedelta(hours=-4))
            for comment in comments:
                created_at = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                created_at_ny = created_at.astimezone(ny_timezone)
                comment['created_at_formatted'] = created_at_ny.strftime('%Y-%m-%d %H:%M:%S EST')

                if comment.get('author_id'):
                    # Try to get user name from cache during enrichment
                    author_name = get_user_name(comment['author_id'])
                    comment['author_name'] = author_name

            logger.info(f"Successfully fetched {len(comments)} comments for ticket {ticket_id}")
            return comments
        else:
            logger.error(f"Zendesk API error: {response.status_code} - {response.text}")
            return []
    except requests.RequestException as e:
        logger.error(f"Error fetching comments from API for ticket {ticket_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching comments for ticket {ticket_id}: {e}")
        return []

def get_user_name(user_id: int) -> str:
    """Get user name from cache or API"""
    # Try cache first for batch user data
    user_cache_key = redis_cache.generate_cache_key("zendesk:users:individual", {"id": user_id})
    cached_name = redis_cache.get_deserialized(user_cache_key)

    if cached_name:
        return cached_name

    # If not in cache, make individual API call
    try:
        url = f"https://{BASE_DOMAIN}/api/v2/users/{user_id}.json"
        headers = {"Content-Type": "application/json"}
        response = requests.get(url, auth=auth, headers=headers, timeout=15)

        if response.status_code == 200:
            user_data = response.json()
            user_name = user_data.get('user', {}).get('name', 'Unknown')

            # Cache the individual user name
            redis_cache.set_serialized(user_cache_key, user_name, CACHE_TTL['user_data'])
            return user_name
        else:
            logger.warning(f"Failed to fetch user {user_id}: {response.status_code}")
            return 'Unknown'
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return 'Unknown'

@app.route('/api/ticket/<ticket_id>/comments')
def get_ticket_comments(ticket_id):
    """API endpoint to fetch ticket comments with caching"""
    try:
        ticket_id_int = int(ticket_id)
        comments, cache_status = get_ticket_comments_with_cache(ticket_id_int)

        return jsonify({
            "ticket_id": ticket_id_int,
            "comments": comments,
            "count": len(comments),
            "cache_status": cache_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    except ValueError:
        return jsonify({
            "error": "Invalid ticket ID",
            "ticket_id": ticket_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 400

    except Exception as e:
        logger.error(f"Error fetching comments for ticket {ticket_id}: {e}")
        return jsonify({
            "error": str(e),
            "ticket_id": ticket_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

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

# ---------- Webhook with Cache Invalidation and Rate Limiting ----------
@app.route('/zendesk-webhook', methods=['POST'])
def handle_zendesk_webhook():
    """Handle Zendesk webhook with rate limiting and cache invalidation"""
    try:
        # Implement basic rate limiting per IP
        client_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
        rate_limit_key = CACHE_KEY_PATTERNS['webhook_rate_limit'].format(identifier=client_ip)

        # Check rate limit
        try:
            current_requests = redis_cache.get_deserialized(rate_limit_key) or 0
            if current_requests >= 30:  # Max 30 requests per minute per IP
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({"message": "Rate limit exceeded"}), 429

            # Increment rate limit counter
            redis_cache.set_serialized(rate_limit_key, current_requests + 1, CACHE_TTL['webhook_rate_limit'])
        except Exception as e:
            logger.warning(f"Rate limiting check failed: {e}")

        # Parse webhook data
        webhook_data = request.get_json()

        if not webhook_data or 'ticket' not in webhook_data:
            return jsonify({"message": "Invalid webhook data format"}), 400

        ticket_data = webhook_data['ticket']
        ticket_id = ticket_data.get('id')

        logger.info(f"Webhook received for ticket {ticket_id} from IP {client_ip}")

        # Invalidate cache and warm it with new data
        try:
            # Invalidate relevant caches
            invalidate_ticket_caches(ticket_id)
        except Exception as e:
            logger.error(f"Error during cache invalidation: {e}")

        logger.info(f"Successfully processed webhook for ticket {ticket_id}")
        return jsonify({"message": "Webhook received and cache invalidated successfully", "ticket_id": ticket_id}), 200

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"message": "Unexpected error processing webhook"}), 500

# ---------- KPI: ticket counts with pagination ----------
def get_ticket_counts_cached(start_date: str, end_date: str) -> tuple:
    """Get ticket counts with Redis caching"""
    cache_key = CACHE_KEY_PATTERNS['dashboard_stats'].format(date_range=f"{start_date}_{end_date}")

    # Try to get from cache first
    try:
        cached_stats = redis_cache.get_deserialized(cache_key)
        if cached_stats:
            logger.info(f"Dashboard KPI cache hit for {start_date} to {end_date}")
            return cached_stats, "cache_hit"
    except Exception as e:
        logger.warning(f"Error reading dashboard cache: {e}")

    # If not in cache, fetch fresh data
    stats, status_code = get_ticket_counts_original(start_date, end_date)

    if stats and not isinstance(stats, dict) or (isinstance(stats, dict) and "error" not in stats):
        redis_cache.set_serialized(cache_key, stats, CACHE_TTL['dashboard_stats'])
        logger.info(f"Dashboard KPI cached with TTL {CACHE_TTL['dashboard_stats']} seconds")

    return stats, "api_call"

def get_ticket_counts_original(start_date: str, end_date: str):
    if not (BASE_DOMAIN and auth):
        return {"error": "Zendesk not configured"}, 0

    headers = {'Content-Type': 'application/json'}

    try:
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

# ---------- Cache Invalidation ----------
def invalidate_ticket_caches(ticket_id: int = None):
    """Invalidate relevant caches when tickets are updated"""
    try:
        # Invalidate recent tickets cache
        redis_cache.delete(CACHE_KEY_PATTERNS['recent_tickets'].format(count=10))

        # Invalidate ticket comments cache if specific ticket is provided
        if ticket_id:
            redis_cache.delete(CACHE_KEY_PATTERNS['ticket_comments'].format(ticket_id=ticket_id))

        # Invalidate dashboard statistics for current month and date ranges
        today = date.today()
        current_month_start = date(today.year, today.month, 1).isoformat()
        current_date_end = today.isoformat()
        redis_cache.delete(CACHE_KEY_PATTERNS['dashboard_stats'].format(date_range=f"{current_month_start}_{current_date_end}"))

        logger.info(f"Cache invalidation completed for ticket {ticket_id if ticket_id else 'all tickets'}")
    except Exception as e:
        logger.error(f"Error during cache invalidation: {e}")

# ---------- Dashboard route with cache buster ----------
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
    cache_status = 'local_cache'

    if request.method == 'POST':
        start_date = request.form.get('start_date') or default_start
        end_date = request.form.get('end_date') or default_end
    else:
        start_date = default_start
        end_date = default_end

    # Use cached version of ticket counts
    stats, result_status = get_ticket_counts_cached(start_date, end_date)
    if result_status == "cache_hit":
        cache_status = 'cache_hit'
    else:
        cache_status = 'api_call'

    if isinstance(stats, dict) and stats.get("error"):
        error = stats["error"]
    elif isinstance(stats, dict) and stats.get("status_code") != 200:
        error = f"Zendesk API returned status {stats.get('status_code', 0)}"
    
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

        open_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        pending_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        solved_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        new_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        on_hold_tickets.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        
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
                           closed_perc=closed_perc,
                           new_perc=new_perc,
                           on_hold_perc=on_hold_perc,
                           solved_perc=solved_perc,
                           zendesk_domain=BASE_DOMAIN,
                           cache_buster=get_cache_buster())  # Add cache buster

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)