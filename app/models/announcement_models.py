from pydantic import BaseModel


class CreateAnnounceRequest(BaseModel):
    type: str
    price: int
    address: str
    area: str
    rooms_count: int
    description: str


class AnnounceResponse(BaseModel):
    id: int
    type: str
    price: int
    address: str
    area: str
    rooms_count: int
    description: str
    owner_id: int
    total_comments: int


class AnnounceResponseFilter(BaseModel):
    id: int
    type: str
    price: int
    address: str
    area: str
    rooms_count: int
