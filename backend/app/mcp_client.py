import os
import json
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from typing import Optional
from app.models import LinkedInProfile, GlassdoorProfile

load_dotenv()

brightdata_server = MCPServerStdio(
    command="npx",
    args=["@brightdata/mcp"],
    env={
        "API_TOKEN": os.getenv("BRIGHTDATA_API_TOKEN"),
        "WEB_UNLOCKER_ZONE": os.getenv("BRIGHTDATA_WEB_UNLOCKER_ZONE"),
        "BROWSER_AUTH": os.getenv("BROWSER_AUTH", ""),
    },
)

system_prompt = (
        "You are a tool-using agent connected to Bright Data's MCP server. "
        "You act as an OSINT investigator whose job is to evaluate companies based on public information. "
        "Your goal is to help users understand whether a company is reputable or potentially suspicious. "
        "You always use Bright Data real-time tools to search, navigate, and extract data from company profiles. "
        "You never guess or assume anything. "
        "Company name matching must be case-sensitive and exact. Do not return data for similarly named or uppercase-variant companies."
    )

linkedin_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=LinkedInProfile,
    mcp_servers=[brightdata_server],
    retries=5,
    system_prompt=system_prompt
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

    async with linkedin_agent.run_mcp_servers():
        result = await linkedin_agent.run(prompt)
        return result.output

glassdoor_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=GlassdoorProfile,
    mcp_servers=[brightdata_server],
    retries=5,
    system_prompt=system_prompt
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
    async with glassdoor_agent.run_mcp_servers():
        result = await glassdoor_agent.run(prompt)
        return result.output