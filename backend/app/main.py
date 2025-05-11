from fastapi import FastAPI, Query, HTTPException
from app.models import CompanyResponse
from app.mcp_client import (
    fetch_linkedin_data,
    fetch_glassdoor_data,
    fetch_crunchbase_data,
    fetch_news_data,
)
from app.summarizer import summarize_company
import asyncio
import logging
import os

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s :: %(levelname)s :: %(processName)s :: %(threadName)s :: %(filename)s :: %(funcName)s :: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/analyze_company", response_model=CompanyResponse)
async def analyze_company(name: str = Query(..., description="Company name")):
    logger.info(f"Starting company analysis for: {name}")
    try:

        linkedin_task = asyncio.create_task(fetch_linkedin_data(name))
        glassdoor_task = asyncio.create_task(fetch_glassdoor_data(name))
        crunchbase_task = asyncio.create_task(fetch_crunchbase_data(name))
        news_task = asyncio.create_task(fetch_news_data(name))

        try:
            linkedin, glassdoor, crunchbase, news = await asyncio.wait_for(
                asyncio.gather(
                    linkedin_task,
                    glassdoor_task,
                    crunchbase_task,
                    news_task,
                    return_exceptions=True,
                ),
                timeout=300,
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching data for company: {name}")
            # If timeout occurs, cancel all tasks
            for task in [linkedin_task, glassdoor_task, crunchbase_task, news_task]:
                if not task.done():
                    task.cancel()
            raise HTTPException(
                status_code=504, detail="Request timeout while fetching company data"
            )

        # Handle exceptions from individual tasks
        linkedin = linkedin if not isinstance(linkedin, Exception) else None
        glassdoor = glassdoor if not isinstance(glassdoor, Exception) else None
        crunchbase = crunchbase if not isinstance(crunchbase, Exception) else None
        news = news if not isinstance(news, Exception) else None

        logger.info(
            f"Data fetch results for {name}: LinkedIn: {'Success' if linkedin else 'Failed'}, "
            f"Glassdoor: {'Success' if glassdoor else 'Failed'}, "
            f"Crunchbase: {'Success' if crunchbase else 'Failed'}, "
            f"News: {'Success' if news else 'Failed'}"
        )

        if all(x is None for x in [linkedin, glassdoor, crunchbase, news]):
            logger.warning(f"All data sources failed for company: {name}")
            return CompanyResponse(
                summary="Unable to gather any information about this company. Please try again later or verify the company name.",
                rating=1,
            )

        logger.info(f"Generating summary for {name} with available data sources")
        summary_result = await summarize_company(
            name, linkedin, glassdoor, crunchbase, news
        )

        logger.info(
            f"Successfully generated summary for {name} with rating: {summary_result.rating}"
        )
        return CompanyResponse(
            summary=summary_result.summary, rating=summary_result.rating
        )

    except Exception as e:
        logger.error(f"Error analyzing company {name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while analyzing the company: {str(e)}",
        )
