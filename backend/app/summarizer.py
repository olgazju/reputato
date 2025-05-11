import openai
import os
import json
from dotenv import load_dotenv
import time

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

async def summarize_company(company_name: str, raw_data: dict) -> str:
    '''prompt = (
        f"Here is some LinkedIn data for {company_name}: {json.dumps(raw_data)}.\n"
        "Write a short summary for a job seeker, explaining how big the company is, "
        "and whether it looks established or early-stage. Keep it friendly and informative."
    )

    completion = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You summarize company profiles for job seekers."},
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content.strip()'''
    time.sleep(5)
    return f"This is a summary of {company_name}"
