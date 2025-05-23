from fastapi import FastAPI, Query, HTTPException
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio
import os
import logging

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.mcp import MCPServerStdio

from app.models import (
    CompanyResponse,
    LinkedInProfile,
    GlassdoorProfile,
    CrunchbaseProfile,
    NewsProfile,
)
from app.summarizer import summarize_company
import logfire

# Load env and configure logging
load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_mcp()
logfire.instrument_pydantic_ai()

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s :: %(levelname)s :: %(processName)s :: %(threadName)s :: %(filename)s :: %(funcName)s :: %(message)s",
)
logger = logging.getLogger(__name__)

# Validate required environment vars
REQUIRED_VARS = [
    "BRIGHTDATA_API_TOKEN",
    "BRIGHTDATA_GLASSDOOR_UNLOCKER_ZONE",
    "BRIGHTDATA_LINKEDIN_UNLOCKER_ZONE",
    "BRIGHTDATA_CRUNCHBASE_UNLOCKER_ZONE",
    "BRIGHTDATA_NEWS_UNLOCKER_ZONE",
    "OPENAI_API_KEY",
]
missing_vars = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing_vars:
    raise EnvironmentError(f"Missing env vars: {', '.join(missing_vars)}")

model = "openai:gpt-4.1-mini"

REQUEST_TIMEOUT = 300
DATA_FETCH_TIMEOUT = 300
SUMMARIZATION_TIMEOUT = 120

# Shared system prompt
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
    "- `web_data_linkedin_company_profile`\n"
    "Do not invoke any other tools even if they are available."
)

# Initialize MCP servers
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

# Initialize agents
linkedin_agent = Agent(
    model,
    output_type=LinkedInProfile,
    mcp_servers=[linkedin_server],
    retries=1,
    system_prompt=system_prompt,
    model_settings=ModelSettings(request_timeout=REQUEST_TIMEOUT, max_tokens=2048),
)

glassdoor_agent = Agent(
    model,
    output_type=GlassdoorProfile,
    mcp_servers=[glassdoor_server],
    retries=1,
    system_prompt=system_prompt,
    model_settings=ModelSettings(request_timeout=REQUEST_TIMEOUT, max_tokens=2048),
)

crunchbase_agent = Agent(
    model,
    output_type=CrunchbaseProfile,
    mcp_servers=[crunchbase_server],
    retries=1,
    system_prompt=system_prompt,
    model_settings=ModelSettings(request_timeout=REQUEST_TIMEOUT, max_tokens=2048),
)

news_agent = Agent(
    model,
    output_type=NewsProfile,
    mcp_servers=[news_server],
    retries=2,
    system_prompt=(
        "You are a tool-using OSINT agent connected to Bright Data's MCP server. "
        "Your job is to search for public news related to companies from 2023-2025. "
        "You must identify any major events including layoffs, scandals, or achievements. "
        "Only include verifiable news events. Do not hallucinate or assume. "
        "Use search tools and extract only clearly dated, relevant headlines. "
        "Return up to 3 short bullet summaries per category."
    ),
    model_settings=ModelSettings(request_timeout=REQUEST_TIMEOUT, max_tokens=2048),
)


# Lifespan: keep MCP servers running between requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    server_ctxs = [
        linkedin_agent.run_mcp_servers(),
        glassdoor_agent.run_mcp_servers(),
        crunchbase_agent.run_mcp_servers(),
        news_agent.run_mcp_servers(),
    ]
    for ctx in server_ctxs:
        await ctx.__aenter__()
    try:
        yield
    finally:
        for ctx in server_ctxs:
            await ctx.__aexit__(None, None, None)


app = FastAPI(lifespan=lifespan)


@app.get("/analyze_company", response_model=CompanyResponse)
async def analyze_company(name: str = Query(..., description="Company name")):
    logger.info(f"Analyzing company: {name}")
    try:
        linkedin_prompt = (
            f"Your task is to find the LinkedIn profile for the company '{name}' and extract specific structured data.\n\n"
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

        glassdoor_prompt = (
            f"Your task is to find the Glassdoor profile for the company '{name}' and extract specific structured data.\n\n"
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

        crunchbase_prompt = (
            f"Search for the Crunchbase profile of the company '{name}'. "
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

        news_prompt = (
            f"Search for news about the company '{name}' from 2023, 2024, and 2025.\n\n"
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

        results = await asyncio.wait_for(
            asyncio.gather(
                linkedin_agent.run(linkedin_prompt),
                glassdoor_agent.run(glassdoor_prompt),
                crunchbase_agent.run(crunchbase_prompt),
                news_agent.run(news_prompt),
                return_exceptions=True,
            ),
            timeout=DATA_FETCH_TIMEOUT,
        )

        linkedin, glassdoor, crunchbase, news = [
            r.output if not isinstance(r, Exception) else None for r in results
        ]

        if all(x is None for x in [linkedin, glassdoor, crunchbase, news]):
            return CompanyResponse(
                summary="Unable to gather any information about this company.", rating=1
            )

        summary_result = await asyncio.wait_for(
            summarize_company(name, linkedin, glassdoor, crunchbase, news),
            timeout=SUMMARIZATION_TIMEOUT,
        )

        return CompanyResponse(
            summary=summary_result.summary, rating=summary_result.rating
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout during summarization.")
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
