# analysis_workflow.py
import json
import logging
import os
import sys
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple, Any  # Added Any import here

# Import core components
from utils import config, helpers
from utils.models import AnalyzedSiteData, HttpUrl, ScrapedPage, ReviewSnippet, LeadershipInfo, LLMAnalysisResult
from scrapers.url_scraper import UrlScraper
from scrapers.site_analyzer import SiteAnalyzer
from scrapers.tech_analyzer import guess_technologies
from scrapers.review_finder import search_review_sites
from scrapers.leadership_scraper import extract_leadership_info
from llm_analyzer import analyze_with_llm # Assuming llm_analyzer.py exists

# Use logger specific to this module
workflow_logger = logging.getLogger(__name__)

# --- Review Filtering Helper (Copied from previous main.py) ---
def filter_review_snippets(snippets: List[ReviewSnippet], company_name: str) -> List[ReviewSnippet]:
    # ... (Keep the exact same filter_review_snippets function here) ...
    if not snippets: return []
    if not company_name: return snippets
    filtered = []
    name_parts = [part for part in re.split(r'\s+|,|\.|&', company_name.lower()) if len(part) > 2]
    generic_terms = {'inc', 'llc', 'ltd', 'corp', 'corporation', 'group', 'co', 'company'}
    name_parts = [p for p in name_parts if p not in generic_terms]
    name_variations = set(name_parts + [company_name.lower()])
    comparison_keywords = {'vs', 'versus', 'compare', 'alternative', 'competitor'}
    workflow_logger.debug(f"Filtering reviews using name variations: {name_variations}")
    for snippet in snippets:
        title_lower = snippet.title.lower(); link_lower = snippet.link_str.lower()
        text_to_check = title_lower + " " + link_lower
        match_found = False
        for variation in name_variations:
             if re.search(r'\b' + re.escape(variation) + r'\b', text_to_check):
                 match_found = True; break
        is_comparison = any(comp_word in title_lower for comp_word in comparison_keywords)
        if match_found and not is_comparison: filtered.append(snippet)
        elif match_found and is_comparison: logging.debug(f"Filtered out comparison snippet: '{snippet.title}'")
        else: logging.debug(f"Filtered out snippet (no name match): '{snippet.title}'")
    workflow_logger.info(f"Review filtering: Started with {len(snippets)}, kept {len(filtered)} snippets.")
    return filtered

