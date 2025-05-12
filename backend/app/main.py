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

# Constants for timeouts
DATA_FETCH_TIMEOUT = 300  # 5 minutes for data fetching
SUMMARIZATION_TIMEOUT = 300  # 5 minutes for summarization


@app.get("/analyze_company", response_model=CompanyResponse)
async def analyze_company(name: str = Query(..., description="Company name")):
    logger.info(f"Starting company analysis for: {name}")
    try:

        tasks = {
            "linkedin": asyncio.create_task(fetch_linkedin_data(name)),
            "glassdoor": asyncio.create_task(fetch_glassdoor_data(name)),
            "crunchbase": asyncio.create_task(fetch_crunchbase_data(name)),
            "news": asyncio.create_task(fetch_news_data(name)),
        }

        done, pending = await asyncio.wait(tasks.values(), timeout=DATA_FETCH_TIMEOUT)

        results = {}
        for key, task in tasks.items():
            if task in done:
                try:
                    results[key] = await task
                    logger.info(f"{key} task completed")
                except Exception as e:
                    results[key] = None
                    logger.warning(f"{key} failed: {e}")
            else:
                task.cancel()
                results[key] = None
                logger.warning(f"{key} task timed out and was cancelled")

        linkedin = results["linkedin"]
        glassdoor = results["glassdoor"]
        crunchbase = results["crunchbase"]
        news = results["news"]

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

        logger.info(f"Starting summarization for {name} with available data sources")
        try:
            # Add timeout for summarization
            summary_result = await asyncio.wait_for(
                summarize_company(name, linkedin, glassdoor, crunchbase, news),
                timeout=SUMMARIZATION_TIMEOUT,
            )
            logger.info(
                f"Successfully generated summary for {name} with rating: {summary_result.rating}"
            )
            return CompanyResponse(
                summary=summary_result.summary, rating=summary_result.rating
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout during summarization for company: {name}")
            raise HTTPException(
                status_code=504,
                detail="Request timeout while generating company summary",
            )

    except Exception as e:
        logger.error(f"Error analyzing company {name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while analyzing the company: {str(e)}",
        )
