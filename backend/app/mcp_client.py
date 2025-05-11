import os
import json
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.exceptions import ModelHTTPError
from typing import Optional
from app.models import LinkedInProfile, GlassdoorProfile, CrunchbaseProfile

load_dotenv()


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

linkedin_agent = Agent(
    "openai:gpt-4.1-mini",
    output_type=LinkedInProfile,
    mcp_servers=[linkedin_server],
    retries=1,
    system_prompt=system_prompt,
    model_settings=ModelSettings(
        request_timeout=120  # timeout in seconds
    )
)

async def fetch_linkedin_data(company_name: str) -> Optional[LinkedInProfile]:
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
        "  \"company_name\": str,\n"
        "  \"description\": str,\n"
        "  \"number_of_employees\": str,\n"
        "  \"linkedin_url\": str,\n"
        "  \"headquarters\": str,\n"
        "  \"founded\": str or null,\n"
        "  \"industry\": str,\n"
        "  \"website\": str,\n"
        "}\n\n"
        "Do not include raw HTML, markdown, explanations, or other fields. "
        "If a field is missing, use null for that field. If the company cannot be found at all, return null."
    )

    try:
        async with linkedin_agent.run_mcp_servers():
            result = await linkedin_agent.run(prompt)
            return result.output
    except ModelHTTPError as e:
        print(f"Linkedin error] {e}")
        return None

glassdoor_agent = Agent(
    "openai:gpt-4.1-mini",
    output_type=GlassdoorProfile,
    mcp_servers=[glassdoor_server],
    retries=1,
    system_prompt=system_prompt,
    model_settings=ModelSettings(
        request_timeout=120  # timeout in seconds
    )

)

async def fetch_glassdoor_data(company_name: str) -> Optional[GlassdoorProfile]:
    prompt = (
        f"Your task is to find the Glassdoor profile for the company '{company_name}' and extract specific structured data.\n\n"
        "Extract the following fields:\n"
        "- Overall company rating (float, out of 5)\n"
        "- Total number of employee reviews\n"
        "- A short summary of the top 5 recent pros and cons from employee reviews\n\n"
        "Use the following tools in order:\n"
        "1. `scraping_browser_navigate` — to go to the Glassdoor company page\n"
        "2. `scraping_browser_get_text` — to extract visible content\n"
        "3. `scraping_browser_links` and `scraping_browser_click` — to find and open the review section if necessary\n\n"
        "Return ONLY a JSON object with the following keys:\n"
        "{\n"
        "  \"rating\": float,\n"
        "  \"num_reviews\": int,\n"
        "  \"review_summary\": str\n"
        "}\n\n"
        "Do not include HTML, markdown, or explanations"
        "If a field is missing, use null for that field. If the company cannot be found at all, return null."
    )
    try:
        async with glassdoor_agent.run_mcp_servers():
            result = await glassdoor_agent.run(prompt)
            return result.output
    except ModelHTTPError as e:
        print(f"[Glassdoor error] {e}")
        return None
    
crunchbase_agent = Agent(
    "openai:gpt-4.1-mini",
    output_type=CrunchbaseProfile,
    mcp_servers=[crunchbase_server],
    retries=1,
    system_prompt=system_prompt,
    model_settings=ModelSettings(
        request_timeout=120  # timeout in seconds
    )
)

async def fetch_crunchbase_data(company_name: str) -> Optional[CrunchbaseProfile]:
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
        "  \"founded\": str or null,\n"
        "  \"funding_round\": str or null,\n"
        "  \"funding_date\": str or null,\n"
        "  \"funding_amount\": str or null,\n"
        "  \"investors\": list[str] or null,\n"
        "  \"key_people\": list[str] or null\n"
        "}\n\n"
        "Do not include HTML, markdown, or explanations"
        "If a field is missing, use null for that field. If the company cannot be found at all, return null."
    )
    try:
        async with crunchbase_agent.run_mcp_servers():
            result = await crunchbase_agent.run(prompt)
            return result.output
    except ModelHTTPError as e:
        print(f"Crunchbase error] {e}")
        return None