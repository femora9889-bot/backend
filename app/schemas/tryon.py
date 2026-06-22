from pydantic import BaseModel


class TryOnRequest(BaseModel):
    product_id: str
    variant_id: str


class FitResult(BaseModel):
    score: float
    assessment: str
    recommended_size: str | None = None
    warning: str | None = None


class TryOnResponse(BaseModel):
    session_id: str
    result_url: str | None
    fit: FitResult
