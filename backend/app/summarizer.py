from pydantic_ai import Agent
from app.models import LinkedInProfile, SummaryOutput, GlassdoorProfile
import json

summarizer_agent = Agent(
    model="openai:gpt-4o",
    output_type=SummaryOutput,
    system_prompt = (
    "You are an OSINT analyst who writes honest and useful summaries of companies for job seekers. "
    "Imagine a friend asked you: 'Should I even consider applying here?' "
    "You write in natural, informal language — short, direct, and with a dry sense of humor. "
    "Your job is to quickly describe what the company does, how big it is, how stable it seems, and what kind of experience to expect. "
    "You are re allowed to be skeptical if something feels off — say so. "
    "Avoid corporate jargon, fake positivity, or vague statements. "
    "Write 4-5 short sentences max. Be critical when needed. This is for people who value honest, no-bullshit career advice."
)
)

async def summarize_company(company_name: str, linkedin: LinkedInProfile, glassdoor: GlassdoorProfile) -> str:

    linkedin_json = json.dumps(linkedin.model_dump(), indent=2)
    glassdoor_json = json.dumps(glassdoor.model_dump(), indent=2)

    prompt = (
        f"You're evaluating a company called '{company_name}' for a curious job seeker.\n\n"
        f"Here is LinkedIn data:\n{linkedin_json}\n\n"
        f"And here is Glassdoor data:\n{glassdoor_json}\n\n"
        "Write a short, honest summary based on these sources.\n"
        "- Mention what the company does, size, location, and whether it's stable or risky.\n"
        "- Use casual, clear language like you're chatting with a friend.\n"
        "- If something seems vague, weird, or bad — say so (politely).\n"
        "- Avoid fluff, intros, or conclusions.\n"
        "- End with a casual verdict like 'seems solid' or 'eh, maybe skip it'."
    )

    result = await summarizer_agent.run(prompt)
    return result.output.summary
