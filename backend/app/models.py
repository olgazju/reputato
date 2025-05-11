from pydantic import BaseModel

class CompanyResponse(BaseModel):
    summary: str
    rating: int
