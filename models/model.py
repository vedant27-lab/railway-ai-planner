from pydantic import BaseModel, Field
from typing import Literal

class JourneyRequest(BaseModel):
    origin: str = Field(min_length=2, max_length=20)
    destination: str = Field(min_length=2, max_length=20)
    max_transfers: int = Field(default=1, ge=0, le=5)
    preference: Literal[
        "fastest", "fewest_transfers", "safest"
    ] = "fastest"
    limit: int = Field(default=3, ge=1, le=10)

    