import sys
print(sys.path)

from fastapi import FastAPI, Query
from app.models import CompanyResponse
from app.rating import generate_rating

from app.mcp_client import fetch_linkedin_data
from app.summarizer import summarize_company


app = FastAPI()

@app.get("/analyze_company", response_model=CompanyResponse)
async def analyze_company(name: str = Query(..., description="Company name")):
    #raw_data = await fetch_linkedin_data(name)
    raw_data = "some json"

    if not raw_data:
        return CompanyResponse(summary="Could not retrieve company data.", rating=0)

    summary = await summarize_company(name, raw_data)
    rating = generate_rating(raw_data)

    return CompanyResponse(summary=summary, rating=rating)