# --- Refactored Main Workflow Function ---
def run_analysis_task(start_url: str,
                      company_name: str,
                      location: Optional[str] = None,
                      dynamic_main_page: bool = False
                     ) -> Tuple[bool, Dict[str, Any]]:
    """
    Orchestrates the scraping and analysis workflow.

    Returns:
        Tuple[bool, Dict]: (success_status, combined_results_dictionary)
                           The dictionary contains 'scrape_analysis' and 'llm_generated_insights' keys.
                           If a fatal error occurs early, success_status is False and dict contains error info.
    """
    try:
        validated_start_url = HttpUrl(start_url)
        start_url_str = str(validated_start_url)
    except Exception as e:
        workflow_logger.error(f"Invalid start URL: {start_url} - {e}", exc_info=True)
        return False, {"error": f"Invalid start URL '{start_url}'."}

    workflow_logger.info(f"--- Starting Analysis Task ---")
    # ... (logging inputs) ...

    analysis_result = AnalyzedSiteData(
        input_url=validated_start_url,
        input_company_name=company_name,
        input_location=location
    )
    url_scraper = UrlScraper()
    try:
        site_analyzer = SiteAnalyzer(start_url_str)
    except ValueError as e:
         workflow_logger.error(f"Failed to initialize SiteAnalyzer: {e}")
         return False, {"error": f"Failed to initialize analyzer with base URL '{start_url_str}'."}

    # --- Step 1: Scrape Main Page ---
    workflow_logger.info("--- Task Step 1: Scraping Main Page ---")
    full_main_page_html: Optional[str] = None
    try:
        main_page_scrape, full_main_page_html = url_scraper.fetch_and_parse(start_url_str, use_dynamic=dynamic_main_page)
        analysis_result.main_page = main_page_scrape
        if not main_page_scrape.success:
            err_msg = f"Main page scrape failed: {main_page_scrape.error_message}"
            workflow_logger.error(err_msg)
            analysis_result.overall_errors.append(err_msg)
        else:
            workflow_logger.info(f"Main page scraped successfully (Final URL: {main_page_scrape.url_str}).")
            if not isinstance(full_main_page_html, str) or len(full_main_page_html) < 100:
                 workflow_logger.warning("Main page scrape success but full HTML content seems missing/short.")
                 full_main_page_html = None
    except Exception as e:
        workflow_logger.exception("Critical error during main page scraping step.")
        err_msg = f"Fatal error during main page scrape: {e}"
        analysis_result.overall_errors.append(err_msg)
        if analysis_result.main_page is None:
             analysis_result.main_page = ScrapedPage(url=validated_start_url, success=False, is_dynamic_scrape=dynamic_main_page, error_message=err_msg)
        full_main_page_html = None

    # --- Step 2: Find Relevant Sub-Pages ---
    workflow_logger.info("--- Task Step 2: Finding Relevant Sub-Pages ---")
    if analysis_result.main_page and analysis_result.main_page.success and full_main_page_html:
        try:
            workflow_logger.info("Analyzing main page full HTML for relevant links...")
            discovered_pages_map = site_analyzer.find_relevant_pages(full_main_page_html)
            analysis_result.discovered_pages = discovered_pages_map # This should now be Dict[str, List[HttpUrl]]
            workflow_logger.info(f"Sub-page link analysis complete. Links found in {len(discovered_pages_map)} categories.")
        except Exception as e:
            workflow_logger.exception("Error during sub-page link finding step.")
            analysis_result.overall_errors.append(f"Error during sub-page link analysis: {e}")
    else:
         workflow_logger.warning("Skipping sub-page discovery: Main page scrape failed or missing full HTML.")
         if analysis_result.main_page:
              analysis_result.overall_errors.append("Sub-page discovery skipped: Main page failed/missing HTML.")

    # --- Step 3: Scrape Sub-Pages & Extract Leadership Info ---
    workflow_logger.info("--- Task Step 3: Scraping Sub-Pages & Extracting Leadership Info ---")
    # ... (Sub-page scraping loop remains the same, using the fixed SiteAnalyzer output) ...
    # It correctly iterates through discovered_pages_map assuming values are List[HttpUrl]
    total_subpages_to_attempt = 0
    unique_urls_to_scrape = set()
    all_potential_urls = []
    leadership_candidates: List[LeadershipInfo] = []
    processed_leadership_people = set()

    for category, urls in analysis_result.discovered_pages.items():
        analysis_result.scraped_subpages[category] = []
        for page_url in urls: # page_url is HttpUrl
             page_url_str = str(page_url)
             if page_url_str not in unique_urls_to_scrape:
                  unique_urls_to_scrape.add(page_url_str)
                  all_potential_urls.append({'url': page_url, 'category': category})

    urls_to_scrape_ordered = all_potential_urls[:config.MAX_TOTAL_SUBPAGES]
    total_subpages_to_attempt = len(urls_to_scrape_ordered)
    workflow_logger.info(f"Attempting to scrape {total_subpages_to_attempt} unique sub-pages (limit: {config.MAX_TOTAL_SUBPAGES})...")
    actual_scraped_count = 0
    for item in urls_to_scrape_ordered:
        page_url: HttpUrl = item['url'] # HttpUrl object
        category: str = item['category']
        page_url_str = str(page_url) # String version

        if len(analysis_result.scraped_subpages.get(category,[])) >= config.MAX_PAGES_PER_CATEGORY:
             workflow_logger.debug(f"Skipping {page_url_str}: Category '{category}' limit reached.")
             continue

        workflow_logger.info(f"  Scraping '{category}' page: {page_url_str}")
        full_sub_page_html: Optional[str] = None
        try:
            time.sleep(config.SUBPAGE_SCRAPE_DELAY_SECONDS)
            sub_page_scrape, full_sub_page_html = url_scraper.fetch_and_parse(page_url_str, use_dynamic=False)
            analysis_result.scraped_subpages.setdefault(category, []).append(sub_page_scrape)
            actual_scraped_count += 1

            if not sub_page_scrape.success:
                 err_msg = f"Sub-page scrape failed ({category} - {page_url_str}): {sub_page_scrape.error_message}"
                 workflow_logger.warning(f"  {err_msg}")
                 analysis_result.overall_errors.append(err_msg)
            else:
                 workflow_logger.debug(f"  Successfully scraped sub-page: {page_url_str}")
                 # Attempt leadership extraction
                 if category in ['about', 'team'] and full_sub_page_html:
                     workflow_logger.info(f"    Attempting leadership extraction from '{category}' page: {page_url_str}")
                     try:
                         extracted_leaders = extract_leadership_info(full_sub_page_html, page_url_str)
                         for leader_dict in extracted_leaders:
                              try:
                                   leader_info = LeadershipInfo(**leader_dict)
                                   leader_key = (leader_info.name, leader_info.title)
                                   if leader_info.name and leader_key not in processed_leadership_people:
                                        leadership_candidates.append(leader_info)
                                        processed_leadership_people.add(leader_key)
                              except Exception as model_val_err:
                                   workflow_logger.warning(f"Validation failed for extracted leader data on {page_url_str}: {model_val_err}")
                     except Exception as leadership_err:
                          workflow_logger.exception(f"    Error during leadership extraction on {page_url_str}")
                          analysis_result.overall_errors.append(f"Leadership extraction error on {page_url_str}: {leadership_err}")
        except Exception as e:
             workflow_logger.exception(f"Critical error scraping sub-page {page_url_str}.")
             err_msg = f"Fatal error scraping sub-page {page_url_str}: {e}"
             analysis_result.overall_errors.append(err_msg)
             fail_record = ScrapedPage(url=page_url, success=False, is_dynamic_scrape=False, error_message=err_msg)
             analysis_result.scraped_subpages.setdefault(category, []).append(fail_record)

    analysis_result.leadership_team = leadership_candidates
    workflow_logger.info(f"Finished sub-page stage. Scraped: {actual_scraped_count}. Found {len(leadership_candidates)} unique leaders.")


    # --- Step 4: Analyze Technology ---
    workflow_logger.info("--- Task Step 4: Guessing Technology Stack ---")
    try:
        tech_info = guess_technologies(start_url_str)
        analysis_result.technology_info = tech_info
        if tech_info and tech_info.error_message:
             workflow_logger.error(f"Tech guess failed: {tech_info.error_message}")
             analysis_result.overall_errors.append(f"Tech guess failed: {tech_info.error_message}")
        else:
             found = bool(tech_info.guessed_technologies if tech_info else False)
             workflow_logger.info(f"Tech analysis complete. Found: {found}")
    except Exception as e:
        workflow_logger.exception("Critical error during technology analysis step.")
        analysis_result.overall_errors.append(f"Fatal error during tech analysis: {e}")

    # --- Step 5: Find & Filter Reviews ---
    workflow_logger.info("--- Task Step 5: Searching and Filtering Reviews ---")
    try:
        raw_review_snippets = search_review_sites(company_name, location)
        filtered_snippets = filter_review_snippets(raw_review_snippets, company_name)
        analysis_result.review_snippets = filtered_snippets
        workflow_logger.info(f"Review search & filter complete. Kept {len(filtered_snippets)} relevant snippets.")
    except Exception as e:
        workflow_logger.exception("Critical error during review finding/filtering step.")
        analysis_result.overall_errors.append(f"Fatal error during review search/filter: {e}")

    # --- Step 5.5: LLM Analysis ---
    workflow_logger.info("--- Task Step 5.5: Performing LLM Analysis ---")
    llm_analysis_result: Union[LLMAnalysisResult, Dict[str, Any]] = {"error": "LLM analysis skipped or failed."}
    try:
        llm_analysis_result = analyze_with_llm(analysis_result)
        if isinstance(llm_analysis_result, dict) and "error" in llm_analysis_result:
             workflow_logger.error(f"LLM Analysis failed: {llm_analysis_result.get('error')}")
             analysis_result.overall_errors.append(f"LLM Analysis Failed: {llm_analysis_result.get('error')}")
        else:
             workflow_logger.info("LLM Analysis completed.")
    except Exception as e:
        workflow_logger.exception("Critical error calling LLM analysis.")
        err_msg = f"Fatal error during LLM Analysis step: {e}"
        analysis_result.overall_errors.append(err_msg)
        llm_analysis_result = {"error": err_msg}

    # --- Step 6: Combine Results & Prepare Return Value ---
    workflow_logger.info("--- Task Step 6: Combining Results ---")
    analysis_result.analysis_timestamp = datetime.now() # Final timestamp

    final_output_data = {
        "scrape_analysis": analysis_result.model_dump(
            exclude={'main_page': {'raw_html_snippet'},
                     'scraped_subpages': {'__all__': {'raw_html_snippet'}}}
        ),
        "llm_generated_insights": llm_analysis_result.model_dump() if isinstance(llm_analysis_result, LLMAnalysisResult) else llm_analysis_result
    }

    # --- Step 7: Save Combined Output (Optional but recommended for persistence) ---
    try:
        safe_company_name = "".join(c if c.isalnum() else '_' for c in company_name[:50]).strip('_') or "unknown"
        location_suffix = ""
        if location:
             safe_loc = "".join(c if c.isalnum() else '_' for c in location[:20]).strip('_')
             if safe_loc: location_suffix = f"_{safe_loc}"
        ts = analysis_result.analysis_timestamp.strftime('%Y%m%d%H%M%S')
        output_filename = os.path.join(config.OUTPUT_DIR, f"{safe_company_name}{location_suffix}_analysis_{ts}.json")
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(final_output_data, f, indent=2, default=str)
        workflow_logger.info(f"Combined analysis results saved to: {output_filename}")
    except Exception as e:
        workflow_logger.exception(f"CRITICAL: Failed to write combined output file")
        # Append error but don't necessarily fail the whole return
        final_output_data.setdefault("scrape_analysis", {}).setdefault("overall_errors", []).append(f"Fatal Error: Could not save output JSON: {e}")


    # --- Return results ---
    # Determine overall success based on critical steps (e.g., main page scrape)
    overall_success = analysis_result.main_page is not None and analysis_result.main_page.success
    workflow_logger.info(f"--- Analysis Task Finished (Success: {overall_success}) ---")
    return overall_success, final_output_data

# Note: The if __name__ == "__main__": block is REMOVED from this file.
# Execution is now handled by the Flask app (app.py).