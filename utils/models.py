# utils/models.py
from pydantic import BaseModel, Field, HttpUrl, field_validator, ValidationError
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# --- Existing Models (ScrapedPage, TechnologyInfo, ReviewSnippet, LeadershipInfo) ---
class ScrapedPage(BaseModel):
    url: HttpUrl
    scrape_timestamp: datetime = Field(default_factory=datetime.now)
    success: bool
    is_dynamic_scrape: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_headings: List[str] = Field(default_factory=list)
    paragraphs: List[str] = Field(default_factory=list)
    raw_html_snippet: Optional[str] = None # Excluded from final JSON by default in main.py

    @property
    def url_str(self) -> str:
        return str(self.url)

class TechnologyInfo(BaseModel):
    guessed_technologies: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ReviewSnippet(BaseModel):
    title: str
    link: HttpUrl
    source_site: str
    query_used: Optional[str] = None

    @property
    def link_str(self) -> str:
        return str(self.link)

class LeadershipInfo(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    bio_snippet: Optional[str] = None
    source_url: str

# --- Existing AnalyzedSiteData (No changes needed here) ---
class AnalyzedSiteData(BaseModel):
    input_url: HttpUrl
    input_company_name: str
    input_location: Optional[str] = None
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    main_page: Optional[ScrapedPage] = None
    discovered_pages: Dict[str, List[HttpUrl]] = Field(default_factory=dict)
    scraped_subpages: Dict[str, List[ScrapedPage]] = Field(default_factory=dict)
    leadership_team: List[LeadershipInfo] = Field(default_factory=list)
    technology_info: Optional[TechnologyInfo] = None
    review_snippets: List[ReviewSnippet] = Field(default_factory=list)
    overall_errors: List[str] = Field(default_factory=list)

    model_config = { "arbitrary_types_allowed": True }

    @property
    def input_url_str(self) -> str:
        return str(self.input_url)


# --- NEW: Models for LLM Analysis Output Structure ---

class SWOTAnalysis(BaseModel):
    """Structure for SWOT analysis results."""
    strengths: List[str] = Field(default_factory=list, description="Strengths identified from text")
    weaknesses: List[str] = Field(default_factory=list, description="Weaknesses identified from text")
    opportunities: List[str] = Field(default_factory=list, description="Opportunities identified from text")
    threats: List[str] = Field(default_factory=list, description="Threats identified from text")

class LLMAnalysisResult(BaseModel):
    """Defines the expected structure of the combined LLM analysis output."""
    swot_analysis: Optional[SWOTAnalysis] = None
    potential_transformation_angles: List[str] = Field(default_factory=list, description="High-level transformation ideas Caprae might explore")
    key_executives_found: List[Dict[str, str]] = Field(default_factory=list, description="List of {'name': Name, 'title': Title} for key execs")
    career_page_themes: List[str] = Field(default_factory=list, description="Recurring themes from careers content")
    potential_contact_points: List[str] = Field(default_factory=list, description="Suggested roles/departments for outreach")
    explicit_mna_funding_mentions: List[str] = Field(default_factory=list, description="Direct mentions of M&A or funding from news")
    technology_flags: List[str] = Field(default_factory=list, description="Potential flags from guessed tech stack (with caveat)")
    review_site_presence: str = Field(default="", description="Summary of presence on review sites")
    data_completeness_notes: List[str] = Field(default_factory=list, description="Notes on missing data based on scraping errors")
    speculation_caveat: str = Field(default="Analysis is preliminary, based on limited public data, and includes speculation. Financials and internal operations are unknown.", description="Mandatory caveat")
    error: Optional[str] = None # Field to store errors during LLM processing/validation

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Union['LLMAnalysisResult', Dict[str, Any]]:
        """Attempts to create model from dict, returns error dict on failure."""
        try:
            # Map potentially missing keys explicitly if needed, or rely on defaults
            # Pydantic V2 handles optional fields well if they are missing in the input dict
            return cls(**data)
        except ValidationError as e:
            logging.error(f"Pydantic validation failed for LLM analysis result: {e}")
            # Return a dictionary indicating validation error
            return {"error": f"LLM output validation failed: {e}", "raw_response_dict": data}
        except Exception as e:
             logging.error(f"Unexpected error creating LLMAnalysisResult model: {e}")
             return {"error": f"Unexpected model creation error: {e}", "raw_response_dict": data}