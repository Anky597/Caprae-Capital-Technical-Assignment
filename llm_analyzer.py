# llm_analyzer.py
import google.generativeai as genai
import json
import os
import logging
import time  # Add this import
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any, Union

# Import models from the utils package
from utils.models import AnalyzedSiteData, LeadershipInfo, ReviewSnippet, TechnologyInfo, LLMAnalysisResult
from utils import helpers # For clean_text if needed

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Constants ---
MAX_INPUT_TEXT_LENGTH = 20000 # Max characters for combined text inputs to manage token limits
MAX_LEADERSHIP_SUMMARY = 15 # Max number of leaders to list in prompt
MAX_REVIEW_SNIPPETS_SUMMARY = 10 # Max review snippets to list

# --- Load API Key ---
try:
    load_dotenv() # Load environment variables from .env file
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in the .env file.")
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Google Generative AI configured successfully.")
except Exception as e:
     logger.error(f"Failed to configure Google Generative AI: {e}", exc_info=True)
     # Application should likely exit if API key isn't configured
     # For now, functions will return error state if model init fails
     GOOGLE_API_KEY = None # Ensure it's None if setup failed

# --- Gemini Configuration ---
GENERATION_CONFIG = {
    "temperature": 0.4, # Lower temp for more focused, less creative analysis
    "top_p": 0.9,
    "top_k": 30, # Adjust top_k based on desired focus
    "max_output_tokens": 8192, # Use a higher limit for comprehensive analysis (e.g., Gemini 1.5 Flash max)
    "response_mime_type": "application/json", # Request JSON output directly
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Initialize the model (handle potential key error)
try:
    LLM_MODEL = genai.GenerativeModel(
        model_name="gemini-2.5-pro-exp-03-25", # Or "gemini-1.5-pro-latest" for potentially better reasoning
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )
    logger.info(f"Initialized Gemini Model: {LLM_MODEL.model_name}")
except Exception as model_init_error:
     logger.error(f"Failed to initialize Gemini Model: {model_init_error}", exc_info=True)
     LLM_MODEL = None


# --- Helper Functions ---

def _prepare_text_snippet(label: str, text_list: List[str], max_len: int = 500) -> str:
    """Joins and truncates a list of text strings for the prompt."""
    if not text_list: return f"{label}: N/A"
    full_text = ". ".join(filter(None, [helpers.clean_text(t) for t in text_list]))
    truncated = full_text[:max_len]
    if len(full_text) > max_len: truncated += "..."
    return f"{label}:\n{truncated}\n"

def _prepare_leadership_summary(leaders: List[LeadershipInfo]) -> str:
    """Creates a concise summary of the leadership team."""
    if not leaders: return "Leadership Found: None"
    summary = "Leadership Found (Name - Title):\n"
    count = 0
    for leader in leaders:
        if leader.name and leader.title and count < MAX_LEADERSHIP_SUMMARY:
            summary += f"- {leader.name} - {leader.title}\n"
            count += 1
        elif leader.name and count < MAX_LEADERSHIP_SUMMARY: # If title missing
             summary += f"- {leader.name} - (Title not specified)\n"
             count += 1
    if len(leaders) > count:
         summary += f"... (and {len(leaders) - count} others found)\n"
    return summary

def _prepare_review_summary(reviews: List[ReviewSnippet]) -> str:
    """Summarizes review site presence."""
    if not reviews: return "Review Site Presence: No relevant snippets found."
    summary = "Review Site Presence Summary:\n"
    sites_found = set(r.source_site for r in reviews)
    summary += f"- Found relevant links on: {', '.join(sorted(sites_found))}\n"
    summary += f"- Total relevant snippets listed (Top {MAX_REVIEW_SNIPPETS_SUMMARY}):\n"
    for i, review in enumerate(reviews[:MAX_REVIEW_SNIPPETS_SUMMARY]):
         summary += f"  - [{review.source_site}] {review.title}\n"
    if len(reviews) > MAX_REVIEW_SNIPPETS_SUMMARY:
         summary += f"  ... (and {len(reviews) - MAX_REVIEW_SNIPPETS_SUMMARY} more)\n"
    return summary

def _prepare_technology_summary(tech_info: Optional[TechnologyInfo]) -> str:
    """Summarizes guessed technology."""
    if not tech_info or tech_info.error_message:
        return "Technology Guess: Failed or not available."
    if not tech_info.guessed_technologies:
        return "Technology Guess: No specific technologies identified."
    summary = "Technology Guess (Categories Found):\n"
    summary += ", ".join(tech_info.guessed_technologies.keys())
    # Optionally list top few techs per category if needed and space allows
    # for category, techs in tech_info.guessed_technologies.items():
    #     summary += f"- {category}: {', '.join(techs[:3])}{'...' if len(techs) > 3 else ''}\n"
    return summary


# --- Core Analysis Function ---

def analyze_with_llm(scraped_data: AnalyzedSiteData) -> Union[LLMAnalysisResult, Dict[str, Any]]:
    """
    Analyzes scraped data using the Gemini LLM based on a combined prompt.

    Args:
        scraped_data: The AnalyzedSiteData object containing scraping results.

    Returns:
        An LLMAnalysisResult object if successful and validation passes,
        otherwise a dictionary containing error information.
    """
    if not LLM_MODEL:
        logger.error("LLM Model not initialized. Cannot perform analysis.")
        return {"error": "LLM Model not initialized due to configuration error."}

    logger.info(f"--- Starting LLM Analysis for: {scraped_data.input_company_name} ---")
    start_time = time.monotonic()

    # --- 1. Prepare Data Snippets for Prompt ---
    # Combine text from various relevant sections, applying truncation
    combined_text_input = ""

    # Main Page Info
    if scraped_data.main_page and scraped_data.main_page.success:
        combined_text_input += _prepare_text_snippet("Main Page Title", [scraped_data.main_page.title])
        combined_text_input += _prepare_text_snippet("Main Page Description", [scraped_data.main_page.meta_description])
        combined_text_input += _prepare_text_snippet("Main Page Key Paragraphs", scraped_data.main_page.paragraphs[:5], max_len=1500) # Limit paragraphs
    else:
        combined_text_input += "Main Page Info: Scrape failed or no data.\n"

    # Sub-page Content (concatenate paragraphs from successful scrapes)
    for category, pages in scraped_data.scraped_subpages.items():
        cat_paras = [p for page in pages if page.success for p in page.paragraphs]
        if cat_paras:
            combined_text_input += _prepare_text_snippet(f"{category.replace('_',' ').title()} Page Content", cat_paras, max_len=2500) # Larger limit for key sections

    # Truncate combined text if it exceeds overall limit
    if len(combined_text_input) > MAX_INPUT_TEXT_LENGTH:
        logger.warning(f"Combined text input exceeds limit ({MAX_INPUT_TEXT_LENGTH} chars), truncating.")
        combined_text_input = combined_text_input[:MAX_INPUT_TEXT_LENGTH] + "... (truncated)"

    # Prepare other structured inputs
    leadership_summary = _prepare_leadership_summary(scraped_data.leadership_team)
    technology_summary = _prepare_technology_summary(scraped_data.technology_info)
    review_summary = _prepare_review_summary(scraped_data.review_snippets)
    scraping_errors_str = "Scraping Errors Logged: " + (", ".join(scraped_data.overall_errors) if scraped_data.overall_errors else "None")

    # --- 2. Construct the Robust Prompt ---
    # Define the desired JSON structure within the prompt instructions clearly
    prompt = f"""**Role:** You are a Senior Investment Analyst at Caprae Capital, specializing in M&A screening and identifying business transformation opportunities. Your task is to analyze the following scraped website data for '{scraped_data.input_company_name}' ({scraped_data.input_location or 'Location N/A'}). Base your analysis *strictly* on the provided text snippets, mentioning limitations where data is missing or potentially unreliable.

**Provided Scraped Data:**

{combined_text_input}

{leadership_summary}

{technology_summary}
*Caveat: Technology guesses are based on basic library analysis and may be incomplete or inaccurate.*

{review_summary}

{scraping_errors_str}

**Analysis Tasks & Output Structure:**

Analyze the provided data and generate a JSON object containing *only* the following structure. Populate each field based *solely* on the provided text, unless inference is explicitly requested for a specific field:

```json
{{
  "llm_analysis": {{
    "swot_analysis": {{
      "strengths": ["Identify 2-3 key strengths mentioned or clearly implied in the text (e.g., market position claims, positive quotes, unique features mentioned)."],
      "weaknesses": ["Identify 1-2 potential weaknesses *directly implied* by the text (e.g., mentions of migration challenges, complexity complaints in hypothetical quotes - be conservative). If none, state 'None apparent from text'."],
      "opportunities": ["Identify 1-2 potential opportunities suggested by the text (e.g., focus on AI in careers/news, expansion mentions, new product launches)."],
      "threats": ["Identify 1-2 potential threats *directly implied* or mentioned (e.g., competitor comparisons mentioned, reliance on specific partners - be conservative). If none, state 'None apparent from text'."]
    }},
    "potential_transformation_angles": [
      "Based on the company's products, stated goals (if any), and focus areas (e.g., AI, data, specific industries), suggest 1-3 high-level potential business transformation strategies Caprae Capital could explore post-acquisition. *This requires strategic inference.* (Example: 'Accelerate AI product integration based on Voyage AI acquisition and market trends mentioned')."
      ],
    "key_executives_found": [
        {{ "name": "Extract Name", "title": "Extract Title" }}
        // Populate based on the 'Leadership Found' section, listing top roles like CEO, CTO, CRO, CPO etc. if found. Limit to 5 key roles. If none found, provide an empty list.
    ],
    "career_page_themes": [
      "Summarize 2-4 main themes observed in the 'Careers Page Content' snippet (e.g., 'Focus on remote/hybrid work', 'Emphasis on specific technologies like AI/Cloud', 'Rapid growth/hiring', 'Statements on culture/inclusion'). If no careers content, state 'No specific career themes identified from text'."
      ],
    "potential_contact_points": [
      "Based on the company type and potential M&A/strategy focus, suggest 2-3 *types* of roles or departments that would be logical initial points of contact for Caprae Capital. *This requires inference.* (Examples: 'Corporate Development/Strategy', 'Office of the CEO/CFO', 'Head of Partnerships')."
      ],
    "explicit_mna_funding_mentions": [
      "List any direct mentions of acquisitions (made or received), funding rounds, or major strategic investments found in the 'Press News Page Content' snippet. If none, provide an empty list."
      ],
    "technology_flags": [
        "Based *only* on the 'Technology Guess' list, mention any potential flags (e.g., 'Presence of Optimizely suggests focus on A/B testing/web optimization', 'Absence of common backend tech in guess indicates potential incompleteness'). State low confidence. If guess failed or empty, state 'Technology guess unavailable or inconclusive'."
        ],
    "review_site_presence": "Summarize findings from 'Review Site Presence Summary' (e.g., 'Present on G2, Trustpilot, Capterra. Location-specific search attempted.').",
    "data_completeness_notes": [
      "Note any significant limitations based on 'Scraping Errors Logged' or missing key sections (e.g., 'Main page scrape failed', 'Investor relations page not found/scraped', 'Sub-page scraping limited by MAX_TOTAL_SUBPAGES')."
      ],
    "speculation_caveat": "Analysis is preliminary, based on limited public website data scraped at a specific time. It lacks financial data, internal operational details, and comprehensive market context. Strategic inferences are speculative."
  }}
}}
"""

    # --- 3. Call Gemini API ---
    logger.info("Sending combined prompt to Gemini...")
    response_text = None
    llm_error = None
    try:
        # Ensure prompt is a simple string for the API call if needed, or handle parts
        response = LLM_MODEL.generate_content(prompt)
        if response.parts:
            response_text = response.text
            # Basic cleanup
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3].strip()
            elif response_text.strip().startswith("```"):
                response_text = response_text.strip()[3:-3].strip()
            logger.info("Received response from Gemini.")
            logger.debug(f"Gemini raw response snippet: {response_text[:500]}...")
        else:
            block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else 'Unknown'
            safety_ratings = response.prompt_feedback.safety_ratings if response.prompt_feedback else 'N/A'
            logger.warning(f"Gemini response empty or blocked. Reason: {block_reason}. Ratings: {safety_ratings}")
            llm_error = f"Gemini response blocked or empty. Reason: {block_reason}"

    except Exception as e:
        logger.exception(f"Error calling Gemini API: {e}")
        llm_error = f"Gemini API call failed: {e}"

    # --- 4. Parse and Validate Response ---
    analysis_duration = time.monotonic() - start_time
    logger.info(f"LLM analysis attempt finished in {analysis_duration:.2f} seconds.")

    if llm_error:
        return {"error": llm_error}
    if not response_text:
        return {"error": "No text response received from Gemini."}

    try:
        parsed_data = json.loads(response_text)
        # Expecting {"llm_analysis": {...}}
        if "llm_analysis" in parsed_data and isinstance(parsed_data["llm_analysis"], dict):
            analysis_content = parsed_data["llm_analysis"]
            # Validate the extracted content against the Pydantic model
            validated_result = LLMAnalysisResult.from_dict(analysis_content)
            if isinstance(validated_result, LLMAnalysisResult):
                logger.info("LLM response parsed and validated successfully.")
                return validated_result # Return the validated Pydantic object
            else:
                # from_dict returned an error dictionary
                logger.error("LLM response parsed but failed Pydantic validation.")
                return validated_result # Return the error dict from validation
        else:
            logger.error(f"LLM JSON response missing expected 'llm_analysis' key. Found keys: {list(parsed_data.keys())}")
            return {"error": "LLM JSON response structure incorrect.", "raw_response": response_text}

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode Gemini JSON response: {e}. Response snippet: {response_text[:500]}...")
        return {"error": f"Failed to decode JSON response: {e}", "raw_response": response_text}
    except Exception as e:
        logger.exception(f"Unexpected error processing LLM response.")
        return {"error": f"Unexpected error processing LLM response: {e}", "raw_response": response_text}