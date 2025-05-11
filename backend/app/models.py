from pydantic import BaseModel
from typing import Optional, List

class SummaryOutput(BaseModel):
    summary: str

class CompanyResponse(BaseModel):
    summary: str
    rating: int

class LinkedInProfile(BaseModel):
    company_name: str
    description: Optional[str]
    number_of_employees: Optional[str]
    linkedin_url: Optional[str]
    headquarters: Optional[str]
    founded: Optional[str]
    industry: Optional[str]
    website: Optional[str]

class GlassdoorProfile(BaseModel):
    rating: Optional[float]
    num_reviews: Optional[int]
    review_summary: Optional[str]
    