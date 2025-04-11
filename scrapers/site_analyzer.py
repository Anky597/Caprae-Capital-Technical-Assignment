# scrapers/site_analyzer.py
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, List, Set, Optional

from utils import helpers, config
from utils.models import HttpUrl # Ensure HttpUrl is imported

class SiteAnalyzer:
    """Finds relevant internal pages within a website based on keywords, using full HTML."""

    def __init__(self, base_url: str):
        try:
            self.base_url = str(HttpUrl(base_url))
            self.base_domain = urlparse(self.base_url).netloc.replace('www.', '')
            if not self.base_domain: raise ValueError("Could not extract domain")
            self.processed_urls: Set[str] = set()
            logging.info(f"SiteAnalyzer initialized for: {self.base_url}")
        except Exception as e:
            logging.error(f"Failed to initialize SiteAnalyzer with base URL '{base_url}': {e}")
            raise ValueError(f"Invalid base URL for SiteAnalyzer: {base_url}") from e

    # --- MODIFIED FUNCTION ---
    def find_relevant_pages(self, full_html_content: Optional[str]) -> Dict[str, List[HttpUrl]]:
        """
        Parses full HTML content to find internal links matching configured keywords.

        Args:
            full_html_content: The raw, full HTML content of the page to analyze.

        Returns:
            A dictionary mapping page categories (e.g., 'about', 'careers')
            to a list of found absolute, validated URLs (HttpUrl models).
        """
        # Initialize with empty lists for all configured categories
        categorized_links: Dict[str, List[HttpUrl]] = {cat: [] for cat in config.PAGE_KEYWORDS}

        if not full_html_content:
            logging.warning(f"Cannot find relevant pages on {self.base_url}: HTML content empty.")
            return categorized_links

        try:
            soup = BeautifulSoup(full_html_content, 'lxml')
        except Exception as e:
            logging.warning(f"lxml parsing failed for {self.base_url}, trying html.parser: {e}")
            try:
                 soup = BeautifulSoup(full_html_content, 'html.parser')
            except Exception as e_html:
                 logging.error(f"Failed to parse HTML content for link finding on {self.base_url}: {e_html}")
                 return categorized_links

        logging.info(f"Analyzing links on {self.base_url}...")
        link_count = 0
        processed_link_tags = 0

        for link_tag in soup.find_all('a', href=True):
            processed_link_tags += 1
            href = link_tag.get('href')
            if not isinstance(href, str) or not href.strip(): continue
            href = href.strip()
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')): continue

            absolute_url_str = helpers.resolve_url(self.base_url, href)
            if not absolute_url_str: continue
            if not helpers.is_internal_link(self.base_url, absolute_url_str): continue
            if absolute_url_str in self.processed_urls: continue

            link_text = helpers.clean_text(link_tag.get_text()).lower()
            url_path = urlparse(absolute_url_str).path.lower() or "/"
            matched_category = None

            for category, keywords in config.PAGE_KEYWORDS.items():
                if len(categorized_links[category]) >= config.MAX_PAGES_PER_CATEGORY: continue

                for keyword in keywords:
                    match = (
                        keyword in link_text or
                        (f'/{keyword}/' in url_path + '/') or
                        (url_path.endswith(f'/{keyword}')) or
                        (f'/{keyword}.' in url_path) or
                        (f'-{keyword}' in url_path) or
                        (url_path == f'/{keyword}')
                    )
                    if match:
                        try:
                            # --- FIX: Append validated HttpUrl directly ---
                            pydantic_url = HttpUrl(absolute_url_str)
                            categorized_links[category].append(pydantic_url)
                            # --- END FIX ---
                            self.processed_urls.add(absolute_url_str)
                            matched_category = category
                            link_count += 1
                            logging.debug(f"Found '{category}' link: {absolute_url_str}")
                            break # Stop checking keywords for this link
                        except Exception as p_err:
                            logging.warning(f"URL validation failed for '{absolute_url_str}': {p_err}")
                            self.processed_urls.add(absolute_url_str)
                            matched_category = "invalid"
                            break # Stop checking keywords
                if matched_category: break # Move to next <a> tag

        logging.info(f"Finished analyzing {processed_link_tags} links. Found {link_count} categorized links.")
        return categorized_links # Return the dictionary with lists of HttpUrl
    # --- END MODIFIED FUNCTION ---

    # _find_links_in_sitemap placeholder remains the same