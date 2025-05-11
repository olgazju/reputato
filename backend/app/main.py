import asyncio
from fastapi import FastAPI, Query
from app.models import CompanyResponse
from app.rating import generate_rating

from app.mcp_client import fetch_linkedin_data, fetch_glassdoor_data
from app.summarizer import summarize_company


app = FastAPI()

@app.get("/analyze_company", response_model=CompanyResponse)
async def analyze_company(name: str = Query(..., description="Company name")):
    #linkedin_task = fetch_linkedin_data(name)
    #glassdoor_task = fetch_glassdoor_data(name)

    #linkedin, glassdoor = await asyncio.gather(
    #    linkedin_task, glassdoor_task
    #)
    linkedin = await fetch_linkedin_data(name)
    glassdoor = await fetch_glassdoor_data(name)

    summary = await summarize_company(company_name=name, linkedin=linkedin, glassdoor=glassdoor)
    rating = generate_rating(linkedin=linkedin, glassdoor=glassdoor)

    return CompanyResponse(summary=summary, rating=rating)
