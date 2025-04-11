export interface CompanyAnalysis {
  scrape_analysis: {
    input_url: string;
    input_company_name: string;
    input_location: string;
    analysis_timestamp: string;
    main_page: {
      url: string;
      title: string;
      meta_description: string;
      h1_headings: string[];
      paragraphs: string[];
    };
    leadership_team: any[];
    technology_info: {
      guessed_technologies: Record<string, string[]>;
      error_message: string | null;
    };
    review_snippets: any[];
    overall_errors: string[];
  };
  llm_generated_insights: {
    swot_analysis: {
      strengths: string[];
      weaknesses: string[];
      opportunities: string[];
      threats: string[];
    };
    potential_transformation_angles: string[];
    key_executives_found: Array<{
      name: string;
      title: string;
    }>;
    career_page_themes: string[];
    potential_contact_points: string[];
    explicit_mna_funding_mentions: string[];
    technology_flags: string[];
    review_site_presence: string;
    data_completeness_notes: string[];
    speculation_caveat: string;
    error: string | null;
  };
}