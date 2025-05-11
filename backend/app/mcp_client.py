import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.exceptions import ModelHTTPError
from typing import Optional
from app.models import LinkedInProfile, GlassdoorProfile, CrunchbaseProfile, NewsProfile
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def log_execution_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}",
                exc_info=True,
            )
            raise

    return wrapper


def validate_env_vars():
    required_vars = [
        "BRIGHTDATA_API_TOKEN",
        "BRIGHTDATA_GLASSDOOR_UNLOCKER_ZONE",
        "BRIGHTDATA_LINKEDIN_UNLOCKER_ZONE",
        "BRIGHTDATA_CRUNCHBASE_UNLOCKER_ZONE",
        "BRIGHTDATA_NEWS_UNLOCKER_ZONE",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


validate_env_vars()

# Initialize MCP servers
try:
    glassdoor_server = MCPServerStdio(
        command="npx",
        args=["@brightdata/mcp"],
        env={
            "API_TOKEN": os.getenv("BRIGHTDATA_API_TOKEN"),
            "WEB_UNLOCKER_ZONE": os.getenv("BRIGHTDATA_GLASSDOOR_UNLOCKER_ZONE"),
            "BROWSER_AUTH": os.getenv("BROWSER_AUTH_GLASSDOOR", ""),
        },
    )

    linkedin_server = MCPServerStdio(
        command="npx",
        args=["@brightdata/mcp"],
        env={
            "API_TOKEN": os.getenv("BRIGHTDATA_API_TOKEN"),
            "WEB_UNLOCKER_ZONE": os.getenv("BRIGHTDATA_LINKEDIN_UNLOCKER_ZONE"),
            "BROWSER_AUTH": os.getenv("BROWSER_AUTH_LINKEDIN", ""),
        },
    )

    crunchbase_server = MCPServerStdio(
        command="npx",
        args=["@brightdata/mcp"],
        env={
            "API_TOKEN": os.getenv("BRIGHTDATA_API_TOKEN"),
            "WEB_UNLOCKER_ZONE": os.getenv("BRIGHTDATA_CRUNCHBASE_UNLOCKER_ZONE"),
            "BROWSER_AUTH": os.getenv("BROWSER_AUTH_CRUNCHBASE", ""),
        },
    )

    news_server = MCPServerStdio(
        command="npx",
        args=["@brightdata/mcp"],
        env={
            "API_TOKEN": os.getenv("BRIGHTDATA_API_TOKEN"),
            "WEB_UNLOCKER_ZONE": os.getenv("BRIGHTDATA_NEWS_UNLOCKER_ZONE"),
            "BROWSER_AUTH": os.getenv("BROWSER_AUTH_NEWS", ""),
        },
    )
    logger.info("Successfully initialized all MCP servers")
except Exception:
    logger.error("Failed to initialize MCP servers", exc_info=True)
    raise

system_prompt = (
    "You are a tool-using agent connected to Bright Data's MCP server. "
    "You act as an OSINT investigator whose job is to evaluate companies based on public information. "
    "Your goal is to help users understand whether a company is reputable or potentially suspicious. "
    "You always use Bright Data real-time tools to search, navigate, and extract data from company profiles. "
    "You never guess or assume anything. "
    "Company name matching must be case-sensitive and exact. Do not return data for similarly named or uppercase-variant companies."
    "Only use the following tools during your investigation:\n"
    "- `search_engine`\n"
    "- `scrape_as_markdown`\n"
    "- `scrape_as_html`\n"
    "- `scraping_browser_navigate`\n"
    "- `scraping_browser_get_text`\n"
    "- `scraping_browser_click`\n"
    "- `scraping_browser_links`\n"
    "Do not invoke any other tools even if they are available."
)

model = "openai:gpt-4.1-mini"

# Initialize agents with proper error handling
try:
    linkedin_agent = Agent(
        model,
        output_type=LinkedInProfile,
        mcp_servers=[linkedin_server],
        retries=1,
        system_prompt=system_prompt,
        model_settings=ModelSettings(request_timeout=300),  # timeout in seconds
    )

    glassdoor_agent = Agent(
        model,
        output_type=GlassdoorProfile,
        mcp_servers=[glassdoor_server],
        retries=1,
        system_prompt=system_prompt,
        model_settings=ModelSettings(request_timeout=300),  # timeout in seconds
    )

    crunchbase_agent = Agent(
        model,
        output_type=CrunchbaseProfile,
        mcp_servers=[crunchbase_server],
        retries=1,
        system_prompt=system_prompt,
        model_settings=ModelSettings(request_timeout=300),  # timeout in seconds
    )

    news_agent = Agent(
        "openai:gpt-4o-mini",
        output_type=NewsProfile,
        mcp_servers=[news_server],
        retries=2,
        system_prompt=(
            "You are a tool-using OSINT agent connected to Bright Data's MCP server. "
            "Your job is to search for public news related to companies from 2023–2025. "
            "You must identify any major events including layoffs, scandals, or achievements. "
            "Only include verifiable news events. Do not hallucinate or assume. "
            "Use search tools and extract only clearly dated, relevant headlines. "
            "Return up to 3 short bullet summaries per category."
        ),
        model_settings=ModelSettings(request_timeout=300),  # timeout in seconds
    )
    logger.info("Successfully initialized all agents")
except Exception:
    logger.error("Failed to initialize agents", exc_info=True)
    raise


@log_execution_time
async def fetch_linkedin_data(company_name: str) -> Optional[LinkedInProfile]:
    logger.info(f"Fetching LinkedIn data for company: {company_name}")
    prompt = (
        f"Your task is to find the LinkedIn profile for the company '{company_name}' and extract specific structured data.\n\n"
        "Use the `web_data_linkedin_company_profile` tool if available to extract the following fields:\n"
        "- Company name\n"
        "- Company description (short summary of what the company does)\n"
        "- Number of employees (as listed on the LinkedIn profile)\n"
        "- Linkedin company profile url\n"
        "- Headquarters address\n"
        "- Year the company was founded (if available)\n"
        "- Industry or sector (e.g., 'Software', 'Healthcare')\n"
        "- Company website\n"
        "If the structured LinkedIn tool is unavailable or insufficient, use the following tools in order:\n"
        "1. `scraping_browser_navigate` — to visit the LinkedIn company page\n"
        "2. `scraping_browser_get_text` — to extract visible page text\n"
        "3. `scraping_browser_links` and `scraping_browser_click` — to navigate if needed\n\n"
        "Return ONLY a JSON object with the following keys:\n"
        "{\n"
        '  "company_name": str,\n'
        '  "description": str,\n'
        '  "number_of_employees": str,\n'
        '  "linkedin_url": str,\n'
        '  "headquarters": str,\n'
        '  "founded": str or null,\n'
        '  "industry": str,\n'
        '  "website": str,\n'
        "}\n\n"
        "Do not include raw HTML, markdown, explanations, or other fields. "
        "If a field is missing, use null for that field. If the company cannot be found at all, return null."
    )

    try:
        async with linkedin_agent.run_mcp_servers():
            result = await linkedin_agent.run(prompt)
            logger.info(f"Successfully fetched LinkedIn data for {company_name}")
            return result.output
    except ModelHTTPError as e:
        logger.error(f"LinkedIn API error for {company_name}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error fetching LinkedIn data for {company_name}: {str(e)}",
            exc_info=True,
        )
        return None


@log_execution_time
async def fetch_glassdoor_data(company_name: str) -> Optional[GlassdoorProfile]:
    logger.info(f"Fetching Glassdoor data for company: {company_name}")
    prompt = (
        f"Your task is to find the Glassdoor profile for the company '{company_name}' and extract specific structured data.\n\n"
        "Extract the following fields:\n"
        "- Overall company rating (float, out of 5)\n"
        "- Total number of employee reviews\n"
        "- A short summary of the top 5 pros and cons from employee reviews posted in 2025 or 2024 only\n\n"
        "Use the following tools in order:\n"
        "1. `scraping_browser_navigate` — to go to the Glassdoor company page\n"
        "2. `scraping_browser_get_text` — to extract visible content\n"
        "3. `scraping_browser_links` and `scraping_browser_click` — to find and open the review section if necessary\n\n"
        "Return ONLY a JSON object with the following keys:\n"
        "{\n"
        '  "rating": float,\n'
        '  "num_reviews": int,\n'
        '  "review_summary": str\n'
        "}\n\n"
        "Only use reviews from 2025 or 2024. Do not include older reviews.\n"
        "Do not include HTML, markdown, or explanations"
        "If a field is missing, use null for that field. If the company cannot be found at all, return null."
    )
    try:
        async with glassdoor_agent.run_mcp_servers():
            result = await glassdoor_agent.run(prompt)
            logger.info(f"Successfully fetched Glassdoor data for {company_name}")
            return result.output
    except ModelHTTPError as e:
        logger.error(f"Glassdoor API error for {company_name}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error fetching Glassdoor data for {company_name}: {str(e)}",
            exc_info=True,
        )
        return None


@log_execution_time
async def fetch_crunchbase_data(company_name: str) -> Optional[CrunchbaseProfile]:
    logger.info(f"Fetching Crunchbase data for company: {company_name}")
    prompt = (
        f"Search for the Crunchbase profile of the company '{company_name}'. "
        "Once you find the correct page, extract the following information:\n"
        "- Year founded (as a string or null)\n"
        "- Latest funding round name\n"
        "- Funding round date\n"
        "- Funding amount\n"
        "- List of known investors (as strings)\n"
        "- Key people (e.g., founders, CEOs, etc)\n\n"
        "Use the following tools in order:\n"
        "1. `scraping_browser_navigate`\n"
        "2. `scraping_browser_get_text`\n"
        "3. `scraping_browser_links` and `scraping_browser_click`\n\n"
        "Return ONLY a JSON object with the following keys:\n"
        "{\n"
        '  "founded": str or null,\n'
        '  "funding_round": str or null,\n'
        '  "funding_date": str or null,\n'
        '  "funding_amount": str or null,\n'
        '  "investors": list[str] or null,\n'
        '  "key_people": list[str] or null\n'
        "}\n\n"
        "Do not include HTML, markdown, or explanations"
        "If a field is missing, use null for that field. If the company cannot be found at all, return null."
    )
    try:
        async with crunchbase_agent.run_mcp_servers():
            result = await crunchbase_agent.run(prompt)
            logger.info(f"Successfully fetched Crunchbase data for {company_name}")
            return result.output
    except ModelHTTPError as e:
        logger.error(
            f"Crunchbase API error for {company_name}: {str(e)}", exc_info=True
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error fetching Crunchbase data for {company_name}: {str(e)}",
            exc_info=True,
        )
        return None


@log_execution_time
async def fetch_news_data(company_name: str) -> Optional[NewsProfile]:
    logger.info(f"Fetching news data for company: {company_name}")
    prompt = (
        f"Search for news about the company '{company_name}' from 2023, 2024, and 2025.\n\n"
        "Extract the following if available:\n"
        "- Layoffs: Dates and brief summaries of any layoff announcements.\n"
        "- Scandals: Brief, neutral headlines about controversies or investigations.\n"
        "- Achievements: Public product launches, funding milestones, acquisitions, or major hires.\n\n"
        "Return a structured JSON object with keys:\n"
        "{\n"
        "  'layoffs': list[str],\n"
        "  'scandals': list[str],\n"
        "  'achievements': list[str]\n"
        "}\n\n"
        "If no news is found in a category, return an empty list. Do not include HTML, explanations, or irrelevant information."
    )
    try:
        async with news_agent.run_mcp_servers():
            result = await news_agent.run(prompt)
            logger.info(f"Successfully fetched news data for {company_name}")
            return result.output
    except ModelHTTPError as e:
        logger.error(f"News API error for {company_name}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error fetching news data for {company_name}: {str(e)}",
            exc_info=True,
        )
        return None
