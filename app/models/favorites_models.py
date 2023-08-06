from pydantic import BaseModel


class FavoritesResponse(BaseModel):
    id: int
    address: str
