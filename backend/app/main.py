from fastapi import FastAPI, Query
from app.models import CompanyResponse
from app.mcp_client import fetch_linkedin_data, fetch_glassdoor_data, fetch_crunchbase_data
from app.summarizer import summarize_company
import asyncio

app = FastAPI()

@app.get("/analyze_company", response_model=CompanyResponse)
async def analyze_company(name: str = Query(..., description="Company name")):

    linkedin_task = asyncio.create_task(fetch_linkedin_data(name))
    glassdoor_task = asyncio.create_task(fetch_glassdoor_data(name))
    crunchbase_task = asyncio.create_task(fetch_crunchbase_data(name))

    linkedin, glassdoor, crunchbase = await asyncio.gather(linkedin_task, glassdoor_task, crunchbase_task)
    #glassdoor = await fetch_glassdoor_data(name)
    #linkedin = await fetch_linkedin_data(name)
    print("linkedin", linkedin)
    print("glassdoor", glassdoor)
    print("crunchbase", crunchbase)

    summary_result = await summarize_company(name, linkedin, glassdoor, crunchbase)

    return CompanyResponse(
        summary=summary_result.summary,
        rating=summary_result.rating
    )