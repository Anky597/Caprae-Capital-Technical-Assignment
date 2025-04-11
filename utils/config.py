# utils/config.py
import random

# --- Scraping Behavior ---
DEFAULT_TIMEOUT = 25 # Seconds for requests/page loads
REQUEST_DELAY_SECONDS = 1.5 # Base delay between HTTP requests to the *same* domain
SUBPAGE_SCRAPE_DELAY_SECONDS = 2.0 # Delay before scraping each discovered sub-page
SELENIUM_DYNAMIC_WAIT_SECONDS = 7 # Default wait time for JS rendering in Selenium
MAX_RETRIES = 2 # Number of retries for failed requests (timeouts, 5xx errors)
RETRY_DELAY_SECONDS = 3 # Delay before retrying a failed request

# --- User Agents ---
# Add more diverse and common User Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
]

def get_random_user_agent():
    """Returns a randomly chosen User-Agent string."""
    return random.choice(USER_AGENTS)

# --- Page Discovery ---
# Keywords to identify relevant pages (lowercase)
# Categories help organize the output
PAGE_KEYWORDS = {
    'about': ['about', 'about us', 'company', 'who we are', 'overview'],
    'team': ['team', 'management', 'leadership', 'founders', 'board'],
    'careers': ['careers', 'jobs', 'hiring', 'work with us', 'opportunities'],
    'product_services': ['product', 'service', 'solution', 'platform', 'technology', 'features', 'pricing'],
    'press_news': ['press', 'news', 'media', 'announcements', 'blog', 'updates', 'releases'],
    'contact': ['contact', 'contact us', 'support', 'get in touch', 'locations'],
    'investors': ['investor relations', 'investors', 'ir', 'financials', 'sec filings'],
    # Add more categories/keywords as needed (e.g., 'partners', 'case studies')
}
MAX_PAGES_PER_CATEGORY = 3 # Limit URLs scraped per discovered category
MAX_TOTAL_SUBPAGES = 20 # Overall limit on sub-pages to scrape

# --- Review Finding ---
REVIEW_SITES_CONFIG = {
    # Business software review sites
    'g2': {
        'domain': 'g2.com', 
        'query_suffix': ' "reviews" OR "ratings"',
        'priority': 1,  # Higher priority sites searched first
        'max_results': 4  # More results for high-quality sites
    },
    'capterra': {
        'domain': 'capterra.com', 
        'query_suffix': ' "reviews" OR "alternatives" OR "pricing"',
        'priority': 1,
        'max_results': 4
    },
    'trustpilot': {
        'domain': 'trustpilot.com', 
        'query_suffix': ' "reviews" OR "customer experience"',
        'priority': 2,
        'max_results': 3
    },
    # Employee review sites
    'glassdoor': {
        'domain': 'glassdoor.com', 
        'query_suffix': ' "company reviews" OR "interview reviews" OR "salaries"',
        'priority': 2,
        'max_results': 3
    },
    'indeed': {
        'domain': 'indeed.com', 
        'query_suffix': ' "company reviews" OR "employee reviews"',
        'priority': 3,
        'max_results': 2
    },
    # Additional industry-specific sites
    'gartner': {
        'domain': 'gartner.com', 
        'query_suffix': ' "reviews" OR "magic quadrant" OR "peer insights"',
        'priority': 3,
        'max_results': 2
    }
}

# Default if not specified in individual site config
MAX_REVIEW_RESULTS_PER_SITE = 3  
# Adjust delay between searches to avoid rate limiting
# Increase the delay between requests to avoid rate limiting
REVIEW_SEARCH_DELAY_SECONDS = 5  # Increase from whatever you currently have

# Optional: Add proxy configuration if you have access to proxies
# PROXIES = [
#     "http://proxy1.example.com:8080",
#     "http://proxy2.example.com:8080",
#     "http://proxy3.example.com:8080",
# ]
# Maximum total review results to collect
MAX_TOTAL_REVIEW_RESULTS = 18

# --- Selenium Configuration ---
SELENIUM_OPTIONS = [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    # Consider adding options to disable images/css for faster loads if needed
    # "--blink-settings=imagesEnabled=false"
]

# --- Technology Guessing ---
# (No specific config needed for builtwith currently)

# Add this to the end of your config.py file
import os

# --- Output Configuration ---
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)