from pydantic_ai import Agent
from app.models import LinkedInProfile, SummaryOutput, GlassdoorProfile, CrunchbaseProfile
import json

summarizer_agent = Agent(
    model="openai:gpt-4.1",
    output_type=SummaryOutput,
    system_prompt = (
    "You are an OSINT analyst who writes honest and useful summaries of companies for job seekers. "
    "Imagine a friend asked you: 'Should I even consider applying here?' "
    "You write in natural, informal language — short, direct, and with a dry sense of humor. "
    "Your job is to quickly describe what the company does, how big it is, how stable it seems, and what kind of experience to expect. "
    "You are re allowed to be skeptical if something feels off — say so. "
    "Avoid corporate jargon, fake positivity, or vague statements. "
    "Write 10-15 short sentences max. Be critical when needed. This is for people who value honest, no-bullshit career advice."
)
)

async def summarize_company(company_name: str, linkedin: LinkedInProfile, glassdoor: GlassdoorProfile, crunchbase: CrunchbaseProfile) -> str:

    linkedin_json = json.dumps(linkedin.model_dump(), indent=2)
    glassdoor_json = json.dumps(glassdoor.model_dump(), indent=2)
    crunchbase_json = json.dumps(crunchbase.model_dump(), indent=2)

    prompt = (
        f"You're evaluating a company called '{company_name}' for a curious job seeker.\n\n"
        f"Here is LinkedIn data:\n{linkedin_json}\n\n"
        f"Here is Glassdoor data:\n{glassdoor_json}\n\n"
        f"Here is Crunchbase data:\n{crunchbase_json}\n\n"
        "Write a short, honest summary based on these sources:\n"
        "- Say clearly what the company does, how big it is, and where it's located.\n"
        "- Mention the founding year and funding stage (like 'Series C').\n"
        "- Highlight Glassdoor rating and recent pros/cons from employees.\n"
        "- List all known investors by name.\n"
        "- Mention key people (especially founders, CTOs, or execs) if available.\n"
        "- Use casual, clear language — like you are chatting with a friend.\n"
        "- Be honest if something feels vague, sketchy, or impressive — but stay polite.\n"
        "- Don't make things up. If something is unclear or missing, say so.\n"
        "- Avoid fluff and corporate speak. Keep it under 5 sentences.\n"
        "- End with a quick verdict like 'seems solid' or 'meh, maybe skip it'."
    )

    result = await summarizer_agent.run(prompt)
    return result.output.summary
