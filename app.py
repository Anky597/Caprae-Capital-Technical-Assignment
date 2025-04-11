# app.py
import logging
import os
import sys
from flask import Flask, request, jsonify
# Remove unused imports if any
# from google.api_core.gapic_v1 import method, method_async

try:
    from analysis_workflow import run_analysis_task
    # Import the custom JSON provider
    from utils.json_provider import CustomJSONProvider # Corrected import path
except ImportError as e:
     print(f"CRITICAL ERROR: Failed to import necessary modules: {e}", file=sys.stderr)
     print("Ensure you are running from the 'caprae_robust_scraper' directory and all modules exist.", file=sys.stderr)
     sys.exit(1)
# Remove the old CustomJSONEncoder import if it exists
# from utils.json_encoder import CustomJSONEncoder # Remove this line

# Add this near the top of your app.py file
from flask_cors import CORS

# Add this after creating your Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- Use the Custom JSON Provider ---
app.json = CustomJSONProvider(app)
# --- End Custom JSON Provider Setup ---

# Remove the old encoder assignment if it exists
# app.json_encoder = CustomJSONEncoder # Remove this line

CORS(app)

app_logger = logging.getLogger('flask.app')

# --- API Endpoints (/analyze, /health, /) remain the same ---
@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    app_logger.info(f"Received /analyze request from {request.remote_addr}")
    if not request.is_json:
        app_logger.warning("Request aborted: Not a JSON request.")
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    url = data.get('url')
    company_name = data.get('company_name')
    location = data.get('location')
    use_dynamic = data.get('dynamic_main', False)
    if not url or not company_name:
        app_logger.warning(f"Request aborted: Missing required fields.")
        return jsonify({"error": "Missing required fields: 'url' and 'company_name'"}), 400
    if not isinstance(url, str) or not isinstance(company_name, str) or \
       (location is not None and not isinstance(location, str)) or \
       not isinstance(use_dynamic, bool):
        return jsonify({"error": "Invalid data types for input fields"}), 400

    app_logger.info(f"Analysis request valid. Triggering task for '{company_name}'...")
    try:
        success, result_data = run_analysis_task(
            start_url=url,
            company_name=company_name,
            location=location,
            dynamic_main_page=use_dynamic
        )
        if success:
            app_logger.info(f"Analysis task completed successfully for '{company_name}'.")
            # result_data should be a dict containing Pydantic models or basic types
            # jsonify will now use CustomJSONProvider to handle serialization
            return jsonify(result_data), 200
        else:
            app_logger.error(f"Analysis task failed for '{company_name}'. Error: {result_data.get('error', 'Unknown internal error')}")
            return jsonify(result_data), 500 # Return error dict directly
    except Exception as e:
        app_logger.exception(f"Unexpected critical error during analysis task execution for '{company_name}'.")
        return jsonify({"error": f"An unexpected internal server error occurred: {e}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Keep the root route for basic info/testing
@app.route('/', methods=['GET'])
def func():
    app_logger.info("Root route accessed.")
    return jsonify({
        "message": "Caprae Robust Scraper & Analyzer API is running.",
        "available_routes": {
            "GET": ["/health", "/"],
            "POST": ["/analyze (Requires JSON body)"]
        },
        "note": "POST /analyze is a long-running, blocking task."
    })

# --- Main Execution Block (remains the same) ---
if __name__ == '__main__':
    flask_log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level_numeric = getattr(logging, flask_log_level_str, logging.INFO)
    # Set levels for Flask app logger and root logger
    app_logger.setLevel(log_level_numeric)
    logging.getLogger().setLevel(log_level_numeric)
    # Set handler levels too
    for handler in logging.getLogger().handlers:
        handler.setLevel(log_level_numeric)

    port = int(os.environ.get("PORT", 7860)) # Use 7860 for HF consistency
    app_logger.info(f"Starting Flask development server on host 0.0.0.0, port {port}")
    # Use debug=False for production-like testing, True for development reloading
    app.run(host='0.0.0.0', port=port, debug=False)