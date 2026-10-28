from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator

RATINGS = {"One", "Two", "Three", "Four", "Five"}


class Book(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: HttpUrl
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def must_be_https(cls, v):
        if not str(v).startswith("https://"):
            raise ValueError("URL must start with https://")
        return v

    @field_validator("rating_text")
    @classmethod
    def valid_rating(cls, v):
        if v not in RATINGS:
            raise ValueError(f"unexpected rating {v!r}")
        return v

    @field_validator("price_gbp")
    @classmethod
    def positive_price(cls, v):
        if v <= 0:
            raise ValueError("price must be positive")
        return v
