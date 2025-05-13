from fastapi import FastAPI, HTTPException
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai import Agent
from dotenv import load_dotenv
import os
from pydantic_ai.settings import ModelSettings
import logfire

from contextlib import AsyncExitStack

stack = AsyncExitStack()

logfire.configure(token="pylf_v1_us_0Qcqm1QV8zKqS397lY2jcMv8VXtGcP5kBvgKcPQMmZQS")

logfire.instrument_mcp()
logfire.instrument_pydantic_ai()

load_dotenv()
app = FastAPI()
model = "openai:gpt-4.1-mini"

# MCP сервер
glassdoor_server = MCPServerStdio(
    command="npx",
    args=["@brightdata/mcp"],
    env={
        "API_TOKEN": os.getenv("BRIGHTDATA_API_TOKEN"),
        "WEB_UNLOCKER_ZONE": os.getenv("BRIGHTDATA_GLASSDOOR_UNLOCKER_ZONE"),
        "BROWSER_AUTH": os.getenv("BROWSER_AUTH_GLASSDOOR", ""),
    },
)

system_prompt = "You are a tool-using agent connected to Bright Data's MCP server. "

REQUEST_TIMEOUT = 120

# Агент
glassdoor_agent = Agent(
    model,
    mcp_servers=[glassdoor_server],
    retries=1,
    system_prompt=system_prompt,
    model_settings=ModelSettings(
        request_timeout=REQUEST_TIMEOUT, max_tokens=5000
    ),  # timeout in seconds
)


# Эндпоинт
@app.get("/glassdoor")
async def analyze_company(name: str):
    prompt = "Scrap this article https://dev.to/olgabraginskaya/when-small-parquet-files-become-a-big-problem-and-how-i-ended-up-writing-a-compactor-in-pyarrow-20b6 and return it as a text without timeout, don't hung out"

    try:

        async with glassdoor_agent.run_mcp_servers():
            result = await glassdoor_agent.run(prompt)
            print(result)
            return {"result": str(result.output)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
