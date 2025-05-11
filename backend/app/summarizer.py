from pydantic_ai import Agent
import unicodedata
import re
from app.models import (
    LinkedInProfile,
    CompanySummaryWithRating,
    GlassdoorProfile,
    CrunchbaseProfile,
    NewsProfile,
)
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)

summarizer_agent = Agent(
    model="openai:gpt-4o",
    output_type=CompanySummaryWithRating,
    system_prompt=(
        "You are an OSINT analyst who writes honest and useful summaries of companies for job seekers. "
        "Imagine a friend asked you: 'Should I even consider applying here?' "
        "You write in natural, informal language — short, direct, and with a dry sense of humor. "
        "Your job is to quickly describe what the company does, how big it is, how stable it seems, and what kind of experience to expect. "
        "You are allowed to be skeptical if something feels off — say so. "
        "Avoid corporate jargon, fake positivity, or vague statements. "
        "Write 15-20 short sentences max. Be critical when needed. This is for people who value honest, no-bullshit career advice."
        "After the summary, assign a Reputato Score (1 to 5), where 5 is excellent and 1 means 'run away'."
        "If some data sources are missing, focus on what you know and be clear about what information is unavailable."
    ),
)


def clean_summary(text: str) -> str:
    # Normalize Unicode characters (smart quotes, etc.)
    normalized = unicodedata.normalize("NFKC", text)
    replacements = {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",  # en-dash
        "—": "-",  # em-dash
        "…": "...",
    }
    for orig, repl in replacements.items():
        normalized = normalized.replace(orig, repl)

    normalized = normalized.replace("$", "\\$")
    # Remove zero-width and invisible characters
    cleaned = re.sub(r"[\u200B-\u200D\uFEFF]", "", normalized)
    # Collapse extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def format_data_for_prompt(data: Optional[dict], source_name: str) -> str:
    if data is None:
        logger.debug(f"No {source_name} data available")
        return f"No {source_name} data available."
    return f"Here is {source_name} data:\n{json.dumps(data, indent=2)}"


async def summarize_company(
    company_name: str,
    linkedin: Optional[LinkedInProfile],
    glassdoor: Optional[GlassdoorProfile],
    crunchbase: Optional[CrunchbaseProfile],
    news: Optional[NewsProfile],
) -> CompanySummaryWithRating:
    logger.info(f"Starting summary generation for {company_name}")

    linkedin_text = format_data_for_prompt(
        linkedin.model_dump() if linkedin else None, "LinkedIn"
    )
    glassdoor_text = format_data_for_prompt(
        glassdoor.model_dump() if glassdoor else None, "Glassdoor"
    )
    crunchbase_text = format_data_for_prompt(
        crunchbase.model_dump() if crunchbase else None, "Crunchbase"
    )
    news_text = format_data_for_prompt(
        news.model_dump() if news else None, "recent news"
    )

    available_sources = sum(
        1 for x in [linkedin, glassdoor, crunchbase, news] if x is not None
    )
    logger.info(
        f"Generating summary using {available_sources} available data sources for {company_name}"
    )

    prompt = (
        f"You're evaluating a company called '{company_name}' for a curious job seeker.\n\n"
        f"{linkedin_text}\n\n"
        f"{glassdoor_text}\n\n"
        f"{crunchbase_text}\n\n"
        f"{news_text}\n\n"
        "Write honest summary based on these sources:\n"
        "- Say clearly what the company does, how big it is, and where it's located.\n"
        "- Mention the founding year and funding stage (like 'Series C') if available.\n"
        "- Highlight Glassdoor rating and recent pros/cons from employees (from 2025 and 2024 only) if available.\n"
        "- List major known investors by name if available.\n"
        "- Mention key people (especially founders, CTOs, or execs) if available.\n"
        "- Include all major news from 2023-2025 — achievements, layoffs, or scandals — as part of the summary if available.\n"
        "- Use casual, clear language — like you are chatting with a friend.\n"
        "- You can be witty, but keep it subtle. Avoid cute metaphors or quirky jokes.\n"
        "- Be honest if something feels vague, sketchy, or impressive — but stay polite.\n"
        "- Don't make things up. If something is unclear or missing, say so.\n"
        "- Avoid fluff and corporate speak.\n"
        "- End with a quick verdict like 'seems solid' or 'meh, maybe skip it'.\n\n"
        f"Note: Only {available_sources} out of 4 data sources are available. Focus on what you know and be clear about what information is missing.\n\n"
        "Then return a Reputato Score between 1 and 5 (as a number, not text)."
    )

    try:
        result = await summarizer_agent.run(prompt)
        result.output.summary = clean_summary(result.output.summary)
        logger.info(
            f"Successfully generated summary for {company_name} with rating {result.output.rating}"
        )
        return result.output
    except Exception as e:
        logger.error(
            f"Error generating summary for {company_name}: {str(e)}", exc_info=True
        )
        raise
