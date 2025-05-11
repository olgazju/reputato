import os
import re
import json
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

load_dotenv()

BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_TOKEN")
WEB_UNLOCKER_ZONE = os.getenv("WEB_UNLOCKER_ZONE")

brightdata_server = MCPServerStdio(
    command="npx",
    args=["@brightdata/mcp"],
    env={
        "API_TOKEN": BRIGHTDATA_API_KEY,
        "WEB_UNLOCKER_ZONE": WEB_UNLOCKER_ZONE,
    }
)

agent = Agent("openai:gpt-4o-mini", mcp_servers=[brightdata_server])

def extract_json(text):
    try:
        match = re.search(r"{.*}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        return None
    return None

async def fetch_linkedin_data(company_name: str) -> dict:
    prompt = (
        f"Search for the LinkedIn profile of the company '{company_name}'. "
        "Once you find the correct page, open it and extract the following information:\n"
        "- Number of employees (as listed on the LinkedIn profile)\n"
        "Return the result as structured JSON only. Do not include HTML, markdown or explanation. "
        "If the company page cannot be found, return null."
    )
    async with agent.run_mcp_servers():
        result = await agent.run(prompt)
        return extract_json(result.output)
