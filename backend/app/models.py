from pydantic import BaseModel
from typing import Optional, List

class CompanySummaryWithRating(BaseModel):
    summary: str
    rating: int  # 1 to 5

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
    
class CrunchbaseProfile(BaseModel):
    founded: Optional[str]
    funding_round: Optional[str]
    funding_date: Optional[str]
    funding_amount: Optional[str]
    investors: Optional[list[str]]
    key_people: Optional[list[str]]

class NewsProfile(BaseModel):
    layoffs: list[str]
    scandals: list[str]
    achievements: list[str]