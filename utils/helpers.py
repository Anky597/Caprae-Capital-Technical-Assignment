# utils/helpers.py
import re
import logging
# Add the missing import
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup, NavigableString, Comment # Import Comment
from typing import Optional, Dict, Any, List

HTML_SNIPPET_LENGTH = 2000 # Max length of raw HTML snippet to store

def clean_text(text: Optional[str]) -> str:
    """Removes excessive whitespace and standardizes text."""
    if not text:
        return ""
    try:
        text = re.sub(r'[\n\t\r]+', ' ', text) # Replace newlines/tabs/CR with space
        text = re.sub(r'\s{2,}', ' ', text)    # Replace multiple spaces with single space
        text = text.strip()
        # Optional: Consider removing unicode non-breaking spaces if they cause issues
        # text = text.replace('\u00a0', ' ')
        return text
    except Exception as e:
        logging.error(f"Error cleaning text snippet: {e}")
        return text if isinstance(text, str) else ""

def extract_page_content(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """
    Extracts key content elements from a BeautifulSoup object, attempting to
    focus on meaningful text and avoid boilerplate.

    Args:
        soup: The BeautifulSoup object representing the parsed HTML.
        url: The URL of the page being parsed (for logging).

    Returns:
        A dictionary containing extracted content elements.
    """
    content = {
        'title': None, 'meta_description': None, 'h1_headings': [], 'paragraphs': [],
        'raw_html_snippet': str(soup)[:HTML_SNIPPET_LENGTH] # Store beginning of HTML
    }
    try:
        # --- Remove Script, Style, Nav, Footer, Header, Aside ---
        # These often contain boilerplate text not relevant for core content analysis
        tags_to_remove = ['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'button']
        # Also remove common cookie/consent banners if possible (requires specific IDs/classes)
        # Example: soup.select_one('#cookie-banner') might work sometimes
        for tag_name in tags_to_remove:
            for tag in soup.find_all(tag_name):
                tag.decompose() # Remove the tag and its content

        # --- Title ---
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            content['title'] = clean_text(title_tag.string)

        # --- Meta Description ---
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_desc_tag and meta_desc_tag.get('content'):
            content['meta_description'] = clean_text(meta_desc_tag.get('content'))
        if not content['meta_description']:
             og_desc_tag = soup.find('meta', property='og:description')
             if og_desc_tag and og_desc_tag.get('content'):
                 content['meta_description'] = clean_text(og_desc_tag.get('content'))

        # --- Headings (H1-H3 for better context) ---
        content['h1_headings'] = [clean_text(tag.get_text()) for tag in soup.find_all('h1') if tag.get_text()]
        # Optionally add H2, H3 if needed:
        # content['h2_headings'] = [clean_text(tag.get_text()) for tag in soup.find_all('h2') if tag.get_text()]
        # content['h3_headings'] = [clean_text(tag.get_text()) for tag in soup.find_all('h3') if tag.get_text()]


        # --- Paragraphs / Main Content Extraction ---
        paragraphs: List[str] = []
        # Try finding a 'main' element or common article containers first
        main_content_area = soup.find('main') or soup.find('article') or soup.select_one('div[role="main"]') or soup.select_one('#content') or soup.select_one('.content') or soup.body # Fallback to body

        if main_content_area:
            potential_texts = set()
            # Find common text-bearing tags within the main area
            text_tags = main_content_area.find_all(['p', 'li', 'div', 'span', 'td']) # Add td for tables if relevant

            # Heuristic filtering criteria
            min_text_length = 50 # Characters
            min_word_count = 5   # Words

            for tag in text_tags:
                # Get text only from this tag, not children with text already processed? Complex.
                # Let's get direct text and clean it
                # Use .find_all(string=True, recursive=False) for direct text? Might miss nested spans.
                # Use .get_text() but be mindful of duplicates from parent tags.

                tag_text = clean_text(tag.get_text(separator=' ', strip=True))

                # Filter based on length and content
                if len(tag_text) >= min_text_length and len(tag_text.split()) >= min_word_count:
                     # Avoid adding if it's just identical to its parent's immediate text?
                     # Simple check: don't add if it contains only whitespace or just child tags
                     if tag.find(recursive=False): # Has child tags
                         if not any(isinstance(c, NavigableString) and clean_text(c) for c in tag.contents):
                             continue # Skip if it only contains children, no direct text

                     # Avoid common boilerplate phrases (very basic example)
                     boilerplate = ['copyright', 'all rights reserved', 'privacy policy', 'terms of use']
                     if any(bp in tag_text.lower() for bp in boilerplate) and len(tag_text) < 150:
                          continue

                     potential_texts.add(tag_text)

            # Post-processing to remove subsets (prioritize longer text)
            sorted_texts = sorted(list(potential_texts), key=len, reverse=True)
            for p in sorted_texts:
                is_subset = False
                for fp in paragraphs: # Check against already added final paragraphs
                    if p in fp:
                        is_subset = True
                        break
                if not is_subset:
                    paragraphs.append(p)
        else:
             logging.warning(f"Could not find main content area for {url}, text extraction might be limited.")


        content['paragraphs'] = paragraphs[:75] # Store more paragraphs if available

    except Exception as e:
        logging.error(f"Error during content extraction for {url}: {e}", exc_info=True)

    return content

def resolve_url(base_url: str, link: str) -> Optional[str]:
    """Resolves a potentially relative URL against a base URL, cleans it."""
    try:
        if not isinstance(link, str): return None
        cleaned_link = urldefrag(link.strip())[0]
        if not cleaned_link: return None
        absolute_url = urljoin(base_url, cleaned_link)
        parsed_abs = urlparse(absolute_url)
        if parsed_abs.scheme in ['http', 'https'] and parsed_abs.netloc:
            return absolute_url
        return None
    except Exception as e:
        logging.warning(f"Could not resolve URL '{link}' against base '{base_url}': {e}")
        return None

def is_internal_link(base_url: str, target_url: str) -> bool:
    """Checks if target_url is on the same domain as base_url, handling www."""
    try:
        base_domain = urlparse(base_url).netloc.replace('www.', '')
        target_domain = urlparse(target_url).netloc.replace('www.', '')
        if not base_domain or not target_domain: return False
        return target_domain == base_domain
    except Exception as e:
        logging.warning(f"Error comparing domains for '{base_url}' and '{target_url}': {e}")
        return False