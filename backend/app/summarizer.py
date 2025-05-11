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

summarizer_agent = Agent(
    model="openai:gpt-4o",
    output_type=CompanySummaryWithRating,
    system_prompt=(
        "You are an OSINT analyst who writes honest and useful summaries of companies for job seekers. "
        "Imagine a friend asked you: 'Should I even consider applying here?' "
        "You write in natural, informal language — short, direct, and with a dry sense of humor. "
        "Your job is to quickly describe what the company does, how big it is, how stable it seems, and what kind of experience to expect. "
        "You are re allowed to be skeptical if something feels off — say so. "
        "Avoid corporate jargon, fake positivity, or vague statements. "
        "Write 15-20 short sentences max. Be critical when needed. This is for people who value honest, no-bullshit career advice."
        "After the summary, assign a Reputato Score (1 to 5), where 5 is excellent and 1 means 'run away'."
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


async def summarize_company(
    company_name: str,
    linkedin: LinkedInProfile,
    glassdoor: GlassdoorProfile,
    crunchbase: CrunchbaseProfile,
    news: NewsProfile,
) -> CompanySummaryWithRating:

    linkedin_json = json.dumps(linkedin.model_dump(), indent=2)
    glassdoor_json = json.dumps(glassdoor.model_dump(), indent=2)
    crunchbase_json = json.dumps(crunchbase.model_dump(), indent=2)
    news_json = json.dumps(news.model_dump(), indent=2)

    prompt = (
        f"You're evaluating a company called '{company_name}' for a curious job seeker.\n\n"
        f"Here is LinkedIn data:\n{linkedin_json}\n\n"
        f"Here is Glassdoor data (only reviews from 2025 and 2024 were considered):\n{glassdoor_json}\n\n"
        f"Here is Crunchbase data:\n{crunchbase_json}\n\n"
        f"Here is recent news (2023-2025):\n{news_json}\n\n"
        "Write honest summary based on these sources:\n"
        "- Say clearly what the company does, how big it is, and where it's located.\n"
        "- Mention the founding year and funding stage (like 'Series C').\n"
        "- Highlight Glassdoor rating and recent pros/cons from employees (from 2025 and 2024 only).\n"
        "- List major known investors by name.\n"
        "- Mention key people (especially founders, CTOs, or execs) if available.\n"
        "- Include all major news from 2023-2025 — achievements, layoffs, or scandals — as part of the summary.\n"
        "- Use casual, clear language — like you are chatting with a friend.\n"
        "- You can be witty, but keep it subtle. Avoid cute metaphors or quirky jokes.\n"
        "- Be honest if something feels vague, sketchy, or impressive — but stay polite.\n"
        "- Don't make things up. If something is unclear or missing, say so.\n"
        "- Avoid fluff and corporate speak.\n"
        "- End with a quick verdict like 'seems solid' or 'meh, maybe skip it'.\n\n"
        "Then return a Reputato Score between 1 and 5 (as a number, not text)."
    )

    result = await summarizer_agent.run(prompt)
    result.output.summary = clean_summary(result.output.summary)

    print(result.output)
    return result.output
